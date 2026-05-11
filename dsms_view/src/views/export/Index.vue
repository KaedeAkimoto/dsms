<template>
  <div class="export-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据导出</span>
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
          <el-table-column prop="count" label="数据量" width="120">
            <template #default="{ row }">
              <span v-if="row.count !== null">{{ row.count }}</span>
              <span v-else class="text-gray">加载中...</span>
            </template>
          </el-table-column>
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
          导出全部表
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

const exportTables = reactive([
  { name: 'production_lines', description: '生产线表', count: null },
  { name: 'device_approvals', description: '设备审批表', count: null },
  { name: 'devices', description: '设备表', count: null },
  { name: 'device_status_history', description: '设备状态历史表', count: null },
  { name: 'defect_types', description: '缺陷类型表', count: null },
  { name: 'detection_records', description: '检测记录表', count: null },
  { name: 'defect_details', description: '缺陷详情表', count: null },
  { name: 'review_tasks', description: '审查任务表', count: null },
  { name: 'roles', description: '角色表', count: null },
  { name: 'departments', description: '部门表', count: null },
  { name: 'titles', description: '职称表', count: null },
  { name: 'users', description: '用户表', count: null },
  { name: 'user_operation_logs', description: '用户操作日志表', count: null },
  { name: 'user_messages', description: '用户消息表', count: null },
  { name: 'system_messages', description: '系统消息表', count: null },
  { name: 'announcements', description: '公告表', count: null },
  { name: 'announcement_readers', description: '公告阅读记录表', count: null }
])

const loadTableCounts = async () => {
  loading.value = true
  try {
    const res = await exportService.getTableCounts()
    if (res.data && res.data.counts) {
      const counts = res.data.counts
      exportTables.forEach(table => {
        table.count = counts[table.name] || 0
      })
    }
  } catch (error) {
    console.error('Load table counts failed:', error)
  } finally {
    loading.value = false
  }
}

const handleExport = async (tableName) => {
  exportingTable.value = tableName
  try {
    const res = await exportService.exportTable(tableName)
    
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${tableName}_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success(`成功导出 ${tableName} 表`)
  } catch (error) {
    console.error('Export table failed:', error)
    ElMessage.error(`导出 ${tableName} 表失败`)
  } finally {
    exportingTable.value = ''
  }
}

const handleBatchExport = async () => {
  exportingAll.value = true
  try {
    const res = await exportService.exportAllTables()
    
    const blob = new Blob([res.data], { type: 'application/zip' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `all_tables_${new Date().toISOString().split('T')[0]}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('成功导出全部表')
  } catch (error) {
    console.error('Export all tables failed:', error)
    ElMessage.error('导出全部表失败')
  } finally {
    exportingAll.value = false
  }
}

onMounted(() => {
  loadTableCounts()
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