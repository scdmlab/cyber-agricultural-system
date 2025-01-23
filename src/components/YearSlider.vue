<template>
  <div v-if="isVisible" class="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-50 bg-white bg-opacity-80 p-4 rounded shadow-md flex flex-col items-center w-3/4 max-w-4xl">
    <div class="flex items-center w-full gap-2">
      <!-- Main controls in a single row -->
      <select 
        v-model="selectedCrop"
        class="p-1 bg-white border border-gray-300 rounded w-24"
      >
        <option value="corn">Corn</option>
        <option value="soybean">Soybean</option>
      </select>

      <select 
        v-model="selectedProperty"
        class="p-1 bg-white border border-gray-300 rounded w-48"
      >
        <option value="pred">Predicted Yield (bu/acre)</option>
        <option value="error">Prediction Error (bu/acre)</option>
        <option value="uncertainty">Model Uncertainty</option>
      </select>

      <select 
        v-model="predictionSelection"
        class="p-1 bg-white border border-gray-300 rounded w-32"
      >
        <optgroup label="In Season">
          <option v-for="{ day, date } in sortedDays" :key="day" :value="`in-season-${day}`">
            {{ date }}
          </option>
        </optgroup>
        <optgroup label="End of Season">
          <option value="end-of-season">End of Season</option>
        </optgroup>
      </select>

      <select 
        v-model="currentYear"
        class="p-1 bg-white border border-gray-300 rounded w-20"
      >
        <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
      </select>

      <!-- Play button -->
      <button 
        @click="togglePlay" 
        class="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 w-10 h-10 flex items-center justify-center ml-2"
      >
        {{ isPlaying ? '⏸' : '▶' }}
      </button>

      <!-- Animation type radio buttons -->
      <div class="flex items-center gap-2 ml-2">
        <label class="inline-flex items-center">
          <input
            type="radio"
            v-model="animationType"
            value="year"
            class="form-radio text-blue-500"
          >
          <span class="ml-1 text-sm whitespace-nowrap">By Year</span>
        </label>
        <label class="inline-flex items-center ml-2">
          <input
            type="radio"
            v-model="animationType"
            value="month"
            class="form-radio text-blue-500"
          >
          <span class="ml-1 text-sm whitespace-nowrap">By Month</span>
        </label>
      </div>
    </div>

    <!-- Time slider -->
    <div class="w-full mt-3 flex items-center gap-2">
      <input
        type="range"
        :min="sliderMin"
        :max="sliderMax"
        :value="sliderValue"
        @input="handleSliderChange"
        class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
      >
    </div>

    <!-- Status display -->
    <div class="text-xs font-bold mt-2">
      Year: {{ currentYear }} | 
      {{ predictionSelection === 'end-of-season' ? 'End of Season' : dayMapping[predictionSelection.split('-')[2]] }} |
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
    const isPlaying = ref(false)
    const intervalId = ref(null)

    // Use computed properties with two-way binding
    const selectedCrop = computed({
      get: () => store.state.currentCrop,
      set: value => store.commit('setCrop', value)
    })

    const selectedProperty = computed({
      get: () => store.state.currentProperty,
      set: value => store.commit('setProperty', value)
    })

    const currentYear = computed({
      get: () => store.state.currentYear,
      set: value => store.commit('setYear', value)
    })

    const predictionSelection = computed({
      get: () => {
        if (store.state.currentPredictionType === 'end-of-season') {
          return 'end-of-season'
        }
        return `in-season-${store.state.currentDay}`
      },
      set: value => {
        if (value === 'end-of-season') {
          store.commit('setPredictionType', 'end-of-season')
          store.commit('setPredictionDay', null)
        } else {
          const day = value.split('-')[2]
          store.commit('setPredictionType', 'in-season')
          store.commit('setPredictionDay', day)
        }
      }
    })

    const propertyLabels = {
      pred: 'Predicted Yield',
      error: 'Prediction Error',
      uncertainty: 'Model Uncertainty'
    }

    const dayMapping = {
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
      const startYear = 2015
      const endYear = predictionSelection.value === 'end-of-season' ? 2023 : 2024
      return Array.from(
        { length: endYear - startYear + 1 }, 
        (_, i) => (startYear + i).toString()
      )
    })

    const sliderMin = computed(() => {
      if (animationType.value === 'year') {
        return 2015
      }
      return 0 // First month index
    })

    const sliderMax = computed(() => {
      if (animationType.value === 'year') {
        return 2023
      }
      return sortedDays.value.length - 1 // Last month index
    })

    const isVisible = computed(() => store.state.yearSliderVisible)

    const animationType = ref('year')

    const sliderValue = computed(() => {
      if (animationType.value === 'year') {
        return parseInt(currentYear.value)
      } else { // by month
        if (predictionSelection.value === 'end-of-season') {
          return 0 // default to first month when switching to month mode
        }
        return sortedDays.value.findIndex(
          d => d.day === predictionSelection.value.split('-')[2]
        )
      }
    })

    // Update predictions whenever any selection changes
    watch(
      [selectedCrop, selectedProperty, currentYear, predictionSelection],
      async () => {
        await updatePredictions()
      }
    )

    async function updatePredictions() {
      // Fetch new prediction data
      const predictions = await store.dispatch('fetchPredictionData')

      // Update choropleth with new data
      if (predictions && predictions.length > 0) {
        const values = predictions.map(p => p[selectedProperty.value]).filter(v => !isNaN(v))
        if (values.length > 0) {
          store.commit('setChoroplethSettings', {
            ...store.state.choroplethSettings,
            minValue: Math.min(...values),
            maxValue: Math.max(...values)
          })
        }
      }
    }

    const handleCropChange = async () => {
      await updatePredictions()
    }

    const handlePropertyChange = async () => {
      await updatePredictions()
    }

    const handleSliderChange = (event) => {
      const value = parseInt(event.target.value)
      if (animationType.value === 'year') {
        // Year mode - slide through years with end-of-season
        store.commit('setYear', value.toString())
        store.commit('setPredictionType', 'end-of-season')
        store.commit('setPredictionDay', null)
      } else {
        // Month mode - slide through months
        store.commit('setPredictionType', 'in-season')
        store.commit('setPredictionDay', sortedDays.value[value].day)
      }
      updatePredictions()
    }

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
        if (animationType.value === 'year') {
          // Always animate through years with end-of-season predictions
          let nextYear = parseInt(currentYear.value) + 1
          if (nextYear > 2023) {
            nextYear = 2015
          }
          store.commit('setYear', nextYear.toString())
          store.commit('setPredictionType', 'end-of-season')
          store.commit('setPredictionDay', null)
        } else {
          // Animate through months for the current year
          if (predictionSelection.value === 'end-of-season') {
            // Start from the first month if currently at end-of-season
            store.commit('setPredictionType', 'in-season')
            store.commit('setPredictionDay', sortedDays.value[0].day)
          } else {
            // Move to next month
            const currentDayIndex = sortedDays.value.findIndex(
              d => d.day === predictionSelection.value.split('-')[2]
            )
            const nextIndex = (currentDayIndex + 1) % sortedDays.value.length
            if (nextIndex === 0) {
              // If we've gone through all months, move to next year
              let nextYear = parseInt(currentYear.value) + 1
              if (nextYear > 2024) {
                nextYear = 2015
              }
              store.commit('setYear', nextYear.toString())
            }
            store.commit('setPredictionDay', sortedDays.value[nextIndex].day)
          }
        }
        await updatePredictions()
      }, 1000)
    }

    const stopPlaying = () => {
      clearInterval(intervalId.value)
    }

    return {
      selectedCrop,
      selectedProperty,
      currentYear,
      predictionSelection,
      isPlaying,
      dayMapping,
      sortedDays,
      years,
      sliderMin,
      sliderMax,
      isVisible,
      propertyLabels,
      handleCropChange,
      handlePropertyChange,
      handleSliderChange,
      togglePlay,
      animationType,
      sliderValue,
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

.slider-thumb::-webkit-slider-runnable-track {
  @apply h-2 rounded-lg bg-gray-200;
}

.slider-thumb::-moz-range-track {
  @apply h-2 rounded-lg bg-gray-200;
}

/* Existing radio button styles */
.form-radio {
  @apply h-4 w-4 text-blue-500 transition duration-150 ease-in-out;
}

.form-radio:focus {
  @apply ring-2 ring-offset-2 ring-blue-500;
}
</style>
