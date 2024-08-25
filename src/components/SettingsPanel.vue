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
  padding: var(--space-large);
  background-color: var(--color-background-mute);
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
  margin-bottom: var(--space-medium);
}

label {
  display: block;
  margin-bottom: var(--space-small);
  color: var(--color-text);
}

select {
  width: 100%;
  padding: var(--space-small);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
}

.apply-button {
  margin-top: var(--space-large);
  padding: var(--space-medium);
  background-color: var(--color-primary);
  color: var(--color-text-button);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: var(--font-size-medium);
}

.apply-button:hover {
  background-color: var(--color-primary-dark);
}
</style>
