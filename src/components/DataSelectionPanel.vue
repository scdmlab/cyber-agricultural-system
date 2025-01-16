<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Data Selection</h2>
    
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
          <option v-for="(date, day) in dayMapping" :key="day" :value="day">{{ date }}</option>
        </select>
      </div>
      
      <div>
        <label for="results" class="block text-sm font-medium text-gray-700">Results:</label>
        <select id="results" v-model="localProperty" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option value="pred">Prediction</option>
          <option value="yield">Actual Yield</option>
          <option value="error">Error</option>
          <option value="uncertainty">Uncertainty</option>
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
      "060": "03/01",
      "076": "03/17",
      "092": "04/02",
      "108": "04/18",
      "124": "05/04",
      "140": "05/20",
      "156": "06/05",
      "172": "06/21",
      "188": "07/07",
      "204": "07/23",
      "220": "08/08",
      "236": "08/24",
      "252": "09/09",
      "268": "09/25",
      "284": "10/11"
    }

    const years = computed(() => {
      return Array.from({ length: 10 }, (_, i) => (2015 + i).toString())
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
      dayMapping,
      applyDataSelection
    }
  }
}
</script>
