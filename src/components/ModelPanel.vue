<template>
  <notifications position="top-right" />
  <div class="model-panel">
    <h2>Run Model</h2>
    
    <details>
      <summary>Latest Model Results</summary>

      <div class="input-group">

      <label for="state">State:</label>
      <select id="state" v-model="selectedState" @change="updateCounties" class="fixed-width">
        <option v-for="state in availableStates" :key="state" :value="state">{{ state }}</option>
      </select>
      </div>

      <div class="input-group">
        <label for="county">County:</label>
        <select id="county" v-model="selectedCounty" :disabled="!selectedState" class="fixed-width">
            <option v-for="county in availableCounties" :key="county.countyFp" :value="county">
            {{ county.name }} 
          </option>
        </select>
      </div>

      <div class="input-group">
        <label for="predictionType">Prediction Type</label>
        <select id="predictionType" v-model="selectedPredictionType" class="fixed-width">
          <option value="In Season">In Season</option>
          <option value="In Season">End of Season</option>
          <!-- Add more prediction type options as needed -->
        </select>
      </div>

      <div class="input-group">
        <label for="model">Select a model:</label>
        <select id="model" v-model="selectedModel" class="fixed-width">
          <option value="Hybrid">Bayesian</option>
          <option value="Hybrid">Partial Domain Adaption</option>
          <option value="Hybrid">Multiple Instance Learning</option>
          <option value="Hybrid">Hybrid</option>
          <!-- Add more model options as needed -->
        </select>
      </div>

      <button @click="runModel" class="run-button" :disabled="isRunning">
        {{ isRunning ? 'Running...' : 'Run Selected Model' }}
        </button>
  
    </details>

    <!-- New summary for drawn polygons -->
    <details>
      <summary>Drawn Polygons</summary>
      <div v-if="drawnPolygons.length > 0">
        <ul class="polygon-list">
          <li v-for="(polygon, index) in drawnPolygons" :key="polygon.id">
            Polygon {{ index + 1 }}: {{ formatPolygonCoordinates(polygon) }}
          </li>
        </ul>
        <button @click="runSelectedArea" class="run-selected-area-button">Run Selected Area</button>
        <button @click="clearAllPolygons" class="clear-polygons-button">Clear All Polygons</button>
      </div>
      <div v-else>
        No polygons have been drawn on the map.
      </div>
    </details>

    <details open>
    <summary>Model Queue</summary>
    <div class="queue-container">
    <div class="table-wrapper">
      <table class="queue-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Prediction</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in modelQueue" :key="job.id">
            <td>{{ job.name || job.county + ', ' + job.state }}</td>
            <td>{{ job.prediction || 'Pending' }}</td>
            <td>
              <span v-if="job.status === 'complete'" class="status-icon complete">✓</span>
              <span v-else-if="job.status === 'failed'" class="status-icon failed">✗</span>
              <span v-else class="status-icon pending">●</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <button @click="clearQueue" class="clear-queue-button">Clear Queue</button>
    </div>
    </details>

      <ProgressBar v-if="isRunning" :value="progress" :text="`${estimatedTime}s remaining`" />
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

        try {
          // Make API request
          const response = await axios.get(`https://us-central1-nifa-webgis.cloudfunctions.net/nifa-pred-get?FIPS=${fullFips}&year=2023`);
          
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
.model-panel {
  background-color: #ffffff;
  padding: 20px;
  border-radius: 8px;
  /* box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); */
}

h2 {
  color: #00a86b;
  margin-top: 0;
  margin-bottom: 20px;
}

.input-group {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

label {
  font-weight: bold;
}

select {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 16px;
}

.fixed-width {
  width: 200px; /* Adjust the width as needed */
}

.run-button {
  background-color: var(--color-primary);
  color: white;
  border: none;
  padding: 10px 20px;
  font-size: 16px;
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
  margin-top: 10px;
}

.run-button:hover {
  background-color: #008f5b;
}

.run-button:disabled {
background-color: #cccccc;
cursor: not-allowed;
}

.queue-container {
  max-height: 300px; /* Adjust the height as needed */
  overflow-y: auto;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.queue-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.queue-table th, .queue-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.queue-table th {
  background-color: #f2f2f2;
}

.status-icon {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  text-align: center;
  line-height: 20px;
}

.status-icon.complete {
  color: green;
  font-weight: bold;
  font-size: 1.4em;
}

.status-icon.pending {
  color: red;
}

.status-icon.failed {
  color: red;
  font-weight: bold;
  font-size: 1.4em;
}

details {
  margin-bottom: 20px;
}

summary {
  cursor: pointer;
  font-weight: bold;
  margin-bottom: 10px;
}

.polygon-list {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.polygon-list li {
  margin-bottom: 10px;
  font-size: 0.9em;
  word-break: break-all;
}

.clear-polygons-button {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.clear-polygons-button:hover {
  background-color: #d32f2f;
}

.run-selected-area-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
  margin-right: 10px;
}

.run-selected-area-button:hover {
  background-color: #45a049;
}
</style>