<template>
  <div class="bg-white p-6 rounded-lg shadow-md h-full flex flex-col overflow-y-auto">
    <h2 class="text-2xl font-bold text-green-600 mb-4">County Selection</h2>
    
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
              <option value="all">All Time</option>
              <option value="eos">End of Season Only</option>
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
                min="2016"
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
            :disabled="!hasSelectedCounties || isExporting"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition duration-300 disabled:opacity-50 flex items-center justify-center mb-4"
          >
            <span v-if="isExporting" class="mr-2">
              <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </span>
            {{ isExporting ? 'Downloading...' : 'Export Data' }}
          </button>

          <button
            @click="displayPlot"
            :disabled="!hasSelectedCounties"
            class="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300 disabled:opacity-50"
          >
            Display Historical Yields
          </button>

          <div class="mt-4 space-y-4">
            <div class="flex items-center space-x-4">
              <label class="text-sm font-medium text-gray-700">Display Mode:</label>
              <select
                v-model="plotDisplayMode"
                class="flex-1 rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
              >
                <option value="predicted">Predictions Only (with uncertainty)</option>
                <option value="both">Predictions & Actual Yields</option>
              </select>
            </div>

            <div class="flex items-center space-x-4">
              <label class="text-sm font-medium text-gray-700">Crop Type:</label>
              <select
                v-model="plotCropType"
                class="flex-1 rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
              >
                <option value="corn">Corn</option>
                <option value="soybean">Soybean</option>
              </select>
            </div>

            <div class="flex items-center space-x-4">
              <label class="text-sm font-medium text-gray-700">County Offset:</label>
              <input
                type="range"
                v-model="plotOffset"
                min="0"
                max="0.3"
                step="0.01"
                class="flex-1"
              />
              <span class="text-sm text-gray-600 w-12">{{ plotOffset }}</span>
            </div>
          </div>

          <div v-if="showPlot" class="mt-4">
            <ScatterPlot
              :datasets="plotData"
              :display-mode="plotDisplayMode"
              :offset-step="parseFloat(plotOffset)"
              :crop-type="plotCropType.charAt(0).toUpperCase() + plotCropType.slice(1)"
              height="500px"
            />
          </div>
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
import ScatterPlot from './ScatterPlot.vue'

