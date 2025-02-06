<!-- MapComponent.vue -->
<template>
  <div id="map-container">
    <YearSlider />
    <ToolbarComponent
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @reset-view="resetViewToCONUS"
        @toggle-sidebar="toggleSidebar"
        @update-settings="updateSettings"
        @toggle-legend="toggleLegend"
        @start-draw-line="startDrawLine"
        @start-draw-polygon="startDrawPolygon"
        @delete-drawing="deleteDrawing"
    />
    <transition name="sidebar">
      <div v-if="isSidebarOpen" class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <div class="resize-handle" @mousedown.prevent="startResize"></div>
        <DataSelectionPanel v-if="activeSidebar === 'data'" />
        <DataAnalysisPanel v-if="activeSidebar === 'analysis'" />
        <MappingPanel v-if="activeSidebar === 'mapping'" />
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
import { scaleLinear } from 'd3-scale'
import { interpolateRgb } from 'd3-interpolate'
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";
import stateBoundaries from '@/assets/gz_2010_us_040_00_20m.json'
import countyBoundaries from '@/assets/gz_2010_us_050_00_20m.json'
import { stateCodeMap } from '@/utils/stateCodeMap'

import DataSelectionPanel from "@/components/DataSelectionPanel.vue";
import ToolbarComponent from "@/components/ToolbarComponent.vue";
import DataAnalysisPanel from "@/components/DataAnalysisPanel.vue";
import MappingPanel from "@/components/MappingPanel.vue";
import LegendComponent from "@/components/LegendComponent.vue";
import YearSlider from "@/components/YearSlider.vue";

