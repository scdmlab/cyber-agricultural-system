<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Time Selection</h2>
    
    <div class="space-y-4">
      <div>
        <label for="crop" class="block text-sm font-medium text-gray-700">Crop:</label>
        <select id="crop" v-model="localCrop" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option value="corn">Corn</option>
          <option value="soybean">Soybean</option>
        </select>
      </div>
      
      <div>
        <label for="year" class="block text-sm font-medium text-gray-700">Year:</label>
        <select id="year" v-model="localYear" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
      
      <div>
        <label for="predictionType" class="block text-sm font-medium text-gray-700">Prediction Type:</label>
        <select id="predictionType" v-model="localPredictionType" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option value="end-of-season">End of Season</option>
          <option value="in-season">In Season</option>
        </select>
      </div>
      
      <div v-if="localPredictionType === 'in-season'">
        <label for="date" class="block text-sm font-medium text-gray-700">Prediction Date:</label>
        <select id="date" v-model="localDay" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option v-for="{ day, date } in sortedDays" :key="day" :value="day">{{ date }}</option>
        </select>
      </div>
      
      <div>
        <label for="results" class="block text-sm font-medium text-gray-700">Results:</label>
        <select id="results" v-model="localProperty" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option value="pred">Predicted Yield (bu/acre)</option>
          <!-- <option value="yield">Actual Yield: Unit: bu/acre</option> -->
          <option value="error">Prediction Error (bu/acre)</option>
          <option value="uncertainty">Model Uncertainty</option>
        </select>
      </div>
    </div>
    
    <button @click="applyDataSelection" class="mt-6 w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300">Apply</button>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'DataSelectionPanel',
  setup() {
    const store = useStore()
    const localCrop = ref(store.state.currentCrop)
    const localYear = ref(store.state.currentYear)
    const localDay = ref(store.state.currentDay)
    const localProperty = ref(store.state.currentProperty)
    const localPredictionType = ref(store.state.currentPredictionType)

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

    const years = computed(() => {
      return Array.from({ length: 10 }, (_, i) => (2015 + i).toString())
    })

    // Create a sorted entries array for the template
    const sortedDays = computed(() => {
      return Object.entries(dayMapping)
        .sort(([dayA], [dayB]) => parseInt(dayA) - parseInt(dayB))
        .map(([day, date]) => ({ day, date }))
    })

    // Watch for prediction type changes
    watch(localPredictionType, (newType) => {
      if (newType === 'end-of-season') {
        localDay.value = null // Clear day selection for end-of-season
      } else if (newType === 'in-season' && !localDay.value) {
        localDay.value = '188' // Set default day for in-season
      }
    })

    async function applyDataSelection() {
      // Update store state
      store.commit('setCrop', localCrop.value)
      store.commit('setYear', localYear.value)
      store.commit('setProperty', localProperty.value)
      store.commit('setPredictionType', localPredictionType.value)
      if (localPredictionType.value === 'in-season') {
        store.commit('setPredictionDay', parseInt(localDay.value))
      }

      // Fetch new prediction data
      const predictions = await store.dispatch('fetchPredictionData')

      // Update choropleth with new data
      if (predictions && predictions.length > 0) {
        const values = predictions.map(p => p[localProperty.value]).filter(v => !isNaN(v))
        if (values.length > 0) {
          const minValue = Math.min(...values)
          const maxValue = Math.max(...values)
          store.commit('setChoroplethSettings', {
            ...store.state.choroplethSettings,
            minValue,
            maxValue
          })
        }
      }
    }

    return {
      localCrop,
      localYear,
      localDay,
      localProperty,
      localPredictionType,
      years,
      sortedDays,
      applyDataSelection
    }
  }
}
</script>
