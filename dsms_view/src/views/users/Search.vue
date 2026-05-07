<template>
  <div class="users-search-container">
    <el-card style="display: flex; flex-direction: column; height: calc(100vh - 160px);">
      <template #header>
        <div class="card-header">
          <span>用户查找</span>
        </div>
      </template>

      <div class="search-form">
        <el-input
          v-model="searchQuery"
          placeholder="输入工号、用户ID或关键词进行查找"
          style="width: 400px; margin-right: 16px;"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">查找</el-button>
        <el-button @click="handleClear">清空结果</el-button>
      </div>

      <div class="search-type">
        <el-radio-group v-model="searchType" size="small">
          <el-radio-button label="exact">精准查找</el-radio-button>
          <el-radio-button label="fuzzy">模糊查找</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="searchResult && searchType === 'exact'" class="result-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">
            <div style="display: flex; gap: 8px; align-items: center;">
              <span>{{ searchResult.user_id }}</span>
              <el-button size="small" @click="copyToClipboard(searchResult.user_id, '用户ID')">复制</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="用户名">{{ searchResult.user_name }}</el-descriptions-item>
          <el-descriptions-item label="真实姓名">{{ searchResult.real_name }}</el-descriptions-item>
          <el-descriptions-item label="工号">
            <div style="display: flex; gap: 8px; align-items: center;">
              <span>{{ searchResult.employee_id || '-' }}</span>
              <el-button v-if="searchResult.employee_id" size="small" @click="copyToClipboard(searchResult.employee_id, '工号')">复制</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ searchResult.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ searchResult.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ searchResult.role_name || searchResult.role_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ searchResult.department_name || searchResult.department_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="职称">{{ searchResult.title_name || searchResult.title_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="最后登录">{{ searchResult.last_login || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="result-actions">
          <el-button type="primary" @click="handleEdit">编辑</el-button>
          <el-button type="success" @click="handleSendMessage(searchResult.user_id, searchResult.real_name || searchResult.user_name)">发消息</el-button>
          <el-button type="warning" @click="handleResetPassword">重置密码</el-button>
          <el-button type="danger" @click="handleDelete">离职</el-button>
        </div>
      </div>

      <div v-else-if="searchType === 'fuzzy' && fuzzyResults.length > 0" class="result-list">
        <div class="result-count">找到 {{ fuzzyResults.length }} 个匹配结果</div>
        <el-table :data="fuzzyResults" size="small" width="100%" :height="tableHeight">
          <el-table-column prop="user_name" label="用户名" min-width="120" />
          <el-table-column prop="real_name" label="真实姓名" min-width="120" />
          <el-table-column prop="employee_id" label="工号" min-width="120" />
          <el-table-column prop="role_name" label="角色" min-width="100" />
          <el-table-column prop="department_name" label="部门" min-width="120" />
          <el-table-column prop="title_name" label="职称" min-width="100" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleViewDetail(row)">查看</el-button>
              <el-button type="success" size="small" @click="handleSendMessage(row.user_id, row.real_name || row.user_name)">发消息</el-button>
              <el-button type="warning" size="small" @click="handleResetPasswordFromRow(row)">重置密码</el-button>
              <el-button type="danger" size="small" @click="handleDeleteFromRow(row)">离职</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="searched" class="no-result">
        <el-empty :description="searchType === 'exact' ? '未找到匹配的用户' : '未找到匹配的搜索结果'" />
      </div>

      <el-dialog v-model="showEditDialog" title="编辑用户" width="500px">
        <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
          <el-form-item label="用户名">
            <el-input v-model="editForm.user_name" disabled />
          </el-form-item>
          <el-form-item label="真实姓名" prop="real_name">
            <el-input v-model="editForm.real_name" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="editForm.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="电话">
            <el-input v-model="editForm.phone" placeholder="请输入电话" />
          </el-form-item>
          <el-form-item label="角色ID">
            <el-input v-model="editForm.role_id" type="number" placeholder="输入角色ID" @input="onRoleIdChange" />
          </el-form-item>
          <el-form-item label="角色名称">
            <el-select v-model="editForm.role_name" filterable clearable placeholder="选择角色名称" @change="onRoleNameChange">
              <el-option v-for="role in roleOptions" :key="role.role_id" :label="role.role_name" :value="role.role_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="部门ID">
            <el-input v-model="editForm.department_id" type="number" placeholder="输入部门ID" @input="onDepartmentIdChange" />
          </el-form-item>
          <el-form-item label="部门名称">
            <el-select v-model="editForm.department_name" filterable clearable placeholder="选择部门名称" @change="onDepartmentNameChange">
              <el-option v-for="dept in departmentOptions" :key="dept.department_id" :label="dept.department_name" :value="dept.department_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="职称ID">
            <el-input v-model="editForm.title_id" type="number" placeholder="输入职称ID" @input="onTitleIdChange" />
          </el-form-item>
          <el-form-item label="职称名称">
            <el-select v-model="editForm.title_name" filterable clearable placeholder="选择职称名称" @change="onTitleNameChange">
              <el-option v-for="title in titleOptions" :key="title.title_id" :label="title.title_name" :value="title.title_name" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" :loading="editLoading" @click="handleUpdate">保存</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showDetailDialog" title="用户详情" width="500px">
        <div class="detail-content">
          <div class="detail-row">
            <span class="detail-label">用户ID</span>
            <span class="detail-value">
              {{ currentDetail.user_id }}
              <el-button size="small" @click="copyToClipboard(currentDetail.user_id, '用户ID')">复制</el-button>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">用户名</span>
            <span class="detail-value">{{ currentDetail.user_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">真实姓名</span>
            <span class="detail-value">{{ currentDetail.real_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">工号</span>
            <span class="detail-value">
              {{ currentDetail.employee_id || '-' }}
              <el-button v-if="currentDetail.employee_id" size="small" @click="copyToClipboard(currentDetail.employee_id, '工号')">复制</el-button>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">邮箱</span>
            <span class="detail-value">{{ currentDetail.email || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">电话</span>
            <span class="detail-value">{{ currentDetail.phone || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">角色</span>
            <span class="detail-value">{{ currentDetail.role_name || currentDetail.role_id || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">部门</span>
            <span class="detail-value">{{ currentDetail.department_name || currentDetail.department_id || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">职称</span>
            <span class="detail-value">{{ currentDetail.title_name || currentDetail.title_id || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">最后登录</span>
            <span class="detail-value">{{ currentDetail.last_login || '-' }}</span>
          </div>
        </div>
        <template #footer>
          <el-button type="primary" @click="handleEditFromDetail">编辑</el-button>
          <el-button type="success" @click="handleSendMessage(currentDetail.user_id, currentDetail.real_name || currentDetail.user_name)">发消息</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showSendMessageDialog" :title="'发送消息给 ' + sendMessageTarget.user_name" width="500px">
        <el-form>
          <el-form-item label="接收人">
            <el-input v-model="sendMessageTarget.user_name" disabled />
          </el-form-item>
          <el-form-item label="消息内容">
            <el-input v-model="messageContent" type="textarea" :rows="4" placeholder="输入消息内容" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showSendMessageDialog = false">取消</el-button>
          <el-button type="primary" :loading="sendMessageLoading" @click="handleConfirmSendMessage" :disabled="!messageContent.trim()">发送</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userService, departmentService, titleService, roleService } from '../../services/user'
import { messageService } from '../../services/message'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const searchQuery = ref('')
const searched = ref(false)
const searchResult = ref(null)
const searchType = ref('exact')
const fuzzyResults = ref([])
const showEditDialog = ref(false)
const showDetailDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref(null)
const showSendMessageDialog = ref(false)
const sendMessageTarget = ref({ user_id: '', user_name: '' })
const messageContent = ref('')
const sendMessageLoading = ref(false)

const roleOptions = ref([])
const departmentOptions = ref([])
const titleOptions = ref([])

const tableHeight = computed(() => {
  return 'calc(100vh - 320px)'
})

const currentDetail = reactive({
  user_id: '',
  user_name: '',
  real_name: '',
  email: '',
  phone: '',
  employee_id: '',
  role_name: '',
  role_id: '',
  department_name: '',
  department_id: '',
  title_name: '',
  title_id: '',
  last_login: ''
})

const editForm = reactive({
  user_id: '',
  user_name: '',
  real_name: '',
  email: '',
  phone: '',
  role_id: null,
  role_name: '',
  department_id: null,
  department_name: '',
  title_id: null,
  title_name: ''
})

const editRules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }]
}

const loadOptions = async () => {
  try {
    const [rolesRes, deptsRes, titlesRes] = await Promise.all([
      roleService.getList({ limit: 1000 }),
      departmentService.getList({ limit: 1000 }),
      titleService.getList({ limit: 1000 })
    ])
    roleOptions.value = rolesRes.data.roles || []
    departmentOptions.value = deptsRes.data.departments || []
    titleOptions.value = titlesRes.data.titles || []
  } catch (error) {
    console.error('Load options failed:', error)
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入查询条件')
    return
  }

  loading.value = true
  searched.value = true

  try {
    const query = searchQuery.value.trim()

    if (searchType.value === 'exact') {
      searchResult.value = null
      let res

      if (/^\d+$/.test(query)) {
        res = await userService.getByEmployeeId(query)
        searchResult.value = res.data.user
      } else {
        res = await userService.getById(query)
        searchResult.value = res.data
      }

      if (searchResult.value) {
        searchResult.value.last_login = formatDateTime(searchResult.value.last_login)
        resolveNames(searchResult.value)
      }
    } else {
      const res = await userService.search({ keyword: query, limit: 100 })
      fuzzyResults.value = (res.data.users || []).map(user => {
        const item = {
          ...user,
          last_login: formatDateTime(user.last_login)
        }
        resolveNames(item)
        return item
      })
    }
  } catch (error) {
    console.error('Search failed:', error)
    if (searchType.value === 'exact') {
      searchResult.value = null
    } else {
      fuzzyResults.value = []
    }
  } finally {
    loading.value = false
  }
}

const resolveNames = (user) => {
  if (user.role_id && !user.role_name) {
    const role = roleOptions.value.find(r => r.role_id === Number(user.role_id))
    user.role_name = role?.role_name || ''
  }
  if (user.department_id && !user.department_name) {
    const dept = departmentOptions.value.find(d => d.department_id === Number(user.department_id))
    user.department_name = dept?.department_name || ''
  }
  if (user.title_id && !user.title_name) {
    const title = titleOptions.value.find(t => t.title_id === Number(user.title_id))
    user.title_name = title?.title_name || ''
  }
}

const handleClear = () => {
  searchQuery.value = ''
  searchResult.value = null
  fuzzyResults.value = []
  searched.value = false
  searchType.value = 'exact'
}

const copyToClipboard = async (text, label) => {
  if (!text) {
    ElMessage.warning(`${label}为空，无法复制`)
    return
  }

  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label}已复制`)
  } catch (error) {
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success(`${label}已复制`)
  }
}

const handleViewDetail = (row) => {
  Object.assign(currentDetail, row)
  showDetailDialog.value = true
}

const handleEditFromDetail = () => {
  showDetailDialog.value = false
  handleEdit()
}

const handleEdit = () => {
  const detail = searchResult.value || currentDetail
  editForm.user_id = detail.user_id
  editForm.user_name = detail.user_name
  editForm.real_name = detail.real_name
  editForm.email = detail.email || ''
  editForm.phone = detail.phone || ''

  const roleId = roleOptions.value.find(r => r.role_name === detail.role_name)?.role_id
  editForm.role_id = roleId || (detail.role_id ? Number(detail.role_id) : null)
  editForm.role_name = detail.role_name || ''

  const deptId = departmentOptions.value.find(d => d.department_name === detail.department_name)?.department_id
  editForm.department_id = deptId || (detail.department_id ? Number(detail.department_id) : null)
  editForm.department_name = detail.department_name || ''

  const titleId = titleOptions.value.find(t => t.title_name === detail.title_name)?.title_id
  editForm.title_id = titleId || (detail.title_id ? Number(detail.title_id) : null)
  editForm.title_name = detail.title_name || ''

  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        await userService.update(editForm.user_id, {
          real_name: editForm.real_name,
          email: editForm.email || undefined,
          phone: editForm.phone || undefined,
          role_id: editForm.role_id || undefined,
          department_id: editForm.department_id || undefined,
          title_id: editForm.title_id || undefined
        })
        ElMessage.success('用户更新成功')
        showEditDialog.value = false
        handleSearch()
      } catch (error) {
        console.error('Update user failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleResetPassword = async () => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt('请输入新密码', '重置密码', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'password'
    })

    if (!newPassword || !newPassword.trim()) {
      ElMessage.warning('密码不能为空')
      return
    }

    await userService.resetPassword(searchResult.value.user_id, newPassword.trim())
    ElMessage.success('密码重置成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Reset password failed:', error)
    }
  }
}

const handleResetPasswordFromRow = async (row) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt('请输入新密码', `重置用户 ${row.user_name} 的密码`, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'password'
    })

    if (!newPassword || !newPassword.trim()) {
      ElMessage.warning('密码不能为空')
      return
    }

    await userService.resetPassword(row.user_id, newPassword.trim())
    ElMessage.success('密码重置成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Reset password failed:', error)
    }
  }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要将用户 ${searchResult.value.user_name} 设为离职吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userService.delete(searchResult.value.user_id)
    ElMessage.success('用户已设为离职')
    searchResult.value = null
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user failed:', error)
    }
  }
}

const handleDeleteFromRow = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要将用户 ${row.user_name} 设为离职吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userService.delete(row.user_id)
    ElMessage.success('用户已设为离职')
    handleSearch()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user failed:', error)
    }
  }
}

const handleSendMessage = (userId, userName) => {
  sendMessageTarget.value = { user_id: userId, user_name: userName }
  messageContent.value = ''
  showSendMessageDialog.value = true
}

const handleConfirmSendMessage = async () => {
  if (!messageContent.value.trim()) {
    ElMessage.warning('消息内容不能为空')
    return
  }

  sendMessageLoading.value = true
  try {
    await messageService.sendMessage({
      receive_user: sendMessageTarget.value.user_id,
      content: messageContent.value.trim()
    })
    ElMessage.success('消息发送成功')
    showSendMessageDialog.value = false
    messageContent.value = ''
  } catch (error) {
    console.error('Send message failed:', error)
    ElMessage.error('消息发送失败')
  } finally {
    sendMessageLoading.value = false
  }
}

const onRoleIdChange = () => {
  const role = roleOptions.value.find(r => r.role_id === Number(editForm.role_id))
  editForm.role_name = role?.role_name || ''
}

const onRoleNameChange = () => {
  const role = roleOptions.value.find(r => r.role_name === editForm.role_name)
  editForm.role_id = role?.role_id || null
}

const onDepartmentIdChange = () => {
  const dept = departmentOptions.value.find(d => d.department_id === Number(editForm.department_id))
  editForm.department_name = dept?.department_name || ''
}

const onDepartmentNameChange = () => {
  const dept = departmentOptions.value.find(d => d.department_name === editForm.department_name)
  editForm.department_id = dept?.department_id || null
}

const onTitleIdChange = () => {
  const title = titleOptions.value.find(t => t.title_id === Number(editForm.title_id))
  editForm.title_name = title?.title_name || ''
}

const onTitleNameChange = () => {
  const title = titleOptions.value.find(t => t.title_name === editForm.title_name)
  editForm.title_id = title?.title_id || null
}

onMounted(() => {
  loadOptions()
})
</script>

<style scoped>
.users-search-container {
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
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}

.search-form {
  margin-bottom: 16px;
}

.search-type {
  margin-bottom: 16px;
}

.result-card {
  background: #f5f7fa;
  padding: 24px;
  border-radius: 8px;
}

.result-list {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.result-count {
  margin-bottom: 12px;
  color: #666;
  font-size: 14px;
}

.result-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.no-result {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-content {
  padding: 16px;
}

.detail-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  width: 100px;
  font-weight: bold;
  color: #606266;
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.detail-value .el-button) {
  padding: 2px 8px;
}

:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table .el-table__header-wrapper),
:deep(.el-table .el-table__body-wrapper) {
  width: 100% !important;
}
</style>
