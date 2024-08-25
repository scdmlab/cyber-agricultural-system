<template>
    <div class="mapping-panel">
      <h2>Mapping Settings</h2>
      <div class="form-group">
        <label for="title">Title:</label>
        <input id="title" v-model="title" @input="updateTitle" placeholder="Crop Property for US in Year">
      </div>
      <div class="form-group">
        <label for="description">Description:</label>
        <textarea id="description" v-model="description" rows="4"></textarea>
      </div>
      <div class="form-group">
        <label for="font">Font:</label>
        <select id="font" v-model="font">
          <option value="Arial">Arial</option>
          <option value="Helvetica">Helvetica</option>
          <option value="Times New Roman">Times New Roman</option>
          <option value="Courier">Courier</option>
        </select>
      </div>
      <div class="form-group">
        <label for="backgroundColor">Background Color:</label>
        <input type="color" id="backgroundColor" v-model="backgroundColor">
      </div>

      <div class="form-group">
        <button @click="exportMap" class="export-button">Export Map</button>
      </div>
    </div>
  </template>
  
  <script>
  import { useStore } from 'vuex';  
  import { computed } from 'vue';
  import { MaplibreExportControl, Size, PageOrientation, Format, DPI  } from '@watergis/maplibre-gl-export';
  export default {
    name: 'MappingPanel',
    setup() {
        const store = useStore()

        const title = computed({
        get: () => store.state.mapTitle,
        set: (value) => store.commit('setMapTitle', value)
        })
        const description = computed({
        get: () => store.state.mapDescription,
        set: (value) => store.commit('setMapDescription', value)
        })
        const font = computed({
        get: () => store.state.mapFont,
        set: (value) => store.commit('setMapFont', value)
        })
        const backgroundColor = computed({
        get: () => store.state.mapBackgroundColor,
        set: (value) => store.commit('setMapBackgroundColor', value)
        })

        const exportMap = () => {
      const map = store.state.map
      if (!map) {
        console.error('Map instance not found')
        return
      }

      const exportControl = new MaplibreExportControl({
        PageSize: Size.A4,
        PageOrientation: PageOrientation.Landscape,
        Format: Format.PNG,
        DPI: DPI[300],
        Filename: `${store.state.mapTitle || 'Map'}_export`,
        Attribution: '© OpenStreetMap contributors',
        Local: 'en',
        Crosshair: false,
        PrintableArea: false,
      });

      map.addControl(exportControl, 'top-left');
    //   exportControl.trigger();
    }

        return {
        title,
        description,
        font,
        backgroundColor,
        exportMap
        }
    }
  }
  </script>
  
  <style scoped>
  .mapping-panel {
    padding: var(--space-medium);
  }
  
  .form-group {
    margin-bottom: var(--space-medium);
  }
  
  label {
    display: block;
    margin-bottom: var(--space-small);
  }
  
  input[type="text"],
  textarea,
  select {
    width: 100%;
    padding: var(--space-small);
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius);
  }
  
  input[type="color"] {
    width: 50px;
    height: 50px;
    padding: 0;
    border: none;
  }

  .export-button {
  background-color: var(--color-primary);
  color: white;
  padding: var(--space-small);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: var(--font-size-base);
}

.export-button:hover {
  background-color: var(--color-primary-dark);
}
  </style>