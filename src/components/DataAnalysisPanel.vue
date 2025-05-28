<template>
  <div class="bg-white p-6 rounded-lg shadow-md h-full flex flex-col overflow-y-auto max-h-screen">
    <h2 class="text-2xl font-bold text-green-600 mb-4">County Selection</h2>
    
    <div class="flex-grow space-y-4">
      <div class="mt-4 space-y-4">
        <!-- State Selector -->
        <label class="block text-sm font-medium text-gray-700">Select State:</label>
        <select
          v-model="selectedState"
          class="block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50 py-0.5 text-sm"
        >
          <option value="">All States</option>
          <option v-for="state in stateOptions" :key="state.code" :value="state.code">
            {{ state.name }}
          </option>
        </select>

        <label class="block text-sm font-medium text-gray-700">Select Counties:</label>
        <div v-for="(county, index) in selectedCounties" :key="index" class="space-y-0.5">
          <div class="flex items-center space-x-2">
            <!-- Use dropdown when state is selected, otherwise use text input -->
            <select
              v-if="selectedState"
              v-model="county.selectedFips"
              @change="selectCountyFromDropdown(index)"
              class="flex-grow block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50 py-0.5 text-sm"
            >
              <option value="">Choose a county...</option>
              <option 
                v-for="availableCounty in availableCountiesForState" 
                :key="availableCounty.fips" 
                :value="availableCounty.fips"
              >
                {{ availableCounty.name }}
              </option>
            </select>
            <input
              v-else
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
          <ul v-if="!selectedState && county.showSuggestions" class="bg-white border border-gray-300 rounded-md shadow-sm mt-1">
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
            <label class="text-sm font-medium text-gray-700">Units:</label>
            <select
              v-model="selectedUnit"
              class="rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
            >
              <option value="bu/acre">Bushels per Acre (bu/acre)</option>
              <option value="t/ha">Tonnes per Hectare (t/ha)</option>
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

          <div class="flex space-x-4 mb-4">
            <button
              @click="exportData"
              :disabled="!hasSelectedCounties || isExporting"
              class="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition duration-300 disabled:opacity-50 flex items-center justify-center"
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
              class="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300 disabled:opacity-50"
            >
              Display Time Series
            </button>

            <button
              @click="displayHistogram"
              class="flex-1 bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 transition duration-300"
            >
              Display Distribution
            </button>
          </div>

          <div class="mt-4 space-y-4">
            <!-- Plot Configuration Options -->
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
          </div>

          <!-- Time Series Plot Section -->
          <div v-if="showPlot" class="mt-6 border rounded-lg p-4 pb-8 mb-6">
            <div class="flex justify-between items-center mb-4 cursor-pointer" @click="showScatterSection = !showScatterSection">
              <h3 class="text-lg font-semibold text-green-600">Time Series Plot</h3>
              <button class="text-gray-500 hover:text-gray-700">
                <span v-if="showScatterSection">▼</span>
                <span v-else>▶</span>
              </button>
            </div>
            
            <div v-if="showScatterSection">
              <div class="mb-4 space-y-4">
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
              
              <ScatterPlot
                :datasets="plotData"
                :display-mode="plotDisplayMode"
                :offset-step="parseFloat(plotOffset)"
                :crop-type="plotCropType.charAt(0).toUpperCase() + plotCropType.slice(1)"
                height="500px"
              />
            </div>
          </div>
          
          <!-- Histogram Plot Section -->
          <div v-if="showHistogram" class="mt-2 border rounded-lg p-4 pb-8">
            <div class="flex justify-between items-center mb-4 cursor-pointer" @click="showHistogramSection = !showHistogramSection">
              <h3 class="text-lg font-semibold text-green-600">Yield Distribution (All Counties)</h3>
              <button class="text-gray-500 hover:text-gray-700">
                <span v-if="showHistogramSection">▼</span>
                <span v-else>▶</span>
              </button>
            </div>
            
            <div v-if="showHistogramSection">
              <div class="mb-4 space-y-4">
                <div class="flex items-center space-x-4">
                  <label class="text-sm font-medium text-gray-700">Year:</label>
                  <select
                    v-model="histogramYear"
                    class="flex-1 rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
                  >
                    <option v-for="year in [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]" :key="year" :value="year">{{ year }}</option>
                  </select>
                </div>

                <div class="flex items-center space-x-4">
                  <label class="text-sm font-medium text-gray-700">Bin Count:</label>
                  <input
                    type="range"
                    v-model="histogramBins"
                    min="5"
                    max="20"
                    step="1"
                    class="flex-1"
                  />
                  <span class="text-sm text-gray-600 w-12">{{ histogramBins }}</span>
                </div>
              </div>
              
              <HistogramPlot
                :all-counties-data="allCountiesData"
                :display-mode="plotDisplayMode"
                :crop-type="plotCropType.charAt(0).toUpperCase() + plotCropType.slice(1)"
                :bin-count="parseInt(histogramBins)"
                :year="histogramYear"
                height="500px"
              />
            </div>
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
import HistogramPlot from './HistogramPlot.vue'

