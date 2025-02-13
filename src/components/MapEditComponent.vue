<template>
  <PopupWindow :title="'Edit Map'" :width="800" :height="600" @close="closeEditor">
    <div class="map-edit-container">
      <div class="map-title" :style="{ fontFamily: mapFont }">{{ mapTitle }}</div>
      <div class="map-metadata">
        <div class="north-arrow">
          <svg width="24" height="48" viewBox="0 0 24 48">
            <!-- North Arrow with professional design -->
            <g transform="translate(12,12)">
              <!-- Main Arrow -->
              <path 
                d="M0,-8 L4,0 L0,-2 L-4,0 Z" 
                fill="#555"
                stroke="#555"
                stroke-width="1"
              />
              <!-- N Letter -->
              <text 
                y="16"
                text-anchor="middle" 
                font-size="10" 
                font-weight="bold" 
                fill="#555"
                font-family="Arial"
              >N</text>
            </g>
          </svg>
        </div>
        <div class="map-description" :style="{ fontFamily: mapFont }">{{ mapDescription }}</div>
        <div class="simple-legend" v-if="currentProperty">
          <span class="legend-min" :style="{ fontFamily: mapFont }">{{ currentMinValue.toFixed(2) }}</span>
          <div class="gradient-bar" :style="{ background: colorGradient }"></div>
          <span class="legend-max" :style="{ fontFamily: mapFont }">{{ currentMaxValue.toFixed(2) }}</span>
        </div>
      </div>
      <div id="map-editor" ref="mapContainer" class="map-container"></div>
      <div class="edit-tools">
        <button @click="exportMap" class="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
          Export Map
        </button>
        <button @click="closeEditor" class="bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700">
          Close
        </button>
      </div>
    </div>
  </PopupWindow>
</template>

<script>
import { onMounted, ref, computed } from 'vue';
import { useStore } from 'vuex';
import PopupWindow from './PopupWindow.vue';
import maplibregl from 'maplibre-gl';


// Define propertyTitleMap directly in this component
const propertyTitleMap = {
  pred: 'Prediction',
  yield: 'Crop Yield',
  error: 'Error',
  uncertainty: 'Uncertainty'
};

