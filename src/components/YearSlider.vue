<template>
  <div v-if="isVisible" class="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-50 bg-white bg-opacity-80 p-2 rounded shadow-md flex flex-col items-center w-3/4 max-w-3xl">
    <div class="flex items-center w-full mb-2">
      <button @click="togglePlay" class="mr-2 p-1 bg-blue-500 text-white rounded">
        {{ isPlaying ? '⏸' : '▶' }}
      </button>
      <!-- Crop dropdown -->
      <select 
        v-model="selectedCrop"
        class="mr-2 p-1 bg-white border border-gray-300 rounded"
        @change="handleCropChange"
      >
        <option value="corn">Corn</option>
        <option value="soybean">Soybean</option>
      </select>
      <!-- Year dropdown -->
      <select 
        :value="currentYear" 
        @change="updateYear($event)"
        class="mr-2 p-1 bg-white border border-gray-300 rounded"
      >
        <option v-for="year in availableYears" :key="year" :value="year">
          {{ year }}
        </option>
      </select>
      <!-- Property dropdown -->
      <select v-model="selectedProperty" class="mr-2 p-1 bg-white border border-gray-300 rounded">
        <option v-for="prop in availableProperties" :key="prop.value" :value="prop.value">
          {{ prop.label }}
        </option>
      </select>
      <input
        type="range"
        :min="sliderMin"
        :max="sliderMax"
        :value="currentYear"
        @input="updateYear"
        class="flex-grow appearance-none bg-gray-200 h-1 rounded-full outline-none slider-thumb"
      />
    </div>
    <div class="text-xs font-bold">Year: {{ currentYear }} &nbsp;&nbsp; {{ currentProperty }}</div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'YearSlider',
  setup() {
    const store = useStore()
    const selectedCrop = ref(store.state.currentCrop)
    const selectedProperty = ref(store.state.currentProperty)
    const isPlaying = ref(false)
    
    // Compute available years based on crop
    const availableYears = computed(() => {
      return selectedCrop.value === 'corn' 
        ? Array.from({ length: 24 }, (_, i) => (2001 + i).toString())
        : ['2024']
    })

    // Compute available properties based on crop
    const availableProperties = computed(() => {
      const commonProps = [
        { value: 'pred', label: 'Prediction' },
        { value: 'yield', label: 'Yield' },
        { value: 'uncertainty', label: 'Uncertainty' }
      ]
      
      return selectedCrop.value === 'corn' 
        ? [...commonProps, { value: 'error', label: 'Error' }]
        : commonProps
    })

    const handleCropChange = async () => {
      store.commit('setCrop', selectedCrop.value)
      // Update property if it's currently 'error'
      if (selectedProperty.value === 'error') {
        selectedProperty.value = 'pred'
        store.commit('setProperty', 'pred')
      }
      await store.dispatch('initializeMapState')
    }

    // Watch for property changes
    watch(selectedProperty, (newProperty) => {
      store.commit('setProperty', newProperty)
    })

    // Watch for crop changes
    watch(selectedCrop, async (newCrop) => {
      if (newCrop === 'soybean') {
        if (selectedProperty.value === 'error') {
          selectedProperty.value = 'pred'
        }
      }
    })

    const sliderMin = computed(() => selectedCrop.value === 'corn' ? 2001 : 2024)
    const sliderMax = computed(() => 2024)

    const currentYear = computed({
      get: () => store.state.currentYear,
      set: value => store.commit('setYear', value)
    })

    const currentProperty = computed({
      get: () => store.state.currentProperty,
      set: value => store.commit('setProperty', value)
    })

    const isVisible = computed(() => store.state.yearSliderVisible)

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

    const updateYear = (event) => {
      const newYear = typeof event === 'object' 
        ? parseInt(event.target.value) 
        : parseInt(event)
      store.commit('setYear', newYear)
    }

    return {
      selectedCrop,
      selectedProperty,
      availableYears,
      availableProperties,
      sliderMin,
      sliderMax,
      isPlaying,
      handleCropChange,
      currentYear,
      currentProperty,
      updateYear,
      isVisible,
      togglePlay
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
