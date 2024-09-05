<!-- MapComponent.vue -->
<template>
  <div id="map-container">

    <ToolbarComponent
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @reset-view="resetViewToCONUS"
        @toggle-sidebar="toggleSidebar"
        @update-settings="updateSettings"
        @toggle-legend="toggleLegend"
    />
    <transition name="sidebar">
      <div v-if="isSidebarOpen" class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <div class="resize-handle" @mousedown.prevent="startResize"></div>
        <DataSelectionPanel v-if="activeSidebar === 'data'" />
        <DataAnalysisPanel v-if="activeSidebar === 'analysis'" />
        <MappingPanel v-if="activeSidebar === 'mapping'" />
        <ModelPanel v-if="activeSidebar === 'run'" />
        <!-- Add other sidebar components as needed -->
      </div>
    </transition>
    <div id="map" ref="mapContainer"></div>
    <LegendComponent
          v-if="showLegend"
          :minValue="choroplethSettings.minValue"
          :maxValue="choroplethSettings.maxValue"
          :colorScale="choroplethSettings.colorScheme"
          @close="toggleLegend"
        />
  </div>
</template>

<script>
import { onMounted, ref, watch, computed, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import {Icon} from '@iconify/vue'
import { scaleLinear } from 'd3-scale'
import { interpolateRgb } from 'd3-interpolate'

import stateBoundaries from '@/assets/gz_2010_us_040_00_20m.json'
import countyBoundaries from '@/assets/gz_2010_us_050_00_20m.json'

import DataSelectionPanel from "@/components/DataSelectionPanel.vue";
import ToolbarComponent from "@/components/ToolbarComponent.vue";
import DataAnalysisPanel from "@/components/DataAnalysisPanel.vue";
import MappingPanel from "@/components/MappingPanel.vue";
import ModelPanel from "@/components/ModelPanel.vue";
import LegendComponent from "@/components/LegendComponent.vue";


export default {
  name: 'MapComponent',
  components: {
    ToolbarComponent,
    DataSelectionPanel,
    Icon,
    DataAnalysisPanel,
    MappingPanel,
    ModelPanel,
    LegendComponent
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
    const colorScale = ref(null)
    const hoveredCountyId = ref(null)
    const baseMapVisible = ref(true)
    const choroplethVisible = ref(true)
    const tooltip = ref(null)
    const showLegend = ref(true)
    const choroplethSettings = computed(() => store.state.choroplethSettings)
    const currentBasemapUrl = computed(() => store.getters.currentBasemapUrl)

    const toggleLegend = () => {
      showLegend.value = !showLegend.value
    }

    const countiesWithFIPS = computed(() => {
      return {
        ...countyBoundaries,
        features: countyBoundaries.features.map(feature => ({
          ...feature,
          properties: {
            ...feature.properties,
            FIPS: `${feature.properties.STATE}${feature.properties.COUNTY.padStart(3, '0')}`
          }
        }))
      }
    })


    const updateChoropleth = (newSettings = null) => {
      const csvData = store.state.csvData
      const currentProperty = store.state.currentProperty

      if (!csvData || !map.value || !map.value.getSource('counties')) {
        return
      }

      const dataById = {}
      csvData.forEach(row => {
        if (row[currentProperty] !== null && row[currentProperty] !== undefined) {
          dataById[row.FIPS] = parseFloat(row[currentProperty])
        }
      })

      const updatedFeatures = countiesWithFIPS.value.features.map(feature => ({
        ...feature,
        properties: {
          ...feature.properties,
          value: dataById[feature.properties.FIPS] !== undefined ? dataById[feature.properties.FIPS] : null
        }
      }))

      const values = Object.values(dataById).filter(v => !isNaN(v))
      let minValue = Math.min(...values)
      let maxValue = Math.max(...values)

      if (newSettings) {
        minValue = newSettings.minValue !== undefined ? newSettings.minValue : minValue
        maxValue = newSettings.maxValue !== undefined ? newSettings.maxValue : maxValue
        
        if (newSettings.colorScheme) {
          colorScale.value = scaleLinear()
            .domain([minValue, maxValue])
            .range(newSettings.colorScheme)
            .interpolate(interpolateRgb)
        }
        
        if (newSettings.choroplethOpacity !== undefined) {
          map.value.setPaintProperty('counties-layer', 'fill-opacity', [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.8,
            newSettings.choroplethOpacity
          ])
        }
      } else {
        colorScale.value = scaleLinear()
          .domain([minValue, maxValue])
          .range(store.state.choroplethSettings.colorScheme)
          .interpolate(interpolateRgb)
      }

      updatedFeatures.forEach(feature => {
        feature.properties.color = getColor(feature.properties.value)
      })

      map.value.getSource('counties').setData({
        type: 'FeatureCollection',
        features: updatedFeatures
      })

      map.value.setPaintProperty('counties-layer', 'fill-color', [
        'case',
        ['boolean', ['feature-state', 'hover'], false],
        '#666666',
        ['get', 'color']
      ])

      console.log("Updated choropleth with data range:", minValue, "-", maxValue);
    }

    const getColor = (value) => {
      if (value === null || value === undefined || isNaN(value)) {
        return 'rgba(0, 0, 0, 0)'
      }
      return colorScale.value(value)
    }
   
    watch(
      () => [
        store.state.currentCrop,
        store.state.currentYear,
        store.state.currentMonth,
        store.state.currentProperty,
        store.state.csvData
      ],
      () => {
        updateChoropleth()
      },
      { deep: true }
    )

    watch(currentBasemapUrl, (newUrl) => {
      if (map.value) {
        console.log("Updating basemap to:", newUrl)
        map.value.getSource('osm').setTiles([newUrl])
      }
    })

    onMounted(() => {
      initializeMap()

      tooltip.value = document.createElement('div')
      tooltip.value.id = 'map-tooltip'
      tooltip.value.className = 'maplibregl-popup maplibregl-popup-anchor-bottom'
      tooltip.value.style.display = 'none'
      document.body.appendChild(tooltip.value)

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
        center: [-92, 43], 
        zoom: 4.8
      })

      

      map.value.on('load', () => {
        addCustomScaleControl()

        map.value.addSource('counties', {
          type: 'geojson',
          data: countiesWithFIPS.value,
          generateId: true
        })

        map.value.addLayer({
          id: 'counties-layer',
          type: 'fill',
          source: 'counties',
          paint: {
            'fill-color': [
              'case',
              ['!=', ['get', 'value'], null],
              [
                'interpolate',
                ['linear'],
                ['get', 'value'],
                0, '#FFEDA0',
                100, '#F03B20'
              ],
              'rgba(0, 0, 0, 0)'
            ],
            'fill-opacity': 0.7,
            'fill-outline-color': '#000000'
          }
        })

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

        map.value.on('mousemove', 'counties-layer', (e) => {
          if (e.features.length > 0) {
            const feature = e.features[0];
            if (feature.properties.value !== null && feature.properties.value !== undefined) {
              if (hoveredCountyId.value !== feature.id) {
                if (hoveredCountyId.value !== null) {
                  map.value.setFeatureState(
                    { source: 'counties', id: hoveredCountyId.value },
                    { hover: false }
                  );
                }
                hoveredCountyId.value = feature.id;
                map.value.setFeatureState(
                  { source: 'counties', id: hoveredCountyId.value },
                  { hover: true }
                );
                
                store.commit('setHoveredCounty', {
                  fips: feature.properties.FIPS,
                  name: `${feature.properties.NAME} County, ${feature.properties.STATE_NAME}`,
                  value: feature.properties.value
                });

                showTooltip(e.lngLat, `${feature.properties.NAME}: ${feature.properties.value.toFixed(2)}`);
              }
            } else {
              if (hoveredCountyId.value !== null) {
                map.value.setFeatureState(
                  { source: 'counties', id: hoveredCountyId.value },
                  { hover: false }
                );
                hoveredCountyId.value = null;
                store.commit('setHoveredCounty', null);
                hideTooltip();
              }
            }
          }
        });

        map.value.on('mouseleave', 'counties-layer', () => {
          if (hoveredCountyId.value !== null) {
            map.value.setFeatureState(
              { source: 'counties', id: hoveredCountyId.value },
              { hover: false }
            );
            hoveredCountyId.value = null;
            
            store.commit('setHoveredCounty', null);
            hideTooltip();
          }
        });

        map.value.on('mouseenter', 'counties-layer', () => {
          map.value.getCanvas().style.cursor = 'default'
        })

        map.value.on('mouseleave', 'counties-layer', () => {
          map.value.getCanvas().style.cursor = ''
        })

        store.commit('setMap', map.value)

        updateChoropleth()

      })
    }

    function showTooltip(lngLat, content) {
      if (tooltip.value && map.value) {
    const point = map.value.project(lngLat);
    tooltip.value.style.display = 'block';
    tooltip.value.style.left = `${point.x}px`;
    tooltip.value.style.top = `${point.y}px`;
    tooltip.value.innerHTML = `
      <div class="maplibregl-popup-content">
        ${content}
      </div>
    `;
  }
    }

    function hideTooltip() {
      if (tooltip.value) {
        tooltip.value.style.display = 'none'
      }
    }

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
            currentUnit.value = this._unit
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
        let x = e.clientX - startX;
        let y = e.clientY - startY;

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
          center: [-98, 39],
          zoom: 3.7,
          bearing: 0,
          pitch: 0
        });
      }
    }

    function toggleSidebar(panel) {
  if (activeSidebar.value === panel) {
    activeSidebar.value = null
    isSidebarOpen.value = false
    if (panel === 'run') {
      restoreMapLayers()
    }
  } else {
    if (activeSidebar.value === 'run') {
      restoreMapLayers()
    }
    
    if (panel === 'run') {
      removeMapLayers()
    }
    
    activeSidebar.value = panel
    isSidebarOpen.value = true
  }
}

    function removeMapLayers() {
      if (map.value) {
        if (map.value.getLayer('osm-layer')) {
          map.value.removeLayer('osm-layer')
          baseMapVisible.value = false
        }
        
        if (map.value.getLayer('counties-layer')) {
          map.value.removeLayer('counties-layer')
          choroplethVisible.value = false
        }
      }
    }

    function restoreMapLayers() {
      if (map.value) {
        if (!baseMapVisible.value && !map.value.getLayer('osm-layer')) {
          map.value.addLayer({
            id: 'osm-layer',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19
          }, 'states-layer')
          baseMapVisible.value = true
        }
        
        if (!choroplethVisible.value && !map.value.getLayer('counties-layer')) {
          map.value.addLayer({
            id: 'counties-layer',
            type: 'fill',
            source: 'counties',
            paint: {
              'fill-color': [
                'case',
                ['!=', ['get', 'value'], null],
                [
                  'interpolate',
                  ['linear'],
                  ['get', 'value'],
                  0, '#FFEDA0',
                  100, '#F03B20'
                ],
                'rgba(0, 0, 0, 0)'
              ],
              'fill-opacity': 0.7,
              'fill-outline-color': '#000000'
            }
          }, 'states-layer')
          choroplethVisible.value = true
        }
        
        if (choroplethVisible.value) {
          updateChoropleth()
        }
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

    const updateSettings = (newSettings) => {
      store.commit('setChoroplethSettings', newSettings)
      updateChoropleth(newSettings)
      if (newSettings.basemapOpacity !== undefined) {
        updateBasemapOpacity(newSettings.basemapOpacity)
      }
    }

    function updateBasemapOpacity(newOpacity) {
      if (map.value && map.value.getLayer('osm-layer')) {
        try {
          map.value.setPaintProperty('osm-layer', 'raster-opacity', newOpacity);
        } catch (error) {
          console.error('Error updating basemap opacity:', error);
        }
      } else {
        console.warn('osm-layer not found or map not initialized');
        }
    }

    onBeforeUnmount(() => {
      if (map.value) {
        if (scaleControl.value) {
          map.value.removeControl(scaleControl.value)
        }
        map.value.remove()
      }

      if (tooltip.value) {
        tooltip.value.remove()
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
      getColor,
      hoveredCountyId,
      updateSettings,
      tooltip,
      showLegend,
      toggleLegend,
      choroplethSettings
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
  top: 86px;
  width: 300px;
  height: calc(100% - 86px);
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

#map-tooltip {
  position: absolute;
  z-index: 9999;
  pointer-events: none;
  transition: all 0.2s ease;
  transform: translate(-50%, 50%);
}

.maplibregl-popup-content {
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  font-size: 14px;
  line-height: 1.4;
}

</style>