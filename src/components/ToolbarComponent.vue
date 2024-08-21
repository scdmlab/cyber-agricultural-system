<!-- ToolbarComponent.vue -->
<template>
  <div class="toolbar">
    <button @click="toggleBasemap" class="tooltip">
      <Icon icon="mdi:map" />
      <span class="tooltiptext">Toggle Basemap</span>
    </button>
    <button @click="zoomIn" class="tooltip">
      <Icon icon="mdi:plus" />
      <span class="tooltiptext">Zoom In</span>
    </button>
    <button @click="zoomOut" class="tooltip">
      <Icon icon="mdi:minus" />
      <span class="tooltiptext">Zoom Out</span>
    </button>
    <button @click="resetView" class="tooltip">
      <Icon icon="mdi:refresh" />
      <span class="tooltiptext">Reset View</span>
    </button>
  </div>
</template>

<script>
import { Icon } from '@iconify/vue'

export default {
  name: 'ToolbarComponent',
  components: {
    Icon
  },
  methods: {
    toggleBasemap() {
      // Implement basemap toggle functionality
      console.log('Toggle basemap')
    },
    zoomIn() {
      // Implement zoom in functionality
      console.log('Zoom in')
    },
    zoomOut() {
      // Implement zoom out functionality
      console.log('Zoom out')
    },
    resetView() {
      // Implement reset view functionality
      console.log('Reset view')
    }
  }
}
</script>

<style scoped>
.toolbar {
  background-color: #f0f0f0;
  padding: 5px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

button {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 30px;
  height: 30px;
  margin-right: 5px;
  padding: 5px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #45a049;
}

.tooltip {
  position: relative;
  display: inline-block;
}

.tooltip .tooltiptext {
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

.tooltip .tooltiptext::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: #555 transparent transparent transparent;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}

/* Style for the icons */
button :deep(svg) {
  width: 20px;
  height: 20px;
}
</style>