export default {
  name: 'DataAnalysisPanel',
  components: {
    ScatterPlot
  },
  setup() {
    const store = useStore()
    
    watch(() => store.state.selectedCounties, (newCounties) => {
      selectedCounties.value = newCounties;
    }, { deep: true });

    const selectedCounties = ref(store.state.selectedCounties.length > 0
      ? store.state.selectedCounties
      : [{
          input: '',
          selected: null,
          showSuggestions: false,
          filteredSuggestions: []
        }]
    );

    watch(() => store.state.selectedCountyFIPS, (newFIPS) => {
      const currentFIPS = selectedCounties.value
        .filter(c => c.selected)
        .map(c => c.selected.fips)
      
      if (!arraysEqual(currentFIPS, newFIPS)) {
        store.commit('setSelectedCounties', selectedCounties.value);
      }
    })

    watch(selectedCounties, (newCounties) => {
      const newFIPS = newCounties
        .filter(c => c.selected)
        .map(c => c.selected.fips)
      
      store.commit('setSelectedCountyFIPS', newFIPS);
    }, { deep: true })

    function arraysEqual(a, b) {
      if (a.length !== b.length) return false;
      return a.every((val, idx) => val === b[idx]);
    }

    const exportCrop = ref('all')
    const yearRange = ref('all')
    const startYear = ref(2016)
    const endYear = ref(2024)
    const predictionTime = ref('all')
    
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

    const isExporting = ref(false)

    async function exportData() {
      isExporting.value = true
      try {
        const selectedCountyData = selectedCounties.value
          .filter(c => c.selected)
          .map(c => ({
            fips: c.selected.fips,
            name: c.selected.name
          }))
        
        if (selectedCountyData.length === 0) {
          console.error('No counties selected')
          return
        }

        const crops = exportCrop.value === 'all'
          ? ['corn', 'soybean']
          : [exportCrop.value]

        const yearStart = yearRange.value === 'all' ? 2016 : parseInt(startYear.value)
        const yearEnd = yearRange.value === 'all' ? 2024 : parseInt(endYear.value)

        const unit = store.state.currentUnit
        const conversionFactor = unit === 't/ha'
          ? (store.state.currentCrop === 'corn' ? 0.06277 : 0.0673)
          : 1
        const unitLabel = unit === 't/ha' ? ' (t/ha)' : ' (bu/acre)'

        for (const crop of crops) {
          const allData = []
          let daysToFetch = []
          
          switch (predictionTime.value) {
            case 'all':
              daysToFetch = ['140', '156', '172', '188', '204', '220', '236', '252', '268', '284']
              break
            case 'eos':
              daysToFetch = ['284']
              break
          }

          for (let year = yearStart; year <= yearEnd; year++) {
            for (const day of daysToFetch) {
              const data = await fetchPredictionData(crop, year, day)
              if (data) {
                data.forEach(row => {
                  const countyData = selectedCountyData.find(c => c.fips === row.FIPS)
                  if (countyData) {
                    const predicted = row.y_test_pred * conversionFactor
                    const actual = row.y_test * conversionFactor
                    const uncertainty = row.y_test_pred_uncertainty * conversionFactor
                    const error = predicted - actual

                    allData.push({
                      'FIPS': row.FIPS,
                      'County': countyData.name,
                      'Crop type': crop,
                      'Year': year,
                      'Day of Year': day,
                      ['Predicted Yield' + unitLabel]: predicted.toFixed(3),
                      ['NASS Reported Yield' + unitLabel]: actual.toFixed(3),
                      ['Prediction Error' + unitLabel]: error.toFixed(3),
                      'Model Uncertainty': uncertainty.toFixed(3)
                    })
                  }
                })
              }
            }
          }

          if (allData.length > 0) {
            const csv = Papa.unparse(allData)
            const blob = new Blob([csv], { type: 'text/csv' })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            const cropName = crop.charAt(0).toUpperCase() + crop.slice(1)
            a.download = `${cropName}_Yield_Prediction_Results_${unit}.csv`
            a.click()
            window.URL.revokeObjectURL(url)
          }
        }
      } catch (error) {
        console.error('Export failed:', error)
      } finally {
        isExporting.value = false
      }
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
      const county = selectedCounties.value[index]
      if (county.selected) {
        store.commit('removeSelectedCountyFIPS', county.selected.fips)
      } else {
        selectedCounties.value.splice(index, 1)
        if (selectedCounties.value.length === 0) {
          selectedCounties.value.push({
            input: '',
            selected: null,
            showSuggestions: false,
            filteredSuggestions: []
          })
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

    function updateSelectedFIPS() {
      const selectedFIPS = selectedCounties.value
        .filter(c => c.selected)
        .map(c => c.selected.fips)
      store.commit('setSelectedCountyFIPS', selectedFIPS)
    }

    const hasSelectedCounties = computed(() => {
      return selectedCounties.value.some(county => county.selected)
    })

    const showPlot = ref(false)
    const plotData = ref([])
    const plotDisplayMode = ref('both')
    const plotCropType = ref('corn')
    const plotOffset = ref('0.1')

    async function displayPlot() {
      showPlot.value = true
      plotData.value = []

      const selectedCountyData = selectedCounties.value
        .filter(c => c.selected)
        .map(c => ({
          fips: c.selected.fips,
          name: c.selected.name
        }))

      const unit = store.state.currentUnit
      const conversionFactor = unit === 't/ha'
        ? (plotCropType.value === 'corn' ? 0.06277 : 0.0673)
        : 1

      for (const county of selectedCountyData) {
        const countyData = {
          countyName: county.name,
          actualData: [],
          predictedData: [],
          uncertainties: []
        }

        for (let year = 2016; year <= 2024; year++) {
          const data = await fetchPredictionData(plotCropType.value, year, '284')
          if (data) {
            const countyYield = data.find(row => row.FIPS === county.fips)
            if (countyYield) {
              if (countyYield.y_test) {
                countyData.actualData.push({
                  x: year,
                  y: parseFloat(countyYield.y_test) * conversionFactor
                })
              }
              
              if (countyYield.y_test_pred) {
                countyData.predictedData.push({
                  x: year,
                  y: parseFloat(countyYield.y_test_pred) * conversionFactor
                })
                
                if (countyYield.y_test_pred_uncertainty) {
                  const uncertainty = parseFloat(countyYield.y_test_pred_uncertainty) * conversionFactor
                  const uncertaintyPercent = (uncertainty / (parseFloat(countyYield.y_test_pred) * conversionFactor)) * 100
                  countyData.uncertainties.push(uncertaintyPercent)
                }
              }
            }
          }
        }

        plotData.value.push(countyData)
      }
    }

    watch([plotDisplayMode, plotCropType], () => {
      if (showPlot.value) {
        displayPlot()
      }
    })

    return {
      selectedCounties,
      exportCrop,
      yearRange,
      startYear,
      endYear,
      predictionTime,
      updateSuggestions,
      selectSuggestion,
      selectCounty,
      addCounty,
      removeCounty,
      clearCounty,
      hasSelectedCounties,
      exportData,
      isExporting,
      showPlot,
      plotData,
      plotDisplayMode,
      displayPlot,
      plotCropType,
      plotOffset
    }
  }
}
</script>