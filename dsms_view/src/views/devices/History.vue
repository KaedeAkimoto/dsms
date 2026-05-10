<template>
  <div class="device-history-card-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备历史状态 - 卡片视图</span>
          <div class="header-right">
            <el-button type="primary" size="small" @click="refreshData">刷新数据</el-button>
          </div>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="filterStatus" placeholder="全部状态" clearable class="filter-select">
          <el-option label="全部" value="" />
          <el-option label="运行中" value="active" />
          <el-option label="故障" value="fault" />
          <el-option label="维护中" value="maintenance" />
          <el-option label="未激活" value="inactive" />
          <el-option label="已删除" value="removed" />
        </el-select>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索设备名称或ID"
          class="search-input"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" size="small" @click="handleSearch">搜索</el-button>
        <el-button size="small" @click="handleReset">重置</el-button>
      </div>

      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-label">全部设备</span>
          <span class="stat-value">{{ totalCount }}</span>
        </div>
        <div class="stat-item online">
          <span class="stat-label">运行中</span>
          <span class="stat-value">{{ activeCount }}</span>
        </div>
        <div class="stat-item fault">
          <span class="stat-label">故障</span>
          <span class="stat-value">{{ faultCount }}</span>
        </div>
        <div class="stat-item maintenance">
          <span class="stat-label">维护中</span>
          <span class="stat-value">{{ maintenanceCount }}</span>
        </div>
        <div class="stat-item inactive">
          <span class="stat-label">未激活</span>
          <span class="stat-value">{{ inactiveCount }}</span>
        </div>
        <div class="stat-item removed">
          <span class="stat-label">已删除</span>
          <span class="stat-value">{{ removedCount }}</span>
        </div>
      </div>

      <div class="cards-container">
        <el-card
          v-for="device in filteredDevices"
          :key="device.device_id"
          :class="['device-card', device.status]"
          @click="handleViewDetail(device)"
        >
          <div class="card-header-row">
            <div class="status-dot" :class="device.status"></div>
            <span class="device-name">{{ device.device_name }}</span>
            <el-tag :type="getStatusType(device.status)" size="small">
              {{ getStatusText(device.status) }}
            </el-tag>
          </div>

          <div class="card-info">
            <div class="info-row">
              <span class="info-label">设备ID</span>
              <span class="info-value">{{ device.device_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">设备类型</span>
              <span class="info-value">{{ device.device_type || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">生产线</span>
              <span class="info-value">{{ device.production_line_id || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">IP地址</span>
              <span class="info-value">{{ device.ip_addr || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">创建时间</span>
              <span class="info-value">{{ formatTime(device.created_at) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">最后更新</span>
              <span class="info-value">{{ formatTime(device.updated_at) }}</span>
            </div>
          </div>

          <div class="card-metrics">
            <div class="metric-item">
              <span class="metric-label">CPU</span>
              <span class="metric-value" :class="getMetricClass(device.cpu_usage)">
                {{ device.cpu_usage || '-' }}%
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">内存</span>
              <span class="metric-value" :class="getMetricClass(device.memory_usage)">
                {{ device.memory_usage || '-' }}%
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">磁盘</span>
              <span class="metric-value" :class="getMetricClass(device.disk_usage)">
                {{ device.disk_usage || '-' }}%
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">网络</span>
              <span class="metric-value" :class="device.network_status === 'connected' ? 'success' : 'danger'">
                {{ device.network_status === 'connected' ? '已连接' : (device.network_status || '-') }}
              </span>
            </div>
          </div>

          <div class="card-actions">
            <el-button type="primary" size="small" @click.stop="handleViewHistory(device)">查看历史</el-button>
            <el-button type="warning" size="small" @click.stop="handleEdit(device)">编辑</el-button>
            <el-button type="danger" size="small" @click.stop="handleDelete(device)">删除</el-button>
          </div>
        </el-card>
      </div>

      <div v-if="filteredDevices.length === 0" class="empty-state">
        <el-empty :description="searchKeyword ? '未找到匹配的设备' : '暂无设备数据'" />
      </div>
    </el-card>

    <el-dialog v-model="showDetailDialog" title="设备详情" width="600px">
      <el-descriptions :column="2" border v-if="selectedDevice">
        <el-descriptions-item label="设备ID">{{ selectedDevice.device_id }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">{{ selectedDevice.device_name }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ selectedDevice.device_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="生产线ID">{{ selectedDevice.production_line_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ selectedDevice.ip_addr || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedDevice.status)">{{ getStatusText(selectedDevice.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="CPU使用率">
          <span :class="getMetricClass(selectedDevice.cpu_usage)">{{ selectedDevice.cpu_usage || '-' }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="内存使用率">
          <span :class="getMetricClass(selectedDevice.memory_usage)">{{ selectedDevice.memory_usage || '-' }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="磁盘使用率">
          <span :class="getMetricClass(selectedDevice.disk_usage)">{{ selectedDevice.disk_usage || '-' }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="网络状态">
          <span :class="selectedDevice.network_status === 'connected' ? 'text-success' : 'text-danger'">
            {{ selectedDevice.network_status === 'connected' ? '已连接' : (selectedDevice.network_status || '-') }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(selectedDevice.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="最后更新">{{ formatTime(selectedDevice.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="showHistoryDialog" title="设备历史记录" width="800px">
      <div v-if="historyData.length > 0">
        <el-table :data="historyData" size="small" width="100%" :height="400">
          <el-table-column prop="status" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ip_addr" label="IP地址" min-width="120" />
          <el-table-column prop="cpu_usage" label="CPU使用率" min-width="100">
            <template #default="{ row }">{{ row.cpu_usage ? row.cpu_usage + '%' : '-' }}</template>
          </el-table-column>
          <el-table-column prop="memory_usage" label="内存使用率" min-width="100">
            <template #default="{ row }">{{ row.memory_usage ? row.memory_usage + '%' : '-' }}</template>
          </el-table-column>
          <el-table-column prop="disk_usage" label="磁盘使用率" min-width="100">
            <template #default="{ row }">{{ row.disk_usage ? row.disk_usage + '%' : '-' }}</template>
          </el-table-column>
          <el-table-column prop="network_status" label="网络状态" min-width="100">
            <template #default="{ row }">
              {{ row.network_status === 'connected' ? '已连接' : (row.network_status || '-') }}
            </template>
          </el-table-column>
          <el-table-column prop="timestamp" label="记录时间" min-width="160" />
        </el-table>
      </div>
      <div v-else class="no-history">
        <el-empty description="该设备暂无历史记录" />
      </div>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑设备" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="editForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-input v-model="editForm.device_type" placeholder="请输入设备类型" />
        </el-form-item>
        <el-form-item label="生产线" prop="production_line_id">
          <el-select v-model="editForm.production_line_id" placeholder="请选择生产线" style="width: 100%;">
            <el-option 
              v-for="line in productionLines" 
              :key="line.production_line_id" 
              :label="line.production_line_name + ' (' + line.production_line_id + ')'" 
              :value="line.production_line_id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="IP地址" prop="ip_addr">
          <el-input v-model="editForm.ip_addr" placeholder="请输入IP地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deviceService } from '../../services/device'

const loading = ref(false)
const devices = ref([])
const filterStatus = ref('')
const searchKeyword = ref('')
const showDetailDialog = ref(false)
const showHistoryDialog = ref(false)
const showEditDialog = ref(false)
const selectedDevice = ref(null)
const historyData = ref([])

const editFormRef = ref(null)

// 生产线列表（用于下拉选择）
const productionLines = ref([])

const editForm = reactive({
  device_name: '',
  device_type: '',
  production_line_id: '',
  ip_addr: ''
})

const editRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }]
}

const totalCount = computed(() => devices.value.length)
const activeCount = computed(() => devices.value.filter(d => d.status === 'active').length)
const faultCount = computed(() => devices.value.filter(d => d.status === 'fault').length)
const inactiveCount = computed(() => devices.value.filter(d => d.status === 'inactive').length)
const maintenanceCount = computed(() => devices.value.filter(d => d.status === 'maintenance').length)
const removedCount = computed(() => devices.value.filter(d => d.status === 'removed').length)

const filteredDevices = computed(() => {
  let result = [...devices.value]
  
  if (filterStatus.value) {
    result = result.filter(d => d.status === filterStatus.value)
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(d => 
      d.device_name.toLowerCase().includes(keyword) ||
      d.device_id.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

const getStatusType = (status) => {
  const types = { active: 'success', fault: 'danger', inactive: 'info', maintenance: 'warning', removed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { active: '运行中', fault: '故障', inactive: '未激活', maintenance: '维护中', removed: '已删除' }
  return texts[status] || status
}

const getMetricClass = (value) => {
  if (!value) return ''
  if (value >= 80) return 'danger'
  if (value >= 60) return 'warning'
  return 'success'
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await deviceService.getList({ limit: 1000 })
    devices.value = res.data.devices || []
  } catch (error) {
    console.error('Load devices failed:', error)
    ElMessage.error('加载设备数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadData()
}

const handleSearch = () => {
}

const handleReset = () => {
  filterStatus.value = ''
  searchKeyword.value = ''
}

const handleViewDetail = (device) => {
  selectedDevice.value = device
  showDetailDialog.value = true
}

const handleViewHistory = async (device) => {
  selectedDevice.value = device
  try {
    const res = await deviceService.getHistory(device.device_id, { limit: 50 })
    historyData.value = res.data.history || []
  } catch (error) {
    console.error('Load history failed:', error)
    historyData.value = []
  }
  showHistoryDialog.value = true
}

const handleEdit = (device) => {
  selectedDevice.value = device
  editForm.device_name = device.device_name
  editForm.device_type = device.device_type || ''
  editForm.production_line_id = device.production_line_id || ''
  editForm.ip_addr = device.ip_addr || ''
  showEditDialog.value = true
}

const handleSaveEdit = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    
    await deviceService.update(selectedDevice.value.device_id, {
      device_name: editForm.device_name,
      device_type: editForm.device_type,
      production_line_id: editForm.production_line_id,
      ip_addr: editForm.ip_addr
    })
    
    ElMessage.success('编辑成功')
    showEditDialog.value = false
    loadData()
  } catch (error) {
    console.error('Update device failed:', error)
    ElMessage.error('编辑失败')
  }
}

const handleDelete = async (device) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除设备 ${device.device_name} 吗？`,
      '提示',
      { type: 'warning' }
    )
    
    await deviceService.delete(device.device_id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete device failed:', error)
      ElMessage.error('删除失败')
    }
  }
}

const loadProductionLines = async () => {
  try {
    const res = await deviceService.getProductionLines()
    productionLines.value = res.data.production_lines || []
  } catch (error) {
    console.error('Load production lines failed:', error)
  }
}

loadData()
loadProductionLines()
</script>

<style scoped>
.device-history-card-view {
  padding: 16px;
  height: calc(100vh - 160px);
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

.header-right {
  display: flex;
  gap: 8px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-select {
  width: 140px;
}

.search-input {
  width: 250px;
}

.stats-bar {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.stat-item.online .stat-value { color: #67C23A; }
.stat-item.fault .stat-value { color: #F56C6C; }
.stat-item.maintenance .stat-value { color: #E6A23C; }
.stat-item.inactive .stat-value { color: #909399; }
.stat-item.removed .stat-value { color: #909399; }

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
  flex: 1;
  overflow: auto;
}

.device-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.device-card.active {
  border-left-color: #67C23A;
}

.device-card.fault {
  border-left-color: #F56C6C;
}

.device-card.maintenance {
  border-left-color: #E6A23C;
}

.device-card.inactive {
  border-left-color: #909399;
}

.device-card.removed {
  border-left-color: #909399;
}

.device-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.online { background: #67C23A; }
.status-dot.fault { background: #F56C6C; }
.status-dot.maintenance { background: #E6A23C; }
.status-dot.inactive { background: #909399; }
.status-dot.removed { background: #909399; }

.device-name {
  flex: 1;
  font-weight: bold;
  font-size: 15px;
}

.card-info {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-label {
  color: #909399;
  font-size: 13px;
}

.info-value {
  color: #303133;
  font-size: 13px;
  font-weight: 500;
}

.card-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 12px;
  background: #f9fafc;
  border-radius: 8px;
  margin-bottom: 12px;
}

.metric-item {
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 14px;
  font-weight: bold;
  color: #67C23A;
}

.metric-value.warning { color: #E6A23C; }
.metric-value.danger { color: #F56C6C; }

.card-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-history {
  padding: 40px;
  text-align: center;
}

.text-success { color: #67C23A; }
.text-danger { color: #F56C6C; }
</style>
