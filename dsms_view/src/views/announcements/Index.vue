<template>
  <div class="announcements-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公告管理</span>
          <el-button type="primary" @click="showCreateDialog = true">发布公告</el-button>
        </div>
      </template>

      <div class="card-grid">
        <el-card
          v-for="item in tableData"
          :key="item.announcement_id"
          class="announcement-card"
          shadow="hover"
          @click="handleView(item)"
        >
          <div class="card-content">
            <div class="card-title">
              <el-tag :type="getReceiverTypeColor(item.receiver_type)" size="small">
                {{ getReceiverTypeText(item.receiver_type) }}
              </el-tag>
              <span class="card-time">{{ item.created_at }}</span>
            </div>
            <div class="card-text">{{ item.content }}</div>
            <div class="card-footer">
              <span class="card-author">{{ getUserName(item.send_user) }}</span>
              <div class="card-buttons">
                <el-button type="primary" size="small" :disabled="isAnnouncementConfirmed(item.announcement_id) || isAnnouncementExpired(item.expired)" @click.stop="handleConfirm(item)">
  {{ isAnnouncementExpired(item.expired) ? '已结束' : (isAnnouncementConfirmed(item.announcement_id) ? '已确认' : '确认') }}
</el-button>
                <el-button type="danger" size="small" @click.stop="handleDelete(item)">删除</el-button>
              </div>
            </div>
          </div>
        </el-card>

        <div v-if="tableData.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无公告" />
        </div>
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="发布公告" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="接收类型" prop="receiver_type">
          <el-select v-model="createForm.receiver_type" @change="handleReceiverTypeChange">
            <el-option label="全部" value="all" />
            <el-option label="按部门" value="department" />
            <el-option label="按角色" value="role" />
            <el-option label="按职称" value="title" />
          </el-select>
        </el-form-item>
        <el-form-item label="接收目标" v-if="createForm.receiver_type !== 'all'">
          <el-select v-model="createForm.receive_target" placeholder="请选择目标">
            <el-option 
              v-for="option in currentTargetOptions" 
              :key="option.value" 
              :label="option.label" 
              :value="option.value" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="createForm.content" type="textarea" :rows="4" placeholder="请输入公告内容" />
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="createForm.expired"
            type="datetime"
            placeholder="选择过期时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">发布</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="公告详情" width="600px">
      <el-form label-width="100px">
        <el-form-item label="公告ID">
          <el-input v-model="detail.announcement_id" disabled />
        </el-form-item>
        <el-form-item label="接收类型">
          <el-tag :type="getReceiverTypeColor(detail.receiver_type)">
            {{ getReceiverTypeText(detail.receiver_type) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="发布人">
          <el-input v-model="detail.send_user_display" disabled />
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input v-model="detail.send_user_id" disabled :append="copyButton" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="detail.content" type="textarea" :rows="6" disabled :append="copyContentButton" />
        </el-form-item>
        <el-form-item label="发布时间">
          <el-input v-model="detail.created_at" disabled />
        </el-form-item>
        <el-form-item label="过期时间">
          <el-input v-model="detail.expired" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" :disabled="isAnnouncementConfirmed(detail.announcement_id) || isAnnouncementExpired(detail.expired)" @click="handleConfirm(detail)">
  {{ isAnnouncementExpired(detail.expired) ? '已结束' : (isAnnouncementConfirmed(detail.announcement_id) ? '已确认' : '确认') }}
</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'Announcements' })
import { ref, reactive, computed, onMounted, onActivated } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { messageService } from '../../services/message'
import { userService, departmentService, titleService, roleService } from '../../services/user'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const tableData = ref([])
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)

const userCache = ref({})
const roleMap = ref({})

const copyButton = {
  icon: 'Copy',
  onClick: async () => {
    try {
      await navigator.clipboard.writeText(detail.send_user_id)
      ElMessage.success('复制成功')
    } catch (error) {
      console.error('Copy failed:', error)
      ElMessage.error('复制失败')
    }
  }
}

const copyContentButton = {
  icon: 'Copy',
  onClick: async () => {
    try {
      await navigator.clipboard.writeText(detail.content)
      ElMessage.success('复制成功')
    } catch (error) {
      console.error('Copy content failed:', error)
      ElMessage.error('复制失败')
    }
  }
}

const departmentMap = ref({})
const titleMap = ref({})
const confirmedAnnouncements = ref(new Set())

const loadConfirmedFromStorage = () => {
  const stored = localStorage.getItem('confirmedAnnouncements')
  if (stored) {
    try {
      const ids = JSON.parse(stored)
      ids.forEach(id => confirmedAnnouncements.value.add(id))
    } catch (e) {
      console.error('Load confirmed announcements from storage failed:', e)
    }
  }
}

