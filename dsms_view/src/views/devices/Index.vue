<template>
  <div class="devices-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备列表</span>
          <div>
            <el-button type="primary" @click="showCreateDialog = true">创建设备</el-button>
            <el-button type="success" @click="handleBatchGenerateTokens" :disabled="selectedDevices.length === 0">批量生成Token</el-button>
            <el-button type="info" @click="handleExportTokens" :disabled="selectedDevices.length === 0">导出Token</el-button>
          </div>
        </div>
      </template>

      <div class="table-wrapper">
        <el-table 
          :data="tableData" 
          v-loading="loading" 
          style="width: 100%;"
          height="100%"
          :header-cell-style="{ position: 'sticky', top: 0, zIndex: 1 }"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="device_id" label="设备ID" width="220" show-overflow-tooltip />
          <el-table-column prop="device_name" label="设备名称" />
          <el-table-column prop="device_type" label="设备类型" width="120" />
          <el-table-column label="生产线" width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ getProductionLineName(row.production_line_id) }}
            </template>
          </el-table-column>
          <el-table-column prop="ip_addr" label="IP地址" width="130" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="340" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="info" size="small" @click="handleView(row)">详情</el-button>
                <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button type="warning" size="small" @click="handleGenerateToken(row)">生成Token</el-button>
                <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建设备" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="createForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-input v-model="createForm.device_type" placeholder="请输入设备类型" />
        </el-form-item>
        <el-form-item label="生产线" prop="production_line_id">
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

    <el-dialog v-model="showEditDialog" title="编辑设备" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="editForm.device_name" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-input v-model="editForm.device_type" />
        </el-form-item>
        <el-form-item label="生产线" prop="production_line_id">
          <el-select
            v-model="editForm.production_line_id"
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
            v-model="editForm.device_manager"
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
          <el-input v-model="editForm.ip_addr" />
        </el-form-item>
        <el-form-item label="MAC地址">
          <el-input v-model="editForm.mac_addr" />
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
      <el-descriptions :column="1" border v-if="detailDevice">
        <el-descriptions-item label="设备ID">{{ detailDevice.device_id }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">{{ detailDevice.device_name }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ detailDevice.device_type }}</el-descriptions-item>
        <el-descriptions-item label="生产线">{{ getProductionLineName(detailDevice.production_line_id) }}</el-descriptions-item>
        <el-descriptions-item label="设备管理员">{{ getUserName(detailDevice.device_manager) }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ detailDevice.ip_addr || '-' }}</el-descriptions-item>
        <el-descriptions-item label="MAC地址">{{ detailDevice.mac_addr || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(detailDevice.status)">{{ getStatusText(detailDevice.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(detailDevice.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(detailDevice.updated_at) }}</el-descriptions-item>
      </el-descriptions>
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
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deviceService } from '../../services/device'
import { productionLineService } from '../../services/productionLine'
import { userService } from '../../services/user'

const loading = ref(false)
const tableData = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDetailDialog = ref(false)
const showTokenDialog = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)
const plLoading = ref(false)
const userLoading = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const selectedDevices = ref([])
const productionLineOptions = ref([])
const userOptions = ref([])
const productionLineMap = ref(new Map())
const userMap = ref(new Map())
const detailDevice = ref(null)

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const createForm = reactive({
  device_name: '',
  device_type: '',
  production_line_id: '',
  device_manager: '',
  ip_addr: '',
  mac_addr: ''
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

const createRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  device_type: [{ required: true, message: '请输入设备类型', trigger: 'blur' }],
  production_line_id: [{ required: true, message: '请选择生产线', trigger: 'change' }],
  device_manager: [{ required: true, message: '请选择设备管理员', trigger: 'change' }]
}

const editRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  device_type: [{ required: true, message: '请输入设备类型', trigger: 'blur' }],
  production_line_id: [{ required: true, message: '请选择生产线', trigger: 'change' }],
  device_manager: [{ required: true, message: '请选择设备管理员', trigger: 'change' }]
}

