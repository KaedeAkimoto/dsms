<template>
  <div class="reviews-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>审查任务</span>
          <el-tabs v-model="activeTab" @tab-change="handleTabChange">
            <el-tab-pane label="全部" name="all" />
            <el-tab-pane label="待审查" name="pending" />
            <el-tab-pane label="已完成" name="completed" />
            <el-tab-pane label="已取消" name="cancel" />
            <el-tab-pane label="已超时" name="timeout" />
          </el-tabs>
        </div>
      </template>

      <div class="table-wrapper">
        <el-table 
          :data="tableData" 
          v-loading="loading" 
          style="width: 100%;"
          height="100%"
          :header-cell-style="{ position: 'sticky', top: 0, zIndex: 1 }"
        >
          <el-table-column prop="review_task_id" label="任务ID" width="220" show-overflow-tooltip />
          <el-table-column prop="record_batch_id" label="批次ID" width="180" show-overflow-tooltip />
          <el-table-column prop="defect_details_id" label="缺陷详情ID" width="180" show-overflow-tooltip />
          <el-table-column prop="reviewer_id" label="审查人ID" width="120" show-overflow-tooltip />
          <el-table-column prop="review_status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.review_status)">
                {{ getStatusText(row.review_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="review_result" label="审查结果" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.review_result" :type="getResultType(row.review_result)">
                {{ getResultText(row.review_result) }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="review_comment" label="审查意见" show-overflow-tooltip />
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.review_status === 'pending'"
                type="primary"
                size="small"
                @click="handleReview(row)"
              >
                审查
              </el-button>
              <el-button type="primary" size="small" @click="handleView(row)">详情</el-button>
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

    <el-dialog v-model="showReviewDialog" title="审查任务" width="900px">
      <div v-if="reviewLoading" class="text-center py-8">
        <div class="el-loading-spinner">
          <svg class="circular" viewBox="25 25 50 50">
            <circle class="path" cx="50" cy="50" r="20" fill="none" stroke-width="4" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="el-loading-text" style="margin-top: 10px;">加载中...</p>
      </div>
      <div v-else>
        <div style="display: flex; gap: 24px;">
          <div style="flex: 1;">
            <el-form :model="reviewForm" label-width="100px" label-position="left">
              <el-form-item label="任务ID">
                <el-input v-model="reviewForm.review_task_id" disabled />
              </el-form-item>
              <el-form-item label="缺陷详情ID">
                <el-input v-model="reviewForm.defect_details_id" disabled />
              </el-form-item>
              <el-form-item label="批次ID">
                <el-input v-model="reviewForm.record_batch_id" disabled />
              </el-form-item>
              <el-form-item label="审查结果">
                <el-select v-model="reviewForm.review_result" style="width: 100%;">
                  <el-option label="确认缺陷" value="confirmed" />
                  <el-option label="误报" value="false_positive" />
                  <el-option label="不确定" value="uncertain" />
                  <el-option label="混淆" value="confusion" />
                </el-select>
              </el-form-item>
              <el-form-item label="缺陷数量">
                <el-input-number v-model="reviewForm.review_defect_count" :min="0" style="width: 100%;" />
              </el-form-item>
              <el-form-item label="是否有更改">
                <el-switch v-model="reviewForm.has_details" />
              </el-form-item>
              <el-form-item label="审查意见">
                <el-input v-model="reviewForm.review_comment" type="textarea" :rows="4" placeholder="请输入审查意见" />
              </el-form-item>
            </el-form>
          </div>
          
          <div v-if="reviewDefectDetail.data" style="width: 320px; border-left: 1px solid #DCDFE6; padding-left: 24px;">
            <h4 style="margin-bottom: 16px; color: #303133;">缺陷详情</h4>
            <div v-if="reviewDefectDetail.data.original_img" style="margin-bottom: 16px;">
              <p style="margin-bottom: 8px; color: #606266; font-size: 14px;">原始图片：</p>
              <img :src="reviewDefectDetail.data.original_img" alt="缺陷图片" style="max-width: 100%; max-height: 200px; object-fit: contain; border: 1px solid #DCDFE6; border-radius: 4px;" />
            </div>
            <div style="margin-bottom: 12px;">
              <p style="color: #606266; font-size: 14px;">缺陷数量：<span style="color: #303133; font-weight: 500;">{{ reviewDefectDetail.data.defect_count || 0 }}</span></p>
            </div>
            <div>
              <p style="color: #606266; font-size: 14px; margin-bottom: 8px;">详细信息：</p>
              <div style="background: #F5F7FA; padding: 12px; border-radius: 4px; max-height: 150px; overflow-y: auto; word-break: break-all; font-size: 13px; color: #606266;">{{ reviewDefectDetail.data.details || '无' }}</div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmitReview">提交审查</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showViewDialog" title="任务详情" width="800px">
      <div v-if="viewLoading" class="text-center py-8">
        <div class="el-loading-spinner">
          <svg class="circular" viewBox="25 25 50 50">
            <circle class="path" cx="50" cy="50" r="20" fill="none" stroke-width="4" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="el-loading-text" style="margin-top: 10px;">加载中...</p>
      </div>
      <div v-else>
        <el-form :model="viewForm" label-width="120px">
          <el-form-item label="任务ID">
            <el-input v-model="viewForm.review_task_id" disabled />
          </el-form-item>
          <el-form-item label="缺陷详情ID">
            <el-input v-model="viewForm.defect_details_id" disabled />
          </el-form-item>
          <el-form-item label="批次ID">
            <el-input v-model="viewForm.record_batch_id" disabled />
          </el-form-item>
          <el-form-item label="被分配人">
            <el-input v-model="viewForm.assignee_name" disabled />
          </el-form-item>
          <el-form-item label="审查人">
            <el-input v-model="viewForm.reviewer_name" disabled />
          </el-form-item>
          <el-form-item label="任务状态">
            <el-tag :type="getStatusType(viewForm.review_status)">
              {{ getStatusText(viewForm.review_status) }}
            </el-tag>
          </el-form-item>
          <el-form-item label="审查结果" v-if="viewForm.review_result">
            <el-tag :type="getResultType(viewForm.review_result)">
              {{ getResultText(viewForm.review_result) }}
            </el-tag>
          </el-form-item>
          <el-form-item label="缺陷数量">
            <span>{{ viewForm.review_defect_count ?? '-' }}</span>
          </el-form-item>
          <el-form-item label="是否有细节变更">
            <span>{{ viewForm.has_details ? '是' : '否' }}</span>
          </el-form-item>
          <el-form-item label="审查意见">
            <div style="word-break: break-all;">{{ viewForm.review_comment || '-' }}</div>
          </el-form-item>
          <el-form-item label="分配时间">
            <span>{{ viewForm.assignee_at || '-' }}</span>
          </el-form-item>
          <el-form-item label="完成时间">
            <span>{{ viewForm.completed_at || '-' }}</span>
          </el-form-item>
          <el-form-item label="创建时间">
            <span>{{ viewForm.created_at || '-' }}</span>
          </el-form-item>
        </el-form>

        <div v-if="defectDetail.data" class="mt-4 pt-4 border-top">
          <h4 class="mb-3">缺陷详情</h4>
          <el-form :model="defectDetail.data" label-width="120px">
            <el-form-item label="原始图片">
              <div v-if="defectDetail.data.original_img" class="image-preview">
                <img :src="defectDetail.data.original_img" alt="缺陷图片" class="max-w-xs" />
              </div>
              <span v-else>-</span>
            </el-form-item>
            <el-form-item label="缺陷数量">
              <span>{{ defectDetail.data.defect_count || 0 }}</span>
            </el-form-item>
            <el-form-item label="详细信息">
              <div style="word-break: break-all; max-height: 200px; overflow-y: auto;">{{ defectDetail.data.details || '-' }}</div>
            </el-form-item>
          </el-form>
        </div>
      </div>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reviewService } from '../../services/review'
import { detectionService } from '../../services/detection'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const tableData = ref([])
const activeTab = ref('all')
const showReviewDialog = ref(false)
const showViewDialog = ref(false)
const reviewLoading = ref(false)
const submitLoading = ref(false)
const viewLoading = ref(false)

const defectDetail = reactive({
  data: null
})

const reviewDefectDetail = reactive({
  data: null
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const reviewForm = reactive({
  review_task_id: '',
  defect_details_id: '',
  record_batch_id: '',
  review_result: 'confirmed',
  review_defect_count: 0,
  has_details: true,
  review_comment: ''
})

const viewForm = reactive({
  review_task_id: '',
  defect_details_id: '',
  record_batch_id: '',
  assignee_name: '',
  reviewer_name: '',
  review_status: '',
  review_result: '',
  review_defect_count: null,
  has_details: false,
  review_comment: '',
  assignee_at: '',
  completed_at: '',
  created_at: ''
})

const getStatusType = (status) => {
  const types = { pending: 'warning', completed: 'success', cancel: 'info', timeout: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '待审查', completed: '已完成', cancel: '已取消', timeout: '已超时' }
  return texts[status] || status
}

const getResultType = (result) => {
  const types = { confirmed: 'success', false_positive: 'info', uncertain: 'warning', confusion: 'danger' }
  return types[result] || 'info'
}

const getResultText = (result) => {
  const texts = { confirmed: '确认缺陷', false_positive: '误报', uncertain: '不确定', confusion: '混淆' }
  return texts[result] || result
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    }
    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }
    const res = await reviewService.getTasks(params)
    const tasks = res.data.tasks || []
    for (const task of tasks) {
      task.created_at = formatDateTime(task.created_at)
      task.reviewed_at = formatDateTime(task.reviewed_at)
    }
    tableData.value = tasks
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('Load reviews failed:', error)
  } finally {
    loading.value = false
  }
}

const handleTabChange = () => {
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

const handleReview = async (row) => {
  reviewLoading.value = true
  reviewDefectDetail.data = null
  
  try {
    reviewForm.review_task_id = row.review_task_id
    reviewForm.defect_details_id = row.defect_details_id || ''
    reviewForm.record_batch_id = row.record_batch_id || ''
    reviewForm.review_result = 'confirmed'
    reviewForm.has_details = false
    reviewForm.review_comment = ''
    
    if (row.defect_details_id) {
      try {
        const defectRes = await detectionService.getDefectDetail(row.defect_details_id)
        reviewDefectDetail.data = defectRes.data
        reviewForm.review_defect_count = defectRes.data?.defect_count || 0
      } catch (defectError) {
        console.error('Load defect detail failed:', defectError)
        reviewForm.review_defect_count = row.defect_count || 0
      }
    } else {
      reviewForm.review_defect_count = row.defect_count || 0
    }
    
    showReviewDialog.value = true
  } finally {
    reviewLoading.value = false
  }
}

const handleReject = (row) => {
  reviewForm.review_task_id = row.review_task_id
  reviewForm.review_result = 'false_positive'
  reviewForm.review_defect_count = 0
  reviewForm.review_comment = ''
  showReviewDialog.value = true
}

const handleSubmitReview = async () => {
  submitLoading.value = true
  try {
    await reviewService.update(reviewForm.review_task_id, {
      review_status: 'completed',
      review_result: reviewForm.review_result,
      review_defect_count: reviewForm.review_defect_count,
      has_details: reviewForm.has_details,
      review_comment: reviewForm.review_comment || undefined
    })
    ElMessage.success('审查提交成功')
    showReviewDialog.value = false
    loadData()
  } catch (error) {
    console.error('Submit review failed:', error)
  } finally {
    submitLoading.value = false
  }
}

const handleView = async (row) => {
  viewLoading.value = true
  defectDetail.data = null
  
  try {
    const res = await reviewService.getById(row.review_task_id)
    const data = res.data
    
    viewForm.review_task_id = data.review_task_id || ''
    viewForm.defect_details_id = data.defect_details_id || ''
    viewForm.record_batch_id = data.record_batch_id || ''
    viewForm.assignee_name = data.assignee_name || data.assignee_id || ''
    viewForm.reviewer_name = data.reviewer_name || data.reviewer_id || ''
    viewForm.review_status = data.review_status || ''
    viewForm.review_result = data.review_result || ''
    viewForm.review_defect_count = data.review_defect_count ?? null
    viewForm.has_details = data.has_details || false
    viewForm.review_comment = data.review_comment || ''
    viewForm.assignee_at = formatDateTime(data.assignee_at) || ''
    viewForm.completed_at = formatDateTime(data.completed_at) || ''
    viewForm.created_at = formatDateTime(data.created_at) || ''
    
    if (data.defect_details_id) {
      try {
        const defectRes = await detectionService.getDefectDetail(data.defect_details_id)
        defectDetail.data = defectRes.data
      } catch (defectError) {
        console.error('Load defect detail failed:', defectError)
      }
    }
    
    showViewDialog.value = true
  } catch (error) {
    console.error('Load review detail failed:', error)
    ElMessage.error('加载详情失败')
  } finally {
    viewLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.reviews-container {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
