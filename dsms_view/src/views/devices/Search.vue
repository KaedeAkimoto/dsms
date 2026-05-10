<template>
  <div class="devices-search-container">
    <el-card style="display: flex; flex-direction: column; height: calc(100vh - 160px);">
      <template #header>
        <div class="card-header">
          <span>设备查找</span>
        </div>
      </template>

      <div class="search-form">
        <el-input
          v-model="searchQuery"
          placeholder="输入设备ID、设备名称或生产线ID进行查找"
          style="width: 400px; margin-right: 16px;"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">查找</el-button>
        <el-button @click="handleClear">清空结果</el-button>
      </div>

      <div class="search-type">
        <el-radio-group v-model="searchType" size="small">
          <el-radio-button value="exact">精准查找</el-radio-button>
          <el-radio-button value="fuzzy">模糊查找</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="searchResult && searchType === 'exact'" class="result-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="设备ID">
            <div style="display: flex; gap: 8px; align-items: center;">
              <span>{{ searchResult.device_id }}</span>
              <el-button size="small" @click="copyToClipboard(searchResult.device_id, '设备ID')">复制</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="设备名称">{{ searchResult.device_name }}</el-descriptions-item>
          <el-descriptions-item label="设备类型">{{ searchResult.device_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="生产线ID">{{ searchResult.production_line_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="设备管理员">{{ searchResult.device_manager || '-' }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ searchResult.ip_addr || '-' }}</el-descriptions-item>
          <el-descriptions-item label="MAC地址">{{ searchResult.mac_addr || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(searchResult.status)">{{ getStatusText(searchResult.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ searchResult.created_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="最后活跃">{{ searchResult.last_active || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="result-actions">
          <el-button type="primary" @click="handleEdit">编辑</el-button>
          <el-button type="warning" @click="handleGenerateToken">生成Token</el-button>
          <el-button type="danger" @click="handleDelete">删除</el-button>
        </div>
      </div>

      <div v-else-if="searchType === 'fuzzy' && fuzzyResults.length > 0" class="result-list">
        <div class="result-count">找到 {{ fuzzyResults.length }} 个匹配结果</div>
        <el-table :data="fuzzyResults" size="small" width="100%" :height="tableHeight">
          <el-table-column prop="device_id" label="设备ID" min-width="200" />
          <el-table-column prop="device_name" label="设备名称" min-width="150" />
          <el-table-column prop="device_type" label="设备类型" min-width="120" />
          <el-table-column prop="production_line_id" label="生产线ID" min-width="150" />
          <el-table-column prop="ip_addr" label="IP地址" min-width="130" />
          <el-table-column prop="status" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleViewDetail(row)">查看</el-button>
              <el-button type="success" size="small" @click="handleGenerateTokenFromRow(row)">生成Token</el-button>
              <el-button type="danger" size="small" @click="handleDeleteFromRow(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="searched" class="no-result">
        <el-empty :description="searchType === 'exact' ? '未找到匹配的设备' : '未找到匹配的搜索结果'" />
      </div>

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
          <el-form-item label="设备管理员" prop="device_manager">
            <el-input v-model="editForm.device_manager" placeholder="请输入设备管理员" />
          </el-form-item>
          <el-form-item label="IP地址">
            <el-input v-model="editForm.ip_addr" placeholder="请输入IP地址" />
          </el-form-item>
          <el-form-item label="MAC地址">
            <el-input v-model="editForm.mac_addr" placeholder="请输入MAC地址" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="editForm.status">
              <el-option label="未激活" value="inactive" />
              <el-option label="运行中" value="active" />
              <el-option label="故障" value="fault" />
              <el-option label="维护中" value="maintenance" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" :loading="editLoading" @click="handleUpdate">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showDetailDialog" title="设备详情" width="500px">
        <div class="detail-content">
          <div class="detail-row">
            <span class="detail-label">设备ID</span>
            <span class="detail-value">
              {{ currentDetail.device_id }}
              <el-button size="small" @click="copyToClipboard(currentDetail.device_id, '设备ID')">复制</el-button>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">设备名称</span>
            <span class="detail-value">{{ currentDetail.device_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">设备类型</span>
            <span class="detail-value">{{ currentDetail.device_type || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">生产线ID</span>
            <span class="detail-value">{{ currentDetail.production_line_id || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">设备管理员</span>
            <span class="detail-value">{{ currentDetail.device_manager || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">IP地址</span>
            <span class="detail-value">{{ currentDetail.ip_addr || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">MAC地址</span>
            <span class="detail-value">{{ currentDetail.mac_addr || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态</span>
            <span class="detail-value">
              <el-tag :type="getStatusType(currentDetail.status)">{{ getStatusText(currentDetail.status) }}</el-tag>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">创建时间</span>
            <span class="detail-value">{{ currentDetail.created_at || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">最后活跃</span>
            <span class="detail-value">{{ currentDetail.last_active || '-' }}</span>
          </div>
        </div>
        <template #footer>
          <el-button type="primary" @click="handleEditFromDetail">编辑</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showTokenDialog" title="设备Token" width="500px">
        <el-form label-width="100px">
          <el-form-item label="设备ID">
            <el-input v-model="tokenInfo.device_id" disabled />
          </el-form-item>
          <el-form-item label="设备名称">
            <el-input v-model="tokenInfo.device_name" disabled />
          </el-form-item>
          <el-form-item label="Token">
            <el-input v-model="tokenInfo.device_upload_token" type="textarea" :rows="3" disabled />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showTokenDialog = false">关闭</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deviceService } from '../../services/device'

const loading = ref(false)
const searchQuery = ref('')
const searched = ref(false)
const searchResult = ref(null)
const searchType = ref('exact')
const fuzzyResults = ref([])
const showEditDialog = ref(false)
const showDetailDialog = ref(false)
const showTokenDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref(null)

const tableHeight = computed(() => {
  return 'calc(100vh - 320px)'
})

const currentDetail = reactive({
  device_id: '',
  device_name: '',
  device_type: '',
  production_line_id: '',
  device_manager: '',
  ip_addr: '',
  mac_addr: '',
  status: '',
  created_at: '',
  last_active: ''
})

const editForm = reactive({
  device_id: '',
  device_name: '',
  device_type: '',
  production_line_id: '',
  device_manager: '',
  ip_addr: '',
  mac_addr: '',
  status: ''
})

const tokenInfo = reactive({
  device_id: '',
  device_name: '',
  device_upload_token: ''
})

const editRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  device_type: [{ required: true, message: '请输入设备类型', trigger: 'blur' }],
  production_line_id: [{ required: true, message: '请输入生产线ID', trigger: 'blur' }],
  device_manager: [{ required: true, message: '请输入设备管理员', trigger: 'blur' }]
}

const getStatusType = (status) => {
  const types = { online: 'success', offline: 'warning', inactive: 'info', removed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { online: '在线', offline: '离线', inactive: '未激活', removed: '已删除' }
  return texts[status] || status
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入查询条件')
    return
  }

  loading.value = true
  searched.value = true

  try {
    const query = searchQuery.value.trim()

    if (searchType.value === 'exact') {
      searchResult.value = null
      const res = await deviceService.getById(query)
      searchResult.value = res.data
    } else {
      const res = await deviceService.getList({ keyword: query, limit: 100 })
      fuzzyResults.value = res.data.devices || []
    }
  } catch (error) {
    console.error('Search failed:', error)
    if (searchType.value === 'exact') {
      searchResult.value = null
    } else {
      fuzzyResults.value = []
    }
  } finally {
    loading.value = false
  }
}

const handleClear = () => {
  searchQuery.value = ''
  searchResult.value = null
  fuzzyResults.value = []
  searched.value = false
  searchType.value = 'exact'
}

const copyToClipboard = async (text, label) => {
  if (!text) {
    ElMessage.warning(`${label}为空，无法复制`)
    return
  }

  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label}已复制`)
  } catch (error) {
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success(`${label}已复制`)
  }
}

const handleViewDetail = (row) => {
  Object.assign(currentDetail, row)
  showDetailDialog.value = true
}

const handleEditFromDetail = () => {
  showDetailDialog.value = false
  handleEdit()
}

const handleEdit = () => {
  const detail = searchResult.value || currentDetail
  Object.assign(editForm, detail)
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        await deviceService.update(editForm.device_id, {
          device_name: editForm.device_name,
          device_type: editForm.device_type,
          production_line_id: editForm.production_line_id,
          device_manager: editForm.device_manager,
          ip_addr: editForm.ip_addr || undefined,
          mac_addr: editForm.mac_addr || undefined,
          status: editForm.status
        })
        ElMessage.success('设备更新成功')
        showEditDialog.value = false
        handleSearch()
      } catch (error) {
        console.error('Update device failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除设备 ${searchResult.value.device_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deviceService.delete(searchResult.value.device_id)
    ElMessage.success('设备删除成功')
    searchResult.value = null
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete device failed:', error)
    }
  }
}

const handleDeleteFromRow = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除设备 ${row.device_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deviceService.delete(row.device_id)
    ElMessage.success('设备删除成功')
    handleSearch()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete device failed:', error)
    }
  }
}

const handleGenerateToken = async () => {
  try {
    const res = await deviceService.generateToken(searchResult.value.device_id)
    Object.assign(tokenInfo, {
      device_id: searchResult.value.device_id,
      device_name: searchResult.value.device_name,
      device_upload_token: res.data.device_upload_token
    })
    showTokenDialog.value = true
  } catch (error) {
    console.error('Generate token failed:', error)
  }
}

const handleGenerateTokenFromRow = async (row) => {
  try {
    const res = await deviceService.generateToken(row.device_id)
    Object.assign(tokenInfo, {
      device_id: row.device_id,
      device_name: row.device_name,
      device_upload_token: res.data.device_upload_token
    })
    showTokenDialog.value = true
  } catch (error) {
    console.error('Generate token failed:', error)
  }
}

onMounted(() => {})
</script>

<style scoped>
.devices-search-container {
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
  display: flex;
  flex-direction: column;
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}

.search-form {
  margin-bottom: 16px;
}

.search-type {
  margin-bottom: 16px;
}

.result-card {
  background: #f5f7fa;
  padding: 24px;
  border-radius: 8px;
}

.result-list {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.result-count {
  margin-bottom: 12px;
  color: #666;
  font-size: 14px;
}

.result-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.no-result {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-content {
  padding: 16px;
}

.detail-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  width: 100px;
  font-weight: bold;
  color: #606266;
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.detail-value .el-button) {
  padding: 2px 8px;
}

:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table .el-table__header-wrapper),
:deep(.el-table .el-table__body-wrapper) {
  width: 100% !important;
}
</style>
