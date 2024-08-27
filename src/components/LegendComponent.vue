<template>
    <div ref="legendContainer" class="legend-container" :style="{ left: position.x + 'px', top: position.y + 'px' }">
      <div class="legend-header" @mousedown="startDrag">
        <span>Legend</span>
        <button @click="$emit('close')" class="close-button">&times;</button>
      </div>
      <div class="legend-content">
        <div class="color-scale">
          <div v-for="(color, index) in interpolatedColorScale" :key="index" :style="{ backgroundColor: color }" class="color-bar"></div>
        </div>
        <div class="scale-labels">
          <span>{{ minValue.toFixed(2) }}</span>
          <span>{{ maxValue.toFixed(2) }}</span>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, computed } from 'vue';
  import { scaleLinear } from 'd3-scale';
  import { interpolateRgb } from 'd3-interpolate';
  
  export default {
    name: 'LegendComponent',
    props: {
      minValue: { type: Number, required: true },
      maxValue: { type: Number, required: true },
      colorScale: { type: Array, required: true },
    },
    emits: ['close'],
    setup(props) {
      const position = ref({ x: window.innerWidth - 250, y: window.innerHeight - 200 });
      const isDragging = ref(false);
      const dragOffset = ref({ x: 0, y: 0 });
      const legendContainer = ref(null);
  
      const interpolatedColorScale = computed(() => {
        const scale = scaleLinear()
          .domain([0, props.colorScale.length - 1])
          .range([props.minValue, props.maxValue]);
  
        const colorInterpolator = scaleLinear()
          .domain(props.colorScale.map((_, i) => scale(i)))
          .range(props.colorScale)
          .interpolate(interpolateRgb);
  
        return Array.from({ length: 100 }, (_, i) => colorInterpolator(scale(i / 99)));
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