export default {
  name: 'MapComponent',
  components: {
    ToolbarComponent,
    DataSelectionPanel,
    DataAnalysisPanel,
    MappingPanel,
    LegendComponent,
    YearSlider
  },
  setup() {
    const store = useStore()
    const mapContainer = ref(null)
    const map = ref(null)
    const draw = ref(null)
    const drawnPolygons = ref([])
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
    const markers = ref([])
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

    function initializeDrawControl() {
      draw.value = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
          line_string: true,
          polygon: true,
          trash: true
        },
      });
      console.log("Draw control initialized:", draw.value);
      map.value.addControl(draw.value);

      map.value.on('draw.create', (e) => {
        drawnPolygons.value = draw.value.getAll().features;
        store.dispatch('saveDrawnPolygons', drawnPolygons.value);
      });

      map.value.on('draw.delete', (e) => {
        drawnPolygons.value = draw.value.getAll().features;
        store.dispatch('saveDrawnPolygons', drawnPolygons.value);
      });

      // Add this new event listener
      map.value.on('draw.update', (e) => {
        drawnPolygons.value = draw.value.getAll().features;
        store.dispatch('saveDrawnPolygons', drawnPolygons.value);
      });





    }


    const addMarker = (marker) => {
    const el = document.createElement('div');
    el.className = 'marker';
    el.style.width = '30px';
    el.style.height = '30px';
    el.style.backgroundSize = '100%';
    el.style.backgroundImage = 'url(marker-icon.png)'; // Use your marker icon

    const popup = new maplibregl.Popup({ offset: 25 }).setText(`${marker.name}: ${marker.value}`);

    const markerInstance = new maplibregl.Marker(el)
      .setLngLat([marker.lon, marker.lat])
      .setPopup(popup)
      .addTo(map.value);

    // Automatically show the popup
    markerInstance.togglePopup();

    markers.value.push(markerInstance);
  };

    const removeMarkers = () => {
      if (markers.value) {
        markers.value.forEach(marker => marker.remove());
        markers.value = [];
      }
    };

    watch(
      () => store.state.markers,
      (newMarkers) => {
        removeMarkers();
        newMarkers.forEach(addMarker);
      },
      { deep: true }
    );


    const updateChoropleth = async () => {
      if (!map.value || !map.value.getSource('counties')) {
        return
      }

      // Fetch prediction data using the store action
      const predictions = await store.dispatch('fetchPredictionData')
      if (!predictions || predictions.length === 0) {
        console.warn('No prediction data available')
        return
      }

      // Create data lookup by FIPS
      const dataById = {}
      predictions.forEach(row => {
        let val
        if (store.state.currentProperty === 'uncertainty') {
          val = row.uncertainty
        } else if (store.state.currentProperty === 'error') {
          val = row.error
        } else {
          val = row[store.state.currentProperty]
        }
        if (!isNaN(val)) {
          dataById[row.FIPS] = val
        }
      })

      // Get min and max values for color scaling
      const values = Object.values(dataById).filter(v => !isNaN(v))
      let minValue = Math.min(...values)
      let maxValue = Math.max(...values)

      // Handle different properties
      if (store.state.currentProperty === 'error') {
        const absMax = Math.max(Math.abs(minValue), Math.abs(maxValue))
        minValue = -absMax
        maxValue = absMax
      } else if (store.state.currentProperty === 'uncertainty') {
        minValue = 0
        maxValue = Math.max(...values)
      }

      // Get color scheme from settings
      const colors = choroplethSettings.value.colorSchemes[store.state.currentProperty] || 
                     choroplethSettings.value.colorSchemes.pred

      // Create appropriate color scale
      if (store.state.currentProperty === 'error') {
        colorScale.value = createDivergingColorScale(minValue, maxValue, colors)
      } else {
        colorScale.value = createSequentialColorScale(minValue, maxValue, colors)
      }

      // Update store with new min/max values
      store.commit('setChoroplethSettings', {
        ...choroplethSettings.value,
        minValue,
        maxValue
      })

      // Update features with colors
      const updatedFeatures = countiesWithFIPS.value.features.map(feature => ({
        ...feature,
        properties: {
          ...feature.properties,
          value: dataById[feature.properties.FIPS],
          color: getColor(dataById[feature.properties.FIPS])
        }
      }))

      // Update the source data
      map.value.getSource('counties').setData({
        type: 'FeatureCollection',
        features: updatedFeatures
      })

      // Update the paint property for the counties layer
      map.value.setPaintProperty('counties-layer', 'fill-color', [
        'case',
        ['has', 'value'],
        ['get', 'color'],
        'rgba(0, 0, 0, 0)' // transparent for counties with no data
      ])

      // Update the counties-layer paint property
      watch(
        () => store.getters.getSelectedCountyFIPS,
        (newSelectedFIPS) => {
          if (map.value) {
            const paintExpression = [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              0.9, // hover opacity
              ['in', ['get', 'FIPS'], ['literal', newSelectedFIPS.length ? newSelectedFIPS : ['']]], // check if FIPS is in selected array
              0.8, // selected opacity
              choroplethSettings.value.choroplethOpacity // default opacity
            ];
            
            map.value.setPaintProperty('counties-layer', 'fill-opacity', paintExpression);
          }
        },
        { deep: true }
      );
    }

    // Helper functions for color scales
    const createSequentialColorScale = (min, max, colors) => {
      return scaleLinear()
        .domain([min, max])
        .range(colors)
        .interpolate(interpolateRgb)
    }

    const createDivergingColorScale = (min, max, colors) => {
      return (value) => {
        if (value === null || value === undefined || isNaN(value)) {
          return 'rgba(0, 0, 0, 0)'
        }
        if (value <= 0) {
          return scaleLinear()
            .domain([min, 0])
            .range([colors[0], colors[1]])
            .interpolate(interpolateRgb)(value)
        } else {
          return scaleLinear()
            .domain([0, max])
            .range([colors[1], colors[2]])
            .interpolate(interpolateRgb)(value)
        }
      }
    }

    const getColor = (value) => {
      if (value === null || value === undefined || isNaN(value)) {
        return 'rgba(0, 0, 0, 0)' // Transparent for no data
      }
      return colorScale.value(value)
    }
    // Watch for changes in the store that should trigger an update
    watch(
      () => [
        store.state.currentCrop,
        store.state.currentYear,
        store.state.currentProperty,
        store.state.currentPredictionType,
        store.state.currentDay
      ],
      async () => {
        await updateChoropleth()
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

      // Create tooltip element
      tooltip.value = document.createElement('div')
      tooltip.value.id = 'map-tooltip'
      tooltip.value.className = 'maplibregl-popup maplibregl-popup-anchor-bottom'
      tooltip.value.style.display = 'none'
      document.body.appendChild(tooltip.value)

      window.addEventListener('mousemove', resizeSidebar)
      window.addEventListener('mouseup', stopResizeSidebar)

      // Initial choropleth update after map loads
      map.value.on('load', () => {
        // ... existing load event code ...
        
        // Trigger initial choropleth update
        updateChoropleth()

        // Add a new layer for selected counties
        map.value.addLayer({
          id: 'selected-counties',
          type: 'line',
          source: 'counties',
          paint: {
            'line-color': '#FFD700', // Gold color for selection
            'line-width': 3,
            'line-opacity': 1
          },
          filter: ['in', ['get', 'FIPS'], ''], // Start with empty filter
        });

        // Update the filter whenever selected counties change
        watch(
          () => store.getters.getSelectedCountyFIPS,
          (newSelectedFIPS) => {
            if (map.value) {
              if (newSelectedFIPS && newSelectedFIPS.length > 0) {
                map.value.setFilter('selected-counties', [
                  'in',
                  ['get', 'FIPS'],
                  ['literal', newSelectedFIPS] // Wrap the FIPS array in a literal expression
                ]);
              } else {
                // When no counties are selected, set an impossible condition
                map.value.setFilter('selected-counties', ['in', ['get', 'FIPS'], '']);
              }
            }
          },
          { deep: true, immediate: true }
        );

        // Also update the counties-layer paint property
        map.value.setPaintProperty('counties-layer', 'fill-opacity', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.9,
          ['in', ['get', 'FIPS'], ['literal', store.getters.getSelectedCountyFIPS.length ? store.getters.getSelectedCountyFIPS : ['']]],
          0.8,
          choroplethSettings.value.choroplethOpacity
        ]);

        // Update the paint property when selections change
        watch(
          () => store.getters.getSelectedCountyFIPS,
          (newSelectedFIPS) => {
            if (map.value) {
              map.value.setPaintProperty('counties-layer', 'fill-opacity', [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                0.9,
                ['in', ['get', 'FIPS'], ['literal', newSelectedFIPS.length ? newSelectedFIPS : ['']]],
                0.8,
                choroplethSettings.value.choroplethOpacity
              ]);
            }
          },
          { deep: true }
        );

        // Update the click handler for counties-layer
        map.value.on('click', 'counties-layer', (e) => {
          if (e.features.length > 0) {
            const feature = e.features[0]
            const fips = feature.properties.FIPS
            // Get state code from FIPS and use stateCodeMap
            const stateCode = fips.substring(0, 2)
            const stateName = stateCodeMap[stateCode] || 'Unknown State'
            const countyName = `${feature.properties.NAME} County, ${stateName}`
            
            if (feature.properties.value !== undefined) {
              if (store.state.selectedCountyFIPS.includes(fips)) {
                store.commit('removeSelectedCountyFIPS', fips)
              } else {
                store.commit('addSelectedCountyFIPS', { 
                  fips, 
                  name: countyName  // Now using the properly formatted county name
                })
              }
            }
          }
        });

        // Change cursor on hover
        map.value.on('mouseenter', 'counties-layer', () => {
          map.value.getCanvas().style.cursor = 'pointer';
        });

        map.value.on('mouseleave', 'counties-layer', () => {
          map.value.getCanvas().style.cursor = '';
        });
      })
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
        
        // Load county boundaries
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
            'fill-color': 'rgba(0, 0, 0, 0)', // Start with transparent fill
            'fill-opacity': [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              0.9, // Opacity when hovered
              ['in', ['get', 'FIPS'], ['literal', store.getters.getSelectedCountyFIPS]],
              0.8,
              0.7
            ],
            'fill-outline-color': [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              '#000', // Outline color when hovered
              '#000'  // Default outline color
            ]
          }
        })

        // Add a second layer for the hover effect
        map.value.addLayer({
          id: 'counties-hover',
          type: 'line',
          source: 'counties',
          paint: {
            'line-color': [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              '#fff', // Bright border color when hovered
              'transparent'  // Invisible when not hovered
            ],
            'line-width': 2
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

        // Update mousemove event
        map.value.on('mousemove', 'counties-layer', (e) => {
          if (e.features.length > 0) {
            const feature = e.features[0];
            // Only apply hover effect if the county has data
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
                
                // Update Vuex store
                store.commit('setHoveredCounty', {
                  fips: feature.properties.FIPS,
                  name: `${feature.properties.NAME} County, ${feature.properties.STATE_NAME}`,
                  value: feature.properties.value
                });

                // Show tooltip
                showTooltip(e.lngLat, `${feature.properties.NAME}: ${feature.properties.value.toFixed(2)}`);
              }
            } else {
              // If the county has no data, clear any existing hover state
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

        // Update mouseleave event
        map.value.on('mouseleave', 'counties-layer', () => {
          if (hoveredCountyId.value !== null) {
            map.value.setFeatureState(
              { source: 'counties', id: hoveredCountyId.value },
              { hover: false }
            );
            hoveredCountyId.value = null;
            
            // Clear hovered county in Vuex store
            store.commit('setHoveredCounty', null);
            hideTooltip();
          }
        });

        // Add cursor style changes
        map.value.on('mouseenter', 'counties-layer', () => {
          map.value.getCanvas().style.cursor = 'default'
        })

        map.value.on('mouseleave', 'counties-layer', () => {
          map.value.getCanvas().style.cursor = ''
        })

        store.commit('setMap', map.value)
        
        // Remove this line as we don't want default choropleth
        // updateChoropleth()
        
        initializeDrawControl()
      })

    }

    function startDrawLine() {
      draw.value.changeMode('draw_line_string');
    }

    function startDrawPolygon() {
      draw.value.changeMode('draw_polygon');
    }

    function deleteDrawing() {
      draw.value.trash();
    }

    function stopDrawing() {
    draw.value.changeMode('simple_select');
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
        let x = e.clientX - startX;
        let y = e.clientY - startY;

        container.style.left = `${x}px`;
        container.style.top = `${y}px`;
      }

      function stopDragging() {
        isDragging = false;
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
          center: [-98, 39], // Approximate center of CONUS
          zoom: 3.7, // Zoom level to show all of CONUS
          bearing: 0,
          pitch: 0
        });
      }
    }

    function toggleSidebar(panel) {
  if (activeSidebar.value === panel) {
    // Closing the current sidebar
    activeSidebar.value = null
    isSidebarOpen.value = false
    if (panel === 'run') {
      restoreMapLayers()
    }
  } else {
    // Switching to a new sidebar or opening a sidebar
    if (activeSidebar.value === 'run') {
      // We're switching from 'run' to another panel
      restoreMapLayers()
    }
    
    if (panel === 'run') {
      // We're switching to 'run' from another panel or from closed state
      removeMapLayers()
    }
    
    activeSidebar.value = panel
    isSidebarOpen.value = true
  }
}

    function removeMapLayers() {
      if (map.value) {
        // Remove basemap
        if (map.value.getLayer('osm-layer')) {
          map.value.removeLayer('osm-layer')
          baseMapVisible.value = false
        }
        
        // Remove choropleth layer
        if (map.value.getLayer('counties-layer')) {
          map.value.removeLayer('counties-layer')
          choroplethVisible.value = false
        }
      }
    }

    function restoreMapLayers() {
      if (map.value) {
        // Restore basemap
        if (!baseMapVisible.value && !map.value.getLayer('osm-layer')) {
          map.value.addLayer({
            id: 'osm-layer',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19
          }, 'states-layer') // Insert below the states layer
          baseMapVisible.value = true
        }
        
        // Restore choropleth layer
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
                  55, '#FFEDA0',
                  215, '#04AA6D'
                ],
                'rgba(0, 0, 0, 0)' // Transparent for counties with no data
              ],
              'fill-opacity': 0.7,
              'fill-outline-color': '#000000'
            }
          }, 'states-layer') // Insert below the states layer
          choroplethVisible.value = true
        }
        
        // Update choropleth if necessary
        if (choroplethVisible.value) {
          updateChoropleth()
        }
      }
    }

    function startResizeSidebar() {
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
      
      // Update choropleth opacity
      if (map.value && map.value.getLayer('counties-layer')) {
        map.value.setPaintProperty('counties-layer', 'fill-opacity', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.9, // hover opacity
          ['in', ['get', 'FIPS'], ['literal', store.getters.getSelectedCountyFIPS.length ? store.getters.getSelectedCountyFIPS : ['']]],
          0.8, // selected opacity
          newSettings.choroplethOpacity // default opacity from settings
        ]);
      }
      
      // Update basemap opacity if needed
      if (newSettings.basemapOpacity !== undefined) {
        updateBasemapOpacity(newSettings.basemapOpacity)
      }
      
      // Update choropleth if needed
      updateChoropleth()
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
      draw,
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
      choroplethSettings,
      startDrawLine,
      startDrawPolygon,
      deleteDrawing,
      stopDrawing,
    }
  }
}
</script>

