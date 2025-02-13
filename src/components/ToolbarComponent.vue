<!-- ToolbarComponent.vue -->
<template>
  <div>
    <nav class="relative bg-gray-100 border-b border-gray-200 shadow-sm py-0.5 px-4 z-30" aria-label="Map controls">
      <div class="flex justify-between items-center h-full w-full">
        <!-- Left group -->
        <div class="flex items-center space-x-2">
          <button @click="toggleSidebar('data')" aria-label="Data" class="toolbar-button">
            <Icon icon="mdi:database" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Time Selection</span>
          </button>
          <button @click="toggleSidebar('analysis')" aria-label="Analysis" class="toolbar-button">
            <Icon icon="mdi:chart-bar" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">County Selection</span>
          </button>
          <button @click="toggleSidebar('mapping')" aria-label="Mapping" class="toolbar-button">
            <Icon icon="mdi:map" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Yield Map</span>
          </button>
        </div>

        <!-- Right group -->
        <div class="flex items-center space-x-2">
          <!-- Commented out data table button
          <button @click="toggleDataPopup" class="toolbar-button">
            <Icon icon="mdi:table-filter" class="text-gray-600" />
            <span class="tooltip">Data Table</span>
          </button>
          <div class="h-6 w-px bg-gray-600 mx-2"></div>
          -->
          <button @click="toggleBasemapPopup" aria-label="Change Basemap" class="toolbar-button">
            <Icon icon="tdesign:map-double" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Change Basemap</span>
          </button>
          <button @click="toggleSettings" aria-label="Map Settings" class="toolbar-button">
            <Icon icon="mdi:cog" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Map Settings</span>
          </button>
          <div class="h-6 w-px bg-gray-600 mx-2"></div>
          <button @click="$emit('toggle-legend')" aria-label="Toggle Legend" class="toolbar-button">
            <Icon icon="material-symbols:legend-toggle-rounded" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Toggle Legend</span>
          </button>
          <div class="h-6 w-px bg-gray-600 mx-2"></div>
          <button @click="$emit('zoom-in')" aria-label="Zoom In" class="toolbar-button">
            <Icon icon="mdi:plus" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Zoom In</span>
          </button>
          <button @click="$emit('reset-view')" aria-label="Reset View" class="toolbar-button">
            <Icon icon="mdi:home" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Reset View</span>
          </button>
          <button @click="$emit('zoom-out')" aria-label="Zoom Out" class="toolbar-button">
            <Icon icon="mdi:minus" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Zoom Out</span>
          </button>
          <div class="h-6 w-px bg-gray-600 mx-2"></div>
          <button @click="toggleYearSlider" aria-label="Toggle Year Slider" class="toolbar-button">
            <Icon icon="mdi:calendar-range" class="text-gray-600" width="24" height="24" />
            <span class="tooltip">Toggle Year Slider</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- Add popups -->
    <MapSettingsPopup
      v-if="showSettings"
      :min-value="minValue"
      :max-value="maxValue"
      :color-scheme="colorScheme"
      :choropleth-opacity="choroplethOpacity"
      :basemap-opacity="basemapOpacity"
      @close="closeSettings"
      @apply="applySettings"
    />

    <BasemapPopup
      v-if="showBasemapPopup"
      @close="toggleBasemapPopup"
    />
  </div>
</template>

<script>
import { Icon } from '@iconify/vue'
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import MapSettingsPopup from '@/components/MapSettingsPopup.vue'
import BasemapPopup from '@/components/BasemapPopup.vue'

export default {
  name: 'ToolbarComponent',
  components: {
    Icon,
    MapSettingsPopup,
    BasemapPopup
  },
  emits: [
    'zoom-in',
    'zoom-out',
    'reset-view',
    'toggle-sidebar',
    'update-settings',
    'toggle-legend',
    'toggle-year-slider'
  ],
  setup(props, { emit }) {
    const store = useStore() // Use Vuex store if needed
    const showSettings = ref(false)
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

    function toggleYearSlider() {
      store.commit('toggleYearSlider')
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
      toggleBasemapPopup,
      showBasemapPopup,
      toggleYearSlider
    }
  }
}
</script>

<style scoped>
nav {
  height: 36px;
  width: 100%;
  display: flex;
  align-items: center; /* Center all content vertically */
}

.toolbar-button {
  @apply p-1 rounded-full transition-colors duration-200 ease-in-out relative;
  @apply hover:bg-gray-200 focus:outline-none focus:ring-1 focus:ring-green-500;
  @apply flex items-center justify-center; /* Center icon within button */
  z-index: 30;
}

.tooltip {
  @apply absolute bottom-full left-1/2 transform -translate-x-1/2 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded-md opacity-0 transition-opacity duration-300 pointer-events-none mb-2;
  z-index: 31;
}

.toolbar-button:hover .tooltip {
  @apply opacity-100;
}

.toolbar-button svg {
  @apply w-6 h-6;
  width: 24px !important;
  height: 24px !important;
  color: currentColor;
}

.h-6 {
  height: 16px;
  margin-top: auto;
  margin-bottom: auto;
}
</style>
