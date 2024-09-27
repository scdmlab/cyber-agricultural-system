<template>
  <notifications position="top-right" />
  <div class="bg-white p-6 rounded-lg shadow-md h-full flex flex-col">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Run Model</h2>
    
    <div class="overflow-y-auto flex-grow">
      <details class="mb-4">
        <summary class="cursor-pointer font-bold mb-2">Latest Model Results</summary>

        <div class="space-y-4">
          <div>
            <label for="state" class="block text-sm font-medium text-gray-700">State:</label>
            <select id="state" v-model="selectedState" @change="updateCounties" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option v-for="state in availableStates" :key="state" :value="state">{{ state }}</option>
            </select>
          </div>

          <div>
            <label for="county" class="block text-sm font-medium text-gray-700">County:</label>
            <select id="county" v-model="selectedCounty" :disabled="!selectedState" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option v-for="county in availableCounties" :key="county.countyFp" :value="county">
                {{ county.name }}
              </option>
            </select>
          </div>

          <div>
            <label for="predictionType" class="block text-sm font-medium text-gray-700">Prediction Type:</label>
            <select id="predictionType" v-model="selectedPredictionType" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option value="In Season">In Season</option>
              <option value="End of Season">End of Season</option>
            </select>
          </div>

          <div>
            <label for="model" class="block text-sm font-medium text-gray-700">Select a model:</label>
            <select id="model" v-model="selectedModel" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option value="Bayesian">Bayesian</option>
              <option value="Partial Domain Adaption">Partial Domain Adaption</option>
              <option value="Multiple Instance Learning">Multiple Instance Learning</option>
              <option value="Hybrid">Hybrid</option>
            </select>
          </div>

          <button @click="runModel" class="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300" :disabled="isRunning">
            {{ isRunning ? 'Running...' : 'Run Selected Model' }}
          </button>
        </div>
      </details>

      <!-- Drawn Polygons section -->
      <details class="mb-4">
        <summary class="cursor-pointer font-bold mb-2">Drawn Polygons</summary>
        <div v-if="drawnPolygons.length > 0">
          <ul class="list-none p-0 m-0">
            <li v-for="(polygon, index) in drawnPolygons" :key="polygon.id" class="mb-2 text-sm">
              Polygon {{ index + 1 }}: {{ formatPolygonCoordinates(polygon) }}
            </li>
          </ul>
          <div class="mt-4 space-x-2">
            <button @click="runSelectedArea" class="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300">Run Selected Area</button>
            <button @click="clearAllPolygons" class="bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700 transition duration-300">Clear All Polygons</button>
          </div>
        </div>
        <div v-else class="text-gray-600">
          No polygons have been drawn on the map.
        </div>
      </details>

      <!-- Model Queue section -->
      <details open class="mb-4">
        <summary class="cursor-pointer font-bold mb-2">Model Queue</summary>
        <div class="overflow-y-auto max-h-64 relative">
          <table class="w-full border-collapse">
            <thead class="sticky top-0 bg-white z-10">
              <tr class="bg-gray-100">
                <th class="p-2 text-left">Name</th>
                <th class="p-2 text-left">Prediction</th>
                <th class="p-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in modelQueue" :key="job.id" class="border-b">
                <td class="p-2">{{ job.name || job.county + ', ' + job.state }}</td>
                <td class="p-2">
                  <template v-if="job.status === 'pending'">
                    <div class="loading-spinner"></div>
                  </template>
                  <template v-else>
                    {{ job.status === 'failed' ? 'Failed' : (job.prediction || 'Pending') }}
                  </template>
                </td>
                <td class="p-2">
                  <span v-if="job.status === 'complete'" class="text-green-600">✓</span>
                  <span v-else-if="job.status === 'failed'" class="text-red-600">✗</span>
                  <span v-else class="text-yellow-600">●</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <button @click="clearQueue" class="mt-4 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700 transition duration-300">Clear Queue</button>
      </details>
    </div>

    <ProgressBar v-if="isRunning" :value="progress" :text="`${estimatedTime}s remaining`" class="mt-4" />
  </div>
</template>

<script>
import { mapState, mapActions, mapGetters } from 'vuex';
import { Notifications, useNotification } from '@kyvg/vue3-notification';
import ProgressBar from 'primevue/progressbar';
import {stateCodeMap} from '@/utils/stateCodeMap';
import axios from 'axios';

