<template>
    <div class="data-analyse-panel">
      <h2>Data Analysis</h2>
      
      <div class="scrollable-content">
        <details open class="county-data-container">
        <summary>County Data</summary>
        <label for="county-input-0">Select Counties:</label>
        <div v-for="(county, index) in selectedCounties" :key="index" class="county-selector">
          <!-- <label :for="`county-input-${index}`">Select County:</label> -->
          <div class="input-group">
            <input
              :id="`county-input-${index}`"
              v-model="county.input"
              @input="updateSuggestions(index)"
              @keydown.enter="selectCounty(index)"
              placeholder="Type a county name"
            />
            <button @click="removeCounty(index)" v-if="selectedCounties.length > 1" class="remove-btn">-</button>
          </div>
          <ul v-if="county.showSuggestions" class="suggestions">
            <li
              v-for="suggestion in county.filteredSuggestions"
              :key="suggestion.fips"
              @click="selectSuggestion(suggestion, index)"
            >
              {{ suggestion.name }}
            </li>
          </ul>
          
        </div>
        <button @click="addCounty" class="add-btn">+</button>

      <!-- <button @click="showHistoryData" :disabled="!hasSelectedCounties">
        Show History Data
      </button> -->
      <!-- <ScatterPlot :datasets="scatterPlotDatasets" :width="340" :height="240" /> -->
      <div class="scatter-plot-wrapper">
        <ScatterPlot :datasets="scatterPlotDatasets" />
      </div>  
      <div ref="chartRef" class="chart-container"></div>
      </details>

      <details class="table-container">
        <summary>Data Table</summary>
        <div class="csv-table" v-if="csvData.length">
          <div ref="tableRef"></div>
        </div>
      </details>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, computed, onMounted, watch } from 'vue'
  import { useStore } from 'vuex'
  import { TabulatorFull as Tabulator } from 'tabulator-tables';
  import { stateCodeMap } from '@/utils/stateCodeMap'
  import ScatterPlot from '@/components/ScatterPlot.vue'

  export default {
    name: 'DataAnalysePanel',
    components: {
      ScatterPlot
    },
    setup() {
      const store = useStore()
      const selectedCounties = ref([{ input: '', showSuggestions: false, selected: null, data: [], filteredSuggestions: [] }])
      const csvData = computed(() => store.state.csvData || [])
      const csvHeaders = computed(() => csvData.value.length ? Object.keys(csvData.value[0]) : [])
      const tableRef = ref(null)
      let table = null

      const historicalData = computed(() => store.state.historicalData || [])
      const chartRef = ref(null)
  
      const scatterPlotDatasets = computed(() => {
  return selectedCounties.value
    .filter(county => county.selected && county.data.length > 0)
    .map(county => ({
      countyName: county.selected.name,
      data: county.data.map(d => ({ x: d.year, y: d.yield }))
    }))
})

      const countySuggestions = computed(() => {
        const uniqueCounties = new Map()
        csvData.value.forEach(row => {
            const stateCode = row.FIPS.substring(0, 2)
            const stateName = stateCodeMap[stateCode] || 'Unknown State'
            const name = `${row.NAME}, ${stateName}`
            uniqueCounties.set(row.FIPS, { name, fips: row.FIPS })
        })
        return Array.from(uniqueCounties.values())
        })
  
        const filteredSuggestions = computed(() => {
            if (!countyInput.value) return []
            const input = countyInput.value.toLowerCase()
            return countySuggestions.value.filter(county => 
                county.name.toLowerCase().includes(input)
            ).slice(0, 5) // Limit to 5 suggestions
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
      updateCountyData(index)
    }
  
// Add a new function to update county data
function updateCountyData(index) {
      const county = selectedCounties.value[index]
      if (county.selected) {
        const fips = county.selected.fips
        county.data = historicalData.value.filter(d => d.FIPS === fips)
        }
      }

    function selectCounty(index) {
      const county = selectedCounties.value[index]
      if (county.filteredSuggestions.length) {
        selectSuggestion(county.filteredSuggestions[0], index)
      }
    }

    function addCounty() {
      selectedCounties.value.push({ input: '', showSuggestions: false, selected: null, data: [], filteredSuggestions: [] })
    }

    function removeCounty(index) {
      selectedCounties.value.splice(index, 1)
    }
  
    const hasSelectedCounties = computed(() => {
      return selectedCounties.value.some(county => county.selected)
    })

    const showHistoryData = () => {
  selectedCounties.value = selectedCounties.value.map(county => {
    if (county.selected) {
      const fips = county.selected.fips
      return {
        ...county,
        data: historicalData.value.filter(d => d.FIPS === fips)
      }
    }
    return county
  })
}



      onMounted(() => {
      if (csvData.value.length) {
        initTable()
      }
    })

    watch(csvData, (newData) => {
      if (newData.length) {
        initTable()
      }
    })

    function initTable() {
      if (table) {
        table.destroy()
      }

      table = new Tabulator(tableRef.value, {
        data: csvData.value,
        columns: [          
          { title: "NAME", field: "NAME", width: 150 },
          { title: "FIPS", field: "FIPS", width: 70 },
          { title: "Yield", field: "yield", width: 70 },
          { title: "Pred", field: "pred", width: 70 },
          { title: "Error", field: "error", width: 70 },
        ],
        layout: "fitColumns",
        height: 400,
        pagination: true,
        paginationSize: 15,
        autoResize: true,
      })
    }
  
      return {
        selectedCounties,
      csvData,
      csvHeaders,
      updateSuggestions,
      selectSuggestion,
      selectCounty,
      showHistoryData,
      tableRef,
      chartRef,
      addCounty,
      removeCounty,
      hasSelectedCounties,
      selectedCounties,
      scatterPlotDatasets,

      }
    }
  }
  </script>
  
  <style>
  @import  "tabulator-tables/dist/css/tabulator.min.css";

  .data-analyse-panel {
    padding: var(--space-large);
  }
  
  .county-selector {
    position: relative;
    /* margin-bottom: var(--space-medium); */
  }
  
  input {
    width: 100%;
    padding: var(--space-small);
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius);
  }
  
  .suggestions {
    position: absolute;
    width: 100%;
    max-height: 200px;
    overflow-y: auto;
    list-style-type: none;
    padding: 0;
    margin: 0;
    border: 1px solid var(--color-border);
    border-top: none;
    border-radius: 0 0 var(--border-radius) var(--border-radius);
    background-color: var(--color-background);
    z-index: 1;
  }
  
  .suggestions li {
    padding: var(--space-small);
    cursor: pointer;
  }
  
  .suggestions li:hover {
    background-color: var(--color-background-soft);
  }
  
  button {
    margin-bottom: var(--space-medium);
    padding: var(--space-small) var(--space-medium);
    background-color: var(--color-primary);
    color: var(--color-text-button);
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  

  .table-container {
  margin-top: var(--space-medium);
  /* border: 1px solid var(--color-border); */
  border-radius: var(--border-radius);
}

summary {
  padding: var(--space-small);
  background-color: var(--color-background-soft);
  cursor: pointer;
  font-weight: bold;
}

summary:hover {
  background-color: var(--color-background-mute);
}

  .csv-table {
  margin-top: var(--space-medium);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.tabulator {
  font-family: inherit;
  border: none;
  background-color: var(--color-background);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.tabulator .tabulator-header {
  background-color: var(--color-background-mute);
  border-bottom: 2px solid var(--color-border);
  font-weight: bold;
}

.tabulator .tabulator-header .tabulator-col {
  background-color: transparent;
  border-right: 1px solid var(--color-border);
  padding: 10px;
}

.tabulator .tabulator-table .tabulator-row {
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.3s;
}

.tabulator .tabulator-table .tabulator-row:nth-child(even) {
  background-color: var(--color-background-soft);
}

.tabulator .tabulator-table .tabulator-row:hover {
  background-color: var(--color-background-mute);
}

.tabulator .tabulator-footer {
  background-color: var(--color-background-mute);
  border-top: 2px solid var(--color-border);
  font-weight: bold;
}

.tabulator .tabulator-footer .tabulator-paginator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
}

.tabulator .tabulator-footer .tabulator-page {
  margin: 0 5px;
  padding: 5px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  background-color: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  transition: background-color 0.3s;
}

.tabulator .tabulator-footer .tabulator-page:hover {
  background-color: var(--color-background-soft);
}

.tabulator .tabulator-footer .tabulator-page[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}

.tabulator .tabulator-tableholder {
  background-color: var(--color-background);
}

.tabulator .tabulator-row .tabulator-cell {
  border-right: 1px solid var(--color-border);
  padding: 10px;
}

.tabulator-row.tabulator-row-even {
  background-color: var(--color-background-soft);
}

.tabulator-row.tabulator-row-odd {
  background-color: var(--color-background);
}

.tabulator-col-title {
  font-weight: bold;
  color: var(--color-heading);
}

.tabulator-header-filter input {
  width: 100%;
  padding: 5px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: 14px;
}

.county-data-container {
  margin-bottom: var(--space-medium);
}

.chart-container {
  margin-top: var(--space-medium);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

/* Add this to ensure the SVG respects the container width */
.chart-container svg {
  max-width: 100%;
}

.data-analyse-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.scrollable-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-medium);
}

.county-data-container,
.table-container {
  margin-bottom: var(--space-medium);
}

.chart-container {
  margin-top: var(--space-medium);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.chart-container svg {
  max-width: 100%;
}

/* Ensure the Tabulator table doesn't overflow */
.tabulator {
  max-width: 100%;
}

.input-group {
  display: flex;
  align-items: center;
  margin-bottom: 0; /* Add this line */
}

.input-group input {
  flex-grow: 1;
  margin-right: 5px;
  margin-bottom: 0; /* Add this line */
}

.remove-btn, .add-btn {
  padding: 5px 10px;
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 16px;
  margin-left: 5px;
  height: 100%; /* Add this line */
}

.remove-btn:hover, .add-btn:hover {
  background-color: var(--color-primary-dark);
}

.add-btn {
  margin-top: 10px;
  width: auto;
  padding: 5px 15px;
}
.scatter-plot-wrapper {
  width: 100%;
  height: 300px; /* Adjust this value as needed */
  margin-top: var(--space-medium);
}
  </style>