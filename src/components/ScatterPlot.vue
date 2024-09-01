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
    datasets: {
      type: Array,
      required: true
    },
    width: {
      type: Number,
      default: null
    },
    height: {
      type: Number,
      default: null
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
          datasets: props.datasets.map((dataset, index) => ({
            label: dataset.countyName,
            data: dataset.data,
            backgroundColor: getColor(index),
          }))
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
                  return `${context.dataset.label} - ${context.parsed.x}: ${context.parsed.y}`;
                }
              }
            }
          },
        }
      })
    }
  
    const getColor = (index) => {
      const colors = ['steelblue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
      return colors[index % colors.length]
    }

      onMounted(() => {
        renderScatterPlot()
      })
  
      watch(() => props.datasets, () => {
      renderScatterPlot()
    }, { deep: true })

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
  width: 100%;
  height: 100%;
}
  </style>