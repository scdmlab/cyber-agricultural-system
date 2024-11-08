<template>
  <PopupWindow
    title="Map Settings"
    :width="400"
    :height="500"
    @close="$emit('close')"
  >
    <div class="setting">
      <label>Choropleth Range:</label>
      <div class="range-inputs">
        <input type="number" v-model.number="localMinValue" :placeholder="defaultMinValue" />
        <span>to</span>
        <input type="number" v-model.number="localMaxValue" :placeholder="defaultMaxValue" />
      </div>
    </div>
    <div class="setting">
    <label>Color Scheme:</label>
      <div class="color-scheme-container">
        <div class="color-preview" :style="{ background: `linear-gradient(to right, ${localColorScheme.join(', ')})` }"></div>
        <div class="color-pickers">
          <input type="color" v-model="localColorScheme[0]" />
          <input type="color" v-model="localColorScheme[1]" />
        </div>
      </div>
    </div>
    <div class="setting">
      <label>Choropleth Opacity: {{ localChoroplethOpacity.toFixed(1) }}</label>
      <div class="slider-container">
        <input type="range" v-model.number="localChoroplethOpacity" min="0" max="1" step="0.1" />
      </div>
    </div>
    <div class="setting">
      <label>Basemap Opacity: {{ localBasemapOpacity.toFixed(1) }}</label>
      <div class="slider-container">
        <input type="range" v-model.number="localBasemapOpacity" min="0" max="1" step="0.1" />
      </div>
    </div>
    <div class="buttons">
      <button @click="apply">Apply</button>
      <button @click="close">Cancel</button>
    </div>
  </PopupWindow>
</template>

<script>
import { ref, watch, computed } from 'vue'
import { useStore } from 'vuex'
import PopupWindow from './PopupWindow.vue'

export default {
  name: 'MapSettingsPopup',
  components: {
    PopupWindow
  },
  props: {
    minValue: Number,
    maxValue: Number,
    colorScheme: Array,
    choroplethOpacity: Number,
    basemapOpacity: Number,
  },
  emits: ['close', 'apply'],
  setup(props, { emit }) {
    const store = useStore()
    const choroplethSettings = store.state.choroplethSettings

    const localMinValue = ref(choroplethSettings.minValue)
    const localMaxValue = ref(choroplethSettings.maxValue)
    const localColorScheme = ref([...choroplethSettings.colorScheme])
    const localChoroplethOpacity = ref(choroplethSettings.choroplethOpacity)
    const localBasemapOpacity = ref(choroplethSettings.basemapOpacity)

    const defaultMinValue = computed(() => choroplethSettings.minValue)
    const defaultMaxValue = computed(() => choroplethSettings.maxValue)

    watch(() => choroplethSettings, (newSettings) => {
      localMinValue.value = newSettings.minValue
      localMaxValue.value = newSettings.maxValue
      localColorScheme.value = [...newSettings.colorScheme]
      localChoroplethOpacity.value = newSettings.choroplethOpacity
      localBasemapOpacity.value = newSettings.basemapOpacity
    }, { deep: true })

    function apply() {
      const newSettings = {
        minValue: localMinValue.value,
        maxValue: localMaxValue.value,
        colorScheme: localColorScheme.value,
        choroplethOpacity: localChoroplethOpacity.value,
        basemapOpacity: localBasemapOpacity.value,
      }
      store.commit('setChoroplethSettings', newSettings)
      emit('apply', newSettings)
      emit('close')
    }

    function close() {
      emit('close')
    }

    return {
      localMinValue,
      localMaxValue,
      localColorScheme,
      localChoroplethOpacity,
      localBasemapOpacity,
      apply,
      close,
      defaultMinValue,
      defaultMaxValue,
    }
  }
}
</script>

<style scoped>
.settings-popup {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: var(--color-background);
  padding: 20px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-medium);
  z-index: var(--z-index-popup);
}

.setting {
  margin-bottom: 15px;
}

.color-preview {
  width: 100%;
  height: 20px;
  margin-bottom: 5px;
}

.color-scheme-container {
display: flex;
flex-direction: column;
align-items: stretch;
}

.color-preview {
  width: 100%;
  height: 20px;
  margin-bottom: 5px;
}

.color-pickers {
  display: flex;
  justify-content: space-between;
}

.color-pickers input[type="color"] {
  width: 30px;
  height: 30px;
  padding: 0;
  border: none;
  cursor: pointer;
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

button {
  padding: 5px 10px;
  background-color: var(--color-primary);
  color: var(--color-text-light);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
}

button:hover {
  background-color: var(--color-primary-dark);
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-inputs input[type="number"] {
  width: 80px;
}

.slider-container {
  width: 200px;
  margin-top: 5px;
}

input[type="range"] {
  width: 100%;
}
</style>