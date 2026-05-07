<template>
  <div class="users-container">
    <el-card style="display: flex; flex-direction: column; height: calc(100vh - 160px);">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div class="search-by-employee">
            <el-input 
              v-model="searchEmployeeId" 
              placeholder="输入工号搜索" 
              style="width: 200px; margin-right: 8px;"
              @keyup.enter="handleSearchByEmployeeId"
            />
            <el-button type="default" @click="handleSearchByEmployeeId">按工号查找</el-button>
            <el-button type="primary" @click="showCreateDialog = true">批量创建用户</el-button>
          </div>
        </div>
      </template>
      <div class="table-wrapper">
        <el-table 
          :data="tableData" 
          v-loading="loading" 
          style="width: 100%; height: 100%;"
        >
          <el-table-column prop="user_name" label="用户名" width="140" />
          <el-table-column prop="real_name" label="真实姓名" />
          <el-table-column prop="employee_id" label="工号" width="120" />
          <el-table-column prop="role_name" label="角色" width="120" />
          <el-table-column prop="department_name" label="部门" width="120" />
          <el-table-column prop="title_name" label="职称" width="120" />
          <el-table-column prop="last_login" label="最后登录" show-overflow-tooltip />
          <el-table-column label="操作" width="360" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="info" size="small" @click="handleView(row)">查看详情</el-button>
                <el-button type="success" size="small" @click="handleSendMessage(row)">发消息</el-button>
                <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button type="warning" size="small" @click="handleResetPassword(row)">重置密码</el-button>
                <el-button type="danger" size="small" @click="handleDelete(row)">离职</el-button>
              </div>
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

    <el-dialog v-model="showViewDialog" title="用户详情" width="500px">
      <el-form :model="viewForm" label-width="100px">
        <el-form-item label="用户ID">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input v-model="viewForm.user_id" disabled style="flex: 1;" />
            <el-button @click="copyToClipboard(viewForm.user_id, '用户ID')">复制</el-button>
          </div>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="viewForm.user_name" disabled />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="viewForm.real_name" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="viewForm.email" disabled />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="viewForm.phone" disabled />
        </el-form-item>
        <el-form-item label="工号">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input v-model="viewForm.employee_id" disabled style="flex: 1;" />
            <el-button @click="copyToClipboard(viewForm.employee_id, '工号')">复制</el-button>
          </div>
        </el-form-item>
        <el-form-item label="角色">
          <el-input v-model="viewForm.role_name" disabled />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="viewForm.department_name" disabled />
        </el-form-item>
        <el-form-item label="职称">
          <el-input v-model="viewForm.title_name" disabled />
        </el-form-item>
        <el-form-item label="最后登录">
          <el-input v-model="viewForm.last_login" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSearchResultDialog" title="搜索结果" width="500px">
      <el-form :model="searchResultForm" label-width="100px">
        <el-form-item label="用户ID">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input v-model="searchResultForm.user_id" disabled style="flex: 1;" />
            <el-button @click="copyToClipboard(searchResultForm.user_id, '用户ID')">复制</el-button>
          </div>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="searchResultForm.user_name" disabled />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="searchResultForm.real_name" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="searchResultForm.email" disabled />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="searchResultForm.phone" disabled />
        </el-form-item>
        <el-form-item label="工号">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input v-model="searchResultForm.employee_id" disabled style="flex: 1;" />
            <el-button @click="copyToClipboard(searchResultForm.employee_id, '工号')">复制</el-button>
          </div>
        </el-form-item>
        <el-form-item label="角色">
          <el-input v-model="searchResultForm.role_name" disabled />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="searchResultForm.department_name" disabled />
        </el-form-item>
        <el-form-item label="职称">
          <el-input v-model="searchResultForm.title_name" disabled />
        </el-form-item>
        <el-form-item label="最后登录">
          <el-input v-model="searchResultForm.last_login" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSearchResultDialog = false">关闭</el-button>
        <el-button type="warning" @click="handleResetPasswordFromSearch">重置密码</el-button>
        <el-button type="primary" @click="handleEditFromSearch">编辑</el-button>
        <el-button type="danger" @click="handleDeleteFromSearch">离职</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateDialog" title="批量创建用户" width="600px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="用户列表" prop="users">
          <el-input
            v-model="createForm.usersText"
            type="textarea"
            :rows="10"
            placeholder="每行一个用户，格式：用户名,密码,真实姓名,邮箱,电话,工号"
          />
        </el-form-item>
        <el-form-item label="默认角色" prop="default_role_id">
          <el-select
            v-model="createForm.default_role_id"
            filterable
            remote
            reserve-keyword
            placeholder="请选择角色"
            :remote-method="loadRoles"
            :loading="roleLoading"
            style="width: 100%;"
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.role_id"
              :label="role.role_name"
              :value="role.role_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleBatchCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑用户" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.user_name" disabled />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="editForm.real_name" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select
            v-model="editForm.role_id"
            filterable
            remote
            reserve-keyword
            placeholder="请选择角色"
            :remote-method="loadRoles"
            :loading="roleLoading"
            @change="onRoleChange"
            clearable
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.role_id"
              :label="role.role_name"
              :value="role.role_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select
            v-model="editForm.department_id"
            filterable
            remote
            reserve-keyword
            placeholder="请选择部门"
            :remote-method="loadDepartments"
            :loading="deptLoading"
            @change="onDepartmentChange"
            clearable
          >
            <el-option
              v-for="dept in departmentOptions"
              :key="dept.department_id"
              :label="dept.department_name"
              :value="dept.department_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="职称">
          <el-select
            v-model="editForm.title_id"
            filterable
            remote
            reserve-keyword
            placeholder="请选择职称"
            :remote-method="loadTitles"
            :loading="titleLoading"
            @change="onTitleChange"
            clearable
          >
            <el-option
              v-for="title in titleOptions"
              :key="title.title_id"
              :label="title.title_name"
              :value="title.title_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleUpdate">保存</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userService, departmentService, titleService, roleService } from '../../services/user'