export default {
  name: 'ModelPanel',
  components: {
    ProgressBar,
    Notifications
  },
  data() {
    return {
      selectedState: '',
      selectedCounty: null,
      selectedPredictionType: 'In Season',
      selectedModel: 'Hybrid',
      isRunning: false,
      progress: 0,
      estimatedTime: 0,
      modelQueue: []
    }
  },
  computed: {
    ...mapState(['countyData', 'countyInfo', 'markers']),
    ...mapGetters(['getDrawnPolygons']),
    drawnPolygons() {
      return this.getDrawnPolygons;
    },
    availableStates() {
      const states = new Set();
      Object.values(this.countyData).forEach(counties => {
        counties.forEach(county => {
          const stateName = this.getStateName(county.stateFp);
          if (stateName !== 'Unknown State') {
            states.add(stateName);
          }
        });
      });
      return Array.from(states).sort();
    },
    availableCounties() {
      if (!this.selectedState) return [];
      const stateFp = this.getStateFp(this.selectedState);
      return Object.entries(this.countyData)
        .flatMap(([name, counties]) => 
          counties.filter(county => county.stateFp === stateFp)
            .map(county => ({ ...county, name }))
        )
        .sort((a, b) => a.name.localeCompare(b.name)); // Sort counties alphabetically
    }
  },
  methods: {
    ...mapActions(['loadCountyData', 'loadCountyInfo', 'clearDrawnPolygons']),
    updateCounties() {
      this.selectedCounty = null;
    },
    getStateName(stateFp) {
    return stateCodeMap[stateFp] || 'Unknown State';
  },

  getStateFp(stateName) {
    return Object.keys(stateCodeMap).find(key => stateCodeMap[key] === stateName) || '';
  },

  async runModel() {
    const stateFips = this.getStateFp(this.selectedState);
    const countyFips = this.selectedCounty.countyFp;
    
    if (stateFips && countyFips) {
      const fullFips = stateFips + countyFips.padStart(3, '0');
      const notification = useNotification();
      
      // Add job to the queue
      const jobId = Date.now();
      this.modelQueue.push({
        id: jobId,
        county: this.selectedCounty.name,
        state: this.selectedState,
        prediction: null,
        status: 'pending'
      });

      notification.notify({
        title: "Model Added to Queue",
        text: `${this.selectedModel} model for ${this.selectedCounty.name}, ${this.selectedState} added to queue`,
        type: "info",
      });

      // Display the longer-lasting toast notification
      const dataRequestToast = notification.notify({
        title: "Requesting Data",
        text: "Requesting latest prediction data...",
        type: "info",
        duration: 10000, // 10 seconds
      });

      try {
        // Make API request
        const response = await axios.get(`https://us-central1-nifa-webgis.cloudfunctions.net/nifa-pred-get?FIPS=${fullFips}&year=2023`);
        
        // Close the data request toast
        if (dataRequestToast && dataRequestToast.close) {
          dataRequestToast.close();
        }

        // Simulate delay (1-3 seconds)
        await new Promise(resolve => setTimeout(resolve, Math.random() * 4000 + 1000));

        const predictionData = response.data[0];
        const prediction = predictionData.pred.toFixed(2);

        // Update job in the queue
        this.updateJobStatus(jobId, 'complete', prediction);
        
        notification.notify({
          title: "Model Completed",
          text: `${this.selectedModel} model run completed for ${this.selectedCounty.name}, ${this.selectedState}`,
          type: "success",
        });

        // Add marker to the map
        const countyInfo = this.countyInfo[fullFips];
        if (countyInfo) {
          const marker = {
            lat: countyInfo.lat,
            lon: countyInfo.lon,
            name: this.selectedCounty.name,
            value: prediction,
          };
          this.$store.commit('addMarker', marker);
        }
      } catch (error) {
        console.error('Error fetching prediction:', error);
        
        // Close the data request toast if it's still open
        if (dataRequestToast && dataRequestToast.close) {
          dataRequestToast.close();
        }

        // Update job status to failed
        this.updateJobStatus(jobId, 'failed');

        notification.notify({
          title: "Error",
          text: "Failed to fetch prediction data",
          type: "error",
        });
      }
    } else {
      const notification = useNotification();
      notification.notify({
        title: "Error",
        text: "Invalid state or county selection",
        type: "error",
      });
    }
  },
    updateJobStatus(jobId, status, prediction = null) {
      const jobIndex = this.modelQueue.findIndex(job => job.id === jobId);
      if (jobIndex !== -1) {
        const updatedJob = {
          ...this.modelQueue[jobIndex],
          status: status,
          prediction: prediction !== null ? prediction : this.modelQueue[jobIndex].prediction
        };
        this.$store.commit('updateModelQueueJob', updatedJob);
      }
    },
    clearQueue() {
      this.modelQueue = [];
      this.$store.commit('clearModelQueue');
      this.$store.commit('removeMarkers');
      const notification = useNotification();
      notification.notify({
        title: "Queue Cleared",
        text: "The model queue has been cleared",
        type: "info",
      });
    },
    formatPolygonCoordinates(polygon) {
      if (!polygon || typeof polygon !== 'object' || !polygon.geometry) {
        console.error('Invalid polygon format:', polygon);
        return 'Invalid polygon data';
      }

      try {
        const coordinates = polygon.geometry.coordinates;
        if (!Array.isArray(coordinates) || coordinates.length === 0) {
          throw new Error('Invalid coordinates format');
        }

        // For a polygon, coordinates[0] is the outer ring
        const outerRing = coordinates[0];
        const vertexCount = outerRing.length;
        const area = this.calculatePolygonArea(outerRing);

        return `Vertices: ${vertexCount}, Area: ${area.toFixed(2)} sq units`;
      } catch (error) {
        console.error('Error formatting polygon:', error);
        return 'Error formatting polygon';
      }
    },

    calculatePolygonArea(coordinates) {
      // Simple implementation of the Shoelace formula
      let area = 0;
      for (let i = 0; i < coordinates.length; i++) {
        let j = (i + 1) % coordinates.length;
        area += coordinates[i][0] * coordinates[j][1];
        area -= coordinates[j][0] * coordinates[i][1];
      }
      return Math.abs(area / 2);
    },

    clearAllPolygons() {
      // Clear polygons from the store
      this.clearDrawnPolygons();

      // Clear polygons from the map
      if (this.$store.state.map) {
        const map = this.$store.state.map;
        const source = map.getSource('drawn-polygons');
        if (source) {
          source.setData({
            type: 'FeatureCollection',
            features: []
          });
        }
      }

      // Notify the user
      const notification = useNotification();
      notification.notify({
        title: "Polygons Cleared",
        text: "All drawn polygons have been removed from the map",
        type: "info",
      });
    },

    async runSelectedArea() {
      const validPolygons = this.drawnPolygons.filter(polygon => {
        const area = this.calculatePolygonArea(polygon.geometry.coordinates[0]);
        return !isNaN(area) && area > 0;
      });

      if (validPolygons.length === 0) {
        const notification = useNotification();
        notification.notify({
          title: "No Valid Polygons",
          text: "No valid polygons found. Please draw at least one polygon on the map.",
          type: "warning",
        });
        return;
      }

      const featureCollection = {
        type: "FeatureCollection",
        features: validPolygons.map(polygon => ({
          type: "Feature",
          properties: {},
          geometry: {
            type: "Polygon",
            coordinates: polygon.geometry.coordinates
          }
        }))
      };

      const jobId = Date.now();
      const polygonName = `Selected Area (${validPolygons.length} polygon${validPolygons.length > 1 ? 's' : ''})`;

      // Add job to the queue
      this.modelQueue.push({
        id: jobId,
        name: polygonName,
        prediction: null,
        status: 'pending'
      });

      const notification = useNotification();
      notification.notify({
        title: "Selected Area Added to Queue",
        text: `${polygonName} added to processing queue`,
        type: "info",
      });

      notification.notify({
          title: "Running Model",
          text: `Running model on the latest data`,
          type: "info",
        });
      
      try {
        const response = await axios.post(
          'https://3a6b477c-5f32-40dd-b06d-69be04ada480-00-3boaaj7j16t6o.riker.replit.dev/api/predict', 
          JSON.stringify(featureCollection),
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );
        console.log('Selected area processed:', response.data);
        
        // Simulate delay (1-3 seconds)
        await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 1000));

        const prediction = response.data.prediction.toFixed(2);

        // Update job in the queue
        this.updateJobStatus(jobId, 'complete', prediction);
        
        notification.notify({
          title: "Selected Area Processed",
          text: `${polygonName} processed successfully`,
          type: "success",
        });

        

      } catch (error) {
        console.error('Error processing selected area:', error);
        
        // Update job status to failed
        this.updateJobStatus(jobId, 'failed');

        notification.notify({
          title: "Error",
          text: `Failed to process ${polygonName}`,
          type: "error",
        });
      }
    },
  },
  created() {
    // Load the model queue from Vuex when the component is created
    this.modelQueue = this.$store.state.modelQueue;
  }
}
</script>

<style scoped>
.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>