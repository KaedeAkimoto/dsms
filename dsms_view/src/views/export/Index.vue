<template>
  <div class="export-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据导出</span>
          <div class="format-select">
            <span class="text-gray">导出格式：</span>
            <el-select 
              v-model="selectedFormat" 
              style="width: 120px;"
              size="small"
            >
              <el-option 
                v-for="format in exportFormats" 
                :key="format.value" 
                :label="format.label" 
                :value="format.value" 
              />
            </el-select>
          </div>
        </div>
      </template>

      <div class="table-wrapper">
        <el-table 
          :data="exportTables" 
          v-loading="loading" 
          style="width: 100%;"
        >
          <el-table-column prop="name" label="表名" width="200" />
          <el-table-column prop="description" label="说明" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                @click="handleExport(row.name)"
                :loading="exportingTable === row.name"
              >
                导出
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="batch-export">
        <el-button 
          type="success" 
          size="large" 
          @click="handleBatchExport"
          :loading="exportingAll"
        >
          <el-icon><Download /></el-icon>
          导出全部数据
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { exportService } from '../../services/export'

const loading = ref(false)
const exportingTable = ref('')
const exportingAll = ref(false)
const exportTables = ref([])

const tableDescriptions = {
  production_lines: '生产线表',
  device_approvals: '设备审批表',
  devices: '设备表',
  device_status_history: '设备状态历史表',
  defect_types: '缺陷类型表',
  detection_records: '检测记录表',
  defect_details: '缺陷详情表',
  review_tasks: '审查任务表',
  roles: '角色表',
  departments: '部门表',
  titles: '职称表',
  users: '用户表',
  user_operation_logs: '用户操作日志表',
  user_messages: '用户消息表',
  system_messages: '系统消息表',
  announcements: '公告表',
  announcement_readers: '公告阅读记录表'
}

const exportFormats = [
  { label: 'JSON', value: 'json', ext: '.json' },
  { label: 'CSV', value: 'csv', ext: '.csv' },
  { label: 'Excel', value: 'excel', ext: '.xlsx' }
]

const selectedFormat = ref('json')

const loadExportTables = async () => {
  loading.value = true
  try {
    const res = await exportService.getExportTables()
    
    const tables = res.data?.tables || res.tables
    if (tables && Array.isArray(tables)) {
      exportTables.value = tables.map(tableName => ({
        name: tableName,
        description: tableDescriptions[tableName] || tableName
      }))
    } else {
      exportTables.value = Object.entries(tableDescriptions).map(([name, description]) => ({
        name,
        description
      }))
    }
  } catch (error) {
    exportTables.value = Object.entries(tableDescriptions).map(([name, description]) => ({
      name,
      description
    }))
  } finally {
    loading.value = false
  }
}

const handleExport = async (tableName) => {
  exportingTable.value = tableName
  try {
    const formatInfo = exportFormats.find(f => f.value === selectedFormat.value)
    const res = await exportService.exportTable(tableName, selectedFormat.value)
    
    const blob = new Blob([res.data], { type: getContentType(selectedFormat.value) })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${tableName}_${new Date().toISOString().split('T')[0]}${formatInfo.ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success(`成功导出 ${tableName} 表`)
  } catch (error) {
    ElMessage.error(`导出 ${tableName} 表失败`)
  } finally {
    exportingTable.value = ''
  }
}

const handleBatchExport = async () => {
  exportingAll.value = true
  try {
    const formatInfo = exportFormats.find(f => f.value === selectedFormat.value)
    const res = await exportService.exportAllTables(selectedFormat.value)
    
    const blob = new Blob([res.data], { type: getContentType(selectedFormat.value) })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `all_data_${new Date().toISOString().split('T')[0]}${formatInfo.ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('成功导出全部数据')
  } catch (error) {
    ElMessage.error('导出全部数据失败')
  } finally {
    exportingAll.value = false
  }
}

const getContentType = (format) => {
  switch (format) {
    case 'json':
      return 'application/json;charset=utf-8;'
    case 'csv':
      return 'text/csv;charset=utf-8;'
    case 'excel':
      return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    default:
      return 'application/octet-stream'
  }
}

onMounted(() => {
  loadExportTables()
})
</script>

<style scoped>
.export-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.format-select {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-wrapper {
  margin-bottom: 20px;
}

.text-gray {
  color: #999;
}

.batch-export {
  display: flex;
  justify-content: center;
  padding: 20px;
}
</style>