<template>
  <div class="bg-white p-6 rounded-lg shadow-md h-full flex flex-col">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Data Export </h2>
    
    <div class="flex-grow space-y-4">
      <div class="mt-4 space-y-4">
        <label class="block text-sm font-medium text-gray-700">Select Counties:</label>
        <div v-for="(county, index) in selectedCounties" :key="index" class="space-y-0.5">
          <div class="flex items-center space-x-2">
            <input
              :id="`county-input-${index}`"
              v-model="county.input"
              @input="updateSuggestions(index)"
              @keydown.enter="selectCounty(index)"
              placeholder="Type a county name"
              class="flex-grow block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50 py-0.5 text-sm"
            />
            <button 
              v-if="selectedCounties.length > 1"
              @click="removeCounty(index)" 
              class="bg-red-500 text-white px-2 py-0.5 rounded-md hover:bg-red-600 transition duration-300 text-sm"
              title="Remove county"
            >
              -
            </button>
            <button 
              v-else-if="county.selected"
              @click="clearCounty(index)" 
              class="bg-gray-400 text-white px-2 py-0.5 rounded-md hover:bg-gray-500 transition duration-300 text-sm"
              title="Clear selection"
            >
              ×
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
          
          <div class="flex items-center space-x-4">
            <label class="text-sm font-medium text-gray-700">Prediction Time:</label>
            <select 
              v-model="predictionTime" 
              class="rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
            >
              <option value="all">All Predictions</option>
              <option value="eos">End of Season Only</option>
              <option value="in-season">In Season Only</option>
              <option value="custom">Custom Day</option>
            </select>
          </div>

          <div v-if="predictionTime === 'custom'" class="flex items-center space-x-4">
            <select 
              v-model="selectedDay" 
              class="rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
            >
              <option v-for="{ day, date } in sortedDays" :key="day" :value="day">
                {{ date }} (Day {{ day }})
              </option>
            </select>
          </div>

          <div class="flex items-center space-x-4">
            <label class="text-sm font-medium text-gray-700">Year Range:</label>
            <select 
              v-model="yearRange" 
              class="rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
            >
              <option value="all">All Years</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>

          <div v-if="yearRange === 'custom'" class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <input 
                type="number"
                v-model="startYear"
                min="2015"
                :max="endYear"
                class="w-24 rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
              />
              <span class="text-gray-500">to</span>
              <input 
                type="number"
                v-model="endYear"
                :min="startYear"
                max="2024"
                class="w-24 rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
              />
            </div>
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
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { stateCodeMap } from '@/utils/stateCodeMap'
import Papa from 'papaparse'

