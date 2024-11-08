// src/store/index.js
import { createStore } from 'vuex'
import Papa from 'papaparse'
import * as d3 from 'd3'
import { getBasemapUrl } from '@/utils/basemaps'

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
        allPredictions: null,
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
          minValue: 55,
          maxValue: 215,
          colorSchemes: {
            pred: ['#ebf8b3', '#074359'],     // Sequential blue-green
            yield: ['#ebf8b3', '#074359'],    // Sequential blue-green
            error: ['#3B4992', '#FFFFFF', '#EE7733'],      // Divergent blue-orange
            uncertainty: ['#ffffff', '#916C07']  // Sequential brown
          },
          colorScheme: ['#ebf8b3', '#074359'], // Default scheme
          choroplethOpacity: 0.7,
          basemapOpacity: 1.0,
          selectedBasemap: 'osm',

      },
      markers: [],
      countyInfo: {},
      modelQueue: [],
      drawnPolygons: [], // Add this line to store drawn polygons
      yearSliderVisible: true,
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
          setAllPredictions(state, data) {
            state.allPredictions = data
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
        setSelectedBasemap(state, basemapId) {
          state.selectedBasemap = basemapId
        },
        addMarker(state, marker) {
          state.markers.push(marker)
        },
        removeMarkers(state) {
          state.markers = [];
        },
        setCountyInfo(state, data) {
          state.countyInfo = data;
        },
        setModelQueue(state, queue) {
          state.modelQueue = queue;
          localStorage.setItem('modelQueue', JSON.stringify(queue)); // Save to localStorage
        },
        addModelQueueJob(state, job) {
          state.modelQueue.push(job);
          localStorage.setItem('modelQueue', JSON.stringify(state.modelQueue)); // Save to localStorage
        },
        updateModelQueueJob(state, updatedJob) {
          const index = state.modelQueue.findIndex(job => job.id === updatedJob.id);
          if (index !== -1) {
            state.modelQueue.splice(index, 1, updatedJob);
            localStorage.setItem('modelQueue', JSON.stringify(state.modelQueue)); // Save to localStorage
          }
        },
        clearModelQueue(state) {
          state.modelQueue = [];
          state.markers = [];
          localStorage.removeItem('modelQueue'); // Clear from localStorage
        },
        setDrawnPolygons(state, polygons) {
          state.drawnPolygons = polygons; // Mutation to set drawn polygons
        },
        clearDrawnPolygons(state) {
          state.drawnPolygons = []; // Mutation to clear drawn polygons
        },
        setCurrentYear(state, year) {
          state.currentYear = year;
        },
        toggleYearSlider(state) {
          state.yearSliderVisible = !state.yearSliderVisible
        },
        setMapTitle(state, title) {
          state.mapTitle = title;
        },
        setMapDescription(state, description) {
          state.mapDescription = description;
        },
        setMapFont(state, font) {
          state.mapFont = font;
        },
    },
    actions: {
        async fetchMapData({ commit, state }) {
            const { currentCrop, currentYear, currentMonth } = state
            try {
                const response = await fetch(`data/${currentCrop}/${currentYear}/${currentMonth}.json`)
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
        async fetchAllPredictions({ commit }) {
          try {
            const response = await fetch('data/prediction23.csv')
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`)
            }
            const csvText = await response.text()
            Papa.parse(csvText, {
              header: true,
              complete: (results) => {
                const allPredictions = results.data
                .map(row => ({
                  FIPS: row.FIPS,
                  year: parseInt(row.year),
                  pred: parseFloat(row.pred).toFixed(2),
                  yield: parseFloat(row.yield).toFixed(2),
                  error: (parseFloat(row.pred) - parseFloat(row.yield)).toFixed(2),
                  uncertainty: Math.abs((parseFloat(row.pred) - parseFloat(row.yield))/parseFloat(row.yield) * 100).toFixed(2)
                }))
                commit('setAllPredictions', allPredictions)
              },
              error: (error) => {
                console.error('Error parsing CSV:', error)
              }
            })
          } catch (error) {
            console.error('Error fetching all predictions:', error)
          }
        },
        async fetchHistoricalData({ commit }) {
          try {
              const response = await fetch('data/corn_yield_US.csv')
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
                const response = await fetch('data/average_pred.csv')
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
              const response = await fetch('data/county.csv');
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

        async loadCountyInfo({ commit }) {
          try {
            const response = await fetch('data/county_info.csv');
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            const csvText = await response.text();
            const parsedData = Papa.parse(csvText, {
              header: true,
              dynamicTyping: true,
              complete: (results) => {
                const countyInfo = {};
                results.data.forEach(row => {
                  const fips = row.FIPS.toString().padStart(5, '0');
                  countyInfo[fips] = { lat: row.lat, lon: row.lon };
                });
                commit('setCountyInfo', countyInfo);
              },
              error: (error) => {
                console.error('Error parsing CSV:', error);
              }
            });
          } catch (error) {
            console.error('Error loading county info:', error);
          }
        },
        loadModelQueue({ commit }) {
          const savedQueue = localStorage.getItem('modelQueue');
          if (savedQueue) {
            commit('setModelQueue', JSON.parse(savedQueue));
          }
        },
        saveModelQueue({ state }) {
          localStorage.setItem('modelQueue', JSON.stringify(state.modelQueue));
        },
        clearModelQueue({ commit }) {
          commit('clearModelQueue');
          localStorage.removeItem('modelQueue');
        },
        saveDrawnPolygons({ commit }, polygons) {
          commit('setDrawnPolygons', polygons); // Action to save drawn polygons
        },
        clearDrawnPolygons({ commit }) {
          commit('clearDrawnPolygons'); // Action to clear drawn polygons
        },

        async initializeData({ dispatch }) {
      await dispatch('loadCsvData');
      await dispatch('fetchHistoricalData');
      await dispatch('fetchAveragePred');
      await dispatch('loadCountyData');
      await dispatch('loadCountyInfo');
      await dispatch('fetchAllPredictions');
    },
    async initializeMapState({ dispatch, commit }) {
      // First load all necessary data
      await dispatch('initializeData')
      
      // Then set the property and year
      commit('setProperty', 'pred')
      commit('setYear', 2024)
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
        getAllPredictions: state => state.allPredictions,
        getAveragePredData: state => state.averagePredData ,
        currentBasemapUrl: (state) => {
          return getBasemapUrl(state.selectedBasemap)
        },
        getMapImage: (state) => {
          if (state.map) {
            const mapImage = state.map.getCanvas().toDataURL()
            return mapImage
          }
          return null
        },
        getDrawnPolygons: (state) => state.drawnPolygons, // Getter to retrieve drawn polygons
    },
})