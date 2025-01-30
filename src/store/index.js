// src/store/index.js
import { createStore } from 'vuex'
import Papa from 'papaparse'
import * as d3 from 'd3'
import { getBasemapUrl } from '@/utils/basemaps'

const baseUrl = import.meta.env.BASE_URL

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
      cachedPredictions: {}, // Add this line to store cached predictions
      currentDay: '284', // Default to day 284 (end of season)
      selectedCountyFIPS: [], // Add this line to track selected counties
      selectedCounties: [], // Add this line to store selected counties
      currentPredictionData: null, // Add this line to store current prediction data
    },
    mutations: {
      setMap(state, data) {
        state.map = data
      },
        setCrop(state, crop) {
            state.currentCrop = crop
            if (crop === 'soybean') {
                state.currentYear = '2024'
                if (state.currentProperty === 'error') {
                    state.currentProperty = 'pred'
                }
            }
            this.commit('updateMapTitle')
        },
        setYear(state, year) {
            state.currentYear = year
            this.commit('updateMapTitle')
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
            console.warn('Deprecated: setCsvData is no longer used')
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
        setCachedPrediction(state, { key, data }) {
            state.cachedPredictions[key] = data;
        },
        setPredictionDay(state, day) {
            state.currentDay = day.toString().padStart(3, '0');
            this.commit('updateMapTitle');
        },
        updateMapTitle(state) {
            const crop = state.currentCrop.charAt(0).toUpperCase() + state.currentCrop.slice(1);
            const year = state.currentYear;
            
            const dateMapping = {
                "140": "May 20 (In Season)",
                "156": "June 5 (In Season)",
                "172": "June 21 (In Season)",
                "188": "July 7 (In Season)",
                "204": "July 23 (In Season)",
                "220": "August 8 (In Season)",
                "236": "August 24 (In Season)",
                "252": "September 9 (In Season)",
                "268": "September 25 (In Season)",
                "284": "October 11 (End of Season)"
            };
            
            const predictionDate = dateMapping[state.currentDay];
            state.mapTitle = `${crop} ${predictionDate} Prediction for US in ${year}`;
        },
        setSelectedCountyFIPS(state, fipsList) {
            state.selectedCountyFIPS = fipsList;
        },
        addSelectedCountyFIPS(state, { fips, name }) {
            if (!state.selectedCountyFIPS.includes(fips)) {
                state.selectedCountyFIPS.push(fips);
                // Also update the selectedCounties array
                state.selectedCounties.push({
                    input: name,
                    selected: { fips, name },
                    showSuggestions: false,
                    filteredSuggestions: []
                });
            }
        },
        removeSelectedCountyFIPS(state, fips) {
            // Remove from selectedCountyFIPS array
            state.selectedCountyFIPS = state.selectedCountyFIPS.filter(f => f !== fips);
            
            // Remove from selectedCounties array
            state.selectedCounties = state.selectedCounties.filter(c => c.selected?.fips !== fips);
            
            // If selectedCounties is empty, initialize with an empty input
            if (state.selectedCounties.length === 0) {
                state.selectedCounties = [{
                    input: '',
                    selected: null,
                    showSuggestions: false,
                    filteredSuggestions: []
                }];
            }
        },
        setCurrentPredictionData(state, data) {
            state.currentPredictionData = data
        },
    },
    actions: {
        async fetchMapData({ commit, state }) {
            const { currentCrop, currentYear, currentMonth } = state
            try {
                const response = await fetch(`/api/data/${currentCrop}/${currentYear}/${currentMonth}.json`)
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

        async fetchPredictionData({ commit, state }) {
          const { currentCrop, currentYear, currentDay } = state
          
          // Create a cache key
          const cacheKey = `${currentCrop}_${currentYear}_${currentDay}`
          
          // Check cache first
          if (state.cachedPredictions[cacheKey]) {
            commit('setCurrentPredictionData', state.cachedPredictions[cacheKey])
            return state.cachedPredictions[cacheKey]
          }

          const paddedDay = currentDay.toString().padStart(3, '0')
          const csvPath = `${baseUrl}result_${currentCrop}/bnn/result${currentYear}_${paddedDay}.csv`

          try {
            console.log("Attempting to fetch from:", csvPath)
            const response = await fetch(csvPath)
            if (!response.ok) {
              throw new Error(`Failed to fetch ${csvPath}: ${response.status}`)
            }
            const csvText = await response.text()
            
            // Parse CSV data
            const parsedData = Papa.parse(csvText, {
              header: true,
              dynamicTyping: true,
              skipEmptyLines: true
            }).data

            const predictions = parsedData
              .filter(row => row.FIPS)
              .map(row => ({
                FIPS: row.FIPS.toString().padStart(5, '0'),
                pred: parseFloat(row.y_test_pred),
                yield: parseFloat(row.y_test),
                uncertainty: parseFloat(row.y_test_pred_uncertainty),
                error: parseFloat(row.y_test_pred) - parseFloat(row.y_test)
              }))

            // Cache and set the current prediction data
            commit('setCachedPrediction', { key: cacheKey, data: predictions })
            commit('setCurrentPredictionData', predictions)
            return predictions

          } catch (error) {
            console.error('Error fetching prediction data:', error)
            return []
          }
        },


        async fetchAllPredictions({ commit, state }) {
            try {
                const predictions = [];
                const startYear = 2015;
                const endYear = 2023;
                
                for (let year = startYear; year <= endYear; year++) {
                    const response = await fetch(`/api/predictions/${state.currentCrop}/${year}`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    
                    const yearPredictions = data
                        .filter(row => row.FIPS)
                        .map(row => ({
                            FIPS: row.FIPS,
                            year: year,
                            pred: parseFloat(row.y_test_pred),
                            yield: parseFloat(row.y_test),
                            uncertainty: parseFloat(row.y_test_pred_uncertainty),
                            error: parseFloat(row.y_test_pred) - parseFloat(row.y_test)
                        }));
                    predictions.push(...yearPredictions);
                }
                
                commit('setAllPredictions', predictions);
            } catch (error) {
                console.error('Error fetching predictions:', error);
            }
        },
        async fetchHistoricalData({ commit }) {
            try {
                const response = await fetch('/api/data/corn_yield_US.csv')
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`)
                }
                const data = await response.json()
                
                // Ensure data is properly formatted
                const transformedData = data.map(d => ({
                    FIPS: d.FIPS.toString().padStart(5, '0'), // Ensure FIPS is properly formatted
                    year: parseInt(d.year),
                    yield: parseFloat(d.yield)
                }))
                
                // console.log('Transformed historical data:', transformedData) // Debug log
                commit('setHistoricalData', transformedData)
            } catch (error) {
                console.error('Error fetching historical data:', error)
            }
        },
        
        async fetchAveragePred({ commit }) {
            try {
                // First try the API endpoint
                const response = await fetch('/api/data/average_pred.csv')
                if (!response.ok) {
                    throw new Error('API endpoint failed')
                }
                const csvText = await response.text()
                const parsedData = d3.csvParse(csvText, d => ({
                    FIPS: d.FIPS,
                    year: +d.YEAR,
                    pred: +d.PRED,
                    yield: +d.YIELD,
                    crop: d.CROP === 'c' ? 'corn' : 'soybean'
                }))
                commit('setAveragePredData', parsedData)
            } catch (error) {
                console.warn('API fetch failed, trying local file:', error)
                try {
                    // Fallback to public directory
                    const response = await fetch('/data/average_pred.csv')
                    if (!response.ok) {
                        throw new Error('Local file fetch failed')
                    }
                    const csvText = await response.text()
                    const parsedData = d3.csvParse(csvText, d => ({
                        FIPS: d.FIPS,
                        year: +d.YEAR,
                        pred: +d.PRED,
                        yield: +d.YIELD,
                        crop: d.CROP === 'c' ? 'corn' : 'soybean'
                    }))
                    commit('setAveragePredData', parsedData)
                } catch (finalError) {
                    console.error('Error fetching average prediction data:', finalError)
                    commit('setAveragePredData', [])
                }
            }
        },
        
        async loadCountyData({ commit }) {
            try {
              const response = await fetch('/api/data/county.csv');
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
            const response = await fetch('/api/data/county_info.csv');
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            const csvText = await response.text();
            Papa.parse(csvText, {
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
    async initializeMapState({ dispatch, commit, state }) {
      await dispatch('initializeData')
      commit('setProperty', 'pred')
      commit('setYear', state.currentCrop === 'soybean' ? 2024 : state.currentYear)
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
        getSelectedCountyFIPS: state => state.selectedCountyFIPS,
    },
})