export default {
  name: 'DataAnalysisPanel',
  setup() {
    const store = useStore()
    
    // Watch for changes in store's selectedCounties
    watch(() => store.state.selectedCounties, (newCounties) => {
      selectedCounties.value = newCounties;
    }, { deep: true });

    // Initialize selectedCounties from store
    const selectedCounties = ref(store.state.selectedCounties.length > 0 
      ? store.state.selectedCounties 
      : [{
          input: '',
          selected: null,
          showSuggestions: false,
          filteredSuggestions: []
        }]
    );

    // Watch for changes in store's selectedCountyFIPS
    watch(() => store.state.selectedCountyFIPS, (newFIPS) => {
      // Sync selectedCounties with store if they don't match
      const currentFIPS = selectedCounties.value
        .filter(c => c.selected)
        .map(c => c.selected.fips)
      
      if (!arraysEqual(currentFIPS, newFIPS)) {
        store.commit('setSelectedCounties', selectedCounties.value);
      }
    })

    // Watch for changes in local selectedCounties
    watch(selectedCounties, (newCounties) => {
      const newFIPS = newCounties
        .filter(c => c.selected)
        .map(c => c.selected.fips)
      
      store.commit('setSelectedCountyFIPS', newFIPS);
    }, { deep: true })

    // Helper function to compare arrays
    function arraysEqual(a, b) {
      if (a.length !== b.length) return false;
      return a.every((val, idx) => val === b[idx]);
    }

    const exportCrop = ref('all')
    const yearRange = ref('all')
    const startYear = ref(2015)
    const endYear = ref(2024)
    const predictionTime = ref('all')
    const selectedDay = ref('188')
    
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

    const csvData = computed(() => store.state.csvData || [])
    const baseUrl = import.meta.env.BASE_URL

    const countySuggestions = computed(() => {
      const uniqueCounties = new Map()
      if (csvData.value) {
        csvData.value.forEach(row => {
          const stateCode = row.FIPS.substring(0, 2)
          const stateName = stateCodeMap[stateCode] || 'Unknown State'
          const countyName = `${row.NAME} County, ${stateName}`
          uniqueCounties.set(row.FIPS, {
            fips: row.FIPS,
            name: countyName
          })
        })
      }
      return Array.from(uniqueCounties.values())
    })

    function updateSuggestions(index) {
      const input = selectedCounties.value[index].input.toLowerCase()
      if (input) {
        selectedCounties.value[index].filteredSuggestions = countySuggestions.value
          .filter(county => county.name.toLowerCase().includes(input))
        selectedCounties.value[index].showSuggestions = true
      } else {
        selectedCounties.value[index].filteredSuggestions = []
        selectedCounties.value[index].showSuggestions = false
      }
    }

    function selectSuggestion(suggestion, index) {
      selectedCounties.value[index] = {
        input: suggestion.name,
        selected: {
          fips: suggestion.fips,
          name: suggestion.name
        },
        showSuggestions: false,
        filteredSuggestions: []
      }
      updateSelectedFIPS()
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
      const selectedCountyData = selectedCounties.value
        .filter(c => c.selected)
        .map(c => ({
          fips: c.selected.fips,
          name: c.selected.name
        }))
      
      if (selectedCountyData.length === 0) {
        console.log('No counties selected')
        return
      }

      const crops = exportCrop.value === 'all' 
        ? ['corn', 'soybean'] 
        : [exportCrop.value]

      const yearStart = yearRange.value === 'all' ? 2015 : parseInt(startYear.value)
      const yearEnd = yearRange.value === 'all' ? 2024 : parseInt(endYear.value)

      const allData = []
      let daysToFetch = []
      
      // Determine which days to fetch based on predictionTime
      switch (predictionTime.value) {
        case 'all':
          daysToFetch = Object.keys(dayMapping)
          break
        case 'eos':
          daysToFetch = []
          break
        case 'in-season':
          daysToFetch = Object.keys(dayMapping)
          break
        case 'custom':
          daysToFetch = [selectedDay.value]
          break
      }

      for (const crop of crops) {
        for (let year = yearStart; year <= yearEnd; year++) {
          // Fetch end of season data if needed
          if (predictionTime.value === 'all' || predictionTime.value === 'eos') {
            const eosData = await fetchPredictionData(crop, year)
            if (eosData) {
              eosData.forEach(row => {
                const countyData = selectedCountyData.find(c => c.fips === row.FIPS)
                if (countyData) {
                  allData.push({
                    FIPS: row.FIPS,
                    county: countyData.name,
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

          // Fetch in-season predictions if needed
          if (daysToFetch.length > 0) {
            for (const day of daysToFetch) {
              const data = await fetchPredictionData(crop, year, day)
              if (data) {
                data.forEach(row => {
                  const countyData = selectedCountyData.find(c => c.fips === row.FIPS)
                  if (countyData) {
                    allData.push({
                      FIPS: row.FIPS,
                      county: countyData.name,
                      crop,
                      year,
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
      const county = selectedCounties.value[index];
      if (county.selected) {
        store.commit('removeSelectedCountyFIPS', county.selected.fips);
      } else {
        // If it's just an empty input, remove it directly
        selectedCounties.value.splice(index, 1);
        if (selectedCounties.value.length === 0) {
          selectedCounties.value.push({
            input: '',
            selected: null,
            showSuggestions: false,
            filteredSuggestions: []
          });
        }
      }
    }

    function clearCounty(index) {
      selectedCounties.value[index] = { 
        input: '', 
        showSuggestions: false, 
        selected: null, 
        filteredSuggestions: [] 
      }
      updateSelectedFIPS()
    }

    // Helper function to update store with current selections
    function updateSelectedFIPS() {
      const selectedFIPS = selectedCounties.value
        .filter(c => c.selected)
        .map(c => c.selected.fips)
      store.commit('setSelectedCountyFIPS', selectedFIPS)
    }

    const hasSelectedCounties = computed(() => {
      return selectedCounties.value.some(county => county.selected)
    })

    return {
      selectedCounties,
      exportCrop,
      yearRange,
      startYear,
      endYear,
      predictionTime,
      selectedDay,
      sortedDays,
      updateSuggestions,
      selectSuggestion,
      selectCounty,
      addCounty,
      removeCounty,
      clearCounty,
      hasSelectedCounties,
      exportData
    }
  }
}
</script>