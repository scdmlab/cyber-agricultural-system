<template>
  <div class="popup-overlay" @click.self="close">
    <div class="popup-content">
      <button class="close-button" @click="close">&times;</button>
      <h2 v-if="title">{{ title }}</h2>
      <slot></slot>
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
    }
  },
  emits: ['close'],
  methods: {
    close() {
      this.$emit('close')
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
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: var(--z-index-popup,100);
}

.popup-content {
  background-color: var(--color-background);
  padding: 20px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-medium);
  max-width: 90%;
  max-height: 90%;
  overflow-y: auto;
  position: relative;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text);
}
</style>