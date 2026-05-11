<template>
  <div class="defect-list-container">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>缺陷详情列表</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="handleRefresh">
              <span>刷新</span>
            </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="设备ID">
          <el-input v-model="searchForm.device_id" placeholder="请输入设备ID" clearable />
        </el-form-item>
        <el-form-item label="批次ID">
          <el-input v-model="searchForm.record_batch_id" placeholder="请输入批次ID" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div v-if="loading" v-loading="loading" class="loading-container">
      </div>

      <div v-else-if="defectRecords.length === 0" class="empty-container">
        <el-empty description="暂无缺陷记录" />
      </div>

      <div v-else class="defect-grid">
        <div 
          v-for="record in defectRecords" 
          :key="record.record_batch_id"
          class="defect-card"
        >
          <div class="card-header">
            <div class="record-info">
              <span class="batch-id" :title="record.record_batch_id">
                {{ truncateText(record.record_batch_id, 16) }}
              </span>
              <el-tag size="small" :type="getStatusType(record)">
                {{ getStatusText(record) }}
              </el-tag>
            </div>
            <div class="device-id">设备: {{ truncateText(record.device_id, 12) }}</div>
          </div>

          <div class="card-body">
            <div v-if="record.defect_details && record.defect_details.length > 0" class="image-gallery">
              <div 
                v-for="(defect, imgIndex) in record.defect_details.slice(0, 4)" 
                :key="defect.defect_details_id"
                class="gallery-item"
                @click="handleImageClick(record, imgIndex)"
              >
                <img 
                  :src="getImageSrc(defect.image_base64, defect.image_format)" 
                  :alt="`缺陷图片 ${imgIndex + 1}`"
                  class="gallery-image"
                />
                <div v-if="imgIndex === 3 && record.defect_details.length > 4" class="image-overlay">
                  +{{ record.defect_details.length - 4 }}
                </div>
                <div class="gallery-hint">点击查看</div>
              </div>
            </div>
            <div v-else class="no-images">
              <span>无缺陷图片</span>
            </div>
          </div>

          <div class="card-footer">
            <div class="stats-row">
              <div class="stat-item">
                <span class="stat-label">检测数</span>
                <span class="stat-value">{{ record.detect_count || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">通过数</span>
                <span class="stat-value pass">{{ record.pass_count || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">缺陷数</span>
                <span class="stat-value defect">{{ getDefectCount(record) }}</span>
              </div>
            </div>
            <div class="time-info">
              <span class="time-label">最新上传:</span>
              <span class="time-value">{{ formatUtcToCst(record.latest_upload_at) }}</span>
            </div>
          </div>

          <div class="card-actions">
            <el-button type="primary" size="small" @click="handleViewDetail(record)">
              查看详情
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="!loading && defectRecords.length > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          :total="pagination.total"
          :page-sizes="[12, 24, 48, 96]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog 
      v-model="imageDialog.visible" 
      width="90%"
      :title="`缺陷图片 - ${imageDialog.recordBatchId}`"
      :close-on-click-modal="true"
      :before-close="closeImageDialog"
    >
      <div v-if="imageDialog.loading" v-loading="imageDialog.loading" class="text-center py-8">
      </div>
      <div v-else-if="imageDialog.images && imageDialog.images.length > 0" class="image-dialog-content">
        <div class="image-carousel">
          <div class="carousel-image-wrapper">
            <img 
              ref="previewImage"
              :src="getImageSrc(imageDialog.images[imageDialog.currentIndex].image_base64, imageDialog.images[imageDialog.currentIndex].image_format)" 
              alt="缺陷图片"
              class="carousel-image"
              @load="onImageLoad"
            />
            <svg v-if="getCurrentDefectDetails.length > 0" class="defect-overlay" ref="overlaySvg">
              <g v-for="(detail, idx) in getCurrentDefectDetails" :key="idx">
                <rect 
                  :x="getRectX(detail.xyhw)"
                  :y="getRectY(detail.xyhw)"
                  :width="getRectWidth(detail.xyhw)"
                  :height="getRectHeight(detail.xyhw)"
                  fill="transparent"
                  stroke="#ff4d4f"
                  stroke-width="2"
                  class="defect-rect"
                  :data-defect-index="idx"
                  @click.stop="selectDefect(idx)"
                />
                <text 
                  :x="getRectX(detail.xyhw)"
                  :y="getRectY(detail.xyhw) - 5"
                  fill="#ff4d4f"
                  font-size="14"
                  font-weight="bold"
                  class="defect-label"
                >
                  {{ defectTypeStore.getDefectNameById(detail.defect_type_id) || '未知' }}
                </text>
              </g>
            </svg>
          </div>
          <div class="carousel-controls">
            <el-button 
              :disabled="imageDialog.currentIndex === 0" 
              @click="prevImage"
            >
              上一张
            </el-button>
            <span class="carousel-indicator">
              {{ imageDialog.currentIndex + 1 }} / {{ imageDialog.images.length }}
            </span>
            <el-button 
              :disabled="imageDialog.currentIndex === imageDialog.images.length - 1" 
              @click="nextImage"
            >
              下一张
            </el-button>
          </div>
        </div>
        <div v-if="getCurrentDefectDetails.length > 0" class="defect-info-panel">
          <h4>缺陷详情</h4>
          <el-table :data="getDialogDefectDetails" style="width: 100%">
            <el-table-column prop="defect_type_id" label="缺陷类型ID" width="100" />
            <el-table-column prop="defect_type_name" label="缺陷类型" />
            <el-table-column prop="xyhw" label="位置(xyhw)">
              <template #default="{ row }">
                {{ row.xyhw ? row.xyhw.join(', ') : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="conf" label="置信度">
              <template #default="{ row }">
                {{ row.conf ? (row.conf * 100).toFixed(1) + '%' : '-' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { detectionService } from '../../services/detection'
import { useDefectTypeStore } from '../../stores/defectType'
import { formatDateTime, formatUtcToCst } from '../../utils/date'

const router = useRouter()
const defectTypeStore = useDefectTypeStore()
const loading = ref(false)
const defectRecords = ref([])
const previewImage = ref(null)
const overlaySvg = ref(null)

const searchForm = reactive({
  device_id: '',
  record_batch_id: ''
})

const pagination = reactive({
  page: 1,
  limit: 24,
  total: 0
})

const imageDialog = reactive({
  visible: false,
  loading: false,
  recordBatchId: '',
  images: [],
  currentIndex: 0
})

const getCurrentDefectDetails = computed(() => {
  if (!imageDialog.images || imageDialog.images.length === 0) return []
  const currentImage = imageDialog.images[imageDialog.currentIndex]
  if (!currentImage) return []
  if (currentImage.details && Array.isArray(currentImage.details)) {
    return currentImage.details
  }
  return [currentImage]
})

const getDefectCount = (record) => {
  return (record.detect_count || 0) - (record.pass_count || 0)
}

const getStatusType = (record) => {
  const defectCount = getDefectCount(record)
  return defectCount > 0 ? 'danger' : 'success'
}

const getStatusText = (record) => {
  const defectCount = getDefectCount(record)
  return defectCount > 0 ? '存在缺陷' : '全部通过'
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const getImageSrc = (base64, format) => {
  if (!base64) return ''
  const mimeType = format === 'png' ? 'image/png' :
                   format === 'webp' ? 'image/webp' : 'image/jpeg'
  return `data:${mimeType};base64,${base64}`
}

const getDialogDefectDetails = computed(() => {
  if (!imageDialog.images || imageDialog.images.length === 0) return []
  const currentImage = imageDialog.images[imageDialog.currentIndex]
  if (!currentImage) return []
  
  if (currentImage.details && Array.isArray(currentImage.details)) {
    return currentImage.details.map(detail => ({
      ...detail,
      defect_type_name: defectTypeStore.getDefectNameById(detail.defect_type_id) || detail.defect_type_name || '未知'
    }))
  }
  
  return [{
    ...currentImage,
    defect_type_name: defectTypeStore.getDefectNameById(currentImage.defect_type_id) || currentImage.defect_type_name || '未知'
  }]
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    }
    
    if (searchForm.device_id) {
      const res = await detectionService.getByDevice(searchForm.device_id, params)
      defectRecords.value = res.data.records || []
      pagination.total = res.data.total || 0
    } else if (searchForm.record_batch_id) {
      const res = await detectionService.getById(searchForm.record_batch_id)
      defectRecords.value = res.data ? [res.data] : []
      pagination.total = res.data ? 1 : 0
    } else {
      const res = await detectionService.getList(params)
      const records = res.data.records || []
      defectRecords.value = records.filter(r => getDefectCount(r) > 0)
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('Load defect list failed:', error)
    ElMessage.error('获取缺陷列表失败')
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
  searchForm.record_batch_id = ''
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

const handleRefresh = () => {
  loadData()
}

const handleViewDetail = (record) => {
  router.push(`/detections/defect-detail/${record.record_batch_id}`)
}

const handleImageClick = async (record, imgIndex) => {
  imageDialog.visible = true
  imageDialog.loading = false
  imageDialog.recordBatchId = record.record_batch_id
  imageDialog.images = record.defect_details || []
  imageDialog.currentIndex = imgIndex
  nextTick(() => {
    adjustOverlaySize()
    setTimeout(() => {
      adjustOverlaySize()
    }, 100)
    setTimeout(() => {
      adjustOverlaySize()
    }, 300)
  })
}

const closeImageDialog = () => {
  imageDialog.visible = false
}

const prevImage = () => {
  if (imageDialog.currentIndex > 0) {
    imageDialog.currentIndex--
    nextTick(() => {
      adjustOverlaySize()
    })
  }
}

const nextImage = () => {
  if (imageDialog.currentIndex < imageDialog.images.length - 1) {
    imageDialog.currentIndex++
    nextTick(() => {
      adjustOverlaySize()
    })
  }
}

const selectDefect = (index) => {
  const details = getDialogDefectDetails.value
  ElMessage.info(`选中缺陷 ${index + 1}: ${details[index]?.defect_type_name}`)
}

const onImageLoad = () => {
  pollForOverlay()
}

let pollTimeout = null

const pollForOverlay = () => {
  if (previewImage.value && overlaySvg.value) {
    adjustOverlaySize()
  } else {
    pollTimeout = setTimeout(() => {
      pollForOverlay()
    }, 50)
  }
}

const adjustOverlaySize = () => {
  if (!previewImage.value || !overlaySvg.value) return
  
  if (pollTimeout) {
    clearTimeout(pollTimeout)
    pollTimeout = null
  }
  
  const imgRect = previewImage.value.getBoundingClientRect()
  const wrapperRect = previewImage.value.parentElement.getBoundingClientRect()
  const svg = overlaySvg.value
  svg.setAttribute('width', imgRect.width)
  svg.setAttribute('height', imgRect.height)
  const leftOffset = imgRect.left - wrapperRect.left
  const topOffset = imgRect.top - wrapperRect.top
  svg.style.left = `${leftOffset}px`
  svg.style.top = `${topOffset}px`
}

const getRectX = (xyhw) => {
  if (!xyhw || !previewImage.value) return 0
  const imgRect = previewImage.value.getBoundingClientRect()
  const scaleX = imgRect.width / previewImage.value.naturalWidth
  return xyhw[0] * scaleX
}

const getRectY = (xyhw) => {
  if (!xyhw || !previewImage.value) return 0
  const imgRect = previewImage.value.getBoundingClientRect()
  const scaleY = imgRect.height / previewImage.value.naturalHeight
  return xyhw[1] * scaleY
}

const getRectWidth = (xyhw) => {
  if (!xyhw || !previewImage.value) return 0
  const imgRect = previewImage.value.getBoundingClientRect()
  const scaleX = imgRect.width / previewImage.value.naturalWidth
  return xyhw[2] * scaleX
}

const getRectHeight = (xyhw) => {
  if (!xyhw || !previewImage.value) return 0
  const imgRect = previewImage.value.getBoundingClientRect()
  const scaleY = imgRect.height / previewImage.value.naturalHeight
  return xyhw[3] * scaleY
}

onMounted(() => {
  Promise.all([
    loadData(),
    defectTypeStore.loadDefectTypes()
  ])
})
</script>

<style scoped>
.defect-list-container {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-form {
  margin-bottom: 20px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
}

.defect-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.defect-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.defect-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.card-header {
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

.record-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-id {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.device-id {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.card-body {
  padding: 12px;
}

.image-gallery {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.gallery-item {
  position: relative;
  aspect-ratio: 1;
  cursor: pointer;
  overflow: hidden;
  border-radius: 4px;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
  font-size: 24px;
  font-weight: bold;
}

.gallery-hint {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  text-align: center;
  padding: 4px;
  font-size: 10px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.gallery-item:hover .gallery-hint {
  opacity: 1;
}

.no-images {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
  background: #fafafa;
  border-radius: 4px;
  color: #909399;
  font-size: 14px;
}

.card-footer {
  padding: 12px 16px;
  background: #fafafa;
  border-top: 1px solid #ebeef5;
}

.stats-row {
  display: flex;
  gap: 24px;
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
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stat-value.pass {
  color: #67c23a;
}

.stat-value.defect {
  color: #f56c6c;
}

.time-info {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.time-label {
  margin-right: 4px;
}

.time-value {
  color: #606266;
}

.card-actions {
  padding: 12px 16px;
  display: flex;
  justify-content: flex-end;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.image-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-carousel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.carousel-image-wrapper {
  position: relative;
  max-height: 60vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow: auto;
}

.carousel-image {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.defect-overlay {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.defect-rect {
  pointer-events: auto;
  cursor: pointer;
}

.defect-rect:hover {
  stroke-width: 3;
  filter: drop-shadow(0 0 4px rgba(255, 77, 79, 0.8));
}

.defect-label {
  pointer-events: none;
  text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
}

.carousel-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.carousel-indicator {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.defect-info-panel {
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
}

.defect-info-panel h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
</style>