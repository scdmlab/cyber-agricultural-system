<template>
  <div v-if="isVisible" class="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-50 bg-white bg-opacity-80 p-2 rounded shadow-md flex flex-col items-center w-3/4 max-w-3xl">
    <div class="flex items-center w-full mb-2">
      <button @click="togglePlay" class="mr-2 p-1 bg-blue-500 text-white rounded">
        {{ isPlaying ? '⏸' : '▶' }}
      </button>
      <!-- Year dropdown -->
      <select 
        :value="currentYear" 
        @change="updateYear($event)"
        class="mr-2 p-1 bg-white border border-gray-300 rounded"
      >
        <option v-for="year in yearRange" :key="year" :value="year">
          {{ year }}
        </option>
      </select>
      <!-- Existing property dropdown -->
      <select v-model="selectedProperty" class="mr-2 p-1 bg-white border border-gray-300 rounded">
        <option value="yield">Yield</option>
        <option value="pred">Prediction</option>
        <option value="error">Error</option>
        <option value="uncertainty">Uncertainty</option>
      </select>
      <input
        type="range"
        :min="2001"
        :max="2024"
        :value="currentYear"
        @input="updateYear"
        class="flex-grow appearance-none bg-gray-200 h-1 rounded-full outline-none slider-thumb"
      />
    </div>
    <div class="text-xs font-bold">Year: {{ currentYear }} &nbsp;&nbsp; {{ currentProperty }}</div>
  </div>
</template>

<script>
import { ref, computed, onUnmounted, watch, onMounted } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'YearSlider',
  setup() {
    const store = useStore()
    const isPlaying = ref(false)
    let intervalId = null

    const currentYear = computed(() => store.state.currentYear)
    const selectedProperty = ref('yield') // Set default value
    const propertyMap = {
      'yield': 'Yield',
      'pred': 'Model Prediction',
      'error': 'Prediction Error',
      'uncertainty': 'Prediction Uncertainty'
    }
    const currentProperty = computed(() => propertyMap[selectedProperty.value])
    const isVisible = computed(() => store.state.yearSliderVisible)

    // Add onMounted to initialize default values
    onMounted(async () => {
      await store.dispatch('initializeMapState')
    })

    // Add computed property for year range
    const yearRange = computed(() => {
      const years = []
      for (let year = 2001; year <= 2024; year++) {
        years.push(year)
      }
      return years
    })

    // Modify updateYear to handle both slider and dropdown
    const updateYear = (event) => {
      const newYear = typeof event === 'object' 
        ? parseInt(event.target.value) 
        : parseInt(event)
      store.commit('setYear', newYear)
    }

    const togglePlay = () => {
      isPlaying.value = !isPlaying.value
      if (isPlaying.value) {
        playYears()
      } else {
        stopPlaying()
      }
    }

    const playYears = () => {
      intervalId = setInterval(() => {
        let nextYear = store.state.currentYear + 1
        if (nextYear > 2024) {
          nextYear = 2001
        }
        store.commit('setYear', nextYear)
      }, 1000) // Change year every second
    }

    const stopPlaying = () => {
      clearInterval(intervalId)
    }

    onUnmounted(() => {
      stopPlaying()
    })

    watch(selectedProperty, (newValue) => {
      store.commit('setProperty', newValue)
    })

    return {
      currentYear,
      currentProperty,
      updateYear,
      isVisible,
      isPlaying,
      togglePlay,
      selectedProperty,
      yearRange
    }
  }
}
</script>

<style>
.slider-thumb::-webkit-slider-thumb {
  @apply appearance-none w-4 h-4 bg-blue-500 rounded-full cursor-pointer;
}
.slider-thumb::-moz-range-thumb {
  @apply w-4 h-4 bg-blue-500 rounded-full cursor-pointer border-none;
}
</style>
