<template>
  <div class="bg-white p-6 rounded-lg shadow-md h-full flex flex-col overflow-hidden">
    <h2 class="text-2xl font-bold text-green-600 mb-2">Download NASS Data</h2>
    <p class="text-sm text-gray-600 mb-4">
      Data from USDA NASS QuickStats (SURVEY program, CROPS sector, FIELD CROPS group)
    </p>
    
    <div class="flex flex-col space-y-4">
      <!-- Data Type Selection -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Statistic Category:</label>
        <select
          v-model="statisticCategory"
          class="w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
        >
          <option value="YIELD">Yield</option>
          <option value="AREA PLANTED">Planted Area</option>
          <option value="AREA HARVESTED">Harvested Area</option>
        </select>
      </div>

      <!-- Crop Selection -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Crop:</label>
        <select
          v-model="selectedCrop"
          class="w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
        >
          <option value="CORN">Corn</option>
          <option value="SOYBEANS">Soybean</option>
        </select>
      </div>

      <!-- Year Selection -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Year:</label>
        <input
          type="number"
          v-model="selectedYear"
          :min="2000"
          :max="2023"
          class="w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50"
        />
      </div>

      <!-- Preview Data Button -->
      <button
        @click="fetchData"
        :disabled="isLoading"
        class="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300 disabled:opacity-50 flex items-center justify-center"
      >
        <span v-if="isLoading" class="mr-2">
          <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </span>
        {{ isLoading ? 'Loading...' : 'Preview Data' }}
      </button>

      <!-- Download CSV Button - Moved above preview -->
      <button
        v-if="previewData.length > 0"
        @click="downloadCsv"
        :disabled="isDownloading"
        class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition duration-300 disabled:opacity-50 flex items-center justify-center"
      >
        <span v-if="isDownloading" class="mr-2">
          <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </span>
        {{ isDownloading ? 'Preparing Download...' : 'Download CSV' }}
      </button>

      <!-- Error Message -->
      <div v-if="error" class="text-red-600 text-sm">
        {{ error }}
      </div>

      <!-- Data Preview in scrollable container -->
      <div v-if="previewData.length > 0" class="flex-grow overflow-auto">
        <h3 class="text-lg font-semibold text-gray-700 mb-2">Preview:</h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(item, index) in previewData.slice(0, 5)" :key="index">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ item.location_desc }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ item.Value }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ item.unit_desc }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="text-sm text-gray-500 mt-2">
          Showing {{ Math.min(5, previewData.length) }} of {{ previewData.length }} records
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import Papa from 'papaparse'

export default {
  name: 'NassDataPanel',
  setup() {
    const statisticCategory = ref('YIELD')
    const selectedCrop = ref('CORN')
    const selectedYear = ref(Math.min(new Date().getFullYear(), 2023))
    const isLoading = ref(false)
    const previewData = ref([])
    const error = ref(null)
    const isDownloading = ref(false)
    
    const currentYear = Math.min(new Date().getFullYear(), 2023)

    const buildApiUrl = () => {
      const baseUrl = 'https://nass-crop-proxy.replit.app/api/nass'
      const params = new URLSearchParams({
        // key: API_KEY,
        commodity_desc: selectedCrop.value,
        year: selectedYear.value,
        agg_level_desc: 'COUNTY',
        statisticcat_desc: statisticCategory.value,
        // Adding required parameters based on NASS QuickStats API requirements
        source_desc: 'SURVEY',
        sector_desc: 'CROPS',
        group_desc: 'FIELD CROPS',
        // Set the specific data item based on crop selection
        short_desc: selectedCrop.value === 'CORN' 
          ? 'CORN, GRAIN - YIELD, MEASURED IN BU / ACRE'
          : 'SOYBEANS - YIELD, MEASURED IN BU / ACRE'
      })
    //   console.log(`${baseUrl}?${params.toString()}`)
      return `${baseUrl}?${params.toString()}`
    }

    const fetchData = async () => {
      isLoading.value = true
      error.value = null
      previewData.value = []

      try {
        const response = await fetch(buildApiUrl())
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        
        if (data.error) {
          throw new Error(data.error)
        }

        previewData.value = data.data || []
        
        if (previewData.value.length === 0) {
          error.value = 'No data found for the selected criteria'
        }

      } catch (err) {
        error.value = `Error fetching data: ${err.message}`
        console.error('Error fetching NASS data:', err)
      } finally {
        isLoading.value = false
      }
    }

    const formatDataForCsv = (data) => {
      return data.map(item => {
        const stateFips = item.state_fips_code.padStart(2, '0')
        const countyFips = (item.county_code || '').padStart(3, '0')
        const fips = stateFips + countyFips

        // Create dynamic value label based on statisticCategory
        const valueLabel = (() => {
          switch (statisticCategory.value) {
            case 'YIELD':
              return 'NASS Reported Yield (bu/acre)'
            case 'AREA PLANTED':
              return 'NASS Reported Planted Area (acres)'
            case 'AREA HARVESTED':
              return 'NASS Reported Harvested Area (acres)'
            default:
              return 'Value'
          }
        })()

        return {
          'FIPS': fips,
          'Location': item.location_desc,
          'Crop type': item.commodity_desc.toLowerCase(),
          'Year': item.year,
          [valueLabel]: item.Value
        }
      })
    }

    const downloadCsv = () => {
      isDownloading.value = true
      try {
        const formattedData = formatDataForCsv(previewData.value)
        
        // Generate CSV using Papa Parse
        const csv = Papa.unparse(formattedData)
        
        // Create blob and download link
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        
        // Set filename with current date
        const date = new Date().toISOString().split('T')[0]
        const filename = `NASS_${selectedCrop.value.toLowerCase()}_${selectedYear.value}_${date}.csv`
        
        link.setAttribute('href', url)
        link.setAttribute('download', filename)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        
        link.click()
        document.body.removeChild(link)
      } catch (err) {
        error.value = `Error downloading CSV: ${err.message}`
        console.error('Error creating CSV:', err)
      } finally {
        isDownloading.value = false
      }
    }

    return {
      statisticCategory,
      selectedCrop,
      selectedYear,
      currentYear,
      isLoading,
      previewData,
      error,
      isDownloading,
      fetchData,
      downloadCsv
    }
  }
}
</script> 