const saveConfirmedToStorage = () => {
  const ids = Array.from(confirmedAnnouncements.value)
  localStorage.setItem('confirmedAnnouncements', JSON.stringify(ids))
}

const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const createForm = reactive({
  receiver_type: 'all',
  receive_target: null,
  content: '',
  expired: ''
})

const currentTargetOptions = computed(() => {
  const type = createForm.receiver_type
  if (type === 'department') {
    return Object.entries(departmentMap.value).map(([id, name]) => ({
      value: Number(id),
      label: `${id} - ${name}`
    }))
  } else if (type === 'role') {
    return Object.entries(roleMap.value).map(([id, name]) => ({
      value: Number(id),
      label: `${id} - ${name}`
    }))
  } else if (type === 'title') {
    return Object.entries(titleMap.value).map(([id, name]) => ({
      value: Number(id),
      label: `${id} - ${name}`
    }))
  }
  return []
})

const detail = reactive({
  announcement_id: '',
  receiver_type: '',
  content: '',
  send_user: '',
  send_user_display: '',
  created_at: '',
  expired: ''
})

const createRules = {
  content: [{ required: true, message: '请输入公告内容', trigger: 'blur' }]
}

const handleReceiverTypeChange = () => {
  createForm.receive_target = null
}

const getReceiverTypeText = (type) => {
  const map = {
    all: '所有人',
    department: '部门公告',
    role: '角色公告',
    title: '职称公告'
  }
  return map[type] || type
}

const getReceiverTypeColor = (type) => {
  const map = {
    all: 'danger',
    department: 'primary',
    role: 'success',
    title: 'warning'
  }
  return map[type] || 'info'
}

const formatUserName = (user) => {
  if (!user) return '未知用户'
  const userName = user.real_name || user.user_name || '未知用户'
  const deptName = user.department_name || '暂无部门'
  const titleName = user.title_name || '暂无职称'
  return `${userName}-${deptName}-${titleName}`
}

const getUserName = (userId) => {
  const user = userCache.value[userId]
  return formatUserName(user)
}

const isAnnouncementConfirmed = (announcementId) => {
  return confirmedAnnouncements.value.has(announcementId)
}

const isAnnouncementExpired = (expiredTime) => {
  if (!expiredTime) return false
  return new Date(expiredTime) < new Date()
}

const loadConfirmedAnnouncements = async () => {
  if (tableData.value.length === 0) return
  
  confirmedAnnouncements.value.clear()
  try {
    const checkStatusPromises = tableData.value.map(async ann => {
      try {
        const statusRes = await messageService.getAnnouncementReadStatus(ann.announcement_id)
        if (statusRes.data.is_read === true) {
          confirmedAnnouncements.value.add(ann.announcement_id)
        }
      } catch (error) {
        console.error(`Check status for announcement ${ann.announcement_id} failed:`, error)
      }
    })
    
    await Promise.all(checkStatusPromises)
  } catch (error) {
    console.error('Load confirmed announcements failed:', error)
  }
}

const loadAllUsers = async () => {
  try {
    let skip = 0
    const limit = 1000
    while (true) {
      const res = await userService.getList({ skip, limit })
      const users = res.data.users || []
      for (const user of users) {
        if (user.role_id) {
          user.role_name = roleMap.value[user.role_id] || user.role_id
        }
        if (user.department_id) {
          user.department_name = departmentMap.value[user.department_id] || user.department_id
        }
        if (user.title_id) {
          user.title_name = titleMap.value[user.title_id] || user.title_id
        }
        user.last_login = formatDateTime(user.last_login)
        userCache.value[user.user_id] = user
      }
      if (users.length < limit) break
      skip += limit
    }
  } catch (error) {
    console.error('Load all users failed:', error)
  }
}

const loadAllRoles = async () => {
  try {
    let skip = 0
    const limit = 1000
    while (true) {
      const res = await roleService.getList({ skip, limit })
      const roles = res.data.roles || []
      for (const role of roles) {
        roleMap.value[role.role_id] = role.role_name
      }
      if (roles.length < limit) break
      skip += limit
    }
  } catch (error) {
    console.error('Load roles failed:', error)
  }
}

const loadAllDepartments = async () => {
  try {
    let skip = 0
    const limit = 1000
    while (true) {
      const res = await departmentService.getList({ skip, limit })
      const depts = res.data.departments || []
      for (const dept of depts) {
        departmentMap.value[dept.department_id] = dept.department_name
      }
      if (depts.length < limit) break
      skip += limit
    }
  } catch (error) {
    console.error('Load departments failed:', error)
  }
}

