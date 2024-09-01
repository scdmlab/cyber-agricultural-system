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
        <button @click="toggleDataPopup">
          <Icon icon="mdi:table-filter" />
          <span class="tooltip">Data Table</span>
        </button>
        <div class="separator"></div>
        <button @click="toggleBasemapPopup" aria-label="Change Basemap">
          <Icon icon="tdesign:map-double"/>
          <span class="tooltip">Change Basemap</span>
        </button>
        <button @click="toggleSettings" aria-label="Map Settings">
          <Icon icon="mdi:cog" />
          <span class="tooltip">Map Settings</span>
        </button>
        <div class="separator"></div>
        <button @click="$emit('toggle-legend')" aria-label="Toggle Legend">
          <Icon icon="material-symbols:legend-toggle-rounded"/>
          <span class="tooltip">Toggle Legend</span>
        </button>
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

    <MapSettingsPopup
      v-if="showSettings"
      :minValue="minValue"
      :maxValue="maxValue"
      :colorScheme="colorScheme"
      :choroplethOpacity="choroplethOpacity"
      :basemapOpacity="basemapOpacity"
      @close="closeSettings"
      @apply="applySettings"
    />

    <DataTablePopup
      v-if="showDataPopup"
      :title="'Current Data'"
      :data="csvData"
      :headers="dataHeaders"
      @close="toggleDataPopup"
    />

    <BasemapPopup v-if="showBasemapPopup" @close="toggleBasemapPopup" />
  </nav>
</template>

<script>
import { Icon } from '@iconify/vue'
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import MapSettingsPopup from '@/components/MapSettingsPopup.vue'
import DataTablePopup from '@/components/DataTablePopup.vue'
import BasemapPopup from '@/components/BasemapPopup.vue'

export default {
  name: 'ToolbarComponent',
  components: {
    Icon,
    MapSettingsPopup,
    DataTablePopup,
    BasemapPopup
  },
  emits: ['zoom-in', 'zoom-out', 'reset-view', 'toggle-sidebar', 'update-settings', 'toggle-legend'],
  setup(props, { emit }) {
    const store = useStore() // Use Vuex store if needed
    const showSettings = ref(false)
    const showDataPopup = ref(false)
    const showBasemapPopup = ref(false)

    const toggleBasemapPopup = () => {
      showBasemapPopup.value = !showBasemapPopup.value
    }
    // Compute these values from your store or pass them as props from MapComponent
    const minValue = computed(() => store.state.minValue || 0)
    const maxValue = computed(() => store.state.maxValue || 100)
    const colorScheme = computed(() => store.state.colorScheme || ['#FFEDA0', '#FEB24C', '#F03B20'])
    const choroplethOpacity = computed(() => store.state.choroplethOpacity || 0.7)
    const basemapOpacity = computed(() => store.state.basemapOpacity || 1)

    const csvData = computed(() => store.state.csvData || [])
    const dataHeaders = computed(() => {
      if (csvData.value.length > 0) {
        return Object.keys(csvData.value[0])
      }
      return []
    })

    function toggleDataPopup() {
      showDataPopup.value = !showDataPopup.value
    }

    function toggleSidebar(panel) {
      emit('toggle-sidebar', panel)
    }

    function toggleSettings() {
      showSettings.value = !showSettings.value;
    }

    function closeSettings() {
      showSettings.value = false
      console.log('Closing settings') // Add this line for debugging
    }

    function applySettings(newSettings) {
      emit('update-settings', newSettings)
      closeSettings()
    }

    return {
      showSettings,
      minValue,
      maxValue,
      colorScheme,
      choroplethOpacity,
      basemapOpacity,
      toggleSidebar,
      toggleSettings,
      closeSettings,
      applySettings,
      toggleDataPopup,
      showDataPopup,
      csvData,
      dataHeaders,
      toggleBasemapPopup,
      showBasemapPopup
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
