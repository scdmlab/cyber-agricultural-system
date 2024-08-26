<template>
    <div class="model-panel">
      <h2>Run Model</h2>
      
      <div class="input-group">
        <label for="state">State:</label>
        <select id="state" v-model="selectedState" @change="updateCounties">
            <option v-for="state in availableStates" :key="state" :value="state">{{ state }}</option>
        </select>
        </div>

        <div class="input-group">
        <label for="county">County:</label>
        <select id="county" v-model="selectedCounty" :disabled="!selectedState">
            <option v-for="county in availableCounties" :key="county" :value="county">{{ county }}</option>
        </select>
        </div>
  
      <div class="input-group">
        <label for="predictionType">Prediction Type</label>
        <select id="predictionType" v-model="selectedPredictionType">
          <option value="In Season">In Season</option>
          <option value="In Season">End of Season</option>
          <!-- Add more prediction type options as needed -->
        </select>
      </div>
  
      <div class="input-group">
        <label for="model">Select a model:</label>
        <select id="model" v-model="selectedModel">
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
        <ProgressBar v-if="isRunning" :value="progress" :text="`${estimatedTime}s remaining`" />
        <notifications position="bottom-right" />
    </div>
  </template>
  
  <script>
  import { mapState, mapActions } from 'vuex';
  import { Notifications, useNotification } from '@kyvg/vue3-notification';
  import ProgressBar from 'primevue/progressbar';

  
  export default {
    name: 'ModelPanel',
    components: {
      ProgressBar
    },
    data() {
      return {
        selectedState: '',
        selectedCounty: '',
        selectedPredictionType: 'In Season',
        selectedModel: 'Hybrid',
        isRunning: false,
        progress: 0,
        estimatedTime: 0
      }
    },
    computed: {
      ...mapState(['countyData', 'availableStates']),
      availableCounties() {
        return this.countyData[this.selectedState] || [];
      }
    },
    methods: {
      ...mapActions(['loadCountyData']),
      updateCounties() {
        this.selectedCounty = '';
      },
      async runModel() {
      const stateFips = this.countyData[this.selectedState].find(c => c.name === this.selectedCounty)?.stateFp;
      const countyFips = this.countyData[this.selectedState].find(c => c.name === this.selectedCounty)?.countyFp;
      
      if (stateFips && countyFips) {
        const fullFips = stateFips + countyFips.padStart(3, '0');
        const notification = useNotification();
        
        this.isRunning = true;
        this.progress = 0;
        this.estimatedTime = 60; // 60 seconds estimated time

        notification.notify({
          title: "Model Running",
          text: `Running ${this.selectedModel} model for ${this.selectedCounty}, ${this.selectedState}`,
          type: "info",
        });

        // Simulate API call and progress
        const interval = setInterval(() => {
          this.progress += 1;
          if (this.progress >= 100) {
            clearInterval(interval);
            this.isRunning = false;
            toast.success(`${this.selectedModel} model run completed for ${this.selectedCounty}, ${this.selectedState}`);
          }
        }, 600);

        // Simulate API call
        // In a real scenario, replace this with an actual API call
        // await this.$api.runModel({ ... });
      } else {
        const notification = useNotification();
        notification.notify({
          title: "Error",
          text: "Invalid state or county selection",
          type: "error",
        });
      }
    },
    mounted() {
      this.loadCountyData();
    }
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
  }
  
  label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
  }
  
  select {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 16px;
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
  </style>