import { messageService } from '../../services/message'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const tableData = ref([])
const showViewDialog = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const showSendMessageDialog = ref(false)
const sendMessageTarget = ref({ user_id: '', user_name: '' })
const messageContent = ref('')
const sendMessageLoading = ref(false)
const roleLoading = ref(false)
const deptLoading = ref(false)
const titleLoading = ref(false)

const roleMap = ref({})
const departmentMap = ref({})
const titleMap = ref({})
const roleOptions = ref([])
const departmentOptions = ref([])
const titleOptions = ref([])

const allUsersCache = ref([])
const cacheLoaded = ref(false)

const searchEmployeeId = ref('')
const showSearchResultDialog = ref(false)
const searchResultForm = reactive({
  user_id: '',
  user_name: '',
  real_name: '',
  email: '',
  phone: '',
  employee_id: '',
  role_name: '',
  department_name: '',
  title_name: '',
  last_login: ''
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const createForm = reactive({
  usersText: '',
  default_role_id: 1
})

const viewForm = reactive({
  user_id: '',
  user_name: '',
  real_name: '',
  email: '',
  phone: '',
  employee_id: '',
  role_name: '',
  department_name: '',
  title_name: '',
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

const createRules = {
  usersText: [{ required: true, message: '请输入用户列表', trigger: 'blur' }],
  default_role_id: [{ required: true, message: '请输入默认角色ID', trigger: 'blur' }]
}

const editRules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }]
}

const loadAllUsersToCache = async () => {
  if (cacheLoaded.value) return
  
  try {
    const allUsers = []
    let skip = 0
    const limit = 100
    
    while (true) {
      try {
        const res = await userService.getList({ skip, limit })
        const users = res.data.users || []
        
        if (users.length === 0) {
          break
        }
        
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
          user.created_at = formatDateTime(user.created_at)
        }
        
        allUsers.push(...users)
        skip += limit
        
        if (users.length < limit) {
          break
        }
      } catch (error) {
        console.error('Load page failed:', error)
        break
      }
    }
    
    allUsersCache.value = allUsers
    cacheLoaded.value = true
  } catch (error) {
    console.error('Load all users to cache failed:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    }
    const res = await userService.getList(params)
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
      user.created_at = formatDateTime(user.created_at)
    }
    
    tableData.value = users
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('Load users failed:', error)
  } finally {
    loading.value = false
  }
}

