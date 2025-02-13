<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Time Selection</h2>
    
    <div class="space-y-4">
      <div>
        <label for="crop" class="block text-sm font-medium text-gray-700">Crop:</label>
        <select
          id="crop"
          v-model="localCrop"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
        >
          <option value="corn">Corn</option>
          <option value="soybean">Soybean</option>
        </select>
      </div>
      
      <div>
        <label for="year" class="block text-sm font-medium text-gray-700">Year:</label>
        <select
          id="year"
          v-model="localYear"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
        >
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
      
      <div>
        <label for="predictionDay" class="block text-sm font-medium text-gray-700">Prediction Time:</label>
        <select
          id="predictionDay"
          v-model="localDay"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
        >
          <option v-for="{ day, date } in sortedDays" :key="day" :value="day">
            {{ date }}
          </option>
        </select>
      </div>
      
      <div>
        <label for="results" class="block text-sm font-medium text-gray-700">Results:</label>
        <select
          id="results"
          v-model="localProperty"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
        >
          <option value="pred">Predicted Yield (t/ha)</option>
          <option value="error">Prediction Error (t/ha)</option>
          <option value="uncertainty">Model Uncertainty</option>
        </select>
      </div>
    </div>
    
    <button
      @click="applyChanges"
      class="mt-6 w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300"
    >
      Apply Changes
    </button>
    
    <button
      @click="exportData"
      :disabled="isExporting"
      class="mt-2 w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition duration-300 disabled:opacity-50 flex items-center justify-center"
    >
      <span v-if="isExporting" class="mr-2">
        <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </span>
      {{ isExporting ? 'Downloading...' : 'Export Data' }}
    </button>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import Papa from 'papaparse'

export default {
  name: 'DataSelectionPanel',
  setup() {
    const store = useStore()
    const isExporting = ref(false)
    
    // Local selections including unit
    const localSelections = ref({
      crop: store.state.currentCrop,
      year: store.state.currentYear,
      day: store.state.currentDay,
      property: store.state.currentProperty,
    })
    
    const localCrop = computed({
      get: () => localSelections.value.crop,
      set: value => localSelections.value.crop = value
    })
    
    const localYear = computed({
      get: () => localSelections.value.year,
      set: value => localSelections.value.year = value
    })
    
    const localDay = computed({
      get: () => localSelections.value.day,
      set: value => localSelections.value.day = value
    })
    
    const localProperty = computed({
      get: () => localSelections.value.property,
      set: value => localSelections.value.property = value
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

    const sortedDays = computed(() => {
      return Object.entries(dayMapping)
        .filter(([day]) => store.state.availableDays.includes(day))
        .sort(([dayA], [dayB]) => parseInt(dayA) - parseInt(dayB))
        .map(([day, date]) => ({ day, date }))
    })

    const years = computed(() => {
      const startYear = 2016
      const endYear = 2024
      return Array.from({ length: endYear - startYear + 1 }, (_, i) => (startYear + i).toString())
    })

    watch(
      [localCrop, localYear],
      async () => {
        await store.dispatch('updateAvailableDays')
      },
      { immediate: true }
    )

    async function applyChanges() {
      store.commit('setCrop', localSelections.value.crop)
      store.commit('setYear', localSelections.value.year)
      store.commit('setPredictionDay', localSelections.value.day)
      store.commit('setProperty', localSelections.value.property)
      
      await store.dispatch('fetchPredictionData')
    }

    async function fetchPredictionData(crop, year, day) {
      const baseUrl = import.meta.env.BASE_URL
      const csvPath = `${baseUrl}result_${crop}/bnn/result${year}_${day.toString().padStart(3, '0')}.csv`

      try {
        const response = await fetch(csvPath)
        if (!response.ok) {
          console.log(`No data found for ${csvPath}`)
          return null
        }
        const csvText = await response.text()
        return Papa.parse(csvText, { header: true, skipEmptyLines: true }).data
      } catch (error) {
        console.error(`Error fetching ${csvPath}:`, error)
        return null
      }
    }

    async function exportData() {
      isExporting.value = true
      try {
        const data = await fetchPredictionData(
          store.state.currentCrop,
          store.state.currentYear,
          store.state.currentDay
        )

        if (data && data.length > 0) {
          // Apply the correct conversion factor based on crop type
          const conversionFactor = store.state.currentCrop === 'corn' ? 0.06277 : 0.0673
          const unitLabel = ' (t/ha)'

          const formattedData = data.map(row => ({
            'FIPS': row.FIPS,
            'Crop type': store.state.currentCrop,
            'Year': store.state.currentYear,
            'Day of Year': store.state.currentDay,
            ['Predicted Yield' + unitLabel]: (parseFloat(row.y_test_pred) * conversionFactor).toFixed(3),
            ['NASS Reported Yield' + unitLabel]: (parseFloat(row.y_test) * conversionFactor).toFixed(3),
            ['Prediction Error' + unitLabel]: ((parseFloat(row.y_test_pred) - parseFloat(row.y_test)) * conversionFactor).toFixed(3),
            'Model Uncertainty': parseFloat(row.y_test_pred_uncertainty).toFixed(3) // Uncertainty remains as percentage
          }))

          const csv = Papa.unparse(formattedData)
          const blob = new Blob([csv], { type: 'text/csv' })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          const cropName = store.state.currentCrop.charAt(0).toUpperCase() + store.state.currentCrop.slice(1)
          const fileName = `${cropName}_Yield_Prediction_${store.state.currentYear}_Day${store.state.currentDay}.csv`
          a.download = fileName
          a.click()
          window.URL.revokeObjectURL(url)
        }
      } catch (error) {
        console.error('Export failed:', error)
      } finally {
        isExporting.value = false
      }
    }

    return {
      localCrop,
      localYear,
      localDay,
      localProperty,
      years,
      sortedDays,
      isExporting,
      exportData,
      applyChanges
    }
  }
}
</script>
