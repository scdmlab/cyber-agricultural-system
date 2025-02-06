<template>
  <div 
    v-if="isVisible" 
    class="absolute z-50 bg-white bg-opacity-80 p-4 rounded shadow-md flex flex-col items-center w-3/8 max-w-4xl"
    :style="{ left: position.x + 'px', top: position.y + 'px', transform: 'none' }"
    ref="sliderContainer"
  >
    <!-- Add drag handle -->
    <div 
      class="absolute top-0 left-0 w-full h-6 bg-gray-100 rounded-t cursor-move flex items-center px-2"
      @mousedown="startDrag"
    >
      <span class="text-gray-500 text-sm">⋮⋮ Drag to move</span>
      <!-- Existing close button -->
      <button 
        @click="closeSlider" 
        class="absolute top-0 right-2 text-gray-500 hover:text-black focus:outline-none"
        aria-label="Close year slider"
      >
        <span class="text-xl">×</span>
      </button>
    </div>

    <!-- Add h-fit to contain the height -->
    <div class="flex flex-col w-full h-fit">
      <div class="flex items-center w-full gap-2 mt-6">
        <!-- Main controls in a single row -->
        <select 
          v-model="selectedCrop"
          class="p-1 bg-white border border-gray-300 rounded w-22"
        >
          <option value="corn">Corn</option>
          <option value="soybean">Soybean</option>
        </select>

        <select 
          v-model="selectedProperty"
          class="p-1 bg-white border border-gray-300 rounded w-52"
        >
          <option value="pred">Predicted Yield (bu/acre)</option>
          <option value="error">Prediction Error (bu/acre)</option>
          <option value="uncertainty">Model Uncertainty</option>
        </select>

        <select 
          v-model="selectedDay"
          class="p-1 bg-white border border-gray-300 rounded w-55"
        >
          <option v-for="{ day, date } in sortedDays" :key="day" :value="day">
            {{ date }}
          </option>
        </select>

        <select 
          v-model="currentYear"
          class="p-1 bg-white border border-gray-300 rounded w-16"
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
      <div class="text-xs font-bold mt-2 mb-1">
        Year: {{ currentYear }} | 
        {{ dayMapping[selectedDay] }} |
        Property: {{ propertyLabels[selectedProperty] }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
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

    const selectedDay = computed({
      get: () => store.state.currentDay,
      set: value => store.commit('setPredictionDay', value)
    })

    const propertyLabels = {
      pred: 'Predicted Yield',
      error: 'Prediction Error',
      uncertainty: 'Model Uncertainty'
    }

    const dayMapping = {
      "140": "May 20 (In Season)",
      "156": "June 5 (In Season)",
      "172": "June 21 (In Season)",
      "188": "July 7 (In Season)",
      "204": "July 23 (In Season)",
      "220": "August 8 (In Season)",
      "236": "August 24 (In Season)",
      "252": "September 9 (In Season)",
      "268": "September 25 (In Season)",
      "284": "October 11 (End of Season)"
    }

    const sortedDays = computed(() => {
      return Object.entries(dayMapping)
        .sort(([dayA], [dayB]) => parseInt(dayA) - parseInt(dayB))
        .map(([day, date]) => ({ day, date }))
    })

    const years = computed(() => {
      const startYear = 2016
      const endYear = 2024
      return Array.from(
        { length: endYear - startYear + 1 }, 
        (_, i) => (startYear + i).toString()
      )
    })

    const sliderMin = computed(() => {
      if (animationType.value === 'year') {
        return 2016
      }
      return 0 // First month index
    })

    const sliderMax = computed(() => {
      if (animationType.value === 'year') {
        return 2024
      }
      return sortedDays.value.length - 1 // Last month index
    })

    const isVisible = computed(() => store.state.yearSliderVisible)

    const animationType = ref('year')

    const sliderValue = computed(() => {
      if (animationType.value === 'year') {
        return parseInt(currentYear.value)
      } else { // by month
        return sortedDays.value.findIndex(
          d => d.day === selectedDay.value
        )
      }
    })

    // Update predictions whenever any selection changes
    watch(
      [selectedCrop, selectedProperty, currentYear, selectedDay],
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
        store.commit('setYear', value.toString())
      } else {
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
          if (nextYear > 2024) {
            nextYear = 2016
          }
          store.commit('setYear', nextYear.toString())
          store.commit('setPredictionDay', sortedDays.value[0].day)
        } else {
          // Animate through months for the current year
          if (selectedDay.value === '284') {
            // Start from the first month if currently at end-of-season
            store.commit('setPredictionDay', sortedDays.value[0].day)
          } else {
            // Move to next month
            const currentDayIndex = sortedDays.value.findIndex(
              d => d.day === selectedDay.value
            )
            const nextIndex = (currentDayIndex + 1) % sortedDays.value.length
            if (nextIndex === 0) {
              // If we've gone through all months, move to next year
              let nextYear = parseInt(currentYear.value) + 1
              if (nextYear > 2024) {
                nextYear = 2016
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

    const closeSlider = () => {
      store.commit('toggleYearSlider')
    }

    // Add dragging functionality
    const position = ref({ x: 0, y: 0 })
    const isDragging = ref(false)
    const dragOffset = ref({ x: 0, y: 0 })
    const sliderContainer = ref(null)

    onMounted(() => {
      // Initialize position to bottom center
      const windowWidth = window.innerWidth
      const windowHeight = window.innerHeight
      position.value = {
        x: (windowWidth / 2) - 400, // Assuming width is roughly 800px
        y: windowHeight - 200
      }
    })

    const startDrag = (event) => {
      isDragging.value = true
      dragOffset.value = {
        x: event.clientX - position.value.x,
        y: event.clientY - position.value.y
      }

      // Add event listeners
      document.addEventListener('mousemove', handleDrag)
      document.addEventListener('mouseup', stopDrag)
    }

    const handleDrag = (event) => {
      if (isDragging.value) {
        // Calculate new position
        const newX = event.clientX - dragOffset.value.x
        const newY = event.clientY - dragOffset.value.y

        // Get window boundaries
        const windowWidth = window.innerWidth
        const windowHeight = window.innerHeight
        const elementWidth = sliderContainer.value?.offsetWidth || 800
        const elementHeight = sliderContainer.value?.offsetHeight || 200

        // Constrain to window boundaries
        position.value = {
          x: Math.min(Math.max(0, newX), windowWidth - elementWidth),
          y: Math.min(Math.max(0, newY), windowHeight - elementHeight)
        }
      }
    }

    const stopDrag = () => {
      isDragging.value = false
      document.removeEventListener('mousemove', handleDrag)
      document.removeEventListener('mouseup', stopDrag)
    }

    // Clean up event listeners
    onUnmounted(() => {
      document.removeEventListener('mousemove', handleDrag)
      document.removeEventListener('mouseup', stopDrag)
    })

    return {
      selectedCrop,
      selectedProperty,
      currentYear,
      selectedDay,
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
      closeSlider,
      position,
      startDrag,
      sliderContainer,
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

/* Add styles for drag handle */
.cursor-move {
  cursor: move;
}
</style>