const handleSearchByEmployeeId = async () => {
  if (!searchEmployeeId.value.trim()) {
    ElMessage.warning('请输入工号')
    return
  }
  
  const targetEmployeeId = searchEmployeeId.value.trim()
  loading.value = true
  try {
    const res = await userService.getByEmployeeId(targetEmployeeId)
    const user = res.data.user
    
    if (!user) {
      ElMessage.info('未找到该工号对应的用户')
      return
    }
    
    searchResultForm.user_id = user.user_id || ''
    searchResultForm.user_name = user.user_name || ''
    searchResultForm.real_name = user.real_name || ''
    searchResultForm.email = user.email || ''
    searchResultForm.phone = user.phone || ''
    searchResultForm.employee_id = user.employee_id || ''
    searchResultForm.role_name = user.role_name || ''
    searchResultForm.department_name = user.department_name || ''
    searchResultForm.title_name = user.title_name || ''
    searchResultForm.last_login = formatDateTime(user.last_login) || ''
    
    showSearchResultDialog.value = true
  } catch (error) {
    console.error('Search by employee ID failed:', error)
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

const handleEditFromSearch = () => {
  editForm.user_id = searchResultForm.user_id
  editForm.user_name = searchResultForm.user_name
  editForm.real_name = searchResultForm.real_name
  editForm.email = searchResultForm.email || ''
  editForm.phone = searchResultForm.phone || ''
  
  const roleId = roleOptions.value.find(r => r.role_name === searchResultForm.role_name)?.role_id
  editForm.role_id = roleId || null
  
  const deptId = departmentOptions.value.find(d => d.department_name === searchResultForm.department_name)?.department_id
  editForm.department_id = deptId || null
  
  const titleId = titleOptions.value.find(t => t.title_name === searchResultForm.title_name)?.title_id
  editForm.title_id = titleId || null
  
  showSearchResultDialog.value = false
  showEditDialog.value = true
  cacheLoaded.value = false
}

const handleResetPasswordFromSearch = async () => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt('请输入新密码', `重置 ${searchResultForm.user_name} 的密码`, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'password'
    })
    
    if (!newPassword || !newPassword.trim()) {
      ElMessage.warning('密码不能为空')
      return
    }
    
    await userService.resetPassword(searchResultForm.user_id, newPassword.trim())
    ElMessage.success('密码重置成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Reset password failed:', error)
      ElMessage.error('密码重置失败')
    }
  }
}

