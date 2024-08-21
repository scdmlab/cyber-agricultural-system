<!-- MapComponent.vue -->
<template>
  <div id="map-container">
    <div id="map" ref="mapContainer"></div>
    <div class="map-controls">
      <button @click="zoomIn" class="tooltip">
        <Icon icon="mdi:plus" />
        <span class="tooltiptext">Zoom In</span>
      </button>
      <button @click="zoomOut" class="tooltip">
        <Icon icon="mdi:minus" />
        <span class="tooltiptext">Zoom Out</span>
      </button>
      <button @click="resetViewToCONUS" class="tooltip">
        <Icon icon="mdi:home" />
        <span class="tooltiptext">Reset View</span>
      </button>
    </div>
  </div>
</template>

<script>
import { onMounted, ref, watch, computed, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import {Icon} from '@iconify/vue'

export default {
  name: 'MapComponent',
  components: {
    Icon
  },
  setup() {
    const store = useStore()
    const mapContainer = ref(null)
    const map = ref(null)

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
        console.log('Map loaded successfully')
        resizeMap()
        store.dispatch('fetchMapData')
      })
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

    onBeforeUnmount(() => {
      if (map.value) {
        map.value.remove()
      }
      window.removeEventListener('resize', resizeMap)
    })

    return {
      mapContainer,
      zoomIn,
      zoomOut,
      resetViewToCONUS
    }
  }
}
</script>

<style>
@import 'maplibre-gl/dist/maplibre-gl.css';

#map-container {
  position: relative;
  flex: 1;
  width: 100%;
  height: 100%;
}

#map {
  position: absolute;
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
</style>