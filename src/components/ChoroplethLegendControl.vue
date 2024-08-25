<template>
    <div class="choropleth-legend maplibregl-ctrl">
      <div class="legend-title">{{ currentProperty }}</div>
      <div class="legend-scale">
        <div v-for="(color, index) in legendColors" :key="index" class="legend-item">
          <div class="color-box" :style="{ backgroundColor: color }"></div>
          <span class="legend-label">{{ legendLabels[index] }}</span>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { computed } from 'vue'
  
  export default {
    name: 'ChoroplethLegendControl',
    props: {
      map: {
        type: Object,
        required: true
      },
      colorScale: {
        type: Function,
        required: true
      },
      minValue: {
        type: Number,
        required: true
      },
      maxValue: {
        type: Number,
        required: true
      },
      currentProperty: {
        type: String,
        required: true
      }
    },
    setup(props) {
      const legendColors = computed(() => {
        if (typeof props.colorScale !== 'function') {
          console.error('colorScale is not a function:', props.colorScale)
          return Array(5).fill('gray') // Fallback color
        }
  
        const steps = 5
        return Array.from({ length: steps }, (_, i) => {
          const value = props.minValue + (i / (steps - 1)) * (props.maxValue - props.minValue)
          return props.colorScale(value)
        })
      })
  
      const legendLabels = computed(() => {
        const steps = 5
        return Array.from({ length: steps }, (_, i) => {
          const value = props.minValue + (i / (steps - 1)) * (props.maxValue - props.minValue)
          return value.toFixed(2)
        })
      })
  
      return {
        legendColors,
        legendLabels
      }
    }
  }
  </script>
  
  <style scoped>
  .choropleth-legend {
    background-color: rgba(255, 255, 255, 0.8);
    border-radius: 4px;
    padding: 10px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
    position: absolute;
    top: 10px;
    right: 10px;
    max-width: 200px;
    z-index: 1;
    cursor: move;
  }
  
  .legend-title {
    font-weight: bold;
    margin-bottom: 5px;
  }
  
  .legend-scale {
    display: flex;
    flex-direction: column;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    margin-bottom: 2px;
  }
  
  .color-box {
    width: 20px;
    height: 20px;
    margin-right: 5px;
  }
  
  .legend-label {
    font-size: 12px;
  }
  </style>