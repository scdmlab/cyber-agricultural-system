<!-- MapComponent.vue -->
<template>
  <div id="map-container">

    <ToolbarComponent
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @reset-view="resetViewToCONUS"
        @toggle-sidebar="toggleSidebar"
    />
    <transition name="sidebar">
      <div v-if="isSidebarOpen" class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <div class="resize-handle" @mousedown="startResize"></div>
        <SettingsPanel v-if="activeSidebar === 'settings'" @apply-settings="applySettings" />
        <!-- Add other sidebar components as needed -->
      </div>
    </transition>
    <div id="map" ref="mapContainer"></div>

  </div>
</template>

<script>
import { onMounted, ref, watch, computed, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import {Icon} from '@iconify/vue'
import SettingsPanel from "@/components/SettingsPanel.vue";
import ToolbarComponent from "@/components/ToolbarComponent.vue";

export default {
  name: 'MapComponent',
  components: {
    ToolbarComponent,
    SettingsPanel,
    Icon
  },
  setup() {
    const store = useStore()
    const mapContainer = ref(null)
    const map = ref(null)
    const activeSidebar = ref(null)
    const scaleControl = ref(null)
    const currentUnit = ref('metric')
    const isSidebarOpen = ref(false)
    const sidebarWidth = ref(300)
    const isResizing = ref(false)

    const mapData = computed(() => store.getters.getMapData)
    const currentProperty = computed(() => store.state.currentProperty)

    onMounted(() => {
      initializeMap()
      window.addEventListener('resize', resizeMap)
    })

    watch(mapData, (newData) => {
      if (newData && map.value) {
        updateChoropleth(newData)
      }
    })

    watch(currentProperty, () => {
      if (mapData.value && map.value) {
        updateChoropleth(mapData.value)
      }
    })

    function initializeMap() {
      map.value = new maplibregl.Map({
        container: mapContainer.value,
        style: {
          version: 8,
          sources: {
            'osm': {
              type: 'raster',
              tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: '© OpenStreetMap contributors'
            }
          },
          layers: [
            {
              id: 'osm-layer',
              type: 'raster',
              source: 'osm',
              minzoom: 0,
              maxzoom: 19
            }
          ]
        },
        center: [-93, 43],
        zoom: 5.5
      })

      map.value.on('load', () => {
        resizeMap()
        store.dispatch('fetchMapData')

        addCustomScaleControl()
        addDraggableControl(maplibregl.NavigationControl, {showCompass:false}, 'top-right');
      })

    }

    // Add scale control
    function addCustomScaleControl() {
      const CustomScaleControl = class extends maplibregl.ScaleControl {
        constructor(options) {
          super(options)
          this._unit = options.unit || 'metric'
        }

        onAdd(map) {
          const container = super.onAdd(map)

          container.addEventListener('click', () => {
            this._unit = this._unit === 'metric' ? 'imperial' : 'metric'
            this.setUnit(this._unit)
            currentUnit.value = this._unit // Update the reactive ref
          })

          container.style.cursor = 'pointer'
          return container
        }
      }

      scaleControl.value = new CustomScaleControl({
        maxWidth: 100,
        unit: currentUnit.value
      })

      map.value.addControl(scaleControl.value, 'bottom-left')

      makeDraggable(scaleControl.value)
    }

    function makeDraggable(control) {
      const container = control._container;
      if (!container) return;

      container.style.cursor = 'move';
      container.style.position = 'absolute';

      let isDragging = false;
      let startX, startY;

      container.addEventListener('mousedown', startDragging);
      document.addEventListener('mousemove', drag);
      document.addEventListener('mouseup', stopDragging);

      function startDragging(e) {
        isDragging = true;
        startX = e.clientX - container.offsetLeft;
        startY = e.clientY - container.offsetTop;
        e.preventDefault();
      }

      function drag(e) {
        if (!isDragging) return;
        const x = e.clientX - startX;
        const y = e.clientY - startY;
        container.style.left = `${x}px`;
        container.style.top = `${y}px`;
      }

      function stopDragging() {
        isDragging = false;
      }
    }

    function addDraggableControl(Control, options = {}, position = 'top-right') {
      const control = new Control(options);
      map.value.addControl(control, position);
      makeDraggable(control);
      return control;
    }

    function updateChoropleth(data) {
      if (!map.value.getSource('counties')) {
        map.value.addSource('counties', {
          type: 'geojson',
          data: data
        })
      } else {
        map.value.getSource('counties').setData(data)
      }

      const colorScale = getColorScale(data)

      if (!map.value.getLayer('counties-layer')) {
        map.value.addLayer({
          id: 'counties-layer',
          type: 'fill',
          source: 'counties',
          paint: {
            'fill-color': [
              'interpolate',
              ['linear'],
              ['get', currentProperty.value],
              ...colorScale
            ],
            'fill-opacity': 0.7
          }
        })

        // Add interaction handlers
        map.value.on('click', 'counties-layer', handleCountyClick)
        map.value.on('mousemove', 'counties-layer', handleCountyHover)
        map.value.on('mouseleave', 'counties-layer', handleCountyLeave)
      } else {
        map.value.setPaintProperty('counties-layer', 'fill-color', [
          'interpolate',
          ['linear'],
          ['get', currentProperty.value],
          ...colorScale
        ])
      }
    }

    function getColorScale(data) {
      const values = data.features.map(f => f.properties[currentProperty.value])
      const min = Math.min(...values)
      const max = Math.max(...values)
      return [
        min, '#ffffcc',
        min + (max - min) * 0.25, '#c2e699',
        min + (max - min) * 0.5, '#78c679',
        min + (max - min) * 0.75, '#31a354',
        max, '#006837'
      ]
    }

    function handleCountyClick(e) {
      if (e.features.length > 0) {
        store.commit('setSelectedLocation', e.features[0].properties)
      }
    }

    function handleCountyHover(e) {
      if (e.features.length > 0) {
        map.value.getCanvas().style.cursor = 'pointer'
        if (!map.value.getLayer('hover-layer')) {
          map.value.addLayer({
            id: 'hover-layer',
            type: 'line',
            source: 'counties',
            paint: {
              'line-color': '#000',
              'line-width': 3
            },
            filter: ['==', 'FIPS', '']
          })
        }
        map.value.setFilter('hover-layer', ['==', 'FIPS', e.features[0].properties.FIPS])
      }
    }

    function handleCountyLeave() {
      map.value.getCanvas().style.cursor = ''
      map.value.setFilter('hover-layer', ['==', 'FIPS', ''])
    }

    function resizeMap() {
      if (map.value) {
        map.value.resize()
      }
    }

    function zoomIn() {
      if (map.value) {
        map.value.zoomIn()
      }
    }

    function zoomOut() {
      if (map.value) {
        map.value.zoomOut()
      }
    }

    function resetViewToCONUS() {
      if (map.value) {
        map.value.flyTo({
          center: [-98.5795, 39.8283], // Approximate center of CONUS
          zoom: 3.5, // Zoom level to show all of CONUS
          bearing: 0,
          pitch: 0
        });
      }
    }

    function toggleSidebar(panel) {
      if (activeSidebar.value === panel) {
        activeSidebar.value = null
        isSidebarOpen.value = false
      } else {
        activeSidebar.value = panel
        isSidebarOpen.value = true
      }
    }

    function startResize(event) {
      isResizing.value = true
      document.addEventListener('mousemove', resize)
      document.addEventListener('mouseup', stopResize)
    }

    function resize(event) {
      if (isResizing.value) {
        const newWidth = event.clientX
        sidebarWidth.value = Math.max(200, Math.min(newWidth, 600))
      }
    }

    function stopResize() {
      isResizing.value = false
      document.removeEventListener('mousemove', resize)
      document.removeEventListener('mouseup', stopResize)
    }

    onBeforeUnmount(() => {
      if (map.value) {
        if (scaleControl.value) {
          map.value.removeControl(scaleControl.value)
        }
        map.value.remove()
      }
      window.removeEventListener('resize', resizeMap)
    })

    return {
      mapContainer,
      zoomIn,
      zoomOut,
      resetViewToCONUS,
      currentUnit,
      toggleSidebar,
      activeSidebar,
    }
  }
}
</script>

<style>
@import 'maplibre-gl/dist/maplibre-gl.css';

#map-container {
  display: flex;
  flex-direction: column;
  //width: 100%;
  height: 100%;
}

