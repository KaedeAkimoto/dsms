<template>
  <div class="production-lines-search-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>生产线查找</span>
        </div>
      </template>

      <div class="search-form">
        <el-input
          v-model="searchId"
          placeholder="请输入生产线ID"
          style="width: 300px; margin-right: 16px;"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleClear">清空</el-button>
      </div>

      <div v-if="searched && result" class="result-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="生产线ID">{{ result.production_line_id }}</el-descriptions-item>
          <el-descriptions-item label="生产线名称">{{ result.line_name }}</el-descriptions-item>
          <el-descriptions-item label="生产线位置">{{ result.line_code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ result.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(result.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(result.updated_at) }}</el-descriptions-item>
        </el-descriptions>
        <div class="result-actions">
          <el-button type="warning" size="small" @click="handleEdit(result)">编辑</el-button>
        </div>
      </div>

      <div v-else-if="searched && !result" class="no-result">
        <el-empty description="未找到该生产线" />
      </div>
    </el-card>

    <el-card style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <span>模糊搜索</span>
        </div>
      </template>

      <div class="search-form">
        <el-input
          v-model="keyword"
          placeholder="输入生产线名称或编号搜索"
          style="width: 300px; margin-right: 16px;"
          clearable
          @keyup.enter="handleFuzzySearch"
        />
        <el-button type="primary" @click="handleFuzzySearch">搜索</el-button>
        <el-button @click="handleClearFuzzy">清空</el-button>
      </div>

      <div v-if="fuzzyResults.length > 0" class="fuzzy-results">
        <el-table :data="fuzzyResults" size="small" max-height="400">
          <el-table-column prop="production_line_id" label="生产线ID" min-width="280" />
          <el-table-column prop="line_name" label="生产线名称" min-width="200" />
          <el-table-column prop="line_code" label="生产线位置" min-width="200" />
          <el-table-column prop="description" label="描述" min-width="250">
            <template #default="{ row }">
              {{ row.description || '-' }}
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
        <el-empty description="未找到匹配的生产线" />
      </div>
    </el-card>

    <el-dialog v-model="showDetailDialog" title="生产线详情" width="500px">
      <el-descriptions :column="1" border v-if="selectedLine">
        <el-descriptions-item label="生产线ID">{{ selectedLine.production_line_id }}</el-descriptions-item>
        <el-descriptions-item label="生产线名称">{{ selectedLine.line_name }}</el-descriptions-item>
        <el-descriptions-item label="生产线位置">{{ selectedLine.line_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ selectedLine.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(selectedLine.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(selectedLine.updated_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="warning" @click="handleEditFromDetail">编辑</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑生产线" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="生产线名称" prop="line_name">
          <el-input v-model="form.line_name" placeholder="请输入生产线名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { productionLineService } from '../../services/productionLine'

const loading = ref(false)
const searchId = ref('')
const searched = ref(false)
const result = ref(null)
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const selectedLine = ref(null)

const keyword = ref('')
const fuzzyResults = ref([])
const fuzzySearched = ref(false)

const formRef = ref(null)
const form = reactive({
  line_name: '',
  description: ''
})

const rules = {
  line_name: [{ required: true, message: '请输入生产线名称', trigger: 'blur' }]
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const handleSearch = async () => {
  if (!searchId.value.trim()) {
    ElMessage.warning('请输入生产线ID')
    return
  }

  loading.value = true
  searched.value = true

  try {
    const res = await productionLineService.getById(searchId.value.trim())
    result.value = res.data
  } catch (error) {
    console.error('Search production line failed:', error)
    result.value = null
    ElMessage.error('未找到该生产线')
  } finally {
    loading.value = false
  }
}

const handleClear = () => {
  searchId.value = ''
  result.value = null
  searched.value = false
}

const handleFuzzySearch = async () => {
  if (!keyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  fuzzySearched.value = true

  try {
    const res = await productionLineService.search({
      keyword: keyword.value.trim(),
      skip: 0,
      limit: 100
    })
    fuzzyResults.value = res.data?.production_lines || []
  } catch (error) {
    console.error('Fuzzy search failed:', error)
    fuzzyResults.value = []
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

const handleClearFuzzy = () => {
  keyword.value = ''
  fuzzyResults.value = []
  fuzzySearched.value = false
}

const handleViewDetail = (line) => {
  selectedLine.value = line
  showDetailDialog.value = true
}

const handleEditFromDetail = () => {
  showDetailDialog.value = false
  form.line_name = selectedLine.value.line_name
  form.description = selectedLine.value.description || ''
  showEditDialog.value = true
}

const handleEdit = (line) => {
  selectedLine.value = line
  form.line_name = line.line_name
  form.description = line.description || ''
  showEditDialog.value = true
}

const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    await productionLineService.update(selectedLine.value.production_line_id, {
      line_name: form.line_name,
      description: form.description
    })
    
    ElMessage.success('编辑成功')
    showEditDialog.value = false
    
    if (result.value && result.value.production_line_id === selectedLine.value.production_line_id) {
      handleSearch()
    }
    if (fuzzyResults.value.length > 0) {
      handleFuzzySearch()
    }
  } catch (error) {
    console.error('Update production line failed:', error)
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped>
.production-lines-search-container {
  padding: 16px;
  height: calc(100vh - 160px);
  box-sizing: border-box;
}

:deep(.el-card) {
  height: auto;
}

:deep(.el-card__body) {
  overflow: auto;
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}

.search-form {
  margin-bottom: 16px;
}

.result-detail {
  margin-top: 16px;
}

.result-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.no-result {
  margin-top: 40px;
  text-align: center;
}

.fuzzy-results {
  margin-top: 16px;
}
</style>
