<template>
  <div ref="legendContainer" class="legend-container" :style="{ left: position.x + 'px', top: position.y + 'px' }">
    <div class="legend-header" @mousedown="startDrag">
      <span>{{ mappedPropertyTitle }}</span>
      <button @click="$emit('close')" class="close-button">&times;</button>
    </div>
    <div class="legend-content">
      <div class="color-scale">
        <div v-for="(color, index) in interpolatedColorScale" :key="index" :style="{ backgroundColor: color }" class="color-bar"></div>
      </div>
      <div class="scale-labels">
        <span>{{ displayMinValue.toFixed(2) }}</span>
        <span>{{ displayMaxValue.toFixed(2) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { useStore } from 'vuex';
import { scaleLinear } from 'd3-scale';
import { interpolateRgb } from 'd3-interpolate';

const propertyTitleMap = {
  pred: 'Predicted Yield (bu/acre)',
  yield: 'Actual Yield (bu/acre)',
  error: 'Prediction Error (bu/acre)',
  uncertainty: 'Uncertainty'
};

export default {
  name: 'LegendComponent',
  props: {
    minValue: { type: Number, required: true },
    maxValue: { type: Number, required: true },
    colorScale: { type: Array, required: true },
  },
  emits: ['close'],
  setup(props) {
    const store = useStore();
    const currentProperty = computed(() => store.state.currentProperty);
    const choroplethSettings = computed(() => store.state.choroplethSettings);
    const currentCrop = computed(() => store.state.currentCrop);
    
    // Conversion factor is now always applied since we're always using t/ha
    const conversionFactor = computed(() => 
      currentCrop.value === 'corn' ? 0.06277 : 0.0673
    );

    // We now use the converted values for display
    const currentMinValue = computed(() => {
      const min = choroplethSettings.value.minValue;
      return isFinite(min) ? min : 0;
    });

    const currentMaxValue = computed(() => {
      const max = choroplethSettings.value.maxValue;
      return isFinite(max) ? max : 100;
    });

    const displayMinValue = computed(() => currentMinValue.value * conversionFactor.value);
    const displayMaxValue = computed(() => currentMaxValue.value * conversionFactor.value);

    const mappedPropertyTitle = computed(() => {
      const titles = {
        pred: 'Predicted Yield (t/ha)',
        yield: 'Actual Yield (t/ha)',
        error: 'Prediction Error (t/ha)',
        uncertainty: 'Uncertainty'
      };
      return titles[currentProperty.value] || currentProperty.value;
    });

    const position = ref({ x: window.innerWidth - 250, y: window.innerHeight - 200 });
    const isDragging = ref(false);
    const dragOffset = ref({ x: 0, y: 0 });
    const legendContainer = ref(null);

    // Update interpolatedColorScale using converted values for "error"
    const interpolatedColorScale = computed(() => {
      const property = currentProperty.value;
      const colorSchemes = choroplethSettings.value.colorSchemes;
      
      if (!colorSchemes || !colorSchemes[property]) {
        console.warn(`No color scheme found for property: ${property}`);
        return Array.from({ length: 100 }, () => '#CCCCCC');
      }

      const colors = colorSchemes[property];
      
      if (property === 'error' && colors.length === 3) {
        const displayMin = displayMinValue.value;
        const displayMax = displayMaxValue.value;
        const midpoint = (displayMin + displayMax) / 2;
        
        const negativeScale = scaleLinear()
          .domain([displayMin, midpoint])
          .range([colors[0], colors[1]])
          .interpolate(interpolateRgb);
          
        const positiveScale = scaleLinear()
          .domain([midpoint, displayMax])
          .range([colors[1], colors[2]])
          .interpolate(interpolateRgb);
          
        return Array.from({ length: 100 }, (_, i) => {
          const value = displayMin + (i / 99) * (displayMax - displayMin);
          return value <= midpoint ? negativeScale(value) : positiveScale(value);
        });
      }
      
      // For non-error properties we simply interpolate colors
      return Array.from({ length: 100 }, (_, i) => {
        const t = i / 99;
        return interpolateRgb(colors[0], colors[1])(t);
      });
    });

    const startDrag = (event) => {
      isDragging.value = true;
      dragOffset.value = {
        x: event.clientX - position.value.x,
        y: event.clientY - position.value.y,
      };
      document.addEventListener('mousemove', drag);
      document.addEventListener('mouseup', stopDrag);
    };
  
    const drag = (event) => {
      if (isDragging.value) {
        position.value = {
          x: event.clientX - dragOffset.value.x,
          y: event.clientY - dragOffset.value.y,
        };
      }
    };
  
    const stopDrag = () => {
      isDragging.value = false;
      document.removeEventListener('mousemove', drag);
      document.removeEventListener('mouseup', stopDrag);
    };
  
    return {
      position,
      legendContainer,
      startDrag,
      interpolatedColorScale,
      mappedPropertyTitle,
      displayMinValue,
      displayMaxValue,
    };
  },
};
</script>

<style scoped>
.legend-container {
  position: absolute;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(21, 11, 11, 1);
  width: 180px;
  z-index: 1000;
  font-size: 14px;
  overflow: hidden;
}
  
.legend-header {
  display: flex;
  justify-content: space-between;
  /* align-items: center; */
  padding: 6px 4px;
  background-color: rgba(240, 240, 240, 0.7);
  cursor: move;
  line-height: 1;
}
  
.close-button {
  color: var(--color-text);
  background: none;
  font-size: 16px;
  cursor: pointer;
  padding: 0px 4px;
  line-height: 1;
}
  
.legend-content {
  padding: 12px;
  margin-top: 6px;
}
  
.color-scale {
  display: flex;
  height: 20px;
  margin-bottom: 4px;
}
  
.color-bar {
  flex-grow: 1;
}
  
.scale-labels {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}
</style>
