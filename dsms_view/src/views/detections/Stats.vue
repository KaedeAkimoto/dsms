<template>
  <div class="stats-container">
    <el-card>
      <template #header>
        <span>检测统计</span>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="searchForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="searchForm.end_time"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-icon total">
            <el-icon><component :is="IconStats" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_count || 0 }}</div>
            <div class="stat-label">检测总数</div>
          </div>
        </el-card>

        <el-card class="stat-card">
          <div class="stat-icon pass">
            <el-icon><component :is="IconCheck" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.pass_count || 0 }}</div>
            <div class="stat-label">通过数</div>
          </div>
        </el-card>

        <el-card class="stat-card">
          <div class="stat-icon fail">
            <el-icon><component :is="IconClose" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.fail_count || 0 }}</div>
            <div class="stat-label">失败数</div>
          </div>
        </el-card>

        <el-card class="stat-card">
          <div class="stat-icon rate">
            <el-icon><component :is="IconTrendingUp" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ passRate }}%</div>
            <div class="stat-label">通过率</div>
          </div>
        </el-card>
      </div>

      <div class="charts-wrapper">
        <el-card class="chart-card">
          <template #header>
            <span>缺陷类型分布</span>
          </template>
          <div ref="defectTypeChart" class="chart"></div>
        </el-card>
      </div>

      <el-card>
        <template #header>
          <span>检测趋势</span>
        </template>
        <div ref="trendChart" class="chart-large"></div>
      </el-card>

      <el-card>
        <template #header>
          <span>缺陷类型趋势</span>
        </template>
        <div ref="defectTrendChart" class="chart-large"></div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis as IconStats, Check as IconCheck, Close as IconClose, TrendCharts as IconTrendingUp } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { detectionService } from '../../services/detection'

const formatDate = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const end = new Date()
const start = new Date()
start.setDate(start.getDate() - 7)

const searchForm = reactive({
  start_time: formatDate(start),
  end_time: formatDate(end)
})

const stats = reactive({
  total_count: 0,
  pass_count: 0,
  fail_count: 0
})

const defectTypeChart = ref(null)
const trendChart = ref(null)
const defectTrendChart = ref(null)

let defectTypeChartInstance = null
let trendChartInstance = null
let defectTrendChartInstance = null

const passRate = computed(() => {
  if (stats.total_count === 0) return '0.00'
  return ((stats.pass_count / stats.total_count) * 100).toFixed(2)
})

const loadStats = async () => {
  try {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 7)
    
    const params = { 
      group_by: 'day',
      start_time: searchForm.start_time || start.toISOString().slice(0, 10),
      end_time: searchForm.end_time || end.toISOString().slice(0, 10)
    }

    const res = await detectionService.getTrend(params)
    console.log('检测趋势接口返回:', JSON.stringify(res, null, 2))
    
    if (res.data && Array.isArray(res.data)) {
      stats.total_count = res.data.reduce((sum, item) => sum + (item.detect_sum || 0), 0)
      stats.pass_count = res.data.reduce((sum, item) => sum + (item.pass_sum || 0), 0)
      stats.fail_count = stats.total_count - stats.pass_count
    }
  } catch (error) {
    console.error('Load stats failed:', error)
    ElMessage.error('加载统计数据失败')
  }
}

