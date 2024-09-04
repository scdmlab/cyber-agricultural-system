<template>
    <PopupWindow :title="'Edit Map'" :width="'80vw'" :height="'80vh'" @close="closeEditor">
      <div class="map-edit-container">
        <div class="map-title">{{ title }}</div>
        <div class="map-description">{{ description }}</div>
        <canvas id="map-edit-canvas" ref="canvasRef"></canvas>
        <div v-if="!mapImage" class="loading-message">Loading map image...</div>
        <div class="edit-tools">
          <button @click="addRectangle">Add Rectangle</button>
          <button @click="addCircle">Add Circle</button>
          <button @click="addText">Add Text</button>
          <button @click="deleteSelected">Delete Selected</button>
          <button @click="saveMap">Save Map</button>
        </div>
      </div>
    </PopupWindow>
  </template>
  
  <script>
  import { onMounted, ref , computed, watch} from 'vue';
  import { useStore, } from 'vuex';
  import PopupWindow from './PopupWindow.vue';
  import * as fabric  from 'fabric';
  
  export default {
    name: 'MapEditComponent',
    components: {
      PopupWindow
    },
    props: {
      title: String,
      description: String
    },
    setup(props, { emit }) {
      const store = useStore();
      const canvas = ref(null);
      const canvasRef = ref(null);
      const mapImage = computed(() => store.getters.getMapImage)
  
      onMounted(() => {
        initCanvas();
      });
  
      const initCanvas = () => {
      if (!canvasRef.value) return;

      canvas.value = new fabric.Canvas('map-edit-canvas', {
        width: window.innerWidth * 0.8,
        height: window.innerHeight * 0.8
      });

      if (mapImage.value) {
        loadMapImage();
      }

      watch(mapImage, (newValue) => {
      if (newValue && canvas.value) {
        loadMapImage();
        }
      });

      // Add title and description
      const title = new fabric.Text(props.title, {
        left: 20,
        top: 20,
        fontSize: 24,
        fontFamily: 'Arial'
      });
      const description = new fabric.Text(props.description, {
        left: 20,
        top: 50,
        fontSize: 16,
        fontFamily: 'Arial'
      });
      canvas.value.add(title, description);
    };

    const loadMapImage = () => {
      fabric.Image.fromURL(mapImage.value, (img) => {
        img.scaleToWidth(canvas.value.width);
        canvas.value.setBackgroundImage(img, canvas.value.renderAll.bind(canvas.value));
      });
    };
  
      function addRectangle() {
        const rect = new fabric.Rect({
          left: 100,
          top: 100,
          fill: 'rgba(255,0,0,0.5)',
          width: 100,
          height: 100
        });
        canvas.value.add(rect);
      }
  
      function addCircle() {
        const circle = new fabric.Circle({
          left: 100,
          top: 100,
          fill: 'rgba(0,255,0,0.5)',
          radius: 50
        });
        canvas.value.add(circle);
      }
  
      function addText() {
        const text = new fabric.IText('Edit me', {
          left: 100,
          top: 100,
          fontFamily: 'Arial'
        });
        canvas.value.add(text);
      }
  
      function deleteSelected() {
        const activeObject = canvas.value.getActiveObject();
        if (activeObject) {
          canvas.value.remove(activeObject);
        }
      }
  
      function saveMap() {
        const dataURL = canvas.value.toDataURL({
          format: 'png',
          quality: 1
        });
        // Here you can implement the logic to save or download the image
        console.log('Map saved:', dataURL);
        emit('save', dataURL);
      }
  
      function closeEditor() {
        emit('close');
      }
  
      return {
        addRectangle,
        addCircle,
        addText,
        deleteSelected,
        saveMap,
        closeEditor,
        mapImage,
        canvasRef
      };
    }
  }
  </script>
  
  <style scoped>
  .map-edit-container {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .map-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 10px;
  }
  
  .map-description {
    font-size: 16px;
    margin-bottom: 20px;
  }
  
  #map-edit-canvas {
    flex-grow: 1;
    border: 1px solid #ccc;
  }
  
  .edit-tools {
    margin-top: 20px;
    display: flex;
    justify-content: space-around;
  }
  
  button {
    padding: 10px 20px;
    background-color: var(--color-primary);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
  }
  
  button:hover {
    background-color: var(--color-primary-dark);
  }
  </style>