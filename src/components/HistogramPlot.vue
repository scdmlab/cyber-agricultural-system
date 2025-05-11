<template>
  <div class="chart-container" :style="{ height: computedHeight }">
    <canvas ref="chartRef"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, watch, onUnmounted, computed } from 'vue'
import { useStore } from 'vuex'
import Chart from 'chart.js/auto'

export default {
  name: 'HistogramPlot',
  props: {
    allCountiesData: {
      type: Array,
      required: true
    },
    cropType: {
      type: String,
      required: true,
      validator: value => ['Corn', 'Soybean'].includes(value)
    },
    displayMode: {
      type: String,
      default: 'predicted', // 'actual', 'predicted', or 'both'
      validator: value => ['actual', 'predicted', 'both'].includes(value)
    },
    width: {
      type: Number,
      default: null
    },
    height: {
      type: [String, Number],
      default: '400px'
    },
    binCount: {
      type: Number,
      default: 10
    },
    year: {
      type: Number,
      default: 2024
    }
  },
  setup(props) {
    const store = useStore()
    const chartRef = ref(null)
    let chart = null

    const computedHeight = computed(() => {
      return typeof props.height === 'number' ? `${props.height}px` : props.height
    })

    const yAxisLabel = computed(() => {
      return 'Frequency'
    })

    const xAxisLabel = computed(() => {
      return store.state.currentUnit === 't/ha'
        ? 'Yield (t/ha)'
        : 'Yield (BU/ACRE)'
    })

    const conversionFactor =
      store.state.currentUnit === 't/ha'
        ? (props.cropType === 'Corn' ? 0.06277 : 0.0673)
        : 1

    const generateTitle = () => {
      const mode = {
        'actual': 'Actual',
        'predicted': 'Predicted',
        'both': 'Predicted vs Actual'
      }[props.displayMode]
      
      return `${props.cropType} Yield Distribution (${props.year}) - ${mode} Values`
    }

    // Function to create histogram data from raw values
    const createHistogramData = (values, binCount) => {
      if (!values || values.length === 0) return { labels: [], data: [] }
      
      // Find min and max values
      const min = Math.min(...values)
      const max = Math.max(...values)
      
      // Calculate bin width
      const binWidth = (max - min) / binCount
      
      // Initialize bins
      const bins = Array(binCount).fill(0)
      const binLabels = []
      
      // Create bin labels
      for (let i = 0; i < binCount; i++) {
        const lowerBound = min + (i * binWidth)
        const upperBound = min + ((i + 1) * binWidth)
        binLabels.push(`${lowerBound.toFixed(1)}-${upperBound.toFixed(1)}`)
      }
      
      // Count values in each bin
      values.forEach(value => {
        // Handle edge case for max value
        if (value === max) {
          bins[binCount - 1]++
        } else {
          const binIndex = Math.floor((value - min) / binWidth)
          if (binIndex >= 0 && binIndex < binCount) {
            bins[binIndex]++
          }
        }
      })
      
      return {
        labels: binLabels,
        data: bins
      }
    }

    const renderHistogramPlot = () => {
      console.log('Rendering histogram plot with data:', props.allCountiesData, 'for year:', props.year)
      if (!chartRef.value) return
      if (!props.allCountiesData || props.allCountiesData.length === 0) {
        console.warn('No data available for histogram')
        return
      }

      if (chart) {
        chart.destroy()
      }

      const ctx = chartRef.value.getContext('2d')
      
      // Extract actual and predicted values from all counties data
      const actualValues = []
      const predictedValues = []
      
      props.allCountiesData.forEach(dataPoint => {
        if (dataPoint.actual !== undefined && dataPoint.actual !== null) {
          actualValues.push(dataPoint.actual * conversionFactor)
        }
        
        if (dataPoint.predicted !== undefined && dataPoint.predicted !== null) {
          predictedValues.push(dataPoint.predicted * conversionFactor)
        }
      })
      
      // Create histogram data
      const actualHistogram = createHistogramData(actualValues, props.binCount)
      const predictedHistogram = createHistogramData(predictedValues, props.binCount)
      
      // Prepare datasets based on display mode
      const chartDatasets = []
      
      if (props.displayMode === 'actual' || props.displayMode === 'both') {
        chartDatasets.push({
          label: 'Actual Yields',
          data: actualHistogram.data,
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        })
      }
      
      if (props.displayMode === 'predicted' || props.displayMode === 'both') {
        chartDatasets.push({
          label: 'Predicted Yields',
          data: predictedHistogram.data,
          backgroundColor: 'rgba(255, 159, 64, 0.5)',
          borderColor: 'rgba(255, 159, 64, 1)',
          borderWidth: 1
        })
      }
      
      // Use labels from whichever histogram has data
      const labels = (actualHistogram.labels.length > 0) 
        ? actualHistogram.labels 
        : predictedHistogram.labels

      chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: chartDatasets
        },
        options: {
          animation: {
            duration: 0 // Disable animation
          },
          responsive: true,
          maintainAspectRatio: false,
          layout: {
            padding: {
              top: 20,
              right: 20,
              bottom: 40,
              left: 20
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: xAxisLabel.value,
                padding: { top: 10, bottom: 15 }
              },
              ticks: {
                maxRotation: 45,
                minRotation: 45
              }
            },
            y: {
              title: {
                display: true,
                text: yAxisLabel.value,
                padding: { bottom: 10 }
              },
              beginAtZero: true
            }
          },
          plugins: {
            title: {
              display: true,
              text: generateTitle(),
              font: {
                size: 16,
                weight: 'bold'
              },
              padding: {
                top: 10,
                bottom: 30
              }
            },
            legend: {
              position: 'top',
              align: 'start',
              labels: {
                boxWidth: 12,
                padding: 15,
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.dataset.label}: ${context.parsed.y} counties`
                }
              }
            }
          }
        }
      })
    }

    onMounted(() => {
      renderHistogramPlot()
    })

    watch(
      () => [props.datasets, props.binCount, props.displayMode, props.year, props.allCountiesData],
      () => {
        renderHistogramPlot()
      },
      { deep: true }
    )

    watch(() => store.state.currentUnit, () => {
      renderHistogramPlot()
    })

    onUnmounted(() => {
      if (chart) {
        chart.destroy()
      }
    })

    return { chartRef, computedHeight }
  }
}
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  min-height: 500px;
  padding: 10px;
}
</style>
