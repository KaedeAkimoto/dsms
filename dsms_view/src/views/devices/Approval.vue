<template>
  <div class="approval-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备审批</span>
          <el-button type="primary" @click="showCreateDialog = true">发起审批</el-button>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="设备ID">
          <el-input v-model="searchForm.device_id" placeholder="请输入设备ID" clearable />
        </el-form-item>
        <el-form-item label="审批状态">
          <el-select v-model="searchForm.status" placeholder="请选择" clearable>
            <el-option label="待审批" value="pending" />
            <el-option label="已批准" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div class="table-wrapper">
        <el-table 
          :data="tableData" 
          v-loading="loading" 
          style="width: 100%;"
          height="100%"
          :header-cell-style="{ position: 'sticky', top: 0, zIndex: 1 }"
        >
          <el-table-column prop="device_approval_id" label="审批ID" width="220" show-overflow-tooltip />
          <el-table-column prop="device_id" label="设备ID" width="180" show-overflow-tooltip />
          <el-table-column prop="device_name" label="设备名称" />
          <el-table-column prop="device_type" label="设备类型" width="120" />
          <el-table-column prop="applicant_name" label="申请人" width="100" />
          <el-table-column prop="apply_time" label="申请时间" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="info" size="small" @click="handleView(row)">详情</el-button>
                <el-button v-if="row.status === 'pending'" type="success" size="small" @click="handleApprove(row)">批准</el-button>
                <el-button v-if="row.status === 'pending'" type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
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

    <el-dialog v-model="showCreateDialog" title="发起设备审批" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="createForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-input v-model="createForm.device_type" placeholder="请输入设备类型" />
        </el-form-item>
        <el-form-item label="生产线ID" prop="production_line_id">
          <el-input v-model="createForm.production_line_id" placeholder="请输入生产线ID" />
        </el-form-item>
        <el-form-item label="设备管理员" prop="device_manager">
          <el-input v-model="createForm.device_manager" placeholder="请输入设备管理员ID" />
        </el-form-item>
        <el-form-item label="申请原因" prop="reason">
          <el-input type="textarea" v-model="createForm.reason" placeholder="请输入申请原因" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">发起</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="审批详情" width="500px">
      <el-form :model="detailData" label-width="100px" disabled>
        <el-form-item label="审批ID">
          <el-input v-model="detailData.device_approval_id" />
        </el-form-item>
        <el-form-item label="设备ID">
          <el-input v-model="detailData.device_id" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="detailData.device_name" />
        </el-form-item>
        <el-form-item label="设备类型">
          <el-input v-model="detailData.device_type" />
        </el-form-item>
        <el-form-item label="申请人">
          <el-input v-model="detailData.applicant_name" />
        </el-form-item>
        <el-form-item label="申请时间">
          <el-input v-model="detailData.apply_time" />
        </el-form-item>
        <el-form-item label="申请原因">
          <el-input type="textarea" v-model="detailData.reason" :rows="3" />
        </el-form-item>
        <el-form-item label="审批状态">
          <el-tag :type="getStatusType(detailData.status)">{{ getStatusText(detailData.status) }}</el-tag>
        </el-form-item>
        <el-form-item v-if="detailData.approver_name" label="审批人">
          <el-input v-model="detailData.approver_name" />
        </el-form-item>
        <el-form-item v-if="detailData.approve_time" label="审批时间">
          <el-input v-model="detailData.approve_time" />
        </el-form-item>
        <el-form-item v-if="detailData.approve_comment" label="审批意见">
          <el-input type="textarea" v-model="detailData.approve_comment" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showApproveDialog" title="审批处理" width="400px">
      <el-form ref="approveFormRef" :model="approveForm" label-width="80px">
        <el-form-item label="审批意见">
          <el-input type="textarea" v-model="approveForm.comment" placeholder="请输入审批意见" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApproveDialog = false">取消</el-button>
        <el-button type="primary" :loading="approveLoading" @click="confirmApprove">确认{{ approveAction === 'approve' ? '批准' : '拒绝' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { deviceService } from '../../services/device'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  device_id: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showApproveDialog = ref(false)
const createLoading = ref(false)
const approveLoading = ref(false)
const approveAction = ref('approve')
const currentApprovalId = ref(null)

const createFormRef = ref(null)
const approveFormRef = ref(null)

const createForm = reactive({
  device_name: '',
  device_type: '',
  production_line_id: '',
  device_manager: '',
  reason: ''
})

const approveForm = reactive({
  comment: ''
})

const detailData = reactive({})

const createRules = {
  device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  device_type: [{ required: true, message: '请输入设备类型', trigger: 'blur' }],
  production_line_id: [{ required: true, message: '请输入生产线ID', trigger: 'blur' }],
  device_manager: [{ required: true, message: '请输入设备管理员ID', trigger: 'blur' }]
}

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待审批',
    approved: '已批准',
    rejected: '已拒绝'
  }
  return texts[status] || status
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    }
    if (searchForm.device_id) params.device_id = searchForm.device_id
    if (searchForm.status) params.status = searchForm.status

    const res = await deviceService.getApprovals(params)
    const records = res.data.records || []
    for (const record of records) {
      record.apply_time = formatDateTime(record.apply_time)
      record.approve_time = record.approve_time ? formatDateTime(record.approve_time) : '-'
    }
    tableData.value = records
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('Load approvals failed:', error)
    ElMessage.error('加载审批列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.device_id = ''
  searchForm.status = ''
  pagination.page = 1
  loadData()
}

const handleSizeChange = (val) => {
  pagination.limit = val
  loadData()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  loadData()
}

const handleView = (row) => {
  Object.assign(detailData, row)
  showDetailDialog.value = true
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await deviceService.createApproval({
          device_name: createForm.device_name,
          device_type: createForm.device_type,
          production_line_id: createForm.production_line_id,
          device_manager: createForm.device_manager,
          reason: createForm.reason
        })
        ElMessage.success('发起审批成功')
        showCreateDialog.value = false
        createForm.device_name = ''
        createForm.device_type = ''
        createForm.production_line_id = ''
        createForm.device_manager = ''
        createForm.reason = ''
        loadData()
      } catch (error) {
        console.error('Create approval failed:', error)
        ElMessage.error('发起审批失败')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleApprove = (row) => {
  currentApprovalId.value = row.device_approval_id
  approveAction.value = 'approve'
  approveForm.comment = ''
  showApproveDialog.value = true
}

const handleReject = (row) => {
  currentApprovalId.value = row.device_approval_id
  approveAction.value = 'reject'
  approveForm.comment = ''
  showApproveDialog.value = true
}

const confirmApprove = async () => {
  approveLoading.value = true
  try {
    await deviceService.approve(currentApprovalId.value, {
      status: approveAction.value === 'approve' ? 'approved' : 'rejected',
      comment: approveForm.comment
    })
    ElMessage.success('审批完成')
    showApproveDialog.value = false
    loadData()
  } catch (error) {
    console.error('Approve failed:', error)
    ElMessage.error('审批失败')
  } finally {
    approveLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.approval-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 16px;
}

.table-wrapper {
  max-height: 500px;
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
