<template>
  <div class="audit-container">
    <el-card>
      <template #header>
        <span>审计日志</span>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户ID">
          <el-input v-model="searchForm.user_id" placeholder="请输入用户ID" clearable />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-input v-model="searchForm.operation_type" placeholder="请输入操作类型" clearable />
        </el-form-item>
        <el-form-item label="操作结果">
          <el-select v-model="searchForm.operation_result" placeholder="请选择" clearable>
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failure" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="searchForm.start_date" type="date" placeholder="选择开始日期" value-format="YYYY-MM-DD" style="width: 150px;" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="searchForm.end_date" type="date" placeholder="选择结束日期" value-format="YYYY-MM-DD" style="width: 150px;" />
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
          @row-dblclick="handleRowDblClick"
        >
          <el-table-column prop="log_id" label="日志ID" width="220" show-overflow-tooltip />
          <el-table-column prop="user_id" label="用户ID" width="150" show-overflow-tooltip />
          <el-table-column label="用户名" width="120">
            <template #default="{ row }">
              {{ getUserName(row.user_id) }}
            </template>
          </el-table-column>
          <el-table-column prop="operation_type" label="操作类型" width="120" />
          <el-table-column prop="operation_details" label="操作详情" show-overflow-tooltip />
          <el-table-column prop="operation_result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.operation_result === 'success' ? 'success' : 'danger'">
                {{ row.operation_result === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_msg" label="错误信息" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="160" />
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

      <el-dialog v-model="detailDialogVisible" title="日志详情" width="600px">
        <el-descriptions :column="1" border v-if="detailData">
          <el-descriptions-item label="日志ID">{{ detailData.log_id }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ detailData.user_id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ getUserName(detailData.user_id) }}</el-descriptions-item>
          <el-descriptions-item label="操作类型">{{ detailData.operation_type }}</el-descriptions-item>
          <el-descriptions-item label="操作详情">{{ detailData.operation_details || '-' }}</el-descriptions-item>
          <el-descriptions-item label="操作结果">
            <el-tag :type="detailData.operation_result === 'success' ? 'success' : 'danger'">
              {{ detailData.operation_result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="错误信息">{{ detailData.error_msg || '-' }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ detailData.created_at }}</el-descriptions-item>
        </el-descriptions>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { auditService } from '../../services/other'
import { userService } from '../../services/user'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const tableData = ref([])
const userCache = new Map()
const detailDialogVisible = ref(false)
const detailData = ref(null)

const formatDate = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const endDate = new Date()
const startDate = new Date()
startDate.setDate(startDate.getDate() - 7)

const searchForm = reactive({
  user_id: '',
  operation_type: '',
  operation_result: '',
  start_date: '',
  end_date: ''
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit,
      user_id: searchForm.user_id || undefined,
      operation_type: searchForm.operation_type || undefined,
      operation_result: searchForm.operation_result || undefined,
      start_date: searchForm.start_date || undefined,
      end_date: searchForm.end_date || undefined
    }
    const res = await auditService.getLogs(params)
    const logs = res.data.logs || []
    for (const log of logs) {
      log.created_at = formatDateTime(log.created_at)
    }
    tableData.value = logs
    pagination.total = res.data.total || 0
    
    // 异步加载用户信息
    await loadUsers(logs)
  } catch (error) {
    console.error('Load audit logs failed:', error)
  } finally {
    loading.value = false
  }
}

const loadUsers = async (logs) => {
  const userIds = [...new Set(logs.map(log => log.user_id).filter(id => id))]
  const loadPromises = userIds.map(async (user_id) => {
    if (userCache.has(user_id)) return
    try {
      const res = await userService.getById(user_id)
      userCache.set(user_id, res.data)
    } catch (error) {
      console.error('Load user failed:', error)
      userCache.set(user_id, null)
    }
  })
  await Promise.all(loadPromises)
  // 触发视图更新
  tableData.value = [...tableData.value]
}

const getUserName = (user_id) => {
  if (!user_id) return '-'
  const user = userCache.get(user_id)
  if (!user) return '-'
  return user.full_name || user.username || '-'
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleRowDblClick = (row) => {
  detailData.value = row
  detailDialogVisible.value = true
}

const handleReset = () => {
  searchForm.user_id = ''
  searchForm.operation_type = ''
  searchForm.operation_result = ''
  searchForm.start_date = ''
  searchForm.end_date = ''
  pagination.page = 1
  loadData()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.audit-container {
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
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.search-form {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
}

.pagination-wrapper {
  padding: 16px;
  border-top: 1px solid #EBEEF5;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

:deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 10;
}

:deep(.el-table__header th) {
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 10;
}
</style>