const handleDeleteFromSearch = async () => {
  try {
    await ElMessageBox.confirm(`确定要将用户 ${searchResultForm.user_name} 设为离职吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userService.delete(searchResultForm.user_id)
    ElMessage.success('用户已设为离职')
    showSearchResultDialog.value = false
    cacheLoaded.value = false
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user failed:', error)
      ElMessage.error('删除失败')
    }
  }
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
    console.error('Copy failed:', error)
    try {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      ElMessage.success(`${label}已复制`)
    } catch (fallbackError) {
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
}

const handleView = (row) => {
  viewForm.user_id = row.user_id || ''
  viewForm.user_name = row.user_name || ''
  viewForm.real_name = row.real_name || ''
  viewForm.email = row.email || ''
  viewForm.phone = row.phone || ''
  viewForm.employee_id = row.employee_id || ''
  viewForm.role_name = row.role_name || ''
  viewForm.department_name = row.department_name || ''
  viewForm.title_name = row.title_name || ''
  viewForm.last_login = row.last_login || ''
  showViewDialog.value = true
}

const handleEdit = (row) => {
  editForm.user_id = row.user_id
  editForm.user_name = row.user_name
  editForm.real_name = row.real_name
  editForm.email = row.email || ''
  editForm.phone = row.phone || ''
  editForm.role_id = row.role_id || null
  editForm.department_id = row.department_id || null
  editForm.title_id = row.title_id || null
  showEditDialog.value = true
}

const onRoleChange = (roleId) => {
  if (!roleId) return
  const role = roleOptions.value.find(r => r.role_id === roleId)
  if (!role) return
  editForm.role_id = roleId
}

const onDepartmentChange = (deptId) => {
  if (!deptId) return
  const dept = departmentOptions.value.find(d => d.department_id === deptId)
  if (!dept) return
  editForm.department_id = deptId
}

const onTitleChange = (titleId) => {
  if (!titleId) return
  const title = titleOptions.value.find(t => t.title_id === titleId)
  if (!title) return
  editForm.title_id = titleId
}

const loadRoles = async (query) => {
  if (!query) {
    return
  }
  roleLoading.value = true
  try {
    const params = query ? { keyword: query, limit: 50 } : { limit: 50 }
    const res = await roleService.getList(params)
    const roles = res.data.roles || []
    roles.forEach(role => {
      if (!roleMap.value[role.role_id]) {
        roleMap.value[role.role_id] = role.role_name
      }
    })
    roleOptions.value = roles
  } catch (error) {
    console.error('Load roles failed:', error)
  } finally {
    roleLoading.value = false
  }
}

const loadDepartments = async (query) => {
  if (!query) {
    return
  }
  deptLoading.value = true
  try {
    const params = query ? { keyword: query, limit: 50 } : { limit: 50 }
    const res = await departmentService.search(params)
    const depts = res.data.departments || []
    depts.forEach(dept => {
      if (!departmentMap.value[dept.department_id]) {
        departmentMap.value[dept.department_id] = dept.department_name
      }
    })
    departmentOptions.value = depts
  } catch (error) {
    console.error('Load departments failed:', error)
  } finally {
    deptLoading.value = false
  }
}

const loadTitles = async (query) => {
  if (!query) {
    return
  }
  titleLoading.value = true
  try {
    const res = await titleService.getList({ limit: 50 })
    const titles = res.data.titles || []
    titles.forEach(title => {
      if (!titleMap.value[title.title_id]) {
        titleMap.value[title.title_id] = title.title_name
      }
    })
    titleOptions.value = titles
  } catch (error) {
    console.error('Load titles failed:', error)
  } finally {
    titleLoading.value = false
  }
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
          title_id: editForm.title_id
        })
        ElMessage.success('用户更新成功')
        showEditDialog.value = false
        cacheLoaded.value = false
        loadData()
      } catch (error) {
        console.error('Update user failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleResetPassword = async (row) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt('请输入新密码', `重置 ${row.user_name} 的密码`, {
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
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Reset password failed:', error)
      ElMessage.error('密码重置失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要将用户 ${row.user_name} 设为离职吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userService.delete(row.user_id)
    ElMessage.success('用户已设为离职')
    cacheLoaded.value = false
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user failed:', error)
    }
  }
}

const handleSendMessage = (row) => {
  sendMessageTarget.value = { user_id: row.user_id, user_name: row.real_name || row.user_name }
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

const handleBatchCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        const users = createForm.usersText.split('\n').filter(line => line.trim()).map(line => {
          const parts = line.split(',').map(p => p.trim())
          return {
            user_name: parts[0],
            password: parts[1],
            real_name: parts[2],
            email: parts[3] || undefined,
            phone: parts[4] || undefined,
            employee_id: parts[5] || undefined
          }
        })
        await userService.createBatch(users, createForm.default_role_id)
        ElMessage.success('批量创建成功')
        showCreateDialog.value = false
        cacheLoaded.value = false
        loadData()
      } catch (error) {
        console.error('Batch create failed:', error)
      } finally {
        createLoading.value = false
      }
    }
  })
}

const loadAllRoles = async () => {
  roleMap.value = {}
  roleOptions.value = []
  let skip = 0
  const limit = 100
  while (true) {
    try {
      const res = await roleService.getList({ skip, limit })
      const roles = res.data.roles || []
      for (const role of roles) {
        roleMap.value[role.role_id] = role.role_name
        roleOptions.value.push({
          role_id: role.role_id,
          role_name: role.role_name
        })
      }
      if (roles.length < limit) break
      skip += limit
    } catch (error) {
      console.error('Load roles failed:', error)
      break
    }
  }
}

const loadAllDepartments = async () => {
  departmentMap.value = {}
  departmentOptions.value = []
  let skip = 0
  const limit = 100
  while (true) {
    try {
      const res = await departmentService.getList({ skip, limit })
      const depts = res.data.departments || []
      for (const dept of depts) {
        departmentMap.value[dept.department_id] = dept.department_name
        departmentOptions.value.push({
          department_id: dept.department_id,
          department_name: dept.department_name
        })
      }
      if (depts.length < limit) break
      skip += limit
    } catch (error) {
      console.error('Load departments failed:', error)
      break
    }
  }
}

const loadAllTitles = async () => {
  titleMap.value = {}
  titleOptions.value = []
  let skip = 0
  const limit = 100
  while (true) {
    try {
      const res = await titleService.getList({ skip, limit })
      const titles = res.data.titles || []
      for (const title of titles) {
        titleMap.value[title.title_id] = title.title_name
        titleOptions.value.push({
          title_id: title.title_id,
          title_name: title.title_name
        })
      }
      if (titles.length < limit) break
      skip += limit
    } catch (error) {
      console.error('Load titles failed:', error)
      break
    }
  }
}

onMounted(async () => {
  await Promise.all([loadAllRoles(), loadAllDepartments(), loadAllTitles()])
  loadData()
})
</script>

<style scoped>
.users-container {
  padding: 0;
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-by-employee {
  display: flex;
  align-items: center;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
}

:deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 10;
}

:deep(.el-table__header) {
  background-color: #fafafa;
}

:deep(.el-table__header th) {
  position: sticky;
  top: 0;
  z-index: 11;
  background-color: #fafafa;
}

.pagination-wrapper {
  padding: 16px;
  border-top: 1px solid #EBEEF5;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  width: 100% !important;
  min-width: 0 !important;
}

:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
</style>
