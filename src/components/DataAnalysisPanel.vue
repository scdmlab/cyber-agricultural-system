<template>
  <div class="bg-white p-6 rounded-lg shadow-md h-full flex flex-col">
    <h2 class="text-2xl font-bold text-green-600 mb-4">County Selection</h2>
    
    <div class="flex-grow space-y-4">
      <div class="mt-4 space-y-4">
        <label class="block text-sm font-medium text-gray-700">Select Counties:</label>
        <div v-for="(county, index) in selectedCounties" :key="index" class="space-y-2">
          <div class="flex items-center space-x-2">
            <input
              :id="`county-input-${index}`"
              v-model="county.input"
              @input="updateSuggestions(index)"
              @keydown.enter="selectCounty(index)"
              placeholder="Type a county name"
              class="flex-grow mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
            />
            <button 
              @click="removeCounty(index)" 
              v-if="selectedCounties.length > 1" 
              class="bg-red-500 text-white p-2 rounded-md hover:bg-red-600 transition duration-300"
            >
              -
            </button>
          </div>
          <ul v-if="county.showSuggestions" class="bg-white border border-gray-300 rounded-md shadow-sm mt-1">
            <li
              v-for="suggestion in county.filteredSuggestions"
              :key="suggestion.fips"
              @click="selectSuggestion(suggestion, index)"
              class="p-2 hover:bg-gray-100 cursor-pointer"
            >
              {{ suggestion.name }}
            </li>
          </ul>
        </div>
        <button 
          @click="addCounty" 
          class="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300"
        >
          Add County
        </button>

        <div class="mt-6 space-y-4">
          <div class="flex items-center space-x-4">
            <label class="text-sm font-medium text-gray-700">Export Data For:</label>
            <select 
              v-model="exportCrop" 
              class="rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
            >
              <option value="all">All Crops</option>
              <option value="corn">Corn Only</option>
              <option value="soybean">Soybean Only</option>
            </select>
          </div>
          <button 
            @click="exportData" 
            :disabled="!hasSelectedCounties"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition duration-300 disabled:opacity-50"
          >
            Export Data
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { stateCodeMap } from '@/utils/stateCodeMap'
import Papa from 'papaparse'

export default {
  name: 'DataAnalysisPanel',
  setup() {
    const store = useStore()
    const selectedCounties = ref([{ 
      input: '', 
      showSuggestions: false, 
      selected: null, 
      filteredSuggestions: [] 
    }])
    const exportCrop = ref('all')
    const csvData = computed(() => store.state.csvData || [])
    const baseUrl = import.meta.env.BASE_URL

    const countySuggestions = computed(() => {
      const uniqueCounties = new Map()
      if (csvData.value) {
        csvData.value.forEach(row => {
          const stateCode = row.FIPS.substring(0, 2)
          const stateName = stateCodeMap[stateCode] || 'Unknown State'
          const name = `${row.NAME}, ${stateName}`
          uniqueCounties.set(row.FIPS, { name, fips: row.FIPS })
        })
      }
      return Array.from(uniqueCounties.values())
    })

    function updateSuggestions(index) {
      const county = selectedCounties.value[index]
      county.showSuggestions = county.input.length > 0
      county.filteredSuggestions = county.input ? 
        countySuggestions.value.filter(c => 
          c.name.toLowerCase().includes(county.input.toLowerCase())
        ).slice(0, 5) : []
    }

    function selectSuggestion(suggestion, index) {
      const county = selectedCounties.value[index]
      county.selected = suggestion
      county.input = suggestion.name
      county.showSuggestions = false
      console.log(`Selected county: ${suggestion.name} (FIPS: ${suggestion.fips})`)
    }

    async function fetchPredictionData(crop, year, day = null) {
      const csvPath = day 
        ? `${baseUrl}result_${crop}/bnn/result${year}_${day.toString().padStart(3, '0')}.csv`
        : `${baseUrl}result_${crop}/bnn/result${year}.csv`

      console.log(`Fetching data from: ${csvPath}`)
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
      console.log('Starting export process...')
      const selectedFips = selectedCounties.value
        .filter(c => c.selected)
        .map(c => c.selected.fips)
      
      if (selectedFips.length === 0) {
        console.log('No counties selected')
        return
      }

      const crops = exportCrop.value === 'all' 
        ? ['corn', 'soybean'] 
        : [exportCrop.value]

      const allData = []
      for (const crop of crops) {
        // End of season predictions (2015-2024)
        for (let year = 2015; year <= 2024; year++) {
          const data = await fetchPredictionData(crop, year)
          if (data) {
            data.forEach(row => {
              if (selectedFips.includes(row.FIPS)) {
                allData.push({
                  FIPS: row.FIPS,
                  crop,
                  year,
                  date: 'eos',
                  predicted: row.y_test_pred,
                  actual: row.y_test,
                  uncertainty: row.y_test_pred_uncertainty,
                  error: row.y_test_pred - row.y_test
                })
              }
            })
          }
        }

        // In-season predictions for 2024
        const days = ['060', '076', '092', '108', '124', '140', '156', '172', '188', '204', '220', '236', '252', '268', '284'] // Add more days if needed
        for (const day of days) {
          const data = await fetchPredictionData(crop, 2024, day)
          if (data) {
            data.forEach(row => {
              if (selectedFips.includes(row.FIPS)) {
                allData.push({
                  FIPS: row.FIPS,
                  crop,
                  year: 2024,
                  date: parseInt(day),
                  predicted: row.y_test_pred,
                  actual: row.y_test,
                  uncertainty: row.y_test_pred_uncertainty,
                  error: row.y_test_pred - row.y_test
                })
              }
            })
          }
        }
      }

      console.log(`Exporting ${allData.length} records`)
      const csv = Papa.unparse(allData)
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'prediction_data.csv'
      a.click()
      window.URL.revokeObjectURL(url)
    }

    function selectCounty(index) {
      const county = selectedCounties.value[index]
      if (county.filteredSuggestions.length) {
        selectSuggestion(county.filteredSuggestions[0], index)
      }
    }

    function addCounty() {
      selectedCounties.value.push({ 
        input: '', 
        showSuggestions: false, 
        selected: null, 
        filteredSuggestions: [] 
      })
    }

    function removeCounty(index) {
      selectedCounties.value.splice(index, 1)
    }

    const hasSelectedCounties = computed(() => {
      return selectedCounties.value.some(county => county.selected)
    })

    return {
      selectedCounties,
      exportCrop,
      updateSuggestions,
      selectSuggestion,
      selectCounty,
      addCounty,
      removeCounty,
      hasSelectedCounties,
      exportData
    }
  }
}
</script>