export default {
  name: 'MapEditComponent',
  components: {
    PopupWindow
  },
  props: {
    title: String,
    description: String,
    font: {
      type: String,
      default: 'Arial'
    },
    backgroundColor: {
      type: String,
      default: '#ffffff'
    }
  },
  setup(props, { emit }) {
    const store = useStore();
    const mapContainer = ref(null);
    let map = null;

    const mapTitle = computed(() => store.state.mapTitle);
    const mapDescription = computed(() => store.state.mapDescription);
    const mapFont = computed(() => store.state.mapFont);

    const currentProperty = computed(() => store.state.currentProperty);
    const choroplethSettings = computed(() => store.state.choroplethSettings);
    
    const currentMinValue = computed(() => {
      const min = choroplethSettings.value.minValue;
      return isFinite(min) ? min : 0;
    });

    const currentMaxValue = computed(() => {
      const max = choroplethSettings.value.maxValue;
      return isFinite(max) ? max : 100;
    });

    const mappedPropertyTitle = computed(() => {
      return propertyTitleMap[currentProperty.value] || currentProperty.value;
    });

    const colorGradient = computed(() => {
      const property = currentProperty.value;
      const colorSchemes = choroplethSettings.value.colorSchemes;
      
      if (!colorSchemes || !colorSchemes[property]) {
        return 'linear-gradient(to right, #CCCCCC, #CCCCCC)';
      }

      const colors = colorSchemes[property];
      
      if (property === 'error' && colors.length === 3) {
        return `linear-gradient(to right, ${colors[0]}, ${colors[1]}, ${colors[2]})`;
      }
      
      return `linear-gradient(to right, ${colors[0]}, ${colors[1]})`;
    });

    onMounted(() => {
      initMap();
    });

    const initMap = () => {
      if (!mapContainer.value) return;

      // Clone the current map configuration
      const currentMap = store.state.map;
      if (!currentMap) {
        console.error('No map instance found in store');
        return;
      }

      map = new maplibregl.Map({
        container: mapContainer.value,
        style: currentMap.getStyle(),
        center: currentMap.getCenter(),
        zoom: currentMap.getZoom(),
        bearing: currentMap.getBearing(),
        pitch: currentMap.getPitch(),
        preserveDrawingBuffer: true // Important for image export
      });

      map.on('load', () => {
        // Copy all sources and layers from the original map
        const originalStyle = currentMap.getStyle();
        Object.keys(originalStyle.sources).forEach(sourceId => {
          if (!map.getSource(sourceId)) {
            map.addSource(sourceId, originalStyle.sources[sourceId]);
          }
        });

        originalStyle.layers.forEach(layer => {
          if (!map.getLayer(layer.id)) {
            map.addLayer(layer);
          }
        });
      });
    };

    const exportMap = () => {
      if (!map) {
        console.error('Map not initialized');
        return;
      }

      try {
        map.once('render', () => {
          const mapCanvas = map.getCanvas();
          const finalCanvas = document.createElement('canvas');
          const ctx = finalCanvas.getContext('2d');

          // Adjust spacing
          const padding = 20; // Reduced from 40
          const titleHeight = mapTitle.value ? 40 : 0; // Reduced from 60
          const metadataHeight = 30; // Height for description, north arrow, and legend
          const totalHeaderHeight = titleHeight + metadataHeight + (padding * 2);

          finalCanvas.width = mapCanvas.width;
          finalCanvas.height = mapCanvas.height + totalHeaderHeight;

          // Background
          ctx.fillStyle = props.backgroundColor;
          ctx.fillRect(0, 0, finalCanvas.width, finalCanvas.height);

          // Title
          if (mapTitle.value) {
            ctx.font = `bold 24px ${mapFont.value}`;
            ctx.fillStyle = '#000000';
            ctx.textAlign = 'center';
            ctx.fillText(mapTitle.value, finalCanvas.width / 2, padding + 24);
          }

          const metadataY = padding + titleHeight + 20;

          // Description (center-aligned)
          if (mapDescription.value) {
            ctx.font = `14px ${mapFont.value}`;
            ctx.fillStyle = '#000000';
            ctx.textAlign = 'center';
            ctx.fillText(mapDescription.value, finalCanvas.width / 2, metadataY);
          }

          // North Arrow (center)
          ctx.save();
          ctx.translate(padding + 20, metadataY - 8);
          ctx.fillStyle = '#666';

          // Draw arrow
          ctx.beginPath();
          ctx.moveTo(12, 0);    // Top point
          ctx.lineTo(17, 10);   // Bottom right
          ctx.lineTo(7, 10);    // Bottom left
          ctx.closePath();
          ctx.fill();

          // Draw stem
          ctx.fillRect(11, 10, 2, 8);

          // Add "N" with more space below the arrow
          ctx.font = 'bold 8px Arial';
          ctx.textAlign = 'center';
          ctx.fillText('N', 12, 28);
          ctx.restore();

          // Legend (right-aligned)
          if (currentProperty.value) {
            const legendWidth = 200;
            const legendX = finalCanvas.width - legendWidth - padding;
            
            // Draw gradient
            const gradient = ctx.createLinearGradient(legendX + 30, 0, legendX + legendWidth - 30, 0);
            const colors = choroplethSettings.value.colorSchemes[currentProperty.value];
            gradient.addColorStop(0, colors[0]);
            gradient.addColorStop(1, colors[1]);
            
            ctx.fillStyle = gradient;
            ctx.fillRect(legendX + 30, metadataY - 6, legendWidth - 60, 12);

            // Legend labels
            ctx.font = '12px Arial';
            ctx.fillStyle = '#666';
            ctx.textAlign = 'right';
            ctx.fillText(currentMinValue.value.toFixed(2), legendX + 25, metadataY + 4);
            ctx.textAlign = 'left';
            ctx.fillText(currentMaxValue.value.toFixed(2), legendX + legendWidth - 25, metadataY + 4);
          }

          // Draw map
          ctx.drawImage(mapCanvas, 0, totalHeaderHeight);

          // Create download link
          const dataUrl = finalCanvas.toDataURL('image/png', 1.0);
          const link = document.createElement('a');
          link.download = `${mapTitle.value || 'map'}_export.png`;
          link.href = dataUrl;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        });

        map.triggerRepaint();
      } catch (error) {
        console.error('Error exporting map:', error);
      }
    };

    const closeEditor = () => {
      if (map) {
        map.remove();
      }
      emit('close');
    };

    return {
      mapContainer,
      exportMap,
      closeEditor,
      mapTitle,
      mapDescription,
      mapFont,
      currentProperty,
      mappedPropertyTitle,
      currentMinValue,
      currentMaxValue,
      colorGradient,
    };
  }
}
</script>

<style scoped>
.map-edit-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1rem;
}

.map-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.map-metadata {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8px 0;
  padding: 0 16px;
  gap: 24px;
}

.north-arrow {
  flex: 0 0 auto;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 6px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.map-description {
  flex: 1;
  text-align: center;
  font-size: 14px;
  color: #333;
}

.simple-legend {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 6px 12px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.gradient-bar {
  width: 120px;
  height: 12px;
  border-radius: 2px;
}

.legend-min, .legend-max {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.map-container {
  flex-grow: 1;
  min-height: 300px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.edit-tools {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
</style>