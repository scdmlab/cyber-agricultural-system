<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Data Selection</h2>
    
    <div class="space-y-4">
      <div>
        <label for="crop" class="block text-sm font-medium text-gray-700">Crop:</label>
        <select id="crop" v-model="localCrop" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option value="corn">Corn</option>
          <option value="soybean">Soybean</option>
        </select>
      </div>
      
      <div>
        <label for="year" class="block text-sm font-medium text-gray-700">Year:</label>
        <select id="year" v-model="localYear" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
      
      <div>
        <label for="month" class="block text-sm font-medium text-gray-700">Prediction Date:</label>
        <select id="month" v-model="localMonth" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option v-for="(date, index) in monthOptions" :key="index" :value="index">{{ date }}</option>
        </select>
      </div>
      
      <div>
        <label for="property" class="block text-sm font-medium text-gray-700">Property:</label>
        <select id="property" v-model="localProperty" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option value="pred">Prediction</option>
          <option value="yield">Yield</option>
          <option value="error">Error</option>
        </select>
      </div>
    </div>
    
    <button @click="applyDataSelection" class="mt-6 w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition duration-300">Apply</button>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'DataSelectionPanel',
  emits: ['apply-data-selection'],
  setup(props, { emit }) {
    const store = useStore()
    const localCrop = ref(store.state.currentCrop)
    const localYear = ref(store.state.currentYear)
    const localMonth = ref(store.state.currentMonth)
    const localProperty = ref(store.state.currentProperty)

    const monthOptions = {
      "0": "05/13",
      "1": "05/29",
      "2": "06/14",
      "3": "06/30",
      "4": "07/16",
      "5": "08/01",
      "6": "08/17",
      "7": "09/02",
      "8": "09/18",
      "9": "10/04"
    }

    const years = computed(() => {
      return Array.from({ length: 12 }, (_, i) => (2010 + i).toString())
    })

    const months = computed(() => {
      return Array.from({ length: 10 }, (_, i) => i.toString())
    })

    function applyDataSelection() {
      store.commit('setCrop', localCrop.value)
      store.commit('setYear', localYear.value)
      store.commit('setMonth', localMonth.value)
      store.commit('setProperty', localProperty.value)
      
      store.dispatch('loadCsvData').then(() => {
        // Get the current data
        const currentYear = parseInt(store.state.currentYear)
        const currentProperty = store.state.currentProperty
        const allPredictions = store.state.allPredictions

        // Filter data for the current year and property
        const values = allPredictions
          .filter(row => row.year === currentYear)
          .map(row => parseFloat(row[currentProperty]))
          .filter(v => !isNaN(v) && v !== null && v !== undefined)

        if (values.length > 0) {
          const minValue = Math.min(...values)
          const maxValue = Math.max(...values)

          // Update choropleth settings with new min/max values
          store.commit('setChoroplethSettings', {
            ...store.state.choroplethSettings,
            minValue,
            maxValue
          })
        }

        // Emit event after data selection is applied
        emit('apply-data-selection')
      })
    }

    return {
      localCrop,
      localYear,
      localMonth,
      localProperty,
      years,
      months,
      applyDataSelection,
      monthOptions
    }
  },
}
</script>
