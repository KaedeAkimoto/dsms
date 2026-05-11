<template>
  <div class="detections-container">
    <el-card>
      <template #header>
        <span>检测记录</span>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="设备ID">
          <el-input v-model="searchForm.device_id" placeholder="请输入设备ID" clearable />
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
          <el-table-column prop="record_batch_id" label="批次ID" width="220" show-overflow-tooltip />
          <el-table-column prop="device_id" label="设备ID" width="180" show-overflow-tooltip />
          <el-table-column prop="detect_count" label="检测数" width="100" />
          <el-table-column prop="pass_count" label="通过数" width="100" />
          <el-table-column prop="latest_upload_at" label="最新上传时间" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleViewDetail(row)">详情</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { detectionService } from '../../services/detection'
import { formatDateTime, formatUtcToCst } from '../../utils/date'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  device_id: ''
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await detectionService.getList({
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    })
    const records = res.data.records || []
    for (const record of records) {
      record.latest_upload_at = formatUtcToCst(record.latest_upload_at)
    }
    tableData.value = records
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('Load detections failed:', error)
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

const handleViewDetail = (row) => {
  router.push(`/detections/defect-detail/${row.record_batch_id}`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.detections-container {
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