<style>
@import 'maplibre-gl/dist/maplibre-gl.css';

#map-container {
  position: relative;
  height: 100vh;
  width: 100%;
}

.content-wrapper {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}

.sidebar {
  position: absolute;
  top: 36px;
  left: 0;
  height: calc(100vh - 36px);
  background-color: var(--color-background);
  box-shadow: var(--shadow-light);
  z-index: 10;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 0 10px;
}

.resize-handle {
  width: 5px;
  height: 100%;
  background-color: transparent;
  position: absolute;
  right: 0;
  top: 0;
  cursor: ew-resize;
  z-index: 11;
  transition: background-color 0.2s;
  border-left: none;
  box-shadow: -2px 0 4px rgba(0, 0, 0, 0.1);
}

.resize-handle:hover {
  background-color: rgba(0, 0, 0, 0.1);
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
  position: absolute;
  top: 36px;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
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



/* Add these styles for the zoom control */
.maplibregl-ctrl-group {
  border-radius: 4px;
  overflow: hidden;
} */

/* .maplibregl-ctrl-group > button {
  width: 30px;
  height: 30px;
  display: block;
  padding: 0;
  outline: none;
  border: 0;
  box-sizing: border-box;
  cursor: pointer;
} */


/* .maplibregl-ctrl-icon {
  display: block;
  width: 100%;
  height: 100%;
  background-repeat: no-repeat;
  background-position: center;
} */

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
  z-index: 15;
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

.mapboxgl-ctrl-top-left {
  z-index: 1000;
}

.mapboxgl-ctrl-group {
  pointer-events: auto;
}

.mapboxgl-ctrl-group button {
  background-color: var(--color-button-bg);
}

.mapboxgl-ctrl-group button:hover {
  background-color: var(--color-button-hover);
}

/* Style for active draw buttons */
.mapboxgl-ctrl-group button.active {
  background-color: var(--color-button-active);
}

/* Update chart container styles */
.chart-container {
  position: relative;
  width: calc(100% - 20px); /* Account for padding */
  height: 300px;
  margin: 0 auto;
  z-index: 9;
  padding: 10px;
  /* Remove right padding since we're using calc for width */
}

/* Ensure proper scrolling in sidebar */
.sidebar {
  position: absolute;
  top: 36px;
  left: 0;
  height: calc(100vh - 36px);
  background-color: var(--color-background);
  box-shadow: var(--shadow-light);
  z-index: 10;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  /* Add padding to prevent content from touching edges */
  padding: 0 10px;
}

</style>





