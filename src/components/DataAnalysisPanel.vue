<template>
    <div class="data-analyse-panel">
      <h2>Data Analysis</h2>
      
      <div class="scrollable-content">
      <details open class="county-data-container">
        <summary>County Data</summary>
        <div class="county-selector">
        <label for="county-input">Select County:</label>
        <input
          id="county-input"
          v-model="countyInput"
          @input="updateSuggestions"
          @keydown.enter="selectCounty"
          placeholder="Type a county name"
        />
        <ul v-if="showSuggestions" class="suggestions">
          <li
            v-for="suggestion in filteredSuggestions"
            :key="suggestion.fips"
            @click="selectSuggestion(suggestion)"
          >
            {{ suggestion.name }}
          </li>
        </ul>
      </div>

        <button @click="showHistoryData" :disabled="!selectedCounty">
          Show History Data
        </button>

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
  import * as d3 from 'd3'



  const stateCodeMap = {
  '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas',
  '06': 'California', '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware',
  '11': 'District of Columbia', '12': 'Florida', '13': 'Georgia', '15': 'Hawaii',
  '16': 'Idaho', '17': 'Illinois', '18': 'Indiana', '19': 'Iowa',
  '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
  '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
  '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska',
  '32': 'Nevada', '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico',
  '36': 'New York', '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio',
  '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island',
  '45': 'South Carolina', '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas',
  '49': 'Utah', '50': 'Vermont', '51': 'Virginia', '53': 'Washington',
  '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
    }
  
  export default {
    name: 'DataAnalysePanel',
    setup() {
      const store = useStore()
      const countyInput = ref('')
      const showSuggestions = ref(false)
      const selectedCounty = ref(null)
  
      const csvData = computed(() => store.state.csvData || [])
      const csvHeaders = computed(() => csvData.value.length ? Object.keys(csvData.value[0]) : [])
      const tableRef = ref(null)
      let table = null

      const historicalData = computed(() => store.state.historicalData || [])
      const chartRef = ref(null)
  
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
  
      function updateSuggestions() {
        showSuggestions.value = countyInput.value.length > 0
      }
  
      function selectSuggestion(suggestion) {
      selectedCounty.value = suggestion
      countyInput.value = suggestion.name
      showSuggestions.value = false
    }
  
      function selectCounty() {
        if (filteredSuggestions.value.length) {
          selectSuggestion(filteredSuggestions.value[0])
        }
      }
  
      function showHistoryData() {
        if (selectedCounty.value) {
        const fips = selectedCounty.value.fips
        const countyData = historicalData.value.filter(d => d.FIPS === fips)
        renderScatterPlot(countyData)
      }
      }

      function renderScatterPlot(data) {
      if (!chartRef.value) return

      // Clear previous chart
      d3.select(chartRef.value).selectAll("*").remove()

      const margin = { top: 20, right: 20, bottom: 30, left: 40 }
      const width = 400 - margin.left - margin.right
      const height = 300 - margin.top - margin.bottom

      const svg = d3.select(chartRef.value)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`)

      const x = d3.scaleLinear()
        .domain(d3.extent(data, d => d.year))
        .range([0, width])

      const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.yield)])
        .range([height, 0])

      svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x).tickFormat(d3.format("d")))

      svg.append("g")
        .call(d3.axisLeft(y))

      svg.selectAll("circle")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => x(d.year))
        .attr("cy", d => y(d.yield))
        .attr("r", 3)
        .attr("fill", "steelblue")

      svg.append("text")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom)
        .style("text-anchor", "middle")
        .text("Year")

      svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x", 0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("Yield (BU/ACRE)")
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
        countyInput,
        showSuggestions,
        selectedCounty,
        csvData,
        csvHeaders,
        filteredSuggestions,
        updateSuggestions,
        selectSuggestion,
        selectCounty,
        showHistoryData,
        tableRef,
        chartRef,
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
    margin-bottom: var(--space-medium);
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
  </style>