export default {
  name: 'DataAnalysisPanel',
  components: {
    ScatterPlot,
    HistogramPlot
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
          selectedFips: '',
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

    // Plot-related variables - moved to the top so they're available for all functions
    const showPlot = ref(false)
    const showHistogram = ref(false)
    const plotData = ref([])
    const plotDisplayMode = ref('both')
    const plotCropType = ref('corn')
    const plotOffset = ref('0.1')
    const plotType = ref('scatter')
    const histogramBins = ref(10)
    const histogramYear = ref(2024)
    const showScatterSection = ref(true)
    const showHistogramSection = ref(true)
    const allCountiesData = ref([])

    const selectedUnit = computed({
      get: () => store.state.currentUnit,
      set: value => store.commit('setCurrentUnit', value)
    })

    // Helper function to fetch prediction data - moved up to be available for other functions
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

    const selectedState = ref('')
    
    // Store available states based on actual data
    const availableStates = ref(new Set())
    
    // Fetch available states based on prediction data
    const fetchAvailableStates = async () => {
      const statesWithData = new Set()
      
      try {
        // Check for data in the most recent year for the current crop
        const data = await fetchPredictionData(plotCropType.value, 2024, '284')
        if (data) {
          data.forEach(row => {
            if (row.FIPS) {
              const fips = row.FIPS.toString().padStart(5, '0')
              const stateCode = fips.substring(0, 2)
              statesWithData.add(stateCode)
            }
          })
        }
      } catch (error) {
        console.error('Error fetching available states:', error)
      }
      
      availableStates.value = statesWithData
    }
    
    // Compute state options based on available states
    const stateOptions = computed(() => {
      return Object.entries(stateCodeMap)
        .filter(([code, name]) => availableStates.value.has(code))
        .map(([code, name]) => ({ code, name }))
        .sort((a, b) => a.name.localeCompare(b.name))
    })

    // Fetch available states when crop type changes
    watch(plotCropType, async () => {
      await fetchAvailableStates()
      // Clear state selection if current state doesn't have data for the new crop
      if (selectedState.value && !availableStates.value.has(selectedState.value)) {
        selectedState.value = ''
      }
    }, { immediate: true })

    // Get available counties from the prediction data when a state is selected
    const availableCountiesForState = ref([])
    const fetchAvailableCountiesForState = async () => {
      if (!selectedState.value) {
        availableCountiesForState.value = []
        return
      }

      const uniqueCounties = new Map()
      
      // Fetch prediction data to get available counties
      try {
        const data = await fetchPredictionData(plotCropType.value, 2024, '284')
        if (data) {
          // Import county boundaries to get proper names
          const { default: countyBoundaries } = await import('@/assets/gz_2010_us_050_00_20m.json')
          
          data.forEach(row => {
            if (row.FIPS) {
              const fips = row.FIPS.toString().padStart(5, '0')
              const stateCode = fips.substring(0, 2)
              
              if (stateCode === selectedState.value) {
                // Find the county in the GeoJSON data
                const countyFeature = countyBoundaries.features.find(feature => {
                  const featureFips = `${feature.properties.STATE}${feature.properties.COUNTY.padStart(3, '0')}`
                  return featureFips === fips
                })
                
                if (countyFeature) {
                  const countyName = countyFeature.properties.NAME
                  const stateName = stateCodeMap[stateCode] || 'Unknown State'
                  uniqueCounties.set(fips, {
                    fips: fips,
                    name: `${countyName} County, ${stateName}`
                  })
                }
              }
            }
          })
        }
      } catch (error) {
        console.error('Error fetching available counties:', error)
      }

      availableCountiesForState.value = Array.from(uniqueCounties.values())
        .sort((a, b) => a.name.localeCompare(b.name))
    }

    // Watch for state or crop changes to update available counties
    watch([selectedState, plotCropType], () => {
      fetchAvailableCountiesForState()
    }, { immediate: true })

    // Reset counties when state changes
    watch(selectedState, () => {
      selectedCounties.value = [{
        input: '',
        selected: null,
        selectedFips: '',
        showSuggestions: false,
        filteredSuggestions: []
      }]
      store.commit('setSelectedCountyFIPS', [])
      store.commit('setSelectedCounties', selectedCounties.value)
    })

    // Helper to extract state FIPS from full county FIPS
    const getStateCode = (fips) => fips?.toString().substring(0, 2)

    // Ensure external additions (e.g., map click) respect current state filter
    watch(() => store.state.selectedCounties, (newCounties) => {
      // If a state filter is active, drop counties from other states
      if (selectedState.value) {
        const filtered = newCounties.filter(c => !c.selected || getStateCode(c.selected.fips) === selectedState.value)
        if (filtered.length !== newCounties.length) {
          store.commit('setSelectedCounties', filtered)
          const newFips = filtered.filter(c => c.selected).map(c => c.selected.fips)
          store.commit('setSelectedCountyFIPS', newFips)
          return // avoid local update until store emits next tick
        }
      }
      // Ensure all counties have the selectedFips property
      selectedCounties.value = newCounties.map(county => ({
        ...county,
        selectedFips: county.selectedFips || (county.selected ? county.selected.fips : '')
      }))
    }, { deep: true })

    const countySuggestions = computed(() => {
      const uniqueCounties = new Map()
      if (csvData.value) {
        csvData.value.forEach(row => {
          const stateCode = row.FIPS.substring(0, 2)

          // Filter by selected state if one is chosen
          if (selectedState.value && stateCode !== selectedState.value) return

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
      // Block selection if it conflicts with chosen state
      const suggestionState = suggestion.fips.substring(0, 2)
      if (selectedState.value && suggestionState !== selectedState.value) {
        return // ignore mismatching county
      }

      selectedCounties.value[index] = {
        input: suggestion.name,
        selected: {
          fips: suggestion.fips,
          name: suggestion.name
        },
        selectedFips: suggestion.fips,
        showSuggestions: false,
        filteredSuggestions: []
      }
      updateSelectedFIPS()
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
        selectedFips: '',
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
            selectedFips: '',
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
        selectedFips: '',
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
    
    async function displayHistogram() {
      showHistogram.value = true
      await fetchAllCountiesData()
      // Ensure the histogram section is visible
      showHistogramSection.value = true
    }

    watch([plotDisplayMode, plotCropType], () => {
      if (showPlot.value) {
        displayPlot()
      }
      if (showHistogram.value) {
        fetchAllCountiesData()
      }
    })

    // Function to fetch data for all counties for the histogram
    async function fetchAllCountiesData() {
      allCountiesData.value = []
      const year = histogramYear.value
      const day = '284' // End of season

      try {
        const data = await fetchPredictionData(plotCropType.value, year, day)
        if (data) {
          data.forEach(row => {
            if (row.y_test || row.y_test_pred) {
              allCountiesData.value.push({
                fips: row.FIPS,
                actual: row.y_test ? parseFloat(row.y_test) : null,
                predicted: row.y_test_pred ? parseFloat(row.y_test_pred) : null,
                uncertainty: row.y_test_pred_uncertainty ? parseFloat(row.y_test_pred_uncertainty) : null
              })
            }
          })
        }
      } catch (error) {
        console.error('Error fetching all counties data:', error)
      }
    }

    // Update all counties data when crop type or year changes
    watch([plotCropType, histogramYear], async () => {
      if (showHistogram.value) {
        await fetchAllCountiesData()
      }
    }, { immediate: false })

    // Initial fetch of all counties data
    fetchAllCountiesData()

    // New function to handle dropdown selection
    function selectCountyFromDropdown(index) {
      const fips = selectedCounties.value[index].selectedFips
      if (!fips) {
        clearCounty(index)
        return
      }

      const county = availableCountiesForState.value.find(c => c.fips === fips)
      if (county) {
        selectedCounties.value[index] = {
          input: county.name,
          selected: {
            fips: county.fips,
            name: county.name
          },
          selectedFips: county.fips,
          showSuggestions: false,
          filteredSuggestions: []
        }
        updateSelectedFIPS()
      }
    }

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
      showHistogram,
      plotData,
      plotDisplayMode,
      displayPlot,
      displayHistogram,
      plotCropType,
      plotOffset,
      selectedUnit,
      plotType,
      histogramBins,
      histogramYear,
      showScatterSection,
      showHistogramSection,
      allCountiesData,
      selectedState,
      stateOptions,
      availableCountiesForState,
      selectCountyFromDropdown
    }
  }
}
</script>