// src/store/index.js
import { createStore } from 'vuex'
import Papa from 'papaparse'

export default createStore({
    state: {
        currentCrop: 'corn',
        currentYear: '2021',
        currentMonth: '0',
        currentProperty: 'pred',
        mapData: null,
        selectedLocation: null,
        csvData: null,
        hoveredCounty: null,
        hoveredCountyId: null,
    },
    mutations: {
        setCrop(state, crop) {
            state.currentCrop = crop
        },
        setYear(state, year) {
            state.currentYear = year
        },
        setMonth(state, month) {
            state.currentMonth = month
        },
        setProperty(state, property) {
            state.currentProperty = property
        },
        setMapData(state, data) {
            state.mapData = data
        },
        setSelectedLocation(state, location) {
            state.selectedLocation = location
        },
        setCsvData(state, data) {
            state.csvData = data
          },
          setHoveredCounty(state, county) {
            state.hoveredCounty = county
            state.hoveredCountyId = county ? county.id : null
        },
    },
    actions: {
        async fetchMapData({ commit, state }) {
            const { currentCrop, currentYear, currentMonth } = state
            try {
                const response = await fetch(`/data/${currentCrop}/${currentYear}/${currentMonth}.json`)
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`)
                }
                const data = await response.json()
                commit('setMapData', data)
            } catch (error) {
                console.error('Error fetching map data:', error)
            }
        },
        async loadCsvData({ state, commit }) {
            const { currentCrop, currentYear, currentMonth } = state
            const csvPath = `csv/${currentCrop}/${currentYear}/${currentMonth}.csv`
        
            try {
              const response = await fetch(csvPath)
              if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
              }
              const csvText = await response.text()
              
              Papa.parse(csvText, {
                header: true,
                complete: (results) => {
                  // Filter out empty rows and convert numeric fields to 2 decimal places
                  const cleanedData = results.data
                    .filter(row => Object.values(row).some(value => value.trim() !== ''))
                    .map(row => ({
                      ...row,
                      yield: parseFloat(row.yield).toFixed(2),
                      pred: parseFloat(row.pred).toFixed(2),
                      error: parseFloat(row.error).toFixed(2)
                    }))
                  commit('setCsvData', cleanedData)
                },
                error: (error) => {
                  console.error('Error parsing CSV:', error)
                }
              })
            } catch (error) {
              console.error('Error loading CSV data:', error)
            }
          }
    },
    getters: {
        getMapData: (state) => state.mapData,
        hoveredCountyId: state => state.hoveredCountyId,
        hoveredCountyFIPS: state => state.hoveredCounty ? state.hoveredCounty.fips : null,
        hoveredCountyName: state => state.hoveredCounty ? state.hoveredCounty.name : null,
        hoveredCountyValue: state => state.hoveredCounty ? state.hoveredCounty.value : null,
    },
})