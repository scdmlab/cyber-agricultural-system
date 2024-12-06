<template>
  <notifications position="top-right" />
  <div class="bg-white p-6 rounded-lg shadow-md h-full flex flex-col">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Run Model</h2>
    
    <div class="overflow-y-auto flex-grow">
      <details class="mb-4">
        <summary class="cursor-pointer font-bold mb-2">Latest Model Results</summary>

        <div class="space-y-4">
          <div>
            <label for="crop" class="block text-sm font-medium text-gray-700">Crop:</label>
            <select id="crop" v-model="selectedCrop" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option value="corn">Corn</option>
              <option value="soybean">Soybean</option>
            </select>
          </div>

          <div>
            <label for="year" class="block text-sm font-medium text-gray-700">Year:</label>
            <select id="year" v-model="selectedYear" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option v-for="year in availableYears" :key="year" :value="year">{{ year }}</option>
            </select>
          </div>

          <div>
            <label for="state" class="block text-sm font-medium text-gray-700">State:</label>
            <select id="state" v-model="selectedState" @change="updateCounties" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option v-for="state in availableStates" :key="state" :value="state">{{ state }}</option>
            </select>
          </div>

          <div>
            <label for="county" class="block text-sm font-medium text-gray-700">County:</label>
            <select id="county" v-model="selectedCounty" :disabled="!selectedState" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option v-for="county in availableCounties" :key="county.fips" :value="county">
                {{ county.name }}
              </option>
            </select>
          </div>

          <div>
            <label for="predictionType" class="block text-sm font-medium text-gray-700">Prediction Type:</label>
            <select id="predictionType" v-model="selectedPredictionType" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
              <option value="in_season">In Season</option>
              <option value="end_of_season">End of Season</option>
            </select>
          </div>

          <button @click="runModel" class="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300">
            Get Prediction
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
      selectedCrop: 'corn',
      selectedYear: new Date().getFullYear().toString(),
      selectedState: null,
      selectedCounty: null,
      selectedPredictionType: 'in_season',
      isRunning: false,
      progress: 0,
      estimatedTime: 0,
      modelQueue: [],
      availableYears: [
        (new Date().getFullYear() - 1).toString(),
        new Date().getFullYear().toString(),
      ],
    }
  },
  computed: {
    ...mapState(['countyData', 'countyInfo', 'markers']),
    ...mapGetters(['getDrawnPolygons']),
    drawnPolygons() {
      return this.getDrawnPolygons;
    },
    availableStates() {
      return [...new Set(Object.values(this.countyInfo)
        .map(county => stateCodeMap[county.stateFips]))]
        .filter(Boolean)
        .sort();
    },
    availableCounties() {
      if (!this.selectedState) return [];
      
      const stateFp = Object.keys(stateCodeMap)
        .find(key => stateCodeMap[key] === this.selectedState);
        
      return Object.values(this.countyInfo)
        .filter(county => county.stateFips === stateFp)
        .map(county => ({
          name: county.name,
          fips: county.fips,
          stateFips: county.stateFips
        }))
        .sort((a, b) => a.name.localeCompare(b.name));
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
    if (!this.selectedCounty) {
      const notification = useNotification();
      notification.notify({
        title: "Error",
        text: "Please select a county",
        type: "error"
      });
      return;
    }

    const notification = useNotification();
    const jobId = Date.now();

    // Add job to queue
    this.modelQueue.push({
      id: jobId,
      name: `${this.selectedCrop} - ${this.selectedCounty.name}, ${this.selectedState}`,
      county: this.selectedCounty.name,
      state: this.selectedState,
      prediction: null,
      status: 'pending'
    });

    try {
      const response = await axios.get(
        `/api/predictions/${this.selectedCrop}/${this.selectedYear}/${this.selectedPredictionType}/${this.selectedCounty.fips}`
      );

      // Update job status with prediction
      const prediction = this.selectedPredictionType === 'in_season' 
        ? Object.values(response.data.predictions).pop().prediction
        : response.data.prediction;

      this.updateJobStatus(jobId, 'complete', prediction);

      notification.notify({
        title: "Prediction Complete",
        text: `Prediction for ${this.selectedCounty.name}, ${this.selectedState} completed successfully`,
        type: "success"
      });

    } catch (error) {
      console.error('Error fetching prediction:', error);
      this.updateJobStatus(jobId, 'failed');
      
      notification.notify({
        title: "Error",
        text: error.response?.data?.detail || "Failed to fetch prediction",
        type: "error"
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
      
      try {
        const response = await axios.post(
          '/api/model/',
          featureCollection,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.data.status === 'success') {
          const prediction = response.data.prediction[0].toFixed(2); // Format to 2 decimal places
          this.updateJobStatus(jobId, 'complete', prediction);
          
          notification.notify({
            title: "Prediction Complete",
            text: `Prediction for selected area: ${prediction} bu/acre`,
            type: "success"
          });
        } else {
          throw new Error('Prediction failed');
        }
        
      } catch (error) {
        console.error('Error processing selected area:', error);
        this.updateJobStatus(jobId, 'failed');
        
        notification.notify({
          title: "Error",
          text: error.response?.data?.detail || "Failed to process selected area",
          type: "error"
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