const getStatusType = (status) => {
  const types = { online: 'success', offline: 'warning', inactive: 'info', removed: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { online: '在线', offline: '离线', inactive: '未激活', removed: '已删除' }
  return texts[status] || status
}

const getProductionLineName = (id) => {
  if (!id) return '-'
  if (productionLineMap.value.has(id)) {
    return productionLineMap.value.get(id)
  }
  return id
}

const getUserName = (id) => {
  if (!id) return '-'
  if (userMap.value.has(id)) {
    return userMap.value.get(id)
  }
  return id
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const [devicesRes, plRes, usersRes] = await Promise.all([
      deviceService.getList({
        skip: (pagination.page - 1) * pagination.limit,
        limit: pagination.limit
      }),
      productionLineService.getList({ limit: 1000 }),
      userService.getList({ limit: 1000 })
    ])
    
    tableData.value = devicesRes.data.devices || []
    pagination.total = devicesRes.data.total || 0
    
    const lines = plRes.data?.production_lines || []
    lines.forEach(pl => {
      productionLineMap.value.set(pl.production_line_id, pl.production_line_name)
    })
    productionLineOptions.value = lines
    
    const users = usersRes.data?.users || []
    users.forEach(u => {
      userMap.value.set(u.user_id, u.real_name || u.user_name)
    })
    userOptions.value = users
  } catch (error) {
    console.error('Load devices failed:', error)
  } finally {
    loading.value = false
  }
}

const loadProductionLines = async (query) => {
  if (!query) {
    productionLineOptions.value = []
    return
  }
  plLoading.value = true
  try {
    const res = await productionLineService.search({ keyword: query, limit: 50 })
    const lines = res.data?.production_lines || []
    lines.forEach(pl => {
      if (!productionLineMap.value.has(pl.production_line_id)) {
        productionLineMap.value.set(pl.production_line_id, pl.production_line_name)
      }
    })
    productionLineOptions.value = lines
  } catch (error) {
    console.error('Load production lines failed:', error)
  } finally {
    plLoading.value = false
  }
}

const loadUsers = async (query) => {
  if (!query) {
    userOptions.value = []
    return
  }
  userLoading.value = true
  try {
    const res = await userService.search({ keyword: query, limit: 50 })
    const users = res.data?.users || []
    users.forEach(u => {
      if (!userMap.value.has(u.user_id)) {
        userMap.value.set(u.user_id, u.real_name || u.user_name)
      }
    })
    userOptions.value = users
  } catch (error) {
    console.error('Load users failed:', error)
  } finally {
    userLoading.value = false
  }
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
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

const handleView = (row) => {
  detailDevice.value = row
  showDetailDialog.value = true
}

const handleEdit = (row) => {
  Object.assign(editForm, row)
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
        loadData()
      } catch (error) {
        console.error('Update device failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除设备 ${row.device_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deviceService.delete(row.device_id)
    ElMessage.success('设备删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete device failed:', error)
    }
  }
}

const handleGenerateToken = async (row) => {
  try {
    const res = await deviceService.generateToken(row.device_id)
    Object.assign(tokenInfo, res.data)
    showTokenDialog.value = true
  } catch (error) {
    console.error('Generate token failed:', error)
  }
}

const handleBatchGenerateTokens = async () => {
  if (selectedDevices.value.length === 0) {
    ElMessage.warning('请先选择设备')
    return
  }
  try {
    const deviceIds = selectedDevices.value.map(item => item.device_id)
    await deviceService.batchGenerateTokens(deviceIds)
    ElMessage.success('批量生成Token成功')
    loadData()
  } catch (error) {
    console.error('Batch generate tokens failed:', error)
  }
}

const handleSelectionChange = (selection) => {
  selectedDevices.value = selection
}

const handleExportTokens = async () => {
  if (selectedDevices.value.length === 0) {
    ElMessage.warning('请先选择要导出的设备')
    return
  }
  try {
    const deviceIds = selectedDevices.value.map(item => item.device_id)
    const tokenData = []
    for (const device of selectedDevices.value) {
      try {
        const res = await deviceService.getToken(device.device_id)
        tokenData.push({
          device_id: device.device_id,
          device_name: device.device_name,
          token: res.data.device_upload_token || ''
        })
      } catch (error) {
        console.error('Get token failed for device:', device.device_id, error)
      }
    }
    
    const csvContent = [
      ['设备ID', '设备名称', 'Token'].join(','),
      ...tokenData.map(row => [row.device_id, row.device_name, row.token].join(','))
    ].join('\n')
    
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `设备Token_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Export tokens failed:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.devices-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-wrapper {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  margin-top: 16px;
  text-align: right;
}
</style>
