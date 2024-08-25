<!-- ToolbarComponent.vue -->
<template>
  <nav class="toolbar" aria-label="Map controls">
    <div class="toolbar-content">
      <div class="left-buttons">
        <button @click="toggleSidebar('run')" aria-label="Run Model">
          <Icon icon="mdi:play" />
          <span class="tooltip">Run  Model</span>
        </button>
        <button @click="toggleSidebar('data')" aria-label="Data">
          <Icon icon="mdi:database" />
          <span class="tooltip">Data Selection</span>
        </button>
        <button @click="toggleSidebar('analysis')" aria-label="Analysis">
          <Icon icon="mdi:chart-bar" />
          <span class="tooltip">Analysis</span>
        </button>
        <button @click="toggleSidebar('analysis')" aria-label="Mapping">
          <Icon icon="mdi:map" />
          <span class="tooltip">Mapping</span>
        </button>
      </div>
      <div class="right-buttons">
        <button @click="$emit('zoom-in')" aria-label="Zoom In">
          <Icon icon="mdi:plus" />
          <span class="tooltip">Zoom In</span>
        </button>
        <button @click="$emit('zoom-out')" aria-label="Zoom Out">
          <Icon icon="mdi:minus" />
          <span class="tooltip">Zoom Out</span>
        </button>
        <button @click="$emit('reset-view')" aria-label="Reset View">
          <Icon icon="mdi:home" />
          <span class="tooltip">Reset View</span>
        </button>
        <button @click="toggleBasemap" aria-label="Toggle Basemap">
          <Icon icon="mdi:layers" />
          <span class="tooltip">Toggle Basemap</span>
        </button>
      </div>
    </div>
  </nav>
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
      console.log('ToolbarComponent: Emitting toggle-sidebar', panel) // Add this line for debugging
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
  background-color: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-small) 0;
  width: 100%;
  box-sizing: border-box;
  position: relative;
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 var(--space-medium);
}

.left-buttons, .right-buttons {
  display: flex;
}

button {
  margin-right: var(--space-medium);
  padding: var(--space-small) var(--space-medium);
  background-color: var(--color-primary);
  color: var(--color-text-button);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

button:hover {
  background-color: var(--color-primary-dark);
}

button:hover .tooltip {
  visibility: visible;
  opacity: 1;
}

.tooltip {
  visibility: hidden;
  width: 120px;
  background-color: var(--color-tooltip-bg);
  color: var(--color-tooltip-text);
  text-align: center;
  border-radius: var(--border-radius);
  padding: var(--space-small) 0;
  position: absolute;
  z-index: var(--z-index-tooltip);
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
  border-color: var(--color-tooltip-bg) transparent transparent transparent;
}

button svg {
  width: var(--icon-size);
  height: var(--icon-size);
}
</style>