.content-wrapper {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}
.sidebar {
  position: absolute;
  top: 50px; /* Adjust based on your toolbar height */
  left: 0;
  width: 300px;
  height: calc(100% - 50px);
  background-color: white;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.resize-handle {
  width: 5px;
  height: 100%;
  background-color: #ccc;
  position: absolute;
  right: 0;
  top: 0;
  cursor: ew-resize;
}

.sidebar-enter-active,
.sidebar-leave-active {
  transition: transform 0.3s ease;
}

.sidebar-enter-from,
.sidebar-leave-to {
  transform: translateX(-100%);
}


#map {
  flex-grow: 1;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
}

.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1;
}

.map-controls .tooltip {
  position: relative;
  display: inline-block;
}

.map-controls .tooltip .tooltiptext {
  visibility: hidden;
  width: 120px;
  background-color: #555;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px 0;
  position: absolute;
  z-index: 1;
  bottom: 125%;
  left: 50%;
  margin-left: -60px;
  opacity: 0;
  transition: opacity 0.3s;
}

.map-controls .tooltip .tooltiptext::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: #555 transparent transparent transparent;
}

.map-controls .tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}

.map-controls button {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 30px;
  height: 30px;
  margin-bottom: 5px;
  padding: 5px;
  background-color: white;
  border: 1px solid #ccc;
  cursor: pointer;
  font-size: 16px;
}

.map-controls button:hover {
  background-color: #f0f0f0;
}

/* Style for the icons */
.map-controls button svg {
  width: 20px;
  height: 20px;
}

/* change custom styles for the scale control if needed */
.maplibregl-ctrl-scale {
  border: 2px solid #333;
  border-top: none;
  padding: 0 5px;
  color: #333;
  font-size: 10px;
  line-height: 18px;
  font-family: 'Helvetica Neue', Arial, Helvetica, sans-serif;
  background-color: rgba(255, 255, 255, 0.75);
  transition: background-color 0.3s ease;
}

.maplibregl-ctrl-scale:hover {
  background-color: rgba(255, 255, 255, 0.9);
}

/* Add styles for draggable controls */
.maplibregl-ctrl {
  z-index: 1;
}

.maplibregl-ctrl-top-right {
  top: 10px;
  right: 40px;
}

.maplibregl-ctrl-bottom-left {
  bottom: 40px;
  left: 10px;
}



</style>