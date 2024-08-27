<template>
  <PopupWindow :title="title" @close="$emit('close')">
    <DataTable :data="data" :headers="headers" columnToExclude="NAMELSA"/>
  </PopupWindow>
</template>

<script>
import PopupWindow from './PopupWindow.vue'
import DataTable from './DataTable.vue'

export default {
  name: 'DataPopup',
  components: {
    PopupWindow,
    DataTable
  },
  props: {
    title: {
      type: String,
      default: 'Data Table'
    },
    data: {
      type: Array,
      required: true
    },
    headers: {
      type: Array,
      required: true
    }
  },
  emits: ['close']
}
</script>

<style scoped>
.data-table-popup :deep(.popup-content) {
  max-width: 1200px;
  max-height: 80vh;
}

.data-table-popup :deep(.popup-body) {
  height: calc(100% - 40px); /* Adjust based on your PopupWindow header height */
  overflow: hidden;
  width: 200px;
}

.data-table-popup :deep(.data-table) {
  height: 100%;
  width: 100%;
  overflow: auto;
}
</style>