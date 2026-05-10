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
              <el-tag :type="row.review_status ? (getStatusType(row.review_status) || 'info') : 'info'">
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
          
          <div v-if="reviewDefectDetail.data" style="width: 400px; border-left: 1px solid #DCDFE6; padding-left: 24px;">
            <h4 style="margin-bottom: 16px; color: #303133;">缺陷标注</h4>
            
            <div v-if="reviewDefectDetail.data.image_base64" style="margin-bottom: 16px;">
              <p style="margin-bottom: 8px; color: #606266; font-size: 14px;">
                原始图片 
                <el-button v-if="reviewForm.has_details" type="text" size="small" @click="clearAllBoxes" style="padding: 0; margin-left: 8px; color: #F56C6C;">
                  清空标注
                </el-button>
              </p>
              <div class="canvas-container" ref="canvasContainer" @mousedown="startDraw" @mousemove="drawing" @mouseup="endDraw">
                <img 
                  :src="`data:image/${reviewDefectDetail.data.image_format};base64,${reviewDefectDetail.data.image_base64}`" 
                  alt="缺陷图片" 
                  class="defect-image"
                  ref="defectImage"
                  draggable="false"
                  @mousedown.prevent
                  @load="onImageLoad"
                />
                <svg class="overlay-svg" ref="overlaySvg" :width="overlayWidth || '100%'" :height="overlayHeight || '100%'" style="position: absolute; top: 0; left: 0;">
                  <rect 
                    v-for="(box, index) in drawnBoxes" 
                    :key="index"
                    :x="getScaledX(box.x)"
                    :y="getScaledY(box.y)"
                    :width="getScaledWidth(box.width)"
                    :height="getScaledHeight(box.height)"
                    :fill="getDefectColor(box.defect_type_id)"
                    fill-opacity="0.3"
                    stroke="red"
                    stroke-width="2"
                    class="drawn-box"
                  />
                  <rect 
                    v-if="isDrawing"
                    :x="getScaledX(currentBox.x)"
                    :y="getScaledY(currentBox.y)"
                    :width="getScaledWidth(currentBox.width)"
                    :height="getScaledHeight(currentBox.height)"
                    fill="blue"
                    fill-opacity="0.2"
                    stroke="blue"
                    stroke-width="2"
                    stroke-dasharray="5,5"
                  />
                </svg>
              </div>
            </div>
            
            <div v-if="reviewForm.has_details" class="mt-4">
              <div style="margin-bottom: 12px;">
                <el-select v-model="selectedDefectType" placeholder="选择缺陷类型" style="width: 100%;">
                  <el-option 
                    v-for="type in defectTypes" 
                    :key="type.defect_type_id" 
                    :label="type.defect_type_name" 
                    :value="type.defect_type_id" 
                  />
                </el-select>
              </div>
              <div style="background: #F5F7FA; padding: 12px; border-radius: 4px;">
                <p style="color: #606266; font-size: 14px; margin-bottom: 8px;">已标注缺陷 ({{ drawnBoxes.length }}个)：</p>
                <ul style="list-style: none; padding: 0; margin: 0; max-height: 150px; overflow-y: auto;">
                  <li 
                    v-for="(box, index) in drawnBoxes" 
                    :key="index"
                    class="defect-item"
                  >
                    <span>{{ getDefectTypeName(box.defect_type_id) }}</span>
                    <el-button type="text" size="small" @click="removeBox(index)" style="color: #F56C6C; float: right;">删除</el-button>
                  </li>
                </ul>
              </div>
            </div>
            
            <div v-else style="margin-bottom: 12px;">
              <p style="color: #606266; font-size: 14px;">缺陷数量：<span style="color: #303133; font-weight: 500;">{{ reviewDefectDetail.data.defect_count || 0 }}</span></p>
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
            <el-tag :type="viewForm.review_status ? (getStatusType(viewForm.review_status) || 'info') : 'info'">
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
              <div v-if="defectDetail.data.image_base64" class="canvas-container" ref="viewCanvasContainer">
                <img 
                  :src="`data:image/${defectDetail.data.image_format};base64,${defectDetail.data.image_base64}`" 
                  alt="缺陷图片" 
                  class="defect-image"
                  ref="viewDefectImage"
                  draggable="false"
                  @load="onViewImageLoad"
                />
                <svg class="overlay-svg" :width="viewOverlayWidth || '100%'" :height="viewOverlayHeight || '100%'" style="position: absolute; top: 0; left: 0;">
                  <rect 
                    v-for="(box, index) in viewDrawnBoxes" 
                    :key="index"
                    :x="getViewScaledX(box.x)"
                    :y="getViewScaledY(box.y)"
                    :width="getViewScaledWidth(box.width)"
                    :height="getViewScaledHeight(box.height)"
                    :fill="getDefectColor(box.defect_type_id)"
                    fill-opacity="0.3"
                    stroke="red"
                    stroke-width="2"
                  />
                </svg>
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reviewService } from '../../services/review'
import { detectionService } from '../../services/detection'
import { useDefectTypeStore } from '../../stores/defectType'
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

