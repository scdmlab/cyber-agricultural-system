<!-- src/components/SettingsPanel.vue -->
<template>
  <div class="settings-panel">
    <h2>Settings</h2>
    <div class="settings-content">
      <div>
        <label for="crop">Crop:</label>
        <select id="crop" v-model="localCrop">
          <option value="corn">Corn</option>
          <option value="soybean">Soybean</option>
        </select>
      </div>
      <div>
        <label for="year">Year:</label>
        <select id="year" v-model="localYear">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
      <div>
        <label for="month">Month:</label>
        <select id="month" v-model="localMonth">
          <option v-for="m in months" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>
      <div>
        <label for="property">Property:</label>
        <select id="property" v-model="localProperty">
          <option value="pred">Prediction</option>
          <option value="yield">Yield</option>
          <option value="error">Error</option>
        </select>
      </div>
    </div>
    <button @click="applySettings" class="apply-button">Apply</button>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'SettingsPanel',
  emits: ['apply-settings'],
  setup() {
    const store = useStore()
    const localCrop = ref(store.state.currentCrop)
    const localYear = ref(store.state.currentYear)
    const localMonth = ref(store.state.currentMonth)
    const localProperty = ref(store.state.currentProperty)

    const years = computed(() => {
      return Array.from({ length: 12 }, (_, i) => (2010 + i).toString())
    })

    const months = computed(() => {
      return Array.from({ length: 10 }, (_, i) => i.toString())
    })

    function applySettings() {
      store.commit('setCrop', localCrop.value)
      store.commit('setYear', localYear.value)
      store.commit('setMonth', localMonth.value)
      store.commit('setProperty', localProperty.value)
      store.dispatch('fetchMapData')
    }

    return {
      localCrop,
      localYear,
      localMonth,
      localProperty,
      years,
      months,
      applySettings,
    }
  },
}
</script>

<style scoped>
.settings-panel {
  padding: 20px;
  background-color: #f0f0f0;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.settings-content {
  flex-grow: 1;
  overflow-y: auto;
}

.settings-content div {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
}

select {
  width: 100%;
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.apply-button {
  margin-top: 20px;
  padding: 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.apply-button:hover {
  background-color: #45a049;
}
</style>