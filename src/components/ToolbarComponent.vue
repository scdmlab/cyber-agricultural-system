<!-- ToolbarComponent.vue -->
<template>
  <div class="toolbar">
    <div class="toolbar-content">
      <div class="left-buttons">
        <button @click="toggleSidebar('settings')">
          <Icon icon="mdi:cog" />
          <span class="tooltip">Settings</span>
        </button>
        <button @click="toggleSidebar('data')">
          <Icon icon="mdi:database" />
          <span class="tooltip">Data</span>
        </button>
        <button @click="toggleSidebar('analysis')">
          <Icon icon="mdi:chart-bar" />
          <span class="tooltip">Analysis</span>
        </button>
      </div>
      <div class="right-buttons">
        <button @click="$emit('zoom-in')">
          <Icon icon="mdi:plus" />
          <span class="tooltip">Zoom In</span>
        </button>
        <button @click="$emit('zoom-out')">
          <Icon icon="mdi:minus" />
          <span class="tooltip">Zoom Out</span>
        </button>
        <button @click="$emit('reset-view')">
          <Icon icon="mdi:home" />
          <span class="tooltip">Reset View</span>
        </button>
        <button @click="toggleBasemap">
          <Icon icon="mdi:layers" />
          <span class="tooltip">Toggle Basemap</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { Icon } from '@iconify/vue'

export default {
  name: 'ToolbarComponent',
  components: {
    Icon
  },
  emits: ['zoom-in', 'zoom-out', 'reset-view', 'toggle-sidebar'],
  methods: {
    toggleSidebar(panel) {
      this.$emit('toggle-sidebar', panel)
    },
    toggleBasemap() {
      // Implement basemap toggle functionality
      console.log('Toggle basemap')
    }
  }
}
</script>

<style scoped>
.toolbar {
  background-color: #f0f0f0;
  border-bottom: 1px solid #ccc;
  padding: 5px 0;
  width: 100%;
  box-sizing: border-box;
  position: relative;
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 10px;
}

.left-buttons, .right-buttons {
  display: flex;
}

button {
  margin-right: 10px;
  padding: 5px 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

button:hover {
  background-color: #45a049;
}

button:hover .tooltip {
  visibility: visible;
  opacity: 1;
}

.tooltip {
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

.tooltip::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: #555 transparent transparent transparent;
}

/* Style for the icons */
button svg {
  width: 20px;
  height: 20px;
}
</style>