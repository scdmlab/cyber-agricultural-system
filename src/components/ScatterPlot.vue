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
    name: 'ScatterPlot',
    props: {
    datasets: {
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
      default: 'actual', // 'actual', 'predicted', or 'both'
      validator: value => ['actual', 'predicted', 'both'].includes(value)
    },
    offsetStep: {
      type: Number,
      default: 0.1
    },
    width: {
      type: Number,
      default: null
    },
    height: {
      type: [String, Number],
      default: '400px'
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
        return store.state.currentUnit === 't/ha'
          ? 'Yield (t/ha)'
          : 'Yield (BU/ACRE)'
      })

      const generateTitle = () => {
        const mode = {
          'actual': 'Actual',
          'predicted': 'Predicted',
          'both': 'Predicted vs Actual'
        }[props.displayMode]
        
        return `End of Season ${props.cropType} Yield - ${mode} Values`
      }

      const renderScatterPlot = () => {
        console.log('Rendering scatter plot with data:', props.datasets)
        if (!chartRef.value) return

        // Destroy previous chart if it exists
        if (chart) {
          chart.destroy()
        }

        const ctx = chartRef.value.getContext('2d')
        
        // Determine conversion factor from current unit.
        // (All original data is in bu/acre.)
        const conversionFactor =
          store.state.currentUnit === 't/ha'
            ? (props.cropType === 'Corn' ? 0.06277 : 0.0673)
            : 1

        // Calculate x-offset for each county (dataset)
        const offsetStep = props.offsetStep
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
            y: point.y * conversionFactor // <-- Conversion applied here
          }))

          if (props.displayMode === 'both') {
            return [
              {
                ...baseConfig,
                label: `${dataset.countyName} (Actual)`,
                data: addOffset(dataset.actualData),
                backgroundColor: getColor(index),
                pointStyle: 'circle',
                pointRadius: 4,
              },
              {
                ...baseConfig,
                label: `${dataset.countyName} (Predicted)`,
                data: addOffset(dataset.predictedData),
                backgroundColor: `${getColor(index)}88`,
                borderColor: getColor(index),
                borderWidth: 1,
                pointStyle: 'triangle',
                pointRadius: 4,
                errorBars: dataset.uncertainties,
              }
            ]
          }

          // For prediction only mode
          return [{
            ...baseConfig,
            data: addOffset(dataset.predictedData),
            errorBars: dataset.uncertainties,
            borderColor: getColor(index),
            borderWidth: 1,
            pointStyle: 'triangle',
            pointRadius: 4,
          }]
        })

        chart = new Chart(ctx, {
          type: 'scatter',
          data: {
            datasets: transformedDatasets
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
                type: 'linear',
                position: 'bottom',
                title: {
                  display: true,
                  text: 'Year',
                  padding: { top: 10, bottom: 15 }
                },
                ticks: {
                  stepSize: 1,
                  padding: 8,
                  callback: function(value) {
                    // Round to nearest year instead of floor
                    return Math.round(value)
                  }
                },
                min: 2015,
                max: 2025
              },
              y: {
                title: {
                  display: true,
                  text: yAxisLabel.value,
                  padding: { bottom: 10 }
                },
                ticks: {
                  padding: 8
                },
                suggestedMin: function(context) {
                  const values = context.chart.data.datasets.flatMap(dataset => {
                    const baseValues = dataset.data.map(point => point.y);
                    // Include lower bounds of error bars if they exist
                    if (dataset.errorBars) {
                      const lowerBounds = dataset.data.map((point, i) => 
                        point.y - (point.y * dataset.errorBars[i] / 100)
                      );
                      return [...baseValues, ...lowerBounds];
                    }
                    return baseValues;
                  }).filter(y => y !== null && y !== undefined);
                  return values.length ? Math.min(...values) * 0.95 : 0;
                },
                suggestedMax: function(context) {
                  const values = context.chart.data.datasets.flatMap(dataset => {
                    const baseValues = dataset.data.map(point => point.y);
                    // Include upper bounds of error bars if they exist
                    if (dataset.errorBars) {
                      const upperBounds = dataset.data.map((point, i) => 
                        point.y + (point.y * dataset.errorBars[i] / 100)
                      );
                      return [...baseValues, ...upperBounds];
                    }
                    return baseValues;
                  }).filter(y => y !== null && y !== undefined);
                  return values.length ? Math.max(...values) * 1.05 : 100;
                }
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
                  usePointStyle: true,
                  generateLabels: (chart) => {
                    const datasets = chart.data.datasets;
                    const labels = [];
                    
                    if (props.displayMode === 'both') {
                      for (let i = 0; i < datasets.length; i += 2) {
                        const meta1 = chart.getDatasetMeta(i);
                        const meta2 = chart.getDatasetMeta(i + 1);
                        const isHidden = meta1.hidden || meta2.hidden;
                        const countyName = datasets[i].label.replace(' (Actual)', '');
                        
                        labels.push({
                          text: countyName,
                          fillStyle: isHidden ? '#ddd' : datasets[i].backgroundColor,
                          strokeStyle: datasets[i].borderColor || datasets[i].backgroundColor,
                          lineWidth: 1,
                          hidden: isHidden,
                          index: i,
                          datasetIndex: [i, i + 1],
                          points: [
                            { 
                              pointStyle: 'circle', 
                              fillStyle: isHidden ? '#ddd' : datasets[i].backgroundColor 
                            },
                            { 
                              pointStyle: 'triangle', 
                              fillStyle: isHidden ? '#ddd' : datasets[i + 1].backgroundColor 
                            }
                          ],
                          font: {
                            color: isHidden ? '#999' : '#666'
                          }
                        });
                      }
                    } else {
                      datasets.forEach((dataset, i) => {
                        const meta = chart.getDatasetMeta(i);
                        labels.push({
                          text: dataset.label,
                          fillStyle: meta.hidden ? '#ddd' : dataset.backgroundColor,
                          strokeStyle: dataset.borderColor || dataset.backgroundColor,
                          lineWidth: 1,
                          hidden: meta.hidden,
                          index: i,
                          datasetIndex: i,
                          pointStyle: dataset.pointStyle,
                          font: {
                            color: meta.hidden ? '#999' : '#666'
                          }
                        });
                      });
                    }
                    return labels;
                  },
                  font: {
                    size: 12
                  }
                },
                onClick: (e, legendItem, legend) => {
                  if (Array.isArray(legendItem.datasetIndex)) {
                    legendItem.datasetIndex.forEach(index => {
                      const meta = legend.chart.getDatasetMeta(index);
                      meta.hidden = !meta.hidden;
                    });
                  } else {
                    const meta = legend.chart.getDatasetMeta(legendItem.datasetIndex);
                    meta.hidden = !meta.hidden;
                  }
                  legend.chart.update();
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    // Round to nearest year instead of floor
                    const year = Math.round(context.parsed.x);
                    let label = `${context.dataset.label} - ${year}: ${context.parsed.y.toFixed(1)} ${store.state.currentUnit === 't/ha' ? 't/ha' : 'bu/acre'}`;
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
              },
              markerLegend: {
                display: true,
                position: { x: 10, y: 20 }
              }
            },
          },
          plugins: [
            {
              id: 'errorBars',
              afterDraw: (chart) => {
                const ctx = chart.ctx;
                chart.data.datasets.forEach((dataset, i) => {
                  const meta = chart.getDatasetMeta(i);
                  if (meta.hidden) return; // Skip hidden datasets

                  // Draw error bars
                  if (dataset.errorBars) {
                    meta.data.forEach((element, index) => {
                      const uncertainty = dataset.errorBars[index];
                      if (uncertainty) {
                        const x = element.x;
                        const y = element.y;
                        const uncertaintyValue = (y * uncertainty) / 100;
                        ctx.save();
                        ctx.beginPath();
                        ctx.moveTo(x, y - uncertaintyValue);
                        ctx.lineTo(x, y + uncertaintyValue);
                        ctx.moveTo(x - 3, y - uncertaintyValue);
                        ctx.lineTo(x + 3, y - uncertaintyValue);
                        ctx.moveTo(x - 3, y + uncertaintyValue);
                        ctx.lineTo(x + 3, y + uncertaintyValue);
                        ctx.strokeStyle = dataset.borderColor;
                        ctx.stroke();
                        ctx.restore();
                      }
                    });
                  }

                  // Draw connecting lines between actual and predicted points
                  if (props.displayMode === 'both' && i % 2 === 1) {
                    const predictedMeta = chart.getDatasetMeta(i);
                    const actualMeta = chart.getDatasetMeta(i - 1);
                    
                    // Only draw if both datasets are visible
                    if (actualMeta.hidden || predictedMeta.hidden) return;
                    
                    predictedMeta.data.forEach((predPoint, index) => {
                      const actualPoint = actualMeta.data[index];
                      if (actualPoint && predPoint) {
                        ctx.save();
                        ctx.beginPath();
                        ctx.moveTo(predPoint.x, predPoint.y);
                        ctx.lineTo(actualPoint.x, actualPoint.y);
                        ctx.strokeStyle = dataset.borderColor;
                        ctx.setLineDash([2, 2]);
                        ctx.stroke();
                        ctx.restore();
                      }
                    });
                  }
                });
              }
            },
            {
              id: 'markerLegend',
              beforeDraw: (chart) => {
                const ctx = chart.ctx;
                const { top, left } = chart.chartArea;
                const position = chart.options.plugins.markerLegend.position;
                
                ctx.save();
                
                // Set styles for the legend
                ctx.font = '12px Arial';
                ctx.fillStyle = '#666';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                
                const startY = top + position.y;
                const spacing = 120; // Horizontal spacing between items
                
                // Draw actual yield marker (circle)
                let startX = left + position.x;
                ctx.beginPath();
                ctx.arc(startX, startY, 4, 0, 2 * Math.PI);
                ctx.fillStyle = '#666';
                ctx.fill();
                ctx.fillText('Actual Yield', startX + 10, startY);
                
                // Draw predicted yield marker (triangle)
                startX += spacing;
                ctx.beginPath();
                ctx.moveTo(startX, startY - 4);
                ctx.lineTo(startX - 4, startY + 4);
                ctx.lineTo(startX + 4, startY + 4);
                ctx.closePath();
                ctx.fillStyle = '#666';
                ctx.fill();
                ctx.fillText('Predicted Yield', startX + 10, startY);
                
                // Draw uncertainty bar
                startX += spacing;
                ctx.beginPath();
                ctx.moveTo(startX, startY - 6);
                ctx.lineTo(startX, startY + 6);
                ctx.moveTo(startX - 3, startY - 6);
                ctx.lineTo(startX + 3, startY - 6);
                ctx.moveTo(startX - 3, startY + 6);
                ctx.lineTo(startX + 3, startY + 6);
                ctx.strokeStyle = '#666';
                ctx.stroke();
                ctx.fillText('Prediction Uncertainty', startX + 10, startY);
                
                ctx.restore();
              }
            }
          ]
        })
      }
  
      const getColor = (index) => {
        const colors = ['steelblue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
        return colors[index % colors.length]
      }

      onMounted(() => {
        renderScatterPlot()
      })
  
      watch(
        () => [props.datasets, props.offsetStep],
        () => {
          renderScatterPlot()
        },
        { deep: true }
      )
      watch(() => store.state.currentUnit, () => {
        renderScatterPlot()
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
  /* Remove fixed height */
}
  </style>