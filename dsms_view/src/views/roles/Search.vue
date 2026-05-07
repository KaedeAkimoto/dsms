<template>
  <div class="roles-search-container">
    <el-card style="display: flex; flex-direction: column; height: calc(100vh - 160px);">
      <template #header>
        <div class="card-header">
          <span>角色精准查找</span>
        </div>
      </template>

      <div class="search-form">
        <el-input
          v-model="searchQuery"
          placeholder="输入角色ID进行精准查找"
          style="width: 400px; margin-right: 16px;"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">查找</el-button>
      </div>

      <div v-if="searchResult" class="result-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="角色ID">
            <div style="display: flex; gap: 8px; align-items: center;">
              <span>{{ searchResult.role_id }}</span>
              <el-button size="small" @click="copyToClipboard(searchResult.role_id, '角色ID')">复制</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="角色名称">{{ searchResult.role_name }}</el-descriptions-item>
          <el-descriptions-item label="角色描述" :span="2">{{ searchResult.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="权限数量">{{ searchResult.permissions?.length || 0 }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ searchResult.created_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="result-section" v-if="searchResult.permissions && searchResult.permissions.length > 0">
          <h4>权限列表</h4>
          <el-table :data="searchResult.permissions" size="small" max-height="200">
            <el-table-column prop="api" label="API路径" show-overflow-tooltip />
            <el-table-column prop="accessibility" label="权限" width="100" />
          </el-table>
        </div>

        <div class="result-actions">
          <el-button type="primary" @click="handleEdit">编辑</el-button>
          <el-button type="danger" @click="handleDelete">删除</el-button>
        </div>
      </div>

      <div v-else-if="searched" class="no-result">
        <el-empty description="未找到匹配的角色" />
      </div>

      <el-dialog v-model="showEditDialog" title="编辑角色" width="600px">
        <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
          <el-form-item label="角色名称" prop="role_name">
            <el-input v-model="editForm.role_name" placeholder="请输入角色名称" />
          </el-form-item>
          <el-form-item label="角色描述">
            <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入角色描述" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" :loading="editLoading" @click="handleUpdate">保存</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { roleService } from '../../services/user'

const loading = ref(false)
const searchQuery = ref('')
const searched = ref(false)
const searchResult = ref(null)
const showEditDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref(null)

const editForm = reactive({
  role_id: '',
  role_name: '',
  description: ''
})

const editRules = {
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入角色ID')
    return
  }

  loading.value = true
  searched.value = true
  searchResult.value = null

  try {
    const res = await roleService.getById(searchQuery.value.trim())
    searchResult.value = res.data
  } catch (error) {
    console.error('Search failed:', error)
    searchResult.value = null
  } finally {
    loading.value = false
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
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success(`${label}已复制`)
  }
}

const handleEdit = () => {
  editForm.role_id = searchResult.value.role_id
  editForm.role_name = searchResult.value.role_name
  editForm.description = searchResult.value.description || ''
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        await roleService.update(editForm.role_id, {
          role_name: editForm.role_name,
          description: editForm.description || undefined
        })
        ElMessage.success('角色更新成功')
        showEditDialog.value = false
        handleSearch()
      } catch (error) {
        console.error('Update role failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除角色 ${searchResult.value.role_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await roleService.delete(searchResult.value.role_id)
    ElMessage.success('角色删除成功')
    searchResult.value = null
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete role failed:', error)
    }
  }
}
</script>

<style scoped>
.roles-search-container {
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
  margin-bottom: 24px;
}

.result-card {
  background: #f5f7fa;
  padding: 24px;
  border-radius: 8px;
}

.result-section {
  margin-top: 24px;
}

.result-section h4 {
  margin-bottom: 12px;
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
</style>