const loadDefectTypeChart = async () => {
  try {
    const params = {}
    if (searchForm.start_time) params.start_time = searchForm.start_time
    if (searchForm.end_time) params.end_time = searchForm.end_time

    const res = await detectionService.getDefectStats(params)
    console.log('缺陷类型图表接口返回类型:', typeof res.data, Array.isArray(res.data))
    
    let data = []
    if (Array.isArray(res.data)) {
      // 接口直接返回缺陷类型统计数组
      data = res.data
    } else if (res.data.data && Array.isArray(res.data.data)) {
      // 返回的是对象，data字段是缺陷类型统计数组
      data = res.data.data
    } else {
      data = res.data.by_type || []
    }

    if (defectTypeChartInstance) {
      defectTypeChartInstance.dispose()
    }

    defectTypeChartInstance = echarts.init(defectTypeChart.value)
    defectTypeChartInstance.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `<div style="padding: 8px;">
            <div style="font-weight: 600; color: ${params.color}; margin-bottom: 4px;">${params.name}</div>
            <div style="color: #666;">数量: <strong>${params.value}</strong></div>
            <div style="color: #666;">占比: <strong>${params.percent}%</strong></div>
          </div>`
        },
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e0e0e0',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#333',
          fontSize: 13
        },
        extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px;'
      },
      legend: {
        orient: 'vertical',
        right: '3%',
        top: 'center',
        itemWidth: 14,
        itemHeight: 14,
        itemGap: 14,
        textStyle: {
          fontSize: 13,
          color: '#555',
          fontWeight: 500
        },
        selectedMode: true
      },
      series: [
        {
          name: '缺陷类型',
          type: 'pie',
          radius: ['35%', '70%'],
          center: ['38%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 3,
            shadowBlur: 4,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.08)'
          },
          label: {
            show: true,
            position: 'outside',
            fontSize: 12,
            fontWeight: 500,
            color: '#555',
            formatter: '{b}: {c}'
          },
          emphasis: {
            scale: true,
            scaleSize: 8,
            label: {
              show: true,
              fontSize: 14,
              fontWeight: '600',
              formatter: '{b}\n{c} ({d}%)',
              color: '#333'
            },
            itemStyle: {
              shadowBlur: 15,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.25)'
            }
          },
          labelLine: {
            show: true,
            length: 15,
            length2: 10,
            smooth: true,
            lineStyle: {
              color: '#ccc'
            }
          },
          animationType: 'scale',
          animationEasing: 'elasticOut',
          animationDelay: (idx) => idx * 100,
          data: data.map((item, index) => ({
            value: item.count,
            name: item.defect_type_name || `类型${index + 1}`,
            itemStyle: {
              color: [
                '#5B8FF9', '#5AD8A6', '#F6BD16', '#E86452', 
                '#6DC8EC', '#9270CA', '#FF9F7F', '#96D3FF',
                '#FFC53D', '#6E7074'
              ][index % 10]
            }
          }))
        }
      ]
    })
  } catch (error) {
    console.error('Load defect type chart failed:', error)
  }
}

const loadTrendChart = async () => {
  try {
    const params = { group_by: 'day' }
    
    if (searchForm.start_time && searchForm.end_time) {
      params.start_time = searchForm.start_time
      params.end_time = searchForm.end_time
    } else {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 7)
      params.start_time = start.toISOString().slice(0, 10)
      params.end_time = end.toISOString().slice(0, 10)
    }

    const res = await detectionService.getTrend(params)
    console.log('趋势接口返回:', res.data)
    const data = Array.isArray(res.data) ? res.data : (res.data.trend || [])

    if (trendChartInstance) {
      trendChartInstance.dispose()
    }

    trendChartInstance = echarts.init(trendChart.value)
    trendChartInstance.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e0e0e0',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#333',
          fontSize: 13
        },
        extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px;',
        axisPointer: {
          type: 'cross',
          lineStyle: {
            color: '#ccc',
            width: 1,
            type: 'dashed'
          },
          label: {
            backgroundColor: '#555',
            color: '#fff',
            fontSize: 12,
            padding: [4, 8]
          }
        },
        formatter: (params) => {
          let result = `<div style="font-weight: 600; margin-bottom: 8px; color: #333;">${params[0].axisValue}</div>`
          params.forEach(item => {
            const color = item.color
            result += `<div style="display: flex; align-items: center; margin-bottom: 4px;">
              <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${color}; margin-right: 8px;"></span>
              <span style="flex: 1; color: #666;">${item.seriesName}</span>
              <span style="font-weight: 600; color: ${color}; margin-left: 12px;">${item.value}</span>
            </div>`
          })
          return result
        }
      },
      legend: {
        data: ['检测数', '通过数', '缺陷数'],
        top: '5%',
        left: 'center',
        itemWidth: 16,
        itemHeight: 10,
        itemGap: 24,
        textStyle: {
          fontSize: 13,
          color: '#555',
          fontWeight: 500
        },
        selectedMode: true
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '8%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.map((item) => item.date),
        axisLine: {
          lineStyle: {
            color: '#e0e0e0'
          }
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12,
          rotate: 0
        }
      },
      yAxis: {
        type: 'value',
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          name: '检测数',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#5B8FF9'
          },
          itemStyle: {
            color: '#5B8FF9',
            borderWidth: 2,
            borderColor: '#fff'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(91, 143, 249, 0.3)' },
                { offset: 1, color: 'rgba(91, 143, 249, 0.05)' }
              ]
            }
          },
          emphasis: {
            scale: true,
            scaleSize: 6,
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(91, 143, 249, 0.5)'
            }
          },
          data: data.map((item) => item.detect_sum || item.total_count || 0)
        },
        {
          name: '通过数',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#5AD8A6'
          },
          itemStyle: {
            color: '#5AD8A6',
            borderWidth: 2,
            borderColor: '#fff'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(90, 216, 166, 0.3)' },
                { offset: 1, color: 'rgba(90, 216, 166, 0.05)' }
              ]
            }
          },
          emphasis: {
            scale: true,
            scaleSize: 6,
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(90, 216, 166, 0.5)'
            }
          },
          data: data.map((item) => item.pass_sum || 0)
        },
        {
          name: '缺陷数',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#E86452'
          },
          itemStyle: {
            color: '#E86452',
            borderWidth: 2,
            borderColor: '#fff'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(232, 100, 82, 0.3)' },
                { offset: 1, color: 'rgba(232, 100, 82, 0.05)' }
              ]
            }
          },
          emphasis: {
            scale: true,
            scaleSize: 6,
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(232, 100, 82, 0.5)'
            }
          },
          data: data.map((item) => (item.detect_sum || 0) - (item.pass_sum || 0))
        }
      ],
      animationType: 'scale',
      animationEasing: 'elasticOut',
      animationDelay: (idx) => idx * 100
    })
  } catch (error) {
    console.error('Load trend chart failed:', error)
  }
}

