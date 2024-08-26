<!-- ToolbarComponent.vue -->
<template>
  <nav class="toolbar" aria-label="Map controls">
    <div class="toolbar-content">
      <div class="left-buttons">
        <button @click="toggleSidebar('run')" aria-label="Run Model">
          <Icon icon="mdi:play" />
          <span class="tooltip">Models</span>
        </button>
        <button @click="toggleSidebar('data')" aria-label="Data">
          <Icon icon="mdi:database" />
          <span class="tooltip">Data Selection</span>
        </button>
        <button @click="toggleSidebar('analysis')" aria-label="Analysis">
          <Icon icon="mdi:chart-bar" />
          <span class="tooltip">Analysis</span>
        </button>
        <button @click="toggleSidebar('mapping')" aria-label="Mapping">
          <Icon icon="mdi:map" />
          <span class="tooltip">Mapping</span>
        </button>
      </div>
      <div class="right-buttons">
        <button @click="toggleBasemap" aria-label="Toggle Basemap">
          <Icon icon="mdi:layers" />
          <span class="tooltip">Basemap</span>
        </button>
        <button @click="toggleBasemap" aria-label="Map Settings">
          <Icon icon="mdi:cog" />
          <span class="tooltip">Map Settings</span>
        </button>
        <div class="separator"></div>
        <button @click="$emit('zoom-in')" aria-label="Zoom In">
          <Icon icon="mdi:plus" />
          <span class="tooltip">Zoom In</span>
        </button>
        <button @click="$emit('reset-view')" aria-label="Reset View">
          <Icon icon="mdi:home" />
          <span class="tooltip">Reset View</span>
        </button>
        <button @click="$emit('zoom-out')" aria-label="Zoom Out">
          <Icon icon="mdi:minus" />
          <span class="tooltip">Zoom Out</span>
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
  background-color: var(--color-background-mute);
  border-bottom: 1px solid var(--color-border);
  border-top: 1px solid var(--color-border);
  padding: 6px 2px;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  height: 40px;
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  /* max-width: var(--max-width); */
  margin-top: 2px;
  margin: 0 auto;
  padding: 0 var(--space-medium);
}

.left-buttons, .right-buttons {
  display: flex;
}

.separator {
  width: 2px;
  height: 24px;
  background-color: var(--color-border);
  margin: 0 0;
}

button {
  margin-left: var(--space-small);
  margin-right: var(--space-small);
  padding: var(--space-xsmall) var(--space-xsmall);
  background-color: transparent;
  color: var(--color-primary);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

button:hover {
  background-color: transparent;
  color: var(--color-primary-dark);
}

button:hover .tooltip {
  visibility: visible;
  opacity: 1;
}

.tooltip {
  visibility: hidden;
  width: 100px;
  background-color: var(--color-tooltip-bg);
  color: var(--color-tooltip-text);
  text-align: center;
  border-radius: var(--border-radius);
  padding: var(--space-small) 0;
  position: absolute;
  z-index: var(--z-index-tooltip);
  bottom: 125%;
  left: 50%;
  margin-left: -50px;
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
  /* width: var(--icon-size);
  height: var(--icon-size); */
  width: 26px;
  height: 26px;
}
</style>
