<template>
  <div class="departments-search-container">
    <el-card style="display: flex; flex-direction: column; height: calc(100vh - 160px);">
      <template #header>
        <div class="card-header">
          <span>部门查找</span>
        </div>
      </template>

      <div class="search-section">
        <div class="section-title">精准查找</div>
        <div class="search-form">
          <el-input
            v-model="searchQuery"
            placeholder="输入部门ID进行精准查找"
            style="width: 400px; margin-right: 16px;"
            clearable
            @keyup.enter="handleSearch"
          />
          <el-button type="primary" @click="handleSearch">查找</el-button>
        </div>
      </div>

      <div v-if="searchResult" class="result-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="部门ID">
            <div style="display: flex; gap: 8px; align-items: center;">
              <span>{{ searchResult.department_id }}</span>
              <el-button size="small" @click="copyToClipboard(searchResult.department_id, '部门ID')">复制</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="部门名称">{{ searchResult.department_name }}</el-descriptions-item>
          <el-descriptions-item label="部门描述" :span="2">{{ searchResult.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ searchResult.created_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="result-actions">
          <el-button type="primary" @click="handleEdit">编辑</el-button>
          <el-button type="danger" @click="handleDelete">删除</el-button>
        </div>
      </div>

      <div v-else-if="searched" class="no-result">
        <el-empty description="未找到匹配的部门" />
      </div>

      <div class="search-section" style="margin-top: 24px;">
        <div class="section-title">模糊搜索</div>
        <div class="search-form">
          <el-input
            v-model="fuzzyQuery"
            placeholder="输入部门名称或编号搜索"
            style="width: 400px; margin-right: 16px;"
            clearable
            @keyup.enter="handleFuzzySearch"
          />
          <el-button type="primary" @click="handleFuzzySearch">搜索</el-button>
          <el-button @click="handleClearFuzzy">清空</el-button>
        </div>
      </div>

      <div v-if="fuzzyResults.length > 0" class="fuzzy-results">
        <el-table :data="fuzzyResults" size="small" style="width: 100%; height: 100%;">
          <el-table-column prop="department_id" label="部门ID" width="100" />
          <el-table-column prop="department_code" label="部门编码" width="120" />
          <el-table-column prop="department_name" label="部门名称" />
          <el-table-column prop="parent_id" label="上级部门ID" width="120">
            <template #default="{ row }">
              {{ row.parent_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleViewDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else-if="fuzzySearched" class="no-result">
        <el-empty description="未找到匹配的部门" />
      </div>

      <el-dialog v-model="showViewDialog" title="部门详情" width="500px">
        <el-descriptions :column="1" border v-if="viewData">
          <el-descriptions-item label="部门ID">{{ viewData.department_id }}</el-descriptions-item>
          <el-descriptions-item label="部门编码">{{ viewData.department_code }}</el-descriptions-item>
          <el-descriptions-item label="部门名称">{{ viewData.department_name }}</el-descriptions-item>
          <el-descriptions-item label="上级部门ID">{{ viewData.parent_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ viewData.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ viewData.created_at || '-' }}</el-descriptions-item>
        </el-descriptions>
        <template #footer>
          <el-button @click="showViewDialog = false">关闭</el-button>
          <el-button type="primary" @click="handleEditFromView">编辑</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showEditDialog" title="编辑部门" width="500px">
        <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
          <el-form-item label="部门名称" prop="department_name">
            <el-input v-model="editForm.department_name" placeholder="请输入部门名称" />
          </el-form-item>
          <el-form-item label="部门描述">
            <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入部门描述" />
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
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { departmentService } from '../../services/user'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const searchQuery = ref('')
const searched = ref(false)
const searchResult = ref(null)
const showEditDialog = ref(false)
const showViewDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref(null)
const viewData = ref(null)

const fuzzyQuery = ref('')
const fuzzyResults = ref([])
const fuzzySearched = ref(false)

const editForm = reactive({
  department_id: '',
  department_name: '',
  description: ''
})

const editRules = {
  department_name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入部门ID')
    return
  }

  loading.value = true
  searched.value = true
  searchResult.value = null

  try {
    const res = await departmentService.getById(searchQuery.value.trim())
    searchResult.value = res.data
  } catch (error) {
    console.error('Search failed:', error)
    searchResult.value = null
  } finally {
    loading.value = false
  }
}

const handleFuzzySearch = async () => {
  if (!fuzzyQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  fuzzySearched.value = true

  try {
    const res = await departmentService.search({
      keyword: fuzzyQuery.value.trim(),
      skip: 0,
      limit: 100
    })
    fuzzyResults.value = res.data?.departments || []
  } catch (error) {
    console.error('Fuzzy search failed:', error)
    fuzzyResults.value = []
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

const handleClearFuzzy = () => {
  fuzzyQuery.value = ''
  fuzzyResults.value = []
  fuzzySearched.value = false
}

const handleViewDetail = (row) => {
  viewData.value = {
    ...row,
    created_at: row.created_at ? formatDateTime(row.created_at) : '-'
  }
  showViewDialog.value = true
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

const handleEditFromView = () => {
  showViewDialog.value = false
  handleEdit(viewData.value)
}

const handleEdit = () => {
  editForm.department_id = searchResult.value?.department_id || viewData.value?.department_id
  editForm.department_name = searchResult.value?.department_name || viewData.value?.department_name
  editForm.description = (searchResult.value?.description || viewData.value?.description) || ''
  showEditDialog.value = true
  showViewDialog.value = false
}

const handleUpdate = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        await departmentService.update(editForm.department_id, {
          department_name: editForm.department_name,
          description: editForm.description || undefined
        })
        ElMessage.success('部门更新成功')
        showEditDialog.value = false
        handleSearch()
      } catch (error) {
        console.error('Update department failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除部门 ${searchResult.value.department_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await departmentService.delete(searchResult.value.department_id)
    ElMessage.success('部门删除成功')
    searchResult.value = null
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete department failed:', error)
    }
  }
}
</script>

<style scoped>
.departments-search-container {
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

.search-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 500;
}

.search-form {
  display: flex;
  align-items: center;
}

.result-card {
  background: #f5f7fa;
  padding: 24px;
  border-radius: 8px;
}

.result-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.no-result {
  padding: 40px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fuzzy-results {
  margin-top: 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
