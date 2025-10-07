<template>
  <div 
    v-if="isVisible" 
    class="absolute z-50 bg-white bg-opacity-80 p-4 rounded shadow-md flex flex-col items-center"
    :class="[isCompact ? 'w-72' : 'w-3/8 max-w-4xl']"
    :style="{ left: position.x + 'px', top: position.y + 'px', transform: 'none' }"
    ref="sliderContainer"
  >
    <!-- Modified header with expand/collapse button -->
    <div 
      class="absolute top-0 left-0 w-full h-6 bg-gray-100 rounded-t cursor-move flex items-center px-2"
      @mousedown="startDrag"
    >
      <span class="text-gray-500 text-base">⋮⋮ Drag to move</span>
      <div class="absolute right-2 flex items-center gap-2">
        <button 
          @click="toggleCompact" 
          class="text-gray-500 hover:text-black focus:outline-none"
          :title="isCompact ? 'Expand' : 'Collapse'"
        >
          <span class="text-xl">{{ isCompact ? '⊏' : '⊐' }}</span>
        </button>
        <button 
          @click="closeSlider" 
          class="text-gray-500 hover:text-black focus:outline-none"
          aria-label="Close year slider"
        >
          <span class="text-xl">×</span>
        </button>
      </div>
    </div>

    <!-- Modified content layout -->
    <div class="flex flex-col w-full h-fit mt-6" :class="{ 'space-y-2': isCompact }">
      <!-- Controls with conditional layout -->
      <div :class="[
        'flex gap-2',
        isCompact ? 'flex-col' : 'items-center w-full'
      ]">
        <select 
          v-model="selectedCrop"
          class="p-1 bg-white border border-gray-300 rounded text-sm md:text-base"
          :class="[isCompact ? 'w-full' : 'w-22']"
        >
          <option value="corn">Corn</option>
          <option value="soybean">Soybean</option>
        </select>

        <select 
          v-model="selectedProperty"
          class="p-1 bg-white border border-gray-300 rounded text-sm md:text-base"
          :class="[isCompact ? 'w-full' : 'w-52']"
        >
          <option value="pred">Predicted Yield</option>
          <option value="error">Prediction Error</option>
          <option value="uncertainty">Model Uncertainty</option>
        </select>

        <select 
          v-model="selectedUnit"
          class="p-1 bg-white border border-gray-300 rounded text-sm md:text-base"
          :class="[isCompact ? 'w-full' : 'w-32']"
        >
          <option value="bu/acre">bu/acre</option>
          <option value="t/ha">t/ha</option>
        </select>

        <select 
          v-model="selectedDay"
          class="p-1 bg-white border border-gray-300 rounded text-sm md:text-base"
          :class="[isCompact ? 'w-full' : 'w-55']"
        >
          <option v-for="{ day, date } in sortedDays" :key="day" :value="day">
            {{ date }}
          </option>
        </select>

        <div :class="[
          'flex items-center',
          isCompact ? 'w-full justify-between' : 'gap-2'
        ]">
          <select 
            v-model="currentYear"
            class="p-1 bg-white border border-gray-300 rounded w-16"
          >
            <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
          </select>

          <button 
            @click="togglePlay" 
            class="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 w-10 h-10 flex items-center justify-center"
            :class="{ 'ml-2': !isCompact }"
          >
            {{ isPlaying ? '⏸' : '▶' }}
          </button>
        </div>

        <!-- Animation type radio buttons -->
        <div :class="[
          'flex items-center justify-between w-full px-1',
          isCompact ? 'mt-2' : 'ml-2'
        ]">
          <label class="inline-flex items-center">
            <input
              type="radio"
              v-model="animationType"
              value="year"
              class="form-radio text-blue-500"
            >
            <span class="ml-1 text-xs sm:text-sm whitespace-nowrap">By Year</span>
          </label>
          <label class="inline-flex items-center">
            <input
              type="radio"
              v-model="animationType"
              value="month"
              class="form-radio text-blue-500"
            >
            <span class="ml-1 text-xs sm:text-sm whitespace-nowrap">By Month</span>
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
      <div class="text-sm md:text-base font-bold mt-2 mb-1" :class="{ 'text-center': isCompact }">
        Year: {{ currentYear }} | 
        {{ dayMapping[selectedDay] }} |
        Property: {{ propertyLabels[selectedProperty] }} |
        Unit: {{ selectedUnit }}
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

    const selectedUnit = computed({
      get: () => store.state.currentUnit,
      set: value => store.commit('setCurrentUnit', value)
    })

    const currentYear = computed({
      get: () => store.state.currentYear,
      set: value => store.commit('setYear', value)
    })

    const selectedDay = computed({
      get: () => store.state.currentDay,
      set: value => store.commit('setPredictionDay', value)
    })

    const propertyLabels = computed(() => {
      const suffix = store.state.currentUnit === 't/ha' ? ' (t/ha)' : ' (bu/acre)';
      return {
        pred: 'Predicted Yield' + suffix,
        error: 'Prediction Error' + suffix,
        uncertainty: 'Model Uncertainty'
      }
    })

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

    const getCurrentDayOfYear = () => {
      const now = new Date()
      const start = new Date(now.getFullYear(), 0, 0)
      const diff = now - start
      const oneDay = 1000 * 60 * 60 * 24
      return Math.floor(diff / oneDay)
    }

    const isDateInFuture = (year, day) => {
      const currentYearValue = new Date().getFullYear()
      const currentDayOfYear = getCurrentDayOfYear()

      const yearNum = parseInt(year)
      const dayNum = parseInt(day)

      if (yearNum > currentYearValue) return true
      if (yearNum === currentYearValue && dayNum > currentDayOfYear) return true
      return false
    }

    const getMostRecentValidDate = () => {
      const currentYearValue = new Date().getFullYear()
      const currentDayOfYear = getCurrentDayOfYear()

      // All possible days in descending order
      const possibleDays = ["284", "268", "252", "236", "220", "204", "188", "172", "156", "140"]

      // For current year, find most recent day that's not in the future
      for (const day of possibleDays) {
        if (parseInt(day) <= currentDayOfYear) {
          return { year: currentYearValue.toString(), day }
        }
      }

      // If no valid day found for current year, use last year's last day
      return { year: (currentYearValue - 1).toString(), day: possibleDays[0] }
    }

    const sortedDays = computed(() => {
      // Filter by available days from the store (based on actual file existence)
      const availableDays = store.state.availableDays || []
      return Object.entries(dayMapping)
        .filter(([day]) => availableDays.includes(day))
        .sort(([dayA], [dayB]) => parseInt(dayA) - parseInt(dayB))
        .map(([day, date]) => ({ day, date }))
    })

    const years = computed(() => {
      const startYear = 2016
      const endYear = 2025
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
        return 2025
      }
      return sortedDays.value.length - 1 // Last month index
    })

    const isVisible = computed(() => store.state.yearSliderVisible)

    const animationType = ref('year')

    // Watch for future date selections
    watch(
      () => ({ year: currentYear.value, day: selectedDay.value }),
      (newVal) => {
        // Check if date is in future
        if (isDateInFuture(newVal.year, newVal.day)) {
          alert('Data is not available. Please check again later.')
          const validDate = getMostRecentValidDate()
          store.commit('setYear', validDate.year)
          store.commit('setPredictionDay', validDate.day)
        }
      }
    )

    const sliderValue = computed(() => {
      if (animationType.value === 'year') {
        return parseInt(currentYear.value)
      } else { // by month
        return sortedDays.value.findIndex(
          d => d.day === selectedDay.value
        )
      }
    })

    // Update available days when crop or year changes
    watch(
      [selectedCrop, currentYear],
      async () => {
        await store.dispatch('updateAvailableDays')
      },
      { immediate: true }
    )

    // Update predictions whenever any selection changes
    watch(
      [selectedCrop, selectedProperty, currentYear, selectedDay, selectedUnit],
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
          if (nextYear > 2025) {
            nextYear = 2016
          }

          // Check if next year/day combo is valid
          const testDay = sortedDays.value[0]?.day || '140'
          if (isDateInFuture(nextYear.toString(), testDay)) {
            // Stop at most recent valid date
            const validDate = getMostRecentValidDate()
            store.commit('setYear', validDate.year)
            store.commit('setPredictionDay', validDate.day)
            stopPlaying()
            return
          }

          store.commit('setYear', nextYear.toString())
          store.commit('setPredictionDay', sortedDays.value[0].day)
        } else {
          // Animate through months for the current year
          const currentDayIndex = sortedDays.value.findIndex(
            d => d.day === selectedDay.value
          )
          const nextIndex = currentDayIndex + 1

          if (nextIndex >= sortedDays.value.length) {
            // Move to next year and first day
            let nextYear = parseInt(currentYear.value) + 1
            if (nextYear > 2025) {
              nextYear = 2016
            }

            const testDay = sortedDays.value[0]?.day || '140'
            if (isDateInFuture(nextYear.toString(), testDay)) {
              // Stop at most recent valid date
              const validDate = getMostRecentValidDate()
              store.commit('setYear', validDate.year)
              store.commit('setPredictionDay', validDate.day)
              stopPlaying()
              return
            }

            store.commit('setYear', nextYear.toString())
            store.commit('setPredictionDay', sortedDays.value[0].day)
          } else {
            // Check if next day is in future
            const nextDay = sortedDays.value[nextIndex].day
            if (isDateInFuture(currentYear.value, nextDay)) {
              // Stop at most recent valid date
              const validDate = getMostRecentValidDate()
              store.commit('setYear', validDate.year)
              store.commit('setPredictionDay', validDate.day)
              stopPlaying()
              return
            }

            store.commit('setPredictionDay', nextDay)
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

    // Add isCompact state
    const isCompact = ref(false)
    
    const toggleCompact = () => {
      isCompact.value = !isCompact.value
    }

    return {
      selectedCrop,
      selectedProperty,
      currentYear,
      selectedDay,
      selectedUnit,
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
      isCompact,
      toggleCompact,
    }
  }
}
</script>

<style>
/* Font size responsive utilities */
.text-responsive {
  font-size: clamp(0.875rem, 1vw + 0.5rem, 1.125rem);
}

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
