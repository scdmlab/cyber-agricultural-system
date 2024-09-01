<template>
    <div class="chart-container">
      <canvas ref="chartRef"></canvas>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, watch, onUnmounted } from 'vue'
  import Chart from 'chart.js/auto'
  
  export default {
    name: 'ScatterPlot',
    props: {
      data: {
        type: Array,
        required: true
      },
      width: {
        type: Number,
        default: 280
      },
      height: {
        type: Number,
        default: 240
      },
      countyName: {
        type: String,
        default: ''
      }
    },
    setup(props) {
      const chartRef = ref(null)
      let chart = null

      const renderScatterPlot = () => {
        if (!chartRef.value) return
  
        // Destroy previous chart if it exists
        if (chart) {
          chart.destroy()
        }
  
        const ctx = chartRef.value.getContext('2d')
        chart = new Chart(ctx, {
          type: 'scatter',
          data: {
            datasets: [{
              label: `${props.countyName}`,
              data: props.data.map(d => ({ x: d.year, y: d.yield })),
              backgroundColor: 'steelblue'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                type: 'linear',
                position: 'bottom',
                title: {
                  display: true,
                  text: 'Year'
                }
              },
              y: {
                title: {
                  display: true,
                  text: 'Yield (BU/ACRE)'
                }
              }
            },
            plugins: {
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.parsed.x}: ${context.parsed.y}`;
                }
              }
            }
          },

          
        }
        })
      }
  
      onMounted(() => {
        renderScatterPlot()
      })
  
      watch(() => props.data, () => {
        renderScatterPlot()
      })
  
      onUnmounted(() => {
        if (chart) {
          chart.destroy()
        }
      })
  
      return { chartRef }
    }
  }
  </script>
  
  <style scoped>
  .chart-container {
    position: relative;
    height: v-bind('height + "px"');
    width: v-bind('width + "px"');
  }
  </style>