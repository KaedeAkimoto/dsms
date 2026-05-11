<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #409eff">
            <el-icon :size="32"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.users || 0 }}</div>
            <div class="stat-label">用户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #67c23a">
            <el-icon :size="32"><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.devices || 0 }}</div>
            <div class="stat-label">设备总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #e6a23c">
            <el-icon :size="32"><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.detections || 0 }}</div>
            <div class="stat-label">检测记录</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #f56c6c">
            <el-icon :size="32"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.pendingReviews || 0 }}</div>
            <div class="stat-label">待审查</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最新检测记录</span>
          </template>
          <el-table :data="recentDetections" class="full-width-table">
            <el-table-column prop="record_batch_id" label="批次ID" width="180" show-overflow-tooltip />
            <el-table-column prop="device_id" label="设备ID" width="120" show-overflow-tooltip />
            <el-table-column prop="detect_count" label="检测数" width="80" />
            <el-table-column prop="pass_count" label="通过数" width="80" />
            <el-table-column prop="latest_upload_at" label="时间" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最新公告</span>
          </template>
          <el-table :data="recentAnnouncements" class="full-width-table">
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column prop="created_at" label="发布时间" width="160" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { User, Monitor, DataAnalysis, Warning } from '@element-plus/icons-vue'
import { userService } from '../services/user'
import { deviceService } from '../services/device'
import { detectionService } from '../services/detection'
import { reviewService } from '../services/review'
import { messageService } from '../services/message'
import { formatDateTime, formatUtcToCst } from '../utils/date'

const stats = ref({
  users: 0,
  devices: 0,
  detections: 0,
  pendingReviews: 0
})

const recentDetections = ref([])
const recentAnnouncements = ref([])

onMounted(async () => {
  try {
    const [usersRes, devicesRes, detectionsRes, reviewsRes, announcementsRes] = await Promise.all([
      userService.getList({ limit: 1 }),
      deviceService.getList({ limit: 1 }),
      detectionService.getList({ limit: 10 }),
      reviewService.getTasks({ status: 'pending', limit: 1 }),
      messageService.getMyAnnouncements({ limit: 5 })
    ])

    stats.value.users = usersRes.data.total || 0
    stats.value.devices = devicesRes.data.total || 0
    stats.value.detections = detectionsRes.data.total || 0
    stats.value.pendingReviews = reviewsRes.data.total || 0
    recentDetections.value = (detectionsRes.data.records || []).map(record => ({
      ...record,
      latest_upload_at: formatUtcToCst(record.latest_upload_at)
    }))
    recentAnnouncements.value = (announcementsRes.data.announcements || []).map(announcement => ({
      ...announcement,
      created_at: formatDateTime(announcement.created_at)
    }))
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.full-width-table {
  width: 100%;
}

:deep(.el-card__body) {
  width: 100%;
}

:deep(.el-table) {
  width: 100% !important;
}
</style>