const loadAllTitles = async () => {
  try {
    let skip = 0
    const limit = 1000
    while (true) {
      const res = await titleService.getList({ skip, limit })
      const titles = res.data.titles || []
      for (const title of titles) {
        titleMap.value[title.title_id] = title.title_name
      }
      if (titles.length < limit) break
      skip += limit
    }
  } catch (error) {
    console.error('Load titles failed:', error)
  }
}

const allAnnouncements = ref([])

const loadAllAnnouncements = async () => {
  const cache = messageService.getAnnouncementCache()
  if (cache.loaded && cache.announcements.length > 0) {
    allAnnouncements.value = [...cache.announcements]
    await loadConfirmedAnnouncements()
    return
  }
  
  allAnnouncements.value = []
  let skip = 0
  const limit = 100
  
  while (true) {
    const res = await messageService.getAnnouncements({ skip, limit })
    const announcements = res.data.announcements || []
    allAnnouncements.value = [...allAnnouncements.value, ...announcements]
    
    if (announcements.length < limit) break
    skip += limit
  }
  
  messageService.setAnnouncements([...allAnnouncements.value])
  messageService.setAnnouncementLoaded()
  
  await loadConfirmedAnnouncements()
}

const loadData = async () => {
  loading.value = true
  try {
    if (allAnnouncements.value.length === 0) {
      await loadAllAnnouncements()
    }
    
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    const paginatedData = allAnnouncements.value.slice(start, end)
    
    for (const announcement of paginatedData) {
      announcement.created_at = formatDateTime(announcement.created_at)
      announcement.expired = formatDateTime(announcement.expired)
    }
    
    tableData.value = paginatedData
    total.value = allAnnouncements.value.length
  } catch (error) {
    console.error('Load announcements failed:', error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  allAnnouncements.value = []
  loadData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadData()
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await messageService.createAnnouncement({
          receiver_type: createForm.receiver_type,
          receive_target: createForm.receive_target || undefined,
          content: createForm.content,
          expired: createForm.expired || undefined
        })
        ElMessage.success('公告发布成功')
        showCreateDialog.value = false
        createForm.content = ''
        createForm.receiver_type = 'all'
        createForm.receive_target = null
        createForm.expired = ''
        
        allAnnouncements.value = []
        messageService.setAnnouncementLoaded(false)
        loadData()
      } catch (error) {
        console.error('Create announcement failed:', error)
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleView = (row) => {
  Object.assign(detail, row)
  detail.created_at = formatDateTime(row.created_at)
  detail.expired = formatDateTime(row.expired)
  detail.send_user_display = getUserName(row.send_user)
  detail.send_user_id = row.send_user || '未知'
  
  showDetailDialog.value = true
}

const handleConfirm = async (row) => {
  try {
    await messageService.markAnnouncementAsRead(row.announcement_id)
    confirmedAnnouncements.value.add(row.announcement_id)
    saveConfirmedToStorage()
    ElMessage.success('确认公告成功')
    showDetailDialog.value = false
    loadData()
    
    window.dispatchEvent(new CustomEvent('announcement-confirmed'))
  } catch (error) {
    console.error('Confirm announcement failed:', error)
    ElMessage.error('确认公告失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除该公告吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await messageService.deleteAnnouncement(row.announcement_id)
    ElMessage.success('公告删除成功')
    confirmedAnnouncements.value.delete(row.announcement_id)
    
    allAnnouncements.value = allAnnouncements.value.filter(ann => ann.announcement_id !== row.announcement_id)
    tableData.value = tableData.value.filter(ann => ann.announcement_id !== row.announcement_id)
    total.value = allAnnouncements.value.length
    
    if (tableData.value.length === 0 && currentPage.value > 1) {
      currentPage.value--
      loadData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete announcement failed:', error)
      ElMessage.error('公告删除失败')
    }
  }
}

onMounted(async () => {
  if (tableData.value.length === 0) {
    loadConfirmedFromStorage()
    loadData()
    
    setTimeout(async () => {
      await Promise.all([
        loadAllRoles(),
        loadAllDepartments(),
        loadAllTitles()
      ])
      await loadAllUsers()
      await loadConfirmedAnnouncements()
    }, 100)
  }
})
</script>

<style scoped>
.announcements-container {
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

.card-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.announcement-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.announcement-card:hover {
  transform: translateY(-2px);
}

.card-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-time {
  font-size: 12px;
  color: #909399;
}

.card-text {
  flex: 1;
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  margin-bottom: 12px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #EBEEF5;
}

.card-author {
  font-size: 13px;
  color: #606266;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-buttons {
  display: flex;
  gap: 8px;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 60px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination-wrapper {
  padding: 16px 0 0 0;
  border-top: 1px solid #EBEEF5;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}
</style>
