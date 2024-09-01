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
      },
      headers: {
        type: Array,
        required: true
      },
      columnToExclude: {
        type: String,
        default: ''
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
        const columns = this.getFormattedColumns();
        this.table = new Tabulator(this.$refs.tableRef, {
        data: this.data,
        columns: columns,
        layout: 'fitDataTable',
        pagination: true,
        paginationSize: 10,
        paginationSizeSelector: [5, 10, 20, 50],
        movableColumns: true,
        responsiveLayout: 'hide',
        height: '100%',
        rowHeight: 30, // Reduced row height
      });
      },
      getFormattedColumns() {
        return this.headers
          .filter(header => header !== this.columnToExclude)
          .map(header => ({
            title: this.getFriendlyName(header),
            field: header,
            headerFilter: true
          }));
      },
      getFriendlyName(header) {
        // Add your mapping logic here
        const nameMap = {
          'FIPS': 'FIPS',
          "NAME":"County",
          'yield': 'Yield',
          'pred':"Prediction",
          "error":"Error",
          
          "NAMELSAD":"NAMELSAD"
        };
        return nameMap[header] || this.capitalizeWords(header);
      },
      capitalizeWords(str) {
        return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      }
    }
  }
  </script>
  
  <style scoped>
  .data-table-wrapper {
    width: 110%;
    overflow-x: auto;
  }

  /* Custom Tabulator Styles */
.tabulator {
  font-size: 14px; /* Adjust as needed */
}

.tabulator .tabulator-header .tabulator-col {
  background-color: #f0aeae;
  border-right: 1px solid #ddd;
}

.tabulator .tabulator-header .tabulator-col-content {
  padding: 2px;
}

.tabulator .tabulator-header .tabulator-col-title {
  color: rgb(177, 67, 67); /* Make header text black */
  font-weight: bold;
}

.tabulator .tabulator-row .tabulator-cell {
  padding: 6px 8px; /* Reduce cell padding to make columns narrower */
}

/* Adjust column widths */
.tabulator-col {
  min-width: 60px; /* Set a minimum width */
  max-width: 200px; /* Set a maximum width */
}

/* Add horizontal scrolling for the table */
.tabulator .tabulator-tableholder {
  overflow-x: auto;
}
  </style>