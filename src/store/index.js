// src/store/index.js
import { createStore } from 'vuex'
import Papa from 'papaparse'
import * as d3 from 'd3'

export default createStore({
    state: {
      map: null,
        currentCrop: 'corn',
        currentYear: '2021',
        currentMonth: '0',
        currentProperty: 'pred',
        mapData: null,
        selectedLocation: null,
        csvData: null,
        hoveredCounty: null,
        hoveredCountyId: null,
        historicalData: [],
        averagePredData: [],
        mapTitle: 'Corn Prediction for US in 2021',
        mapDescription: '',
        mapFont: 'Arial',
        mapBackgroundColor: '#FFFFFF',
        countyData: {},
        availableStates: [],
        choroplethSettings: {
          minValue: 0,
          maxValue: 100,
          colorScheme: ['#FFEDA0', '#FEB24C', '#F03B20'],
          choroplethOpacity: 0.7,
          basemapOpacity: 1.0,
      },
    },
    mutations: {
      setMap(state, data) {
        state.map = data
      },
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
        setHistoricalData(state, data) {
            state.historicalData = data
        },
        setAveragePredData(state, data) {
            state.averagePredData = data
        },
        setCountyData(state, data) {
            state.countyData = data
            state.availableStates = Object.keys(data)
        },
        setChoroplethSettings(state, settings) {
          state.choroplethSettings = settings
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
        },
        async fetchHistoricalData({ commit }) {
          try {
              const response = await fetch('/data/corn_yield_US.csv')
              if (!response.ok) {
                  throw new Error(`HTTP error! status: ${response.status}`)
              }
              const csvText = await response.text()
              const parsedData = d3.csvParse(csvText, d => ({
                  FIPS: d.FIPS,
                  year: +d.year,
                  yield: +d.yield
              }))
              commit('setHistoricalData', parsedData)
          } catch (error) {
              console.error('Error fetching historical data:', error)
          }
        },
        async fetchAveragePred({ commit }) {
            try {
                const response = await fetch('/data/average_pred.csv')
                const csvText = await response.text()
                const parsedData = d3.csvParse(csvText, d => ({
                    FIPS: d.FIPS,
                    year: +d.YEAR,
                    pred: +d.PRED,
                    yield: +d.YIELD,
                    crop: d.CROP === 'c'? 'corn' : 'soybean'
                }))
                commit('setAveragePredData', parsedData)
            } catch (error) {
                console.error('Error fetching historical data:', error)
            }
        },
        
        async loadCountyData({ commit }) {
            try {
              const response = await fetch('/data/county.csv');
              if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
              }
              const csvText = await response.text();
              
              Papa.parse(csvText, {
                header: true,
                complete: (results) => {
                  const countyData = {};
                  results.data.forEach(row => {
                    if (row.STATEFP && row.COUNTYFP && row.NAME) {
                      if (!countyData[row.NAME]) {
                        countyData[row.NAME] = [];
                      }
                      countyData[row.NAME].push({
                        name: row.NAME,
                        stateFp: row.STATEFP,
                        countyFp: row.COUNTYFP
                      });
                    }
                  });
                  commit('setCountyData', countyData);
                },
                error: (error) => {
                  console.error('Error parsing CSV:', error);
                }
              });
            } catch (error) {
              console.error('Error loading county data:', error);
            }
        },
        async initializeData({ dispatch }) {
      await dispatch('loadCsvData');
      await dispatch('fetchHistoricalData');
      await dispatch('fetchAveragePred');
      await dispatch('loadCountyData');
    }
    },
    getters: {
        getMap: (state) => state.map,
        getMapData: (state) => state.mapData,
        hoveredCountyId: state => state.hoveredCountyId,
        hoveredCountyFIPS: state => state.hoveredCounty ? state.hoveredCounty.fips : null,
        hoveredCountyName: state => state.hoveredCounty ? state.hoveredCounty.name : null,
        hoveredCountyValue: state => state.hoveredCounty ? state.hoveredCounty.value : null,
        getHistoryData: state => state.historicalData ,
        getAveragePredData: state => state.averagePredData ,
    },
})