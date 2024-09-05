<template>
  <notifications position="top-right" />
  <div class="model-panel">
    <h2>Run Model</h2>
    
    <details>
      <summary>Running Config</summary>

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

    <details open>
    <summary>Model Queue</summary>
    <div class="queue-container">
    <div class="table-wrapper">
      <table class="queue-table">
        <thead>
          <tr>
            <th>County</th>
            <th>State</th>
            <th>Prediction</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in modelQueue" :key="job.id">
            <td>{{ job.county }}</td>
            <td>{{ job.state }}</td>
            <td>{{ job.prediction || 'Pending' }}</td>
            <td>
              <span v-if="job.status === 'complete'" class="status-icon complete">✓</span>
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
import { mapState, mapActions } from 'vuex';
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
    availableStates() {
      const states = new Set();
      Object.values(this.countyData).forEach(counties => {
        counties.forEach(county => states.add(this.getStateName(county.stateFp)));
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
        );
    }
  },
  methods: {
    ...mapActions(['loadCountyData', 'loadCountyInfo']),
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
      this.$store.commit('removeMarkers');
      const notification = useNotification();
      notification.notify({
        title: "Queue Cleared",
        text: "The model queue has been cleared",
        type: "info",
      });
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
}

.status-icon.pending {
  color: red;
}

details {
  margin-bottom: 20px;
}

summary {
  cursor: pointer;
  font-weight: bold;
  margin-bottom: 10px;
}

.clear-queue-button {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 10px 20px;
  font-size: 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.clear-queue-button:hover {
  background-color: #d32f2f;
}
</style>