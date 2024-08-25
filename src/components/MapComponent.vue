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
        <div class="resize-handle" @mousedown.prevent="startResize"></div>
        <DataSelectionPanel v-if="activeSidebar === 'data'" />
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
import DataSelectionPanel from "@/components/DataSelectionPanel.vue";
import ToolbarComponent from "@/components/ToolbarComponent.vue";
import stateBoundaries from '@/../data/gz_2010_us_040_00_20m.json'
import countyBoundaries from '@/../data/gz_2010_us_050_00_20m.json'

export default {
  name: 'MapComponent',
  components: {
    ToolbarComponent,
    DataSelectionPanel,
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

    onMounted(() => {
      initializeMap()

      window.addEventListener('mousemove', resizeSidebar)
      window.addEventListener('mouseup', stopResizeSidebar)
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
        center: [-98.5795, 39.8283], // Center of the US
        zoom: 4
      })

      map.value.on('load', () => {
        addCustomScaleControl()
        addDraggableControl(maplibregl.NavigationControl, {showCompass:false}, 'top-right')

        // Load county boundaries
        map.value.addSource('counties', {
          type: 'geojson',
          data: countyBoundaries
        })

        map.value.addLayer({
          id: 'counties-layer',
          type: 'fill',
          source: 'counties',
          paint: {
            'fill-color': '#627BC1',
            'fill-opacity': 0.5,
            'fill-outline-color': '#000000'
          }
        })

        // Add state boundaries
        map.value.addSource('states', {
          type: 'geojson',
          data: stateBoundaries
        })

        map.value.addLayer({
          id: 'states-layer',
          type: 'line',
          source: 'states',
          paint: {
            'line-color': '#000',
            'line-width': 2
          }
        })
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

    function startResizeSidebar(event) {
      isResizing.value = true
      document.addEventListener('mousemove', resizeSidebar)
      document.addEventListener('mouseup', stopResizeSidebar)
    }

    function resizeSidebar(event) {
      if (isResizing.value) {
        const newWidth = event.clientX
        sidebarWidth.value = Math.max(200, Math.min(newWidth, 600))
      }
    }

    function stopResizeSidebar() {
      isResizing.value = false
    }

    onBeforeUnmount(() => {
      if (map.value) {
        if (scaleControl.value) {
          map.value.removeControl(scaleControl.value)
        }
        map.value.remove()
      }
      window.removeEventListener('mousemove', resizeSidebar)
      window.removeEventListener('mouseup', stopResizeSidebar)
    })

    return {
      mapContainer,
      zoomIn,
      zoomOut,
      resetViewToCONUS,
      currentUnit,
      toggleSidebar,
      activeSidebar,
      isSidebarOpen,
      sidebarWidth,
      startResize: startResizeSidebar,
    }
  }
}
</script>

<style>
@import 'maplibre-gl/dist/maplibre-gl.css';

#map-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.content-wrapper {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}

.sidebar {
  position: absolute;
  top: calc(var(--toolbar-height, 50px) + 75px);
  width: 300px;
  height: calc(100% - var(--toolbar-height, 50px) - 70px);
  background-color: var(--color-background);
  box-shadow: var(--shadow-light);
  z-index: var(--z-index-sidebar);
}

.resize-handle {
  width: 5px;
  height: 100%;
  background-color: var(--color-border);
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
  width: 100%;
  height: 100%;
}

.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: var(--z-index-controls);
}

.map-controls .tooltip {
  position: relative;
  display: inline-block;
}

.map-controls .tooltip .tooltiptext {
  visibility: hidden;
  width: 120px;
  background-color: var(--color-tooltip-bg);
  color: var(--color-tooltip-text);
  text-align: center;
  border-radius: var(--border-radius);
  padding: 5px 0;
  position: absolute;
  z-index: var(--z-index-tooltip);
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
  border-color: var(--color-tooltip-bg) transparent transparent transparent;
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
  background-color: var(--color-button-bg);
  border: 1px solid var(--color-border);
  cursor: pointer;
  font-size: 16px;
}

.map-controls button:hover {
  background-color: var(--color-button-hover);
}

.map-controls button svg {
  width: 20px;
  height: 20px;
}

.maplibregl-ctrl-scale {
  border: 2px solid var(--color-scale-border);
  border-top: none;
  padding: 0 5px;
  color: var(--color-scale-text);
  font-size: 10px;
  line-height: 18px;
  font-family: var(--font-family),sans-serif;
  background-color: var(--color-scale-bg);
  transition: background-color 0.3s ease;
}

.maplibregl-ctrl-scale:hover {
  background-color: var(--color-scale-bg-hover);
}

.maplibregl-ctrl {
  z-index: var(--z-index-maplibre-controls);
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