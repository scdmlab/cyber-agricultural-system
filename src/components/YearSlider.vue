<template>
  <div v-if="isVisible" class="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-50 bg-white bg-opacity-80 p-2 rounded shadow-md flex flex-col items-center w-3/4 max-w-3xl">
    <div class="flex items-center w-full mb-2">
      <!-- Play/Pause Button -->
      <button @click="togglePlay" class="mr-2 p-1 bg-blue-500 text-white rounded hover:bg-blue-600">
        {{ isPlaying ? '⏸' : '▶' }}
      </button>

      <!-- Crop Selection -->
      <select 
        v-model="selectedCrop"
        class="mr-2 p-1 bg-white border border-gray-300 rounded"
        @change="handleCropChange"
      >
        <option value="corn">Corn</option>
        <option value="soybean">Soybean</option>
      </select>

      <!-- Property Selection -->
      <select 
        v-model="selectedProperty"
        class="mr-2 p-1 bg-white border border-gray-300 rounded"
        @change="handlePropertyChange"
      >
        <option value="pred">Predicted Yield (bu/acre)</option>
        <option value="error">Prediction Error (bu/acre)</option>
        <option value="uncertainty">Model Uncertainty</option>
      </select>

      <!-- Prediction Type -->
      <select 
        v-model="selectedPredictionType"
        class="mr-2 p-1 bg-white border border-gray-300 rounded"
      >
        <option value="end-of-season">End of Season</option>
        <option value="in-season">In Season</option>
      </select>

      <!-- Year Selection -->
      <select 
        v-model="currentYear"
        class="mr-2 p-1 bg-white border border-gray-300 rounded"
      >
        <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
      </select>

      <!-- Slider (for days in in-season mode, years in end-of-season mode) -->
      <input
        type="range"
        :min="sliderMin"
        :max="sliderMax"
        :value="selectedPredictionType === 'in-season' ? selectedDayIndex : currentYear"
        @input="handleSliderChange"
        class="flex-grow appearance-none bg-gray-200 h-1 rounded-full outline-none slider-thumb"
      />
    </div>
    <div class="text-xs font-bold">
      Year: {{ currentYear }} | 
      {{ selectedPredictionType === 'in-season' 
        ? `Day: ${dayMapping[sortedDays[selectedDayIndex].day]}` 
        : 'End of Season' 
      }} |
      Property: {{ propertyLabels[selectedProperty] }}
    </div>
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
    const selectedPredictionType = ref(store.state.currentPredictionType)
    const selectedProperty = ref(store.state.currentProperty)
    const selectedDayIndex = ref(0)
    const isPlaying = ref(false)
    const intervalId = ref(null)

    const propertyLabels = {
      pred: 'Predicted Yield',
      error: 'Prediction Error',
      uncertainty: 'Model Uncertainty'
    }

    const dayMapping = {
      "060": "March 1",
      "076": "March 17",
      "092": "April 2",
      "108": "April 18",
      "124": "May 4",
      "140": "May 20",
      "156": "June 5",
      "172": "June 21",
      "188": "July 7",
      "204": "July 23",
      "220": "August 8",
      "236": "August 24",
      "252": "September 9",
      "268": "September 25",
      "284": "October 11"
    }

    const sortedDays = computed(() => {
      return Object.entries(dayMapping)
        .sort(([dayA], [dayB]) => parseInt(dayA) - parseInt(dayB))
        .map(([day, date]) => ({ day, date }))
    })

    const years = computed(() => {
      return Array.from({ length: 9 }, (_, i) => (2015 + i).toString())
    })

    const sliderMin = computed(() => {
      return selectedPredictionType.value === 'in-season' ? 0 : 2015
    })

    const sliderMax = computed(() => {
      return selectedPredictionType.value === 'in-season' 
        ? sortedDays.value.length - 1 
        : 2023
    })

    const currentYear = computed({
      get: () => store.state.currentYear,
      set: value => store.commit('setYear', value)
    })

    const isVisible = computed(() => store.state.yearSliderVisible)

    async function updatePredictions() {
      store.commit('setCrop', selectedCrop.value)
      store.commit('setProperty', selectedProperty.value)
      store.commit('setPredictionType', selectedPredictionType.value)
      if (selectedPredictionType.value === 'in-season') {
        store.commit('setPredictionDay', sortedDays.value[selectedDayIndex.value].day)
      }
      await store.dispatch('fetchPredictionData')
    }

    const handleCropChange = async () => {
      await updatePredictions()
    }

    const handlePropertyChange = async () => {
      await updatePredictions()
    }

    const handleSliderChange = async (event) => {
      const value = parseInt(event.target.value)
      if (selectedPredictionType.value === 'in-season') {
        selectedDayIndex.value = value
        store.commit('setPredictionDay', sortedDays.value[value].day)
      } else {
        store.commit('setYear', value.toString())
      }
      await updatePredictions()
    }

    watch([selectedPredictionType], async (newVal) => {
      if (newVal === 'in-season') {
        selectedDayIndex.value = sortedDays.value.findIndex(d => d.day === store.state.currentDay) || 0
      }
      await updatePredictions()
    })

    const togglePlay = () => {
      isPlaying.value = !isPlaying.value
      if (isPlaying.value) {
        playAnimation()
      } else {
        stopPlaying()
      }
    }

    const playAnimation = () => {
      intervalId.value = setInterval(async () => {
        if (selectedPredictionType.value === 'in-season') {
          // Animate through days
          let nextIndex = selectedDayIndex.value + 1
          if (nextIndex >= sortedDays.value.length) {
            nextIndex = 0
          }
          selectedDayIndex.value = nextIndex
          store.commit('setPredictionDay', sortedDays.value[nextIndex].day)
        } else {
          // Animate through years
          let nextYear = parseInt(currentYear.value) + 1
          if (nextYear > sliderMax.value) {
            nextYear = sliderMin.value
          }
          store.commit('setYear', nextYear.toString())
        }
        await updatePredictions()
      }, 1000)
    }

    const stopPlaying = () => {
      clearInterval(intervalId.value)
    }

    return {
      selectedCrop,
      selectedPredictionType,
      selectedProperty,
      selectedDayIndex,
      dayMapping,
      sortedDays,
      years,
      sliderMin,
      sliderMax,
      isPlaying,
      currentYear,
      isVisible,
      propertyLabels,
      handleCropChange,
      handlePropertyChange,
      handleSliderChange,
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
