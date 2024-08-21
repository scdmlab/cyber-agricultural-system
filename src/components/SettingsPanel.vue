<!-- src/components/SettingsPanel.vue -->
<template>
  <div class="settings-panel">
    <h2>Settings</h2>
    <div>
      <label for="crop">Crop:</label>
      <select id="crop" v-model="crop" @change="updateSettings">
        <option value="corn">Corn</option>
        <option value="soybean">Soybean</option>
      </select>
    </div>
    <div>
      <label for="year">Year:</label>
      <select id="year" v-model="year" @change="updateSettings">
        <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
      </select>
    </div>
    <div>
      <label for="month">Month:</label>
      <select id="month" v-model="month" @change="updateSettings">
        <option v-for="m in months" :key="m" :value="m">{{ m }}</option>
      </select>
    </div>
    <div>
      <label for="property">Property:</label>
      <select id="property" v-model="property" @change="updateSettings">
        <option value="pred">Prediction</option>
        <option value="yield">Yield</option>
        <option value="error">Error</option>
      </select>
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'SettingsPanel',
  setup() {
    const store = useStore()
    const crop = ref(store.state.currentCrop)
    const year = ref(store.state.currentYear)
    const month = ref(store.state.currentMonth)
    const property = ref(store.state.currentProperty)

    const years = computed(() => {
      return Array.from({ length: 12 }, (_, i) => (2010 + i).toString())
    })

    const months = computed(() => {
      return Array.from({ length: 10 }, (_, i) => i.toString())
    })

    function updateSettings() {
      store.commit('setCrop', crop.value)
      store.commit('setYear', year.value)
      store.commit('setMonth', month.value)
      store.commit('setProperty', property.value)
      store.dispatch('fetchMapData')
    }

    return {
      crop,
      year,
      month,
      property,
      years,
      months,
      updateSettings,
    }
  },
}
</script>

<style scoped>
.settings-panel {
  padding: 20px;
  background-color: #f0f0f0;
  border-radius: 5px;
}

.settings-panel div {
  margin-bottom: 10px;
}

label {
  display: inline-block;
  width: 80px;
}

select {
  width: 120px;
}
</style>