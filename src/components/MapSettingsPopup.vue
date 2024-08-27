<template>
    <PopupWindow title="Map Settings" @close="close">
      <div class="setting">
        <label>Choropleth Range:</label>
        <input type="number" v-model.number="localMinValue" />
        <input type="number" v-model.number="localMaxValue" />
      </div>
      <div class="setting">
      <label>Color Scheme:</label>
        <div class="color-scheme-container">
          <div class="color-preview" :style="{ background: `linear-gradient(to right, ${localColorScheme.join(', ')})` }"></div>
          <div class="color-pickers">
            <input type="color" v-model="localColorScheme[0]" />
            <input type="color" v-model="localColorScheme[1]" />
            <input type="color" v-model="localColorScheme[2]" />
          </div>
        </div>
      </div>
      <div class="setting">
        <label>Choropleth Opacity:</label>
        <input type="range" v-model.number="localChoroplethOpacity" min="0" max="1" step="0.1" />
      </div>
      <div class="setting">
        <label>Basemap Opacity:</label>
        <input type="range" v-model.number="localBasemapOpacity" min="0" max="1" step="0.1" />
      </div>
      <div class="buttons">
        <button @click="apply">Apply</button>
        <button @click="close">Cancel</button>
      </div>
    </PopupWindow>
  </template>
  
  <script>
  import { ref, watch, computed } from 'vue'
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
    const localMinValue = ref(props.minValue)
    const localMaxValue = ref(props.maxValue)
    const localColorScheme = ref([...props.colorScheme])
    const localChoroplethOpacity = ref(props.choroplethOpacity)
    const localBasemapOpacity = ref(props.basemapOpacity)

    const defaultMinValue = computed(() => props.minValue)
    const defaultMaxValue = computed(() => props.maxValue)

    watch(() => props, (newProps) => {
      localMinValue.value = newProps.minValue
      localMaxValue.value = newProps.maxValue
      localColorScheme.value = [...newProps.colorScheme]
      localChoroplethOpacity.value = newProps.choroplethOpacity
      localBasemapOpacity.value = newProps.basemapOpacity
    }, { deep: true })

    function apply() {
      emit('apply', {
        minValue: localMinValue.value,
        maxValue: localMaxValue.value,
        colorScheme: localColorScheme.value,
        choroplethOpacity: localChoroplethOpacity.value,
        basemapOpacity: localBasemapOpacity.value,
      })
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
  </style>