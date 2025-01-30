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
    displayMode: {
      type: String,
      default: 'actual', // 'actual', 'predicted', or 'both'
      validator: value => ['actual', 'predicted', 'both'].includes(value)
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
        console.log('Rendering scatter plot with data:', props.datasets)
        if (!chartRef.value) return

        // Destroy previous chart if it exists
        if (chart) {
          chart.destroy()
        }

        const ctx = chartRef.value.getContext('2d')
        
        // Calculate x-offset for each county (dataset)
        const offsetStep = 0.08 // Adjust this value to control spread
        const totalDatasets = props.datasets.length
        const offsetStart = -((totalDatasets - 1) * offsetStep) / 2

        // Transform datasets based on display mode
        const transformedDatasets = props.datasets.flatMap((dataset, index) => {
          const baseConfig = {
            label: dataset.countyName,
            backgroundColor: getColor(index),
          }

          // Calculate x-offset for this dataset
          const xOffset = offsetStart + (index * offsetStep)

          // Add offset to x-values
          const addOffset = (data) => data.map(point => ({
            x: point.x + xOffset,
            y: point.y
          }))

          if (props.displayMode === 'both') {
            return [
              {
                ...baseConfig,
                label: `${dataset.countyName} (Actual)`,
                data: addOffset(dataset.actualData),
                backgroundColor: getColor(index),
              },
              {
                ...baseConfig,
                label: `${dataset.countyName} (Predicted)`,
                data: addOffset(dataset.predictedData),
                backgroundColor: getColor(index),
                errorBars: dataset.uncertainties,
                borderColor: getColor(index),
                borderWidth: 1,
                pointStyle: 'circle',
                pointRadius: 4,
              }
            ]
          }

          return [{
            ...baseConfig,
            data: addOffset(props.displayMode === 'actual' ? dataset.actualData : dataset.predictedData),
            errorBars: props.displayMode === 'predicted' ? dataset.uncertainties : undefined,
          }]
        })

        chart = new Chart(ctx, {
          type: 'scatter',
          data: {
            datasets: transformedDatasets
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
                  text: 'Year',
                  padding: { top: 10 }
                },
                ticks: {
                  stepSize: 1,
                  padding: 8,
                  callback: function(value) {
                    return Math.round(value)
                  }
                },
                min: 2015,
                max: 2025
              },
              y: {
                title: {
                  display: true,
                  text: 'Yield (BU/ACRE)',
                  padding: { bottom: 10 }
                },
                min: 100,
                ticks: {
                  padding: 8
                }
              }
            },
            layout: {
              padding: {
                top: 20,
                right: 20,
                bottom: 20,
                left: 20
              }
            },
            plugins: {
              legend: {
                position: 'top',
                align: 'start',
                labels: {
                  boxWidth: 12,
                  padding: 15,
                  usePointStyle: true
                },
                maxHeight: 80 // Limit legend height
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    let label = `${context.dataset.label} - ${context.parsed.x}: ${context.parsed.y.toFixed(1)} bu/acre`;
                    if (props.displayMode === 'predicted' || 
                       (props.displayMode === 'both' && context.dataset.label.includes('Predicted'))) {
                      const uncertainty = context.dataset.errorBars?.[context.dataIndex];
                      if (uncertainty) {
                        label += ` (±${uncertainty.toFixed(1)}%)`;
                      }
                    }
                    return label;
                  }
                }
              }
            },
          },
          plugins: [{
            id: 'errorBars',
            afterDraw: (chart) => {
              const ctx = chart.ctx;
              chart.data.datasets.forEach((dataset, i) => {
                if (dataset.errorBars) {
                  const meta = chart.getDatasetMeta(i);
                  meta.data.forEach((element, index) => {
                    const uncertainty = dataset.errorBars[index];
                    if (uncertainty) {
                      const x = element.x;
                      const y = element.y;
                      // Convert percentage to actual yield value
                      const uncertaintyValue = (y * uncertainty) / 100;
                      ctx.save();
                      ctx.beginPath();
                      ctx.moveTo(x, y - uncertaintyValue);
                      ctx.lineTo(x, y + uncertaintyValue);
                      ctx.strokeStyle = dataset.borderColor;
                      ctx.stroke();
                      ctx.restore();
                    }
                  });
                }
              });
            }
          }]
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
  padding: 10px;
  /* Ensure proper spacing at bottom */
  margin-bottom: 20px;
}
  </style>