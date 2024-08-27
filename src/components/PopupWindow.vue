<template>
  <div class="popup-overlay" @click.self="close">
    <div class="popup-content" 
        :style="{ 
           width: width,
           height: height,
           transform: `translate(${positionX}px, ${positionY}px)`
         }">
      <div class="popup-header"
           @mousedown="startDrag"
           @mousemove="drag"
           @mouseup="stopDrag">
        <h2 v-if="title">{{ title }}</h2>
        <button class="close-button" @click="close">&times;</button>
      </div>
      <div class="popup-body">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PopupWindow',
  props: {
    title: {
      type: String,
      default: ''
    },
    width: {
      type: String,
      default: '400px'
    },
    height: {
      type: String,
      default: '300px'
    }
  },
  emits: ['close'],
  data() {
    return {
      isDragging: false,
      popupWidth: 400,
      popupHeight: 300,
      positionX: 0,
      positionY: 0,
      startX: 0,
      startY: 0,
    };
  },
  methods: {
    close() {
      this.$emit('close')
    }
  },
  methods: {
    close() {
      this.$emit('close');
    },
    startDrag(event) {
      if (event.target.closest('.popup-header')) {
        this.isDragging = true;
        this.startX = event.clientX - this.positionX;
        this.startY = event.clientY - this.positionY;
        document.addEventListener('mousemove', this.drag);
        document.addEventListener('mouseup', this.stopDrag);
      }
    },
    drag(event) {
      if (this.isDragging) {
        this.positionX = event.clientX - this.startX;
        this.positionY = event.clientY - this.startY;
      }
    },
    stopDrag() {
      this.isDragging = false;
      document.removeEventListener('mousemove', this.drag);
      document.removeEventListener('mouseup', this.stopDrag);
    },
    startResize(event) {
      this.isResizing = true;
      this.startX = event.clientX;
      this.startY = event.clientY;
      this.startWidth = this.popupWidth;
      this.startHeight = this.popupHeight;
      document.addEventListener('mousemove', this.resize);
      document.addEventListener('mouseup', this.stopResize);
    },
    stopResize() {
      this.isResizing = false;
      document.removeEventListener('mousemove', this.resize);
      document.removeEventListener('mouseup', this.stopResize);
    },
    resize(event) {
      if (this.isResizing) {
        const newWidth = this.startWidth + (event.clientX - this.startX);
        const newHeight = this.startHeight + (event.clientY - this.startY);
        this.popupWidth = Math.max(200, newWidth); // Minimum width of 200px
        this.popupHeight = Math.max(150, newHeight); // Minimum height of 150px
      }
    }
  }
}
</script>

<style scoped>


.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: var(--z-index-popup, 100);
  pointer-events: none;
}

.popup-content {
  background-color: var(--color-background);
  padding: 0;
  display: flex;
  border-radius: var(--border-radius);
  box-shadow: 1px 4px 4px rgba(21, 11, 11, 0.8);
  /* width: 100%;
  height: 100%; */
  overflow: auto;
  position: relative;
  pointer-events: auto;
  flex-direction: column;
}

.popup-header {
  flex-shrink: 0;
  background-color: var(--color-background-soft);
  padding: 8px 15px; /* Slightly reduced top/bottom padding */
  cursor: move;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.popup-header h2 {
  margin: 0; /* Remove default margins from h2 */
  font-size: 1.2rem; /* Adjust font size as needed */
  line-height: 1;
  user-select: none;
}

.popup-body {
  flex-grow: 1;
  overflow: auto;
  padding: 10px;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text);
  padding: 0;
  margin: 0; /* Remove any margin */
  line-height: 1; /* Align button text with header text */
  display: flex; /* Use flexbox for vertical centering */
  align-items: center;
  justify-content: center;
}

input[type="number"],
input[type="range"] {
  width: 100px;
  max-width: 100%;
}
</style>