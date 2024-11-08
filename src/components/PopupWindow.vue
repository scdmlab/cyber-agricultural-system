<template>
  <div class="fixed flex z-[999]" 
       :style="{ 
         left: `${initialX + positionX}px`, 
         top: `${initialY + positionY}px` 
       }">
    <div class="bg-white rounded-lg shadow-xl flex flex-col overflow-auto relative"
         :style="{ 
           width: `${popupWidth}px`,
           height: `${popupHeight}px`
         }">
      <div class="flex-shrink-0 bg-gray-100 p-2 cursor-move w-full flex justify-between items-center"
           @mousedown="startDrag">
        <h2 v-if="title" class="m-0 text-lg leading-none select-none text-gray-800">{{ title }}</h2>
        <button class="bg-transparent border-none text-2xl cursor-pointer text-gray-600 hover:text-gray-800 p-0 m-0 leading-none flex items-center justify-center" 
                @click="close">&times;</button>
      </div>
      <div class="flex-grow overflow-auto p-2.5">
        <slot></slot>
      </div>
      <div class="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize" 
           @mousedown="startResize"></div>
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
      type: Number,
      default: 400
    },
    height: {
      type: Number,
      default: 300
    },
    initialX: {
      type: Number,
      default: 100
    },
    initialY: {
      type: Number,
      default: 100
    }
  },
  emits: ['close'],
  data() {
    return {
      isDragging: false,
      isResizing: false,
      popupWidth: this.width,
      popupHeight: this.height,
      positionX: 0,
      positionY: 0,
      startX: 0,
      startY: 0,
      startWidth: 0,
      startHeight: 0,
    };
  },
  methods: {
    close() {
      this.$emit('close');
    },
    startDrag(event) {
      this.isDragging = true;
      this.startX = event.clientX - this.positionX;
      this.startY = event.clientY - this.positionY;
      document.addEventListener('mousemove', this.drag);
      document.addEventListener('mouseup', this.stopDrag);
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
      document.addEventListener('mousemove', this.resize, { passive: true });
      document.addEventListener('mouseup', this.stopResize, { passive: true });
      event.preventDefault();
    },
    resize(event) {
      if (!this.isResizing) return;
      
      const deltaX = event.clientX - this.startX;
      const deltaY = event.clientY - this.startY;
      
      this.popupWidth = Math.max(200, this.startWidth + deltaX);
      this.popupHeight = Math.max(150, this.startHeight + deltaY);
    },
    stopResize() {
      if (!this.isResizing) return;
      this.isResizing = false;
      document.removeEventListener('mousemove', this.resize);
      document.removeEventListener('mouseup', this.stopResize);
    },
    beforeUnmount() {
      this.stopDrag();
      this.stopResize();
    }
  }
}
</script>

<style scoped>
input[type="number"],
input[type="range"] {
  @apply w-[100px] max-w-full;
}
</style>