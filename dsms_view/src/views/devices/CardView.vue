<template>
  <div class="devices-card-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备总览</span>
          <div class="header-right">
            <el-button type="primary" size="small" @click="showCreateDialog = true">创建设备</el-button>
            <el-button type="primary" size="small" @click="refreshData">刷新数据</el-button>
          </div>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="filterStatus" placeholder="全部状态" clearable class="filter-select">
          <el-option label="全部" value="" />
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
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
          <span class="stat-label">在线</span>
          <span class="stat-value">{{ onlineCount }}</span>
        </div>
        <div class="stat-item offline">
          <span class="stat-label">离线</span>
          <span class="stat-value">{{ offlineCount }}</span>
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
          </div>
          <div v-if="device.status !== 'removed'" class="card-actions">
            <el-button type="primary" size="small" @click.stop="handleEdit(device)">编辑</el-button>
            <el-button type="warning" size="small" @click.stop="handleGenerateToken(device)">生成Token</el-button>
            <el-button type="danger" size="small" @click.stop="handleDelete(device)">删除</el-button>
          </div>
        </el-card>
      </div>

      <div v-if="filteredDevices.length === 0" class="empty-state">
        <el-empty :description="searchKeyword ? '未找到匹配的设备' : '暂无设备数据'" />
      </div>
    </el-card>

    <el-dialog v-model="showDetailDialog" title="设备详情" width="700px">
      <el-descriptions :column="2" border v-if="selectedDevice">
        <el-descriptions-item label="设备ID">{{ selectedDevice.device_id }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">{{ selectedDevice.device_name }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ selectedDevice.device_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="生产线ID">{{ selectedDevice.production_line_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ selectedDevice.ip_addr || '-' }}</el-descriptions-item>
        <el-descriptions-item label="MAC地址">{{ selectedDevice.mac_addr || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备管理员">{{ selectedDevice.device_manager || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedDevice.status)">{{ getStatusText(selectedDevice.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Token" :span="2">
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <span style="word-break: break-all;">{{ selectedDevice.token || '-' }}</span>
            <el-button 
              v-if="selectedDevice.token" 
              type="link" 
              size="small" 
              style="align-self: flex-start;"
              @click="copyToken(selectedDevice.token)"
            >
              复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(selectedDevice.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(selectedDevice.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑设备" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="editForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-input v-model="editForm.device_type" placeholder="请输入设备类型" />
        </el-form-item>
        <el-form-item label="生产线ID" prop="production_line_id">
          <el-input v-model="editForm.production_line_id" placeholder="请输入生产线ID" />
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

    <el-dialog v-model="showCreateDialog" title="创建设备" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="createForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-input v-model="createForm.device_type" placeholder="请输入设备类型" />
        </el-form-item>
        <el-form-item label="生产线ID" prop="production_line_id">
          <el-select
            v-model="createForm.production_line_id"
            filterable
            remote
            reserve-keyword
            placeholder="请选择生产线"
            :remote-method="loadProductionLines"
            :loading="plLoading"
            clearable
          >
            <el-option
              v-for="pl in productionLineOptions"
              :key="pl.production_line_id"
              :label="`${pl.production_line_id} - ${pl.production_line_name}`"
              :value="pl.production_line_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备管理员" prop="device_manager">
          <el-select
            v-model="createForm.device_manager"
            filterable
            remote
            reserve-keyword
            placeholder="请选择管理员"
            :remote-method="loadUsers"
            :loading="userLoading"
            clearable
          >
            <el-option
              v-for="user in userOptions"
              :key="user.user_id"
              :label="`${user.user_id} - ${user.real_name} (${user.user_name})`"
              :value="user.user_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="IP地址">
          <el-input v-model="createForm.ip_addr" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="MAC地址">
          <el-input v-model="createForm.mac_addr" placeholder="请输入MAC地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deviceService } from '../../services/device'
import { productionLineService } from '../../services/productionLine'
import { userService } from '../../services/user'

const loading = ref(false)
const devices = ref([])
const removedDevices = ref([])
const productionLineOptions = ref([])
const userOptions = ref([])
const plLoading = ref(false)
const userLoading = ref(false)
const filterStatus = ref('')
const searchKeyword = ref('')
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const showCreateDialog = ref(false)
const selectedDevice = ref(null)
const createLoading = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const editForm = reactive({
  device_name: '',
  device_type: '',
  production_line_id: '',
  ip_addr: ''
})

const editRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }]
}

const createForm = reactive({
  device_name: '',
  device_type: '',
  production_line_id: '',
  device_manager: '',
  ip_addr: '',
  mac_addr: ''
})

const createRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  device_type: [{ required: true, message: '请输入设备类型', trigger: 'blur' }],
  production_line_id: [{ required: true, message: '请输入生产线ID', trigger: 'blur' }],
  device_manager: [{ required: true, message: '请输入设备管理员', trigger: 'blur' }]
}

const totalCount = computed(() => devices.value.length)
const onlineCount = computed(() => devices.value.filter(d => d.status === 'online').length)
const offlineCount = computed(() => devices.value.filter(d => d.status === 'offline').length)
const inactiveCount = computed(() => devices.value.filter(d => d.status === 'inactive').length)
const removedCount = computed(() => removedDevices.value.length)

const filteredDevices = computed(() => {
  let result = []

  if (filterStatus.value === 'removed') {
    result = [...removedDevices.value]
  } else {
    result = [...devices.value]
  }

  if (filterStatus.value && filterStatus.value !== 'removed') {
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
  const types = { online: 'success', offline: 'warning', inactive: 'info', removed: 'danger' }
  return types[status] || ''
}

const getStatusText = (status) => {
  const texts = { online: '在线', offline: '离线', inactive: '未激活', removed: '已删除' }
  return texts[status] || status
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const [normalRes, removedRes] = await Promise.all([
      deviceService.getList({ limit: 1000 }),
      deviceService.getList({ limit: 1000, status: 'removed' })
    ])
    devices.value = normalRes.data.devices || []
    removedDevices.value = removedRes.data.devices || []
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

const loadProductionLines = async (keyword = '') => {
  plLoading.value = true
  try {
    const res = await productionLineService.getList({ limit: 100 })
    let lines = res.data.production_lines || []
    if (keyword) {
      lines = lines.filter(pl => 
        pl.production_line_id.toString().includes(keyword) ||
        pl.production_line_name.toLowerCase().includes(keyword.toLowerCase())
      )
    }
    productionLineOptions.value = lines
  } catch (error) {
    console.error('Load production lines failed:', error)
  } finally {
    plLoading.value = false
  }
}

const loadUsers = async (keyword = '') => {
  userLoading.value = true
  try {
    const res = await userService.getList({ limit: 100 })
    let users = res.data.users || []
    if (keyword) {
      users = users.filter(user => 
        user.user_id.toString().includes(keyword) ||
        user.user_name.toLowerCase().includes(keyword.toLowerCase()) ||
        user.real_name.toLowerCase().includes(keyword.toLowerCase())
      )
    }
    userOptions.value = users
  } catch (error) {
    console.error('Load users failed:', error)
  } finally {
    userLoading.value = false
  }
}

const handleViewDetail = async (device) => {
  selectedDevice.value = device
  showDetailDialog.value = true
  try {
    const res = await deviceService.getToken(device.device_id)
    if (res.data && res.data.device_upload_token) {
      selectedDevice.value = {
        ...selectedDevice.value,
        token: res.data.device_upload_token
      }
    }
  } catch (error) {
    console.error('Get token failed:', error)
  }
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

const handleGenerateToken = async (device) => {
  try {
    await deviceService.generateToken(device.device_id)
    ElMessage.success('Token生成成功')
  } catch (error) {
    console.error('Generate token failed:', error)
    ElMessage.error('Token生成失败')
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

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await deviceService.create(createForm)
        ElMessage.success('设备创建成功')
        showCreateDialog.value = false
        Object.keys(createForm).forEach(key => createForm[key] = '')
        loadData()
      } catch (error) {
        console.error('Create device failed:', error)
      } finally {
        createLoading.value = false
      }
    }
  })
}

const copyToken = async (token) => {
  try {
    await navigator.clipboard.writeText(token)
    ElMessage.success('Token已复制到剪贴板')
  } catch (error) {
    console.error('Copy token failed:', error)
    ElMessage.error('复制失败')
  }
}

loadData()
</script>

<style scoped>
.devices-card-view {
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
.stat-item.offline .stat-value { color: #E6A23C; }
.stat-item.inactive .stat-value { color: #909399; }
.stat-item.removed .stat-value { color: #F56C6C; }

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  flex: 1;
  overflow: auto;
}

.device-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.device-card.online {
  border-left-color: #67C23A;
}

.device-card.offline {
  border-left-color: #E6A23C;
}

.device-card.inactive {
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
.status-dot.offline { background: #E6A23C; }
.status-dot.inactive { background: #909399; }

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
</style>
