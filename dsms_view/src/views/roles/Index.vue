<template>
  <div class="roles-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="showCreateDialog = true">创建角色</el-button>
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
          <el-table-column prop="role_id" label="角色ID" width="100" />
          <el-table-column prop="role_name" label="角色名称" width="150" />
          <el-table-column prop="desc" label="描述" show-overflow-tooltip />
          <el-table-column prop="is_system_role" label="系统角色" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_system_role ? 'danger' : 'success'">
                {{ row.is_system_role ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="info" size="small" @click="handleView(row)">详情</el-button>
                <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button
                  type="danger"
                  size="small"
                  :disabled="row.is_system_role"
                  @click="handleDelete(row)"
                >
                  删除
                </el-button>
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

    <el-dialog v-model="showCreateDialog" title="创建角色" width="650px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="createForm.role_name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述" prop="desc">
          <el-input v-model="createForm.desc" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="权限列表">
          <div class="permission-input-row" style="display: block; width: 100%; margin-bottom: 12px;">
            <el-autocomplete
              v-model="createPermissionApi"
              :fetch-suggestions="querySearch"
              placeholder="搜索API路径"
              :trigger-on-focus="false"
              class="permission-api-input"
            />
          </div>
          <div style="display: flex; gap: 12px; margin-bottom: 16px;">
            <el-select v-model="createPermissionAccess" placeholder="请选择权限" style="width: 150px;">
              <el-option label="全部" value="*" />
              <el-option label="只读" value="GET" />
              <el-option label="创建" value="POST" />
              <el-option label="更新" value="PUT" />
              <el-option label="删除" value="DELETE" />
            </el-select>
            <el-button type="success" size="small" @click="addCreatePermission">添加</el-button>
          </div>
          <div class="permissions-container" style="max-height: 200px; overflow-y: auto;">
            <div class="permissions-header">
              <span class="permissions-col-api">API路径</span>
              <span class="permissions-col-access">权限</span>
              <span class="permissions-col-action">操作</span>
            </div>
            <div class="permissions-list">
              <div v-for="(item, index) in createPermissions" :key="index" class="permissions-item">
                <span class="permissions-col-api" :title="item.api">{{ item.api }}</span>
                <span class="permissions-col-access">{{ item.accessibility }}</span>
                <span class="permissions-col-action">
                  <button class="delete-btn" type="button" @click="removeCreatePermission(index)">删除</button>
                </span>
              </div>
              <div v-if="createPermissions.length === 0" class="permissions-empty">
                暂无权限，请添加
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑角色" width="600px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="editForm.role_name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述" prop="desc">
          <el-input v-model="editForm.desc" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="权限列表">
          <div class="permissions-container" style="max-height: 300px; overflow-y: auto;">
            <div class="permissions-header">
              <span class="permissions-col-api">API路径</span>
              <span class="permissions-col-access">权限</span>
              <span class="permissions-col-action">操作</span>
            </div>
            <div class="permissions-list">
              <div v-for="(item, index) in editPermissions" :key="index" class="permissions-item">
                <span class="permissions-col-api" :title="item.api">{{ item.api }}</span>
                <span class="permissions-col-access">{{ item.accessibility }}</span>
                <span class="permissions-col-action">
                  <button class="delete-btn" type="button" @click="removePermission(index)">删除</button>
                </span>
              </div>
              <div v-if="editPermissions.length === 0" class="permissions-empty">
                暂无权限
              </div>
            </div>
          </div>
          <div style="margin-top: 12px;">
            <el-button type="success" size="small" @click="showAddPermissionDialog = true">添加权限</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showViewDialog" title="角色详情" width="600px">
      <el-form :model="viewForm" label-width="100px" disabled>
        <el-form-item label="角色ID">
          <el-input v-model="viewForm.role_id" />
        </el-form-item>
        <el-form-item label="角色名称">
          <el-input v-model="viewForm.role_name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="viewForm.desc" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="系统角色">
          <el-tag :type="viewForm.is_system_role ? 'danger' : 'success'">
            {{ viewForm.is_system_role ? '是' : '否' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-input v-model="viewForm.created_at" />
        </el-form-item>
        <el-form-item label="权限列表">
          <div class="permissions-container" style="max-height: 300px; overflow-y: auto;">
            <div class="permissions-header">
              <span class="permissions-col-api">API路径</span>
              <span class="permissions-col-access">权限</span>
            </div>
            <div class="permissions-list">
              <div v-for="(item, index) in viewPermissions" :key="index" class="permissions-item">
                <span class="permissions-col-api" :title="item.api">{{ item.api }}</span>
                <span class="permissions-col-access">{{ item.accessibility }}</span>
              </div>
              <div v-if="viewPermissions.length === 0" class="permissions-empty">
                暂无权限
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddPermissionDialog" title="添加权限" width="450px">
      <el-form ref="permissionFormRef" :model="permissionForm" :rules="permissionRules" label-width="100px">
        <el-form-item label="API路径" prop="api">
          <el-autocomplete
            v-model="permissionForm.api"
            :fetch-suggestions="querySearch"
            placeholder="例如: /api/v1/users/*"
            :trigger-on-focus="false"
          />
        </el-form-item>
        <el-form-item label="访问权限" prop="accessibility">
          <el-select v-model="permissionForm.accessibility" placeholder="请选择权限">
            <el-option label="全部权限" value="*" />
            <el-option label="只读" value="GET" />
            <el-option label="创建" value="POST" />
            <el-option label="更新" value="PUT" />
            <el-option label="删除" value="DELETE" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPermissionDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddPermission">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { roleService } from '../../services/user'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const tableData = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showViewDialog = ref(false)
const showAddPermissionDialog = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const permissionFormRef = ref(null)

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const createForm = reactive({
  role_name: '',
  desc: ''
})

const editForm = reactive({
  role_id: null,
  role_name: '',
  desc: ''
})

const editPermissions = ref([])

const createPermissions = ref([])
const createPermissionApi = ref('')
const createPermissionAccess = ref('*')

const viewForm = reactive({
  role_id: '',
  role_name: '',
  desc: '',
  is_system_role: false,
  created_at: ''
})

const viewPermissions = ref([])

const permissionForm = reactive({
  api: '',
  accessibility: '*'
})

const apiSuggestions = [
  { value: '/api/v1/users/*', label: '用户管理全部权限' },
  { value: '/api/v1/users/', label: '用户列表' },
  { value: '/api/v1/users/{id}', label: '单个用户' },
  { value: '/api/v1/roles/*', label: '角色管理全部权限' },
  { value: '/api/v1/roles/', label: '角色列表' },
  { value: '/api/v1/roles/{id}', label: '单个角色' },
  { value: '/api/v1/departments/*', label: '部门管理全部权限' },
  { value: '/api/v1/departments/', label: '部门列表' },
  { value: '/api/v1/departments/{id}', label: '单个部门' },
  { value: '/api/v1/devices/*', label: '设备管理全部权限' },
  { value: '/api/v1/devices/', label: '设备列表' },
  { value: '/api/v1/devices/{id}', label: '单个设备' },
  { value: '/api/v1/device-approvals/*', label: '设备审批全部权限' },
  { value: '/api/v1/production-lines/*', label: '生产线管理全部权限' },
  { value: '/api/v1/detection-records/*', label: '检测记录全部权限' },
  { value: '/api/v1/common/*', label: '通用接口全部权限' }
]

const querySearch = (queryString, callback) => {
  const results = queryString
    ? apiSuggestions.filter(item => item.value.toLowerCase().includes(queryString.toLowerCase()) || 
                                   item.label.toLowerCase().includes(queryString.toLowerCase()))
    : apiSuggestions
  callback(results)
}

const createRules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

const editRules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

const permissionRules = {
  api: [{ required: true, message: '请输入API路径', trigger: 'blur' }],
  accessibility: [{ required: true, message: '请选择访问权限', trigger: 'change' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await roleService.getList({
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    })
    const roles = res.data.roles || []
    for (const role of roles) {
      role.created_at = formatDateTime(role.created_at)
    }
    tableData.value = roles
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('Load roles failed:', error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
}

const handleCreate = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await roleService.create({
          role_name: createForm.role_name,
          desc: createForm.desc || undefined,
          permissions: createPermissions.value
        })
        ElMessage.success('角色创建成功')
        showCreateDialog.value = false
        createForm.role_name = ''
        createForm.desc = ''
        createPermissions.value = []
        createPermissionApi.value = ''
        createPermissionAccess.value = '*'
        loadData()
      } catch (error) {
        console.error('Create role failed:', error)
      } finally {
        createLoading.value = false
      }
    }
  })
}

const addCreatePermission = () => {
  if (!createPermissionApi.value.trim()) {
    ElMessage.warning('请输入API路径')
    return
  }
  const exists = createPermissions.value.some(p => p.api === createPermissionApi.value && p.accessibility === createPermissionAccess.value)
  if (exists) {
    ElMessage.warning('该权限已存在')
    return
  }
  createPermissions.value.push({
    api: createPermissionApi.value,
    accessibility: createPermissionAccess.value
  })
  createPermissionApi.value = ''
}

const removeCreatePermission = (index) => {
  createPermissions.value.splice(index, 1)
}

const handleView = async (row) => {
  try {
    const res = await roleService.getById(row.role_id)
    const role = res.data
    viewForm.role_id = role.role_id
    viewForm.role_name = role.role_name
    viewForm.desc = role.desc || ''
    viewForm.is_system_role = role.is_system_role
    viewForm.created_at = formatDateTime(role.created_at)
    viewPermissions.value = role.permissions || []
    showViewDialog.value = true
  } catch (error) {
    console.error('Get role detail failed:', error)
    ElMessage.error('获取角色详情失败')
  }
}

const handleEdit = async (row) => {
  try {
    const res = await roleService.getById(row.role_id)
    const role = res.data
    editForm.role_id = role.role_id
    editForm.role_name = role.role_name
    editForm.desc = role.desc || ''
    editPermissions.value = role.permissions ? JSON.parse(JSON.stringify(role.permissions)) : []
    showEditDialog.value = true
  } catch (error) {
    console.error('Get role detail failed:', error)
    ElMessage.error('获取角色详情失败')
  }
}

const handleAddPermission = () => {
  if (!permissionFormRef.value) return

  permissionFormRef.value.validate((valid) => {
    if (valid) {
      editPermissions.value.push({
        api: permissionForm.api,
        accessibility: permissionForm.accessibility
      })
      permissionForm.api = ''
      permissionForm.accessibility = '*'
      showAddPermissionDialog.value = false
    }
  })
}

const removePermission = (index) => {
  editPermissions.value.splice(index, 1)
}

const handleUpdate = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        await roleService.update(editForm.role_id, {
          role_name: editForm.role_name,
          desc: editForm.desc || undefined,
          permissions: editPermissions.value
        })
        ElMessage.success('角色更新成功')
        showEditDialog.value = false
        loadData()
      } catch (error) {
        console.error('Update role failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色 ${row.role_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await roleService.delete(row.role_id)
    ElMessage.success('角色删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete role failed:', error)
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.roles-container {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
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
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.permission-input-row {
  display: block !important;
  width: 100% !important;
}

.permission-api-input {
  width: 100% !important;
  display: block !important;
}

.permission-api-input :deep(.el-input) {
  width: 100% !important;
}

.permission-api-input :deep(.el-input__wrapper) {
  width: 100% !important;
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

.permissions-container {
  width: 100%;
  min-width: 0;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.permissions-header {
  display: flex;
  background: #fafafa;
  border-bottom: 1px solid #ebeef5;
  padding: 8px 12px;
  font-weight: 600;
  font-size: 13px;
}

.permissions-list {
  max-height: calc(300px - 40px);
  overflow-y: auto;
}

.permissions-item {
  display: flex;
  border-bottom: 1px solid #ebeef5;
  padding: 8px 12px;
  align-items: center;
  transition: background-color 0.2s;
}

.permissions-item:hover {
  background: #fafafa;
}

.permissions-col-api {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.permissions-col-access {
  width: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.permissions-col-action {
  width: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.delete-btn {
  background: #f56c6c;
  border: none;
  border-radius: 4px;
  color: white;
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-width: 48px;
}

.delete-btn:hover {
  background: #f78989;
}

.permissions-empty {
  text-align: center;
  color: #999;
  padding: 20px;
}
</style>