const defectTypeStore = useDefectTypeStore()
const defectTypes = ref([])
const selectedDefectType = ref('')
const drawnBoxes = ref([])
const isDrawing = ref(false)
const currentBox = reactive({ x: 0, y: 0, width: 0, height: 0 })
const startPoint = reactive({ x: 0, y: 0 })
const canvasContainer = ref(null)
const defectImage = ref(null)
const overlaySvg = ref(null)
const overlayWidth = ref(0)
const overlayHeight = ref(0)
const scaleX = ref(1)
const scaleY = ref(1)

const viewDrawnBoxes = ref([])
const viewOverlayWidth = ref(0)
const viewOverlayHeight = ref(0)
const viewScaleX = ref(1)
const viewScaleY = ref(1)
const viewCanvasContainer = ref(null)
const viewDefectImage = ref(null)

const defectColors = {
  1: '#F56C6C',
  2: '#E6A23C',
  3: '#67C23A',
  4: '#409EFF',
  5: '#909399'
}

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
  if (!status || typeof status !== 'string') return 'info'
  const types = { pending: 'warning', completed: 'success', cancel: 'info', timeout: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { pending: '待审查', completed: '已完成', cancel: '已取消', timeout: '已超时' }
  return texts[status] || status
}

const getResultType = (result) => {
  if (!result || typeof result !== 'string') return 'info'
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
  drawnBoxes.value = []
  selectedDefectType.value = ''
  
  try {
    reviewForm.review_task_id = row.review_task_id
    reviewForm.defect_details_id = row.defect_details_id || ''
    reviewForm.record_batch_id = row.record_batch_id || ''
    reviewForm.review_result = 'confirmed'
    reviewForm.has_details = false
    reviewForm.review_comment = ''
    
    await defectTypeStore.loadDefectTypes()
    defectTypes.value = defectTypeStore.defectTypes || []
    
    if (row.defect_details_id) {
      try {
        const defectRes = await detectionService.getDefectDetail(row.defect_details_id)
        reviewDefectDetail.data = defectRes.data
        reviewForm.review_defect_count = defectRes.data?.defect_count || 0
        
        if (defectRes.data?.details) {
          try {
            const details = typeof defectRes.data.details === 'string' ? JSON.parse(defectRes.data.details) : defectRes.data.details
            if (Array.isArray(details)) {
              details.forEach(detail => {
                if (detail.xyhw && detail.defect_type_id) {
                  drawnBoxes.value.push({
                    x: detail.xyhw[0],
                    y: detail.xyhw[1],
                    width: detail.xyhw[2],
                    height: detail.xyhw[3],
                    defect_type_id: detail.defect_type_id,
                    conf: detail.conf || 0.9
                  })
                }
              })
            }
          } catch (e) {
            console.error('Parse details failed:', e)
          }
        }
      } catch (defectError) {
        console.error('Load defect detail failed:', defectError)
        reviewForm.review_defect_count = row.defect_count || 0
      }
    } else {
      reviewForm.review_defect_count = row.defect_count || 0
    }
    
    showReviewDialog.value = true
    
    await nextTick()
    adjustOverlaySize()
  } finally {
    reviewLoading.value = false
  }
}

const adjustOverlaySize = () => {
  if (!defectImage.value) return
  const imgRect = defectImage.value.getBoundingClientRect()
  overlayWidth.value = imgRect.width
  overlayHeight.value = imgRect.height
  
  if (defectImage.value.naturalWidth && defectImage.value.naturalHeight) {
    scaleX.value = imgRect.width / defectImage.value.naturalWidth
    scaleY.value = imgRect.height / defectImage.value.naturalHeight
  }
}

const onImageLoad = () => {
  nextTick(() => {
    adjustOverlaySize()
  })
}

const onViewImageLoad = () => {
  nextTick(() => {
    adjustViewOverlaySize()
  })
}

const adjustViewOverlaySize = () => {
  if (!viewDefectImage.value) return
  const imgRect = viewDefectImage.value.getBoundingClientRect()
  viewOverlayWidth.value = imgRect.width
  viewOverlayHeight.value = imgRect.height
  
  if (viewDefectImage.value.naturalWidth && viewDefectImage.value.naturalHeight) {
    viewScaleX.value = imgRect.width / viewDefectImage.value.naturalWidth
    viewScaleY.value = imgRect.height / viewDefectImage.value.naturalHeight
  }
}

const getViewScaledX = (x) => {
  return x * viewScaleX.value
}

const getViewScaledY = (y) => {
  return y * viewScaleY.value
}

const getViewScaledWidth = (width) => {
  return width * viewScaleX.value
}

const getViewScaledHeight = (height) => {
  return height * viewScaleY.value
}

const getScaledX = (x) => {
  return x * scaleX.value
}

const getScaledY = (y) => {
  return y * scaleY.value
}

const getScaledWidth = (width) => {
  return width * scaleX.value
}

const getScaledHeight = (height) => {
  return height * scaleY.value
}

