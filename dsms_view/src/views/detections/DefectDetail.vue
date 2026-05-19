<template>
  <div class="defect-detail-container">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>检测缺陷详情</span>
          <div class="header-actions">
            <el-button 
              v-if="hasDefect && !hasReviewTask" 
              type="warning" 
              size="small" 
              @click="openAssigneeDialog"
              :loading="submitting"
            >
              提交人工检测
            </el-button>
            <el-button type="primary" size="small" @click="goBack">返回列表</el-button>
          </div>
        </div>
      </template>

      <div v-if="loading" class="text-center py-12">
        <div class="loading-spinner"></div>
        <span class="loading-text">加载中...</span>
      </div>

      <div v-else-if="detailData" class="detail-content">
        <el-form :model="detailData" label-width="140px" class="basic-info">
          <h3 class="section-title">检测记录信息</h3>
          <div class="form-row">
            <el-form-item label="批次ID">
              <span class="detail-value">{{ detailData.record_batch_id }}</span>
            </el-form-item>
            <el-form-item label="设备ID">
              <span class="detail-value">{{ detailData.device_id }}</span>
            </el-form-item>
          </div>
          <div class="form-row">
            <el-form-item label="检测总数">
              <span class="detail-value">{{ detailData.detect_count || 0 }}</span>
            </el-form-item>
            <el-form-item label="通过数量">
              <span class="detail-value">{{ detailData.pass_count || 0 }}</span>
            </el-form-item>
          </div>
          <div class="form-row">
            <el-form-item label="缺陷数量">
              <span class="detail-value highlight">
                {{ (detailData.detect_count || 0) - (detailData.pass_count || 0) }}
              </span>
            </el-form-item>
            <el-form-item label="检测状态">
              <el-tag :type="hasDefect ? 'danger' : 'success'">
                {{ hasDefect ? '存在缺陷' : '全部通过' }}
              </el-tag>
            </el-form-item>
          </div>
          <div class="form-row">
            <el-form-item label="创建时间">
              <span class="detail-value">{{ formatDateTime(detailData.created_at) }}</span>
            </el-form-item>
            <el-form-item label="最新上传时间">
              <span class="detail-value">{{ formatDateTime(detailData.latest_upload_at) }}</span>
            </el-form-item>
          </div>
        </el-form>

        <div v-if="detailData.defect_details && detailData.defect_details.length > 0" class="mt-6">
          <h3 class="section-title">缺陷图片</h3>
          <div class="image-grid">
            <div 
              v-for="(defect, index) in detailData.defect_details" 
              :key="defect.defect_details_id"
              class="image-card"
              @click="openImageDialog(index)"
            >
              <div class="image-wrapper">
                <img 
                  :src="getImageSrc(defect.image_base64, defect.image_format)" 
                  :alt="`缺陷图片 ${index + 1}`"
                  class="defect-image"
                />
                <div class="click-hint">点击放大查看</div>
              </div>
              <div class="image-info">
                <div class="info-row">
                  <span class="label">缺陷数:</span>
                  <span class="value">{{ defect.defect_count || 0 }}</span>
                </div>
                <div class="info-row">
                  <span class="label">图片格式:</span>
                  <span class="value">{{ defect.image_format }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="detailData.defect_details && detailData.defect_details.length > 0" class="mt-6">
          <h3 class="section-title">缺陷详情列表</h3>
          <el-table 
            :data="flattenedDefects" 
            style="width: 100%;"
            :header-cell-style="{ background: '#f5f7fa' }"
          >
            <el-table-column prop="imageIndex" label="图片编号" width="100" />
            <el-table-column prop="defect_type_id" label="缺陷类型ID" width="120" />
            <el-table-column prop="defect_type_name" label="缺陷类型名称" />
            <el-table-column prop="position" label="位置(xyhw)" />
            <el-table-column prop="confidence" label="置信度" width="100" />
            <el-table-column prop="created_at" label="创建时间">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="!detailData.defect_details || detailData.defect_details.length === 0" class="mt-6 empty-state">
          <el-empty description="该检测记录无缺陷信息" />
        </div>
      </div>
    </el-card>

    <el-dialog 
      v-model="imageDialog.visible" 
      title="缺陷图片详情" 
      width="90%" 
      :close-on-click-modal="false"
      :before-close="closeImageDialog"
    >
      <div class="image-dialog-content">
        <div class="image-container">
          <div class="image-wrapper-large">
            <img 
              ref="previewImage"
              :src="getImageSrc(currentDefect?.image_base64, currentDefect?.image_format)" 
              :alt="`缺陷图片 ${imageDialog.currentIndex + 1}`"
              class="preview-image"
              @load="onImageLoad"
            />
            <svg v-if="currentDefect?.details && currentDefect.details.length > 0" class="defect-overlay" ref="overlaySvg">
              <g v-for="(detail, idx) in currentDefect.details" :key="idx">
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
        </div>
        
        <div class="image-nav">
          <el-button 
            type="primary" 
            icon="el-icon-arrow-left" 
            @click="prevImage"
            :disabled="imageDialog.currentIndex === 0"
          >上一张</el-button>
          <span class="image-counter">
            {{ imageDialog.currentIndex + 1 }} / {{ detailData?.defect_details?.length || 0 }}
          </span>
          <el-button 
            type="primary" 
            icon="el-icon-arrow-right" 
            @click="nextImage"
            :disabled="imageDialog.currentIndex === (detailData?.defect_details?.length - 1)"
          >下一张</el-button>
        </div>

        <div v-if="currentDefect?.details && currentDefect.details.length > 0" class="defect-info-panel">
          <h4>缺陷标记详情</h4>
          <el-table :data="currentDefectWithNames.details" style="width: 100%">
            <el-table-column prop="defect_type_id" label="缺陷类型ID" width="100" />
            <el-table-column prop="defect_type_name" label="缺陷类型" />
            <el-table-column prop="xyhw" label="位置(xyhw)">
              <template #default="{ row }">
                {{ row.xyhw?.join(', ') || '-' }}
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

    <el-dialog v-model="showAssigneeDialog" title="选择质检员" width="400px">
      <el-form :model="assigneeForm" label-width="100px">
        <el-form-item label="质检员" required>
          <el-select 
            v-model="assigneeForm.assignee_id" 
            placeholder="请选择质检员"
            filterable
            clearable
          >
            <el-option 
              v-for="user in inspectorUsers" 
              :key="user.user_id" 
              :label="user.real_name || user.user_name" 
              :value="user.user_id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssigneeDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitReview">确认提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>import { ref, computed, onMounted, onActivated, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { detectionService } from '../../services/detection';
import { reviewService } from '../../services/review';
import { userService } from '../../services/user';
import { useDefectTypeStore } from '../../stores/defectType';
import { useAuthStore } from '../../stores/auth';
import { formatDateTime } from '../../utils/date';
const router = useRouter();
const route = useRoute();
const defectTypeStore = useDefectTypeStore();
const authStore = useAuthStore();
const loading = ref(false);
const submitting = ref(false);
const detailData = ref(null);
const previewImage = ref(null);
const overlaySvg = ref(null);
const imageDialog = ref({
 visible: false,
 currentIndex: 0
});
const showAssigneeDialog = ref(false);
const assigneeForm = ref({
 assignee_id: ''
});
const inspectorUsers = ref([]);
const hasDefect = computed(() => {
 if (!detailData.value)
 return false;
 const detectCount = detailData.value.detect_count || 0;
 const passCount = detailData.value.pass_count || 0;
 return detectCount > passCount;
});
const hasReviewTask = computed(() => {
 return detailData.value?.review_task_id || detailData.value?.has_review_task;
});
const currentDefect = computed(() => {
 if (!detailData.value?.defect_details)
 return null;
 return detailData.value.defect_details[imageDialog.value.currentIndex];
});
const currentDefectWithNames = computed(() => {
 if (!currentDefect.value)
 return { details: [] };
 const defect = currentDefect.value;
 if (defect.details && Array.isArray(defect.details)) {
 return {
 details: defect.details.map(detail => ({
 ...detail,
 defect_type_name: defectTypeStore.getDefectNameById(detail.defect_type_id) || detail.defect_type_name || '未知'
 }))
 };
 }
 return {
 details: [{
 ...defect,
 defect_type_name: defectTypeStore.getDefectNameById(defect.defect_type_id) || defect.defect_type_name || '未知'
 }]
 };
});
const flattenedDefects = computed(() => {
 const defects = [];
 if (detailData.value?.defect_details) {
 detailData.value.defect_details.forEach((defect, imageIndex) => {
 if (defect.details && defect.details.length > 0) {
 defect.details.forEach((detail) => {
 const defectName = defectTypeStore.getDefectNameById(detail.defect_type_id);
 defects.push({
 imageIndex: imageIndex + 1,
 defect_type_id: detail.defect_type_id,
 defect_type_name: defectName || detail.defect_type_name || '未知',
 position: detail.xyhw ? detail.xyhw.join(', ') : '-',
 confidence: detail.conf ? (detail.conf * 100).toFixed(1) + '%' : '-',
 created_at: defect.created_at
 });
 });
 }
 else {
 defects.push({
 imageIndex: imageIndex + 1,
 defect_type_id: '-',
 defect_type_name: '-',
 position: '-',
 confidence: '-',
 created_at: defect.created_at
 });
 }
 });
 }
 return defects;
});
const getImageSrc = (base64, format) => {
 if (!base64)
 return '';
 const mimeType = format === 'png' ? 'image/png' :
 format === 'webp' ? 'image/webp' : 'image/jpeg';
 return `data:${mimeType};base64,${base64}`;
};
const openImageDialog = (index) => {
 imageDialog.value.currentIndex = index;
 imageDialog.value.visible = true;
 nextTick(() => {
 adjustOverlaySize();
 setTimeout(() => {
 adjustOverlaySize();
 }, 100);
 });
};
const closeImageDialog = () => {
 imageDialog.value.visible = false;
};
const prevImage = () => {
 if (imageDialog.value.currentIndex > 0) {
 imageDialog.value.currentIndex--;
 nextTick(() => {
 adjustOverlaySize();
 });
 }
};
const nextImage = () => {
 if (imageDialog.value.currentIndex < (detailData.value?.defect_details?.length - 1)) {
 imageDialog.value.currentIndex++;
 nextTick(() => {
 adjustOverlaySize();
 });
 }
};
const selectDefect = (index) => {
 ElMessage.info(`选中缺陷 ${index + 1}: ${currentDefectWithNames.value.details[index]?.defect_type_name}`);
};
let pollTimeout = null;
const onImageLoad = () => {
  pollForOverlay();
};
const pollForOverlay = () => {
  if (previewImage.value && overlaySvg.value) {
    adjustOverlaySize();
  } else {
    pollTimeout = setTimeout(() => {
      pollForOverlay();
    }, 50);
  }
};
const adjustOverlaySize = () => {
  if (!previewImage.value || !overlaySvg.value)
    return;
    
  if (pollTimeout) {
    clearTimeout(pollTimeout);
    pollTimeout = null;
  }
  
  const imgRect = previewImage.value.getBoundingClientRect();
  const wrapperRect = previewImage.value.parentElement.getBoundingClientRect();
  const svg = overlaySvg.value;
  svg.setAttribute('width', imgRect.width);
  svg.setAttribute('height', imgRect.height);
  const leftOffset = imgRect.left - wrapperRect.left;
  const topOffset = imgRect.top - wrapperRect.top;
  svg.style.left = `${leftOffset}px`;
  svg.style.top = `${topOffset}px`;
};
const getRectX = (xyhw) => {
  if (!xyhw || !previewImage.value)
    return 0;
  const imgRect = previewImage.value.getBoundingClientRect();
  const scaleX = imgRect.width / previewImage.value.naturalWidth;
  return xyhw[0] * scaleX;
};
const getRectY = (xyhw) => {
  if (!xyhw || !previewImage.value)
    return 0;
  const imgRect = previewImage.value.getBoundingClientRect();
  const scaleY = imgRect.height / previewImage.value.naturalHeight;
  return xyhw[1] * scaleY;
};
const getRectWidth = (xyhw) => {
  if (!xyhw || !previewImage.value)
    return 0;
  const imgRect = previewImage.value.getBoundingClientRect();
  const scaleX = imgRect.width / previewImage.value.naturalWidth;
  return xyhw[2] * scaleX;
};
const getRectHeight = (xyhw) => {
  if (!xyhw || !previewImage.value)
    return 0;
  const imgRect = previewImage.value.getBoundingClientRect();
  const scaleY = imgRect.height / previewImage.value.naturalHeight;
  return xyhw[3] * scaleY;
};
const goBack = () => {
  router.back();
};
const openAssigneeDialog = async () => {
 try {
 const res = await userService.getList({ limit: 1000 });
 inspectorUsers.value = res.data.users || [];
 showAssigneeDialog.value = true;
 } catch (error) {
 console.error('Load users failed:', error);
 ElMessage.error('加载用户列表失败');
 }
};
const handleSubmitReview = async () => {
 if (!detailData.value?.record_batch_id) {
 ElMessage.error('缺少批次ID');
 return;
 }
 
 if (!assigneeForm.value.assignee_id) {
 ElMessage.error('请选择质检员');
 return;
 }
 
 submitting.value = true;
 try {
 const defectDetails = detailData.value.defect_details || [];
 const defectDetailsIds = defectDetails.map(d => d.defect_details_id).filter(Boolean);
 
 if (defectDetailsIds.length === 0) {
 ElMessage.error('没有可提交的缺陷详情');
 submitting.value = false;
 return;
 }
 
 const assigneeId = assigneeForm.value.assignee_id;
 await Promise.all(defectDetailsIds.map(defectDetailsId => {
 return reviewService.create({
 defect_details_id: defectDetailsId,
 assignee_id: assigneeId
 });
 }));
 
 ElMessage.success('提交人工检测成功');
 detailData.value.has_review_task = true;
 showAssigneeDialog.value = false;
 assigneeForm.value.assignee_id = '';
 } catch (error) {
 console.error('Submit review task failed:', error);
 ElMessage.error('提交人工检测失败');
 } finally {
 submitting.value = false;
 }
};
const loadDetail = async () => {
  loading.value = true;
  const recordBatchId = route.params.recordBatchId;
  
  if (!recordBatchId) {
    ElMessage.error('缺少批次ID参数');
    loading.value = false;
    return;
  }
  try {
    const [res] = await Promise.all([
      detectionService.getById(recordBatchId),
      defectTypeStore.loadDefectTypes()
    ]);
    detailData.value = res.data;
  }
  catch (error) {
    console.error('Load defect detail failed:', error);
    ElMessage.error('获取缺陷详情失败');
  }
  finally {
    loading.value = false;
  }
};
onMounted(() => {
  loadDetail();
});

onActivated(() => {
  const currentRecordBatchId = route.params.recordBatchId;
  if (currentRecordBatchId !== detailData.value?.record_batch_id) {
    loadDetail();
  }
});
</script>

<style scoped>
.defect-detail-container {
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

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.form-row {
  display: flex;
  gap: 40px;
}

.detail-value {
  color: #606266;
  font-size: 14px;
}

.detail-value.highlight {
  color: #f56c6c;
  font-weight: bold;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.image-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.image-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
}

.defect-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.click-hint {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  text-align: center;
  padding: 8px;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-card:hover .click-hint {
  opacity: 1;
}

.image-info {
  padding: 12px;
  background: #fafafa;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  color: #909399;
  font-size: 12px;
}

.info-row .value {
  color: #606266;
  font-size: 12px;
  font-weight: 500;
}

.empty-state {
  padding: 40px 0;
}

.image-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  max-height: 60vh;
  overflow: auto;
}

.image-wrapper-large {
  position: relative;
  width: 100%;
  max-height: 60vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.preview-image {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border: 1px solid #ebeef5;
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

.image-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.image-counter {
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

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #909399;
  font-size: 14px;
}
</style>