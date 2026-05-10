<template>
  <div class="device-history-overview">
    <el-card style="height: calc(100vh - 160px); display: flex; flex-direction: column;">
      <template #header>
        <div class="card-header">
          <span>设备历史状态总览</span>
          <el-button type="primary" size="small" @click="refreshData">刷新数据</el-button>
        </div>
      </template>

      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-icon online">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.online_count }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon fault">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.offline_count }}</div>
            <div class="stat-label">故障设备</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon maintenance">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.maintenance_count }}</div>
            <div class="stat-label">维护中</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon inactive">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.inactive_count }}</div>
            <div class="stat-label">未激活设备</div>
          </div>
        </el-card>
      </div>

      <div class="charts-container">
        <div class="chart-wrapper">
          <div class="chart-title">设备状态分布</div>
          <div ref="statusPieChart" class="chart"></div>
        </div>
        <div class="chart-wrapper">
          <div class="chart-title">在线率趋势（近7天）</div>
          <div ref="trendChart" class="chart"></div>
        </div>
        <div class="chart-wrapper full-width">
          <div class="chart-title">设备资源使用率统计</div>
          <div ref="resourceChart" class="chart"></div>
        </div>
      </div>

      <div class="chart-wrapper full-width">
        <div class="chart-title">各生产线设备状态统计</div>
        <div ref="lineChart" class="chart"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>import { ref, onMounted, onUnmounted, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import { Monitor, DataAnalysis, Warning, User } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import { deviceService } from '../../services/device';
const stats = reactive({
 online_count: 0,
 offline_count: 0,
 inactive_count: 0,
 total_count: 0
});
const statusPieChart = ref(null);
const trendChart = ref(null);
const resourceChart = ref(null);
const lineChart = ref(null);
let pieChartInstance = null;
let trendChartInstance = null;
let resourceChartInstance = null;
let lineChartInstance = null;
const mockTrendData = [
 { date: '12-01', online_rate: 85 },
 { date: '12-02', online_rate: 88 },
 { date: '12-03', online_rate: 82 },
 { date: '12-04', online_rate: 90 },
 { date: '12-05', online_rate: 87 },
 { date: '12-06', online_rate: 92 },
 { date: '12-07', online_rate: 89 }
];
const mockResourceData = [
 { name: 'CPU平均使用率', value: 45 },
 { name: '内存平均使用率', value: 62 },
 { name: '磁盘平均使用率', value: 38 },
 { name: '网络连接率', value: 94 }
];
const mockLineData = [
 { line: 'A生产线', active: 12, fault: 3, maintenance: 1, inactive: 1 },
 { line: 'B生产线', active: 8, fault: 2, maintenance: 0, inactive: 0 },
 { line: 'C生产线', active: 15, fault: 1, maintenance: 2, inactive: 2 },
 { line: 'D生产线', active: 10, fault: 4, maintenance: 1, inactive: 1 }
];
const initCharts = () => {
 if (statusPieChart.value) {
 pieChartInstance = echarts.init(statusPieChart.value);
 pieChartInstance.setOption({
 tooltip: {
 trigger: 'item',
 formatter: '{b}: {c} ({d}%)'
 },
 legend: {
 orient: 'horizontal',
 bottom: 0
 },
 series: [
 {
 name: '设备状态',
 type: 'pie',
 radius: ['40%', '70%'],
 avoidLabelOverlap: false,
 itemStyle: {
 borderRadius: 10,
 borderColor: '#fff',
 borderWidth: 2
 },
 label: {
 show: false,
 position: 'center'
 },
 emphasis: {
 label: {
 show: true,
 fontSize: 18,
 fontWeight: 'bold'
 }
 },
 labelLine: {
 show: false
 },
 data: [
{ value: stats.online_count, name: '运行中', itemStyle: { color: '#67C23A' } },
{ value: stats.offline_count, name: '故障', itemStyle: { color: '#F56C6C' } },
{ value: stats.maintenance_count, name: '维护中', itemStyle: { color: '#E6A23C' } },
{ value: stats.inactive_count, name: '未激活', itemStyle: { color: '#909399' } }
]
 }
 ]
 });
 }
 if (trendChart.value) {
 trendChartInstance = echarts.init(trendChart.value);
 trendChartInstance.setOption({
 tooltip: {
 trigger: 'axis',
 formatter: '{b}<br/>在线率: {c}%'
 },
 grid: {
 left: '3%',
 right: '4%',
 bottom: '3%',
 containLabel: true
 },
 xAxis: {
 type: 'category',
 boundaryGap: false,
 data: mockTrendData.map(item => item.date)
 },
 yAxis: {
 type: 'value',
 min: 0,
 max: 100,
 axisLabel: {
 formatter: '{value}%'
 }
 },
 series: [
 {
 name: '在线率',
 type: 'line',
 smooth: true,
 areaStyle: {
 color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
 { offset: 0, color: 'rgba(103, 194, 58, 0.5)' },
 { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
 ])
 },
 data: mockTrendData.map(item => item.online_rate)
 }
 ]
 });
 }
 if (resourceChart.value) {
 resourceChartInstance = echarts.init(resourceChart.value);
 resourceChartInstance.setOption({
 tooltip: {
 trigger: 'axis',
 axisPointer: {
 type: 'shadow'
 },
 formatter: '{b}: {c}%'
 },
 grid: {
 left: '3%',
 right: '4%',
 bottom: '3%',
 containLabel: true
 },
 xAxis: {
 type: 'category',
 data: mockResourceData.map(item => item.name)
 },
 yAxis: {
 type: 'value',
 min: 0,
 max: 100,
 axisLabel: {
 formatter: '{value}%'
 }
 },
 series: [
 {
 type: 'bar',
 data: mockResourceData.map((item, index) => ({
 value: item.value,
 itemStyle: {
 color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
 { offset: 0, color: ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C'][index] },
 { offset: 1, color: ['#85CE61', '#67B8F7', '#F0C78A', '#F89898'][index] }
 ])
 }
 }))
 }
 ]
 });
 }
 if (lineChart.value) {
 lineChartInstance = echarts.init(lineChart.value);
 lineChartInstance.setOption({
 tooltip: {
 trigger: 'axis',
 axisPointer: {
 type: 'shadow'
 }
 },
 legend: {
 data: ['运行中', '故障', '维护中', '未激活']
 },
 grid: {
 left: '3%',
 right: '4%',
 bottom: '3%',
 containLabel: true
 },
 xAxis: {
 type: 'category',
 data: mockLineData.map(item => item.line)
 },
 yAxis: {
 type: 'value'
 },
 series: [
 {
 name: '运行中',
 type: 'bar',
 stack: 'total',
 label: {
 show: true,
 position: 'inside'
 },
 emphasis: {
 focus: 'series'
 },
 data: mockLineData.map(item => item.active),
 itemStyle: { color: '#67C23A' }
 },
 {
 name: '故障',
 type: 'bar',
 stack: 'total',
 label: {
 show: true,
 position: 'inside'
 },
 emphasis: {
 focus: 'series'
 },
 data: mockLineData.map(item => item.fault),
 itemStyle: { color: '#F56C6C' }
 },
 {
 name: '维护中',
 type: 'bar',
 stack: 'total',
 label: {
 show: true,
 position: 'inside'
 },
 emphasis: {
 focus: 'series'
 },
 data: mockLineData.map(item => item.maintenance),
 itemStyle: { color: '#E6A23C' }
 },
 {
 name: '未激活',
 type: 'bar',
 stack: 'total',
 label: {
 show: true,
 position: 'inside'
 },
 emphasis: {
 focus: 'series'
 },
 data: mockLineData.map(item => item.inactive),
 itemStyle: { color: '#909399' }
 }
 ]
 });
 }
};
const refreshData = async () => {
  try {
    const res = await deviceService.getList();
    const devices = (res.data.devices || []).filter(d => d.status !== 'removed');
    stats.total_count = devices.length;
    stats.online_count = devices.filter(d => d.status === 'active').length;
    stats.offline_count = devices.filter(d => d.status === 'fault').length;
    stats.inactive_count = devices.filter(d => d.status === 'inactive').length;
    stats.maintenance_count = devices.filter(d => d.status === 'maintenance').length;
 if (pieChartInstance) {
 pieChartInstance.setOption({
 series: [
 {
 data: [
{ value: stats.online_count, name: '运行中', itemStyle: { color: '#67C23A' } },
{ value: stats.offline_count, name: '故障', itemStyle: { color: '#F56C6C' } },
{ value: stats.maintenance_count, name: '维护中', itemStyle: { color: '#E6A23C' } },
{ value: stats.inactive_count, name: '未激活', itemStyle: { color: '#909399' } }
]
 }
 ]
 });
 }
 ElMessage.success('数据刷新成功');
 }
 catch (error) {
 console.error('Refresh data failed:', error);
 ElMessage.error('数据刷新失败');
 }
};
const handleResize = () => {
 pieChartInstance?.resize();
 trendChartInstance?.resize();
 resourceChartInstance?.resize();
 lineChartInstance?.resize();
};
onMounted(() => {
 refreshData();
 setTimeout(() => {
 initCharts();
 }, 100);
 window.addEventListener('resize', handleResize);
});
onUnmounted(() => {
 window.removeEventListener('resize', handleResize);
 pieChartInstance?.dispose();
 trendChartInstance?.dispose();
 resourceChartInstance?.dispose();
 lineChartInstance?.dispose();
});
</script>

<style scoped>
.device-history-overview {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
}

:deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex: 1;
  overflow: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
}

.stat-icon.online {
  background: rgba(103, 194, 58, 0.1);
  color: #67C23A;
}

.stat-icon.fault {
  background: rgba(245, 108, 108, 0.1);
  color: #F56C6C;
}

.stat-icon.maintenance {
  background: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
}

.stat-icon.inactive {
  background: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.chart-wrapper {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chart-wrapper.full-width {
  grid-column: span 2;
}

.chart-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
}

.chart {
  height: 250px;
}

.chart-wrapper.full-width .chart {
  height: 300px;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .chart-wrapper.full-width {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
}
</style>
