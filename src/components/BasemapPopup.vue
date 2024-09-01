<template>
    <PopupWindow title="Select Basemap" @close="closePopup">
        <div class="basemap-grid">
        <button
            v-for="basemap in basemaps"
            :key="basemap.id"
            @click="selectBasemap(basemap.id)"
            :class="{ 'selected': basemap.id === selectedBasemap, 'no-thumbnail': !imageExists(basemap.thumbnail) }"
        >
            <img v-if="imageExists(basemap.thumbnail)" :src="basemap.thumbnail" :alt="basemap.name">
            <div v-else class="no-thumbnail-text">{{ basemap.name }}</div>
            <span>{{ basemap.name }}</span>
        </button>
        </div>
    </PopupWindow>
</template>
  
  <script>
  import { defineComponent, computed } from 'vue'
  import { useStore } from 'vuex'
  import PopupWindow from './PopupWindow.vue'
  import { basemaps } from '@/utils/basemaps'
  
  export default defineComponent({
    name: 'BasemapPopup',
    components: { PopupWindow },
    emits: ['close'],
    setup(props, { emit }) {
      const store = useStore()
  
      const selectedBasemap = computed(() => store.state.selectedBasemap)
  
      const selectBasemap = (basemapId) => {
        store.commit('setSelectedBasemap', basemapId)
        }
  
      const closePopup = () => {
        emit('close')
      }

      const imageExists = (url) => {
      const img = new Image()
      img.src = url
      return img.complete && img.naturalHeight !== 0
    }
  
      return {
        basemaps,
        selectedBasemap,
        selectBasemap,
        closePopup,
        imageExists
      }
    },
  })
  </script>
  
  <style scoped>
  .basemap-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 10px;
}

.basemap-grid button {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  background-color: var(--color-background);
  cursor: pointer;
  transition: all 0.3s ease;
}

.basemap-grid button:hover {
  background-color: var(--color-background-soft);
}

.basemap-grid button.selected {
  border-color: var(--color-primary);
  background-color: var(--color-background-mute);
}

.basemap-grid button img {
  width: 100%;
  height: auto;
  margin-bottom: 5px;
  border-radius: var(--border-radius);
}

.basemap-grid button span {
  font-size: 0.9em;
}

.basemap-grid button.no-thumbnail {
  background-color: #3498db !important; /* Blue color */
}

.no-thumbnail-text {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100px; /* Adjust as needed */
  color: white;
  font-weight: bold;
  text-align: center;
}

.basemap-grid button.no-thumbnail:hover {
  background-color: #2980b9 !important; /* Darker blue on hover */
}

.basemap-grid button.no-thumbnail.selected {
  background-color: #2c3e50 !important; /* Even darker blue when selected */
}
  </style>