const getDefectColor = (defectTypeId) => {
  return defectColors[defectTypeId] || '#F56C6C'
}

const getDefectTypeName = (defectTypeId) => {
  const type = defectTypes.value.find(t => t.defect_type_id === defectTypeId)
  return type?.defect_type_name || `未知(${defectTypeId})`
}

const startDraw = (e) => {
  if (!reviewForm.has_details) return
  if (!selectedDefectType.value) {
    ElMessage.warning('请先选择缺陷类型')
    return
  }
  
  isDrawing.value = true
  const rect = canvasContainer.value.getBoundingClientRect()
  const imgRect = defectImage.value.getBoundingClientRect()
  const scaleX = defectImage.value.naturalWidth / imgRect.width
  const scaleY = defectImage.value.naturalHeight / imgRect.height
  
  startPoint.x = (e.clientX - rect.left) * scaleX
  startPoint.y = (e.clientY - rect.top) * scaleY
  
  currentBox.x = startPoint.x
  currentBox.y = startPoint.y
  currentBox.width = 0
  currentBox.height = 0
}

const drawing = (e) => {
  if (!isDrawing.value) return
  
  const rect = canvasContainer.value.getBoundingClientRect()
  const imgRect = defectImage.value.getBoundingClientRect()
  const scaleX = defectImage.value.naturalWidth / imgRect.width
  const scaleY = defectImage.value.naturalHeight / imgRect.height
  
  const currentX = (e.clientX - rect.left) * scaleX
  const currentY = (e.clientY - rect.top) * scaleY
  
  currentBox.x = Math.min(startPoint.x, currentX)
  currentBox.y = Math.min(startPoint.y, currentY)
  currentBox.width = Math.abs(currentX - startPoint.x)
  currentBox.height = Math.abs(currentY - startPoint.y)
}

const endDraw = () => {
  if (!isDrawing.value) return
  
  isDrawing.value = false
  
  if (currentBox.width > 5 && currentBox.height > 5) {
    drawnBoxes.value.push({
      x: currentBox.x,
      y: currentBox.y,
      width: currentBox.width,
      height: currentBox.height,
      defect_type_id: selectedDefectType.value,
      conf: 0.9
    })
    reviewForm.review_defect_count = drawnBoxes.value.length
  }
  
  currentBox.width = 0
  currentBox.height = 0
}

const removeBox = (index) => {
  drawnBoxes.value.splice(index, 1)
  reviewForm.review_defect_count = drawnBoxes.value.length
}

const clearAllBoxes = () => {
  drawnBoxes.value = []
  reviewForm.review_defect_count = 0
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
    const authStore = useAuthStore()
    const currentUser = authStore.currentUser
    
    const updateData = {
      review_status: 'completed',
      review_result: reviewForm.review_result,
      review_defect_count: reviewForm.review_defect_count,
      has_details: reviewForm.has_details,
      review_comment: reviewForm.review_comment || undefined,
      reviewer_id: currentUser?.user_id
    }
    
    if (reviewForm.has_details && drawnBoxes.value.length > 0) {
      updateData.review_details = drawnBoxes.value.map(box => ({
        defect_type_id: box.defect_type_id,
        xyhw: [box.x, box.y, box.width, box.height],
        conf: box.conf || 0.9
      }))
    }
    
    await reviewService.update(reviewForm.review_task_id, updateData)
    ElMessage.success('审查提交成功')
    showReviewDialog.value = false
    drawnBoxes.value = []
    loadData()
  } catch (error) {
    console.error('Submit review failed:', error)
    ElMessage.error('提交审查失败')
  } finally {
    submitLoading.value = false
  }
}

const handleView = async (row) => {
  viewLoading.value = true
  defectDetail.data = null
  viewDrawnBoxes.value = []
  
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
        
        if (defectRes.data?.details) {
          try {
            const details = typeof defectRes.data.details === 'string' ? JSON.parse(defectRes.data.details) : defectRes.data.details
            if (Array.isArray(details)) {
              details.forEach(detail => {
                if (detail.xyhw && detail.defect_type_id) {
                  viewDrawnBoxes.value.push({
                    x: detail.xyhw[0],
                    y: detail.xyhw[1],
                    width: detail.xyhw[2],
                    height: detail.xyhw[3],
                    defect_type_id: detail.defect_type_id,
                    conf: detail.conf || 0.9
                  })
                }
              })
            }
          } catch (e) {
            console.error('Parse details failed:', e)
          }
        }
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

.canvas-container {
  position: relative;
  display: inline-block;
  cursor: crosshair;
  border: 1px solid #DCDFE6;
  border-radius: 4px;
  overflow: hidden;
}

.defect-image {
  display: block;
  max-width: 100%;
  height: auto;
}

.overlay-svg {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.drawn-box {
  cursor: pointer;
  pointer-events: auto;
}

.defect-item {
  padding: 4px 0;
  border-bottom: 1px solid #EBEEF5;
}

.defect-item:last-child {
  border-bottom: none;
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
