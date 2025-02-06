<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-2xl font-bold text-green-600 mb-4">Mapping Settings</h2>
    
    <div class="space-y-4">
      <div>
        <label for="title" class="block text-sm font-medium text-gray-700">Title:</label>
        <input id="title" :value="title" readonly
          class="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm">
      </div>
      
      <div>
        <label for="description" class="block text-sm font-medium text-gray-700">Description:</label>
        <textarea id="description" v-model="description" rows="4" 
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-300 focus:ring focus:ring-green-200 focus:ring-opacity-50">
        </textarea>
      </div>
      
      <div>
        <label for="font" class="block text-sm font-medium text-gray-700">Font:</label>
        <select id="font" v-model="font" 
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-300 focus:ring focus:ring-green-200 focus:ring-opacity-50">
          <option value="Arial">Arial</option>
          <option value="Helvetica">Helvetica</option>
          <option value="Times New Roman">Times New Roman</option>
          <option value="Courier">Courier</option>
        </select>
      </div>

      <div class="flex space-x-4">
        <button @click="openMapEditor" class="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
          Edit Map
        </button>
      </div>
    </div>

    <MapEditComponent
      v-if="showMapEditor"
      :title="title"
      :description="description"
      :font="font"
      @close="closeMapEditor"
      @save="handleMapSave"
    />
  </div>
</template>

<script>
import { useStore } from 'vuex';  
import { computed, ref } from 'vue';
import MapEditComponent from './MapEditComponent.vue';

export default {
  name: 'MappingPanel',
  components: {
    MapEditComponent
  },
  setup() {
    const store = useStore()
    const showMapEditor = ref(false)

    const title = computed(() => store.state.mapTitle)
    const description = computed({
      get: () => store.state.mapDescription,
      set: (value) => store.commit('setMapDescription', value)
    })
    const font = computed({
      get: () => store.state.mapFont,
      set: (value) => store.commit('setMapFont', value)
    })

    const openMapEditor = () => {
      showMapEditor.value = true;
    };

    const closeMapEditor = () => {
      showMapEditor.value = false;
    };

    const handleMapSave = (dataURL) => {
      console.log('Saved map:', dataURL);
      closeMapEditor();
    };

    return {
      title,
      description,
      font,
      showMapEditor,
      openMapEditor,
      closeMapEditor,
      handleMapSave
    }
  }
}
</script>