const loadDefectTrendChart = async () => {
  try {
    const params = { group_by: 'day' }
    
    if (searchForm.start_time && searchForm.end_time) {
      params.start_time = searchForm.start_time
      params.end_time = searchForm.end_time
    } else {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 7)
      params.start_time = start.toISOString().slice(0, 10)
      params.end_time = end.toISOString().slice(0, 10)
    }

    const res = await detectionService.getDefectTrend(params)
    const data = Array.isArray(res.data) ? res.data : []

    if (defectTrendChartInstance) {
      defectTrendChartInstance.dispose()
    }

    if (data.length === 0 || !data[0].defects) {
      defectTrendChartInstance = echarts.init(defectTrendChart.value)
      defectTrendChartInstance.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#999', fontSize: 14 }
        }
      })
      return
    }

    const colors = ['#5B8FF9', '#5AD8A6', '#F6BD16', '#E86452', '#6DC8EC', '#9270CA', '#FF9F7F', '#96D3FF']
    
    const defectTypeMap = {}
    data.forEach(dayData => {
      if (dayData.defects) {
        dayData.defects.forEach(defect => {
          if (!defectTypeMap[defect.defect_type_id]) {
            defectTypeMap[defect.defect_type_id] = {
              name: defect.defect_type_name,
              color: colors[Object.keys(defectTypeMap).length % colors.length]
            }
          }
        })
      }
    })

    const series = Object.keys(defectTypeMap).map(typeId => {
      const defectType = defectTypeMap[typeId]
      return {
        name: defectType.name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 2,
          color: defectType.color
        },
        itemStyle: {
          color: defectType.color,
          borderWidth: 2,
          borderColor: '#fff'
        },
        emphasis: {
          scale: true,
          scaleSize: 4,
          itemStyle: {
            shadowBlur: 8,
            shadowColor: defectType.color
          }
        },
        data: data.map(dayData => {
          const defect = dayData.defects?.find(d => d.defect_type_id === parseInt(typeId))
          return defect ? defect.count : 0
        })
      }
    })

    const dates = data.map(item => item.date)

    defectTrendChartInstance = echarts.init(defectTrendChart.value)
    defectTrendChartInstance.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e0e0e0',
        borderWidth: 1,
        padding: [12, 16],
        textStyle: {
          color: '#333',
          fontSize: 13
        },
        extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px;'
      },
      legend: {
        data: Object.values(defectTypeMap).map(d => d.name),
        top: '5%',
        left: 'center',
        itemWidth: 14,
        itemHeight: 10,
        itemGap: 16,
        textStyle: {
          fontSize: 12,
          color: '#555'
        },
        selectedMode: true
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '8%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLine: {
          lineStyle: {
            color: '#e0e0e0'
          }
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12
        }
      },
      yAxis: {
        type: 'value',
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        }
      },
      series
    })
  } catch (error) {
    console.error('Load defect trend chart failed:', error)
  }
}

const handleSearch = () => {
  loadStats()
  loadDefectTypeChart()
  loadTrendChart()
  loadDefectTrendChart()
}

const handleReset = () => {
  searchForm.start_time = ''
  searchForm.end_time = ''
  handleSearch()
}

const handleResize = () => {
  defectTypeChartInstance?.resize()
  trendChartInstance?.resize()
  defectTrendChartInstance?.resize()
}

onMounted(() => {
  loadStats()
  loadDefectTypeChart()
  loadTrendChart()
  loadDefectTrendChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  defectTypeChartInstance?.dispose()
  trendChartInstance?.dispose()
  defectTrendChartInstance?.dispose()
})
</script>

<style scoped>
.stats-container {
  padding: 20px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.stats-container::-webkit-scrollbar {
  width: 6px;
}

.stats-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.stats-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.stats-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.search-form {
  margin-bottom: 20px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.pass {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.stat-icon.fail {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-icon.rate {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 26px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
}

.charts-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.chart-card {
  width: 100%;
  height: 400px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.chart {
  height: calc(100% - 50px);
}

.chart-large {
  height: 380px;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
