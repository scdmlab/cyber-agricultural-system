<template>
    <div class="data-table-wrapper">
      <div ref="tableRef"></div>
    </div>
  </template>
  
  <script>
  import { TabulatorFull as Tabulator } from 'tabulator-tables';
  import 'tabulator-tables/dist/css/tabulator.min.css';

  
  export default {
    name: 'DataTable',
    props: {
      data: {
        type: Array,
        required: true
      }
    },
    data() {
      return {
        table: null
      }
    },
    mounted() {
      this.initializeTable();
    },
    methods: {
      initializeTable() {
        const columns = [
          { 
            title: 'FIPS',
            field: 'FIPS',
            headerFilter: true,
            width: 100
          },
          {
            title: 'Predicted Yield',
            field: 'pred',
            headerFilter: true,
            formatter: 'number',
            formatterParams: {
              precision: 2
            },
            width: 150
          },
          {
            title: 'Actual Yield',
            field: 'yield',
            headerFilter: true,
            formatter: 'number',
            formatterParams: {
              precision: 2
            },
            width: 150
          },
          {
            title: 'Error',
            field: 'error',
            headerFilter: true,
            formatter: 'number',
            formatterParams: {
              precision: 2
            },
            width: 120
          },
          {
            title: 'Uncertainty',
            field: 'uncertainty',
            headerFilter: true,
            formatter: 'number',
            formatterParams: {
              precision: 2
            },
            width: 120
          }
        ];

        this.table = new Tabulator(this.$refs.tableRef, {
          data: this.data,
          columns: columns,
          layout: 'fitColumns',
          pagination: true,
          paginationSize: 15,
          paginationSizeSelector: [10, 15, 20, 50],
          movableColumns: true,
          responsiveLayout: 'hide',
          height: '400px',
          rowHeight: 30,
          initialSort: [
            { column: 'FIPS', dir: 'asc' }
          ]
        });
      }
    },
    watch: {
      data: {
        handler(newData) {
          if (this.table) {
            this.table.setData(newData);
          }
        },
        deep: true
      }
    }
  }
  </script>
  
  <style scoped>
  .data-table-wrapper {
    width: 100%;
    overflow-x: auto;
    padding: 1rem;
  }

  /* Custom Tabulator Styles */
  :deep(.tabulator) {
    font-size: 14px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }

  :deep(.tabulator .tabulator-header) {
    background-color: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
  }

  :deep(.tabulator .tabulator-header .tabulator-col) {
    background-color: #f8f9fa;
    border-right: 1px solid #dee2e6;
  }

  :deep(.tabulator .tabulator-header .tabulator-col-title) {
    color: #495057;
    font-weight: 600;
  }

  :deep(.tabulator .tabulator-row) {
    border-bottom: 1px solid #dee2e6;
  }

  :deep(.tabulator .tabulator-row.tabulator-row-even) {
    background-color: #f8f9fa;
  }

  :deep(.tabulator .tabulator-row.tabulator-row-odd) {
    background-color: #ffffff;
  }

  :deep(.tabulator .tabulator-footer) {
    background-color: #f8f9fa;
    border-top: 2px solid #dee2e6;
  }
  </style>