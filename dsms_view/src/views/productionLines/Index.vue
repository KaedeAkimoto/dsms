<template>
  <div class="production-lines-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>生产线管理</span>
          <el-button type="primary" size="small" @click="handleCreate">新建生产线</el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索生产线名称"
          class="search-input"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" size="small" @click="handleSearch">搜索</el-button>
        <el-button size="small" @click="handleReset">重置</el-button>
      </div>

      <div class="result-list" v-if="tableData.length > 0">
        <el-table :data="tableData" size="small" width="100%" :height="tableHeight">
          <el-table-column prop="production_line_id" label="生产线ID" min-width="280" />
          <el-table-column prop="production_line_name" label="生产线名称" min-width="200" />
          <el-table-column prop="production_line_loc" label="生产线位置" min-width="200" />
          <el-table-column prop="production_line_manager" label="管理员" min-width="200" />
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleViewDetail(row)">查看</el-button>
              <el-button type="warning" size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

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
      </div>

      <div v-else class="empty-state">
        <el-empty :description="searchKeyword ? '未找到匹配的生产线' : '暂无生产线数据'" />
      </div>
    </el-card>

    <el-dialog v-model="showDetailDialog" title="生产线详情" width="500px">
      <el-descriptions :column="1" border v-if="selectedLine">
        <el-descriptions-item label="生产线ID">{{ selectedLine.production_line_id }}</el-descriptions-item>
        <el-descriptions-item label="生产线名称">{{ selectedLine.production_line_name }}</el-descriptions-item>
        <el-descriptions-item label="生产线位置">{{ selectedLine.production_line_loc }}</el-descriptions-item>
        <el-descriptions-item label="管理员">{{ selectedLine.production_line_manager || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(selectedLine.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(selectedLine.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="showEditDialog" :title="isEdit ? '编辑生产线' : '新建生产线'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="生产线名称" prop="production_line_name">
          <el-input v-model="form.production_line_name" placeholder="请输入生产线名称" />
        </el-form-item>
        <el-form-item label="生产线位置" prop="production_line_loc">
          <el-input v-model="form.production_line_loc" placeholder="请输入生产线位置" />
        </el-form-item>
        <el-form-item label="管理员" prop="production_line_manager">
          <el-select
            v-model="form.production_line_manager"
            filterable
            remote
            reserve-keyword
            placeholder="请选择管理员"
            :remote-method="loadUsers"
            :loading="userLoading"
            clearable
          >
            <el-option
              v-for="user in userOptions"
              :key="user.user_id"
              :label="`${user.real_name} (${user.user_name})`"
              :value="user.user_id"
            />
          </el-select>
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
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { productionLineService } from '../../services/productionLine'
import { userService } from '../../services/user'

const loading = ref(false)
const searchKeyword = ref('')
const tableData = ref([])
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const isEdit = ref(false)
const selectedLine = ref(null)
const userLoading = ref(false)
const userOptions = ref([])

const formRef = ref(null)
const form = reactive({
  production_line_name: '',
  production_line_loc: '',
  production_line_manager: ''
})

const rules = {
  production_line_name: [{ required: true, message: '请输入生产线名称', trigger: 'blur' }],
  production_line_loc: [{ required: true, message: '请输入生产线位置', trigger: 'blur' }]
}

const tableHeight = computed(() => {
  return 'calc(100vh - 320px)'
})

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const skip = (pagination.page - 1) * pagination.limit
    const res = await productionLineService.getList({
      skip,
      limit: pagination.limit
    })
    const lines = res.data?.production_lines || []
    
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      tableData.value = lines.filter(line => 
        (line.production_line_name || '').toLowerCase().includes(keyword) ||
        (line.production_line_id || '').toLowerCase().includes(keyword)
      )
    } else {
      tableData.value = lines
    }
    
    pagination.total = res.data?.total || lines.length
  } catch (error) {
    console.error('Load production lines failed:', error)
    ElMessage.error('加载生产线失败')
  } finally {
    loading.value = false
  }
}

const loadUsers = async (query) => {
  if (!query) {
    userOptions.value = []
    return
  }
  userLoading.value = true
  try {
    const res = await userService.search({ keyword: query, limit: 50 })
    userOptions.value = res.data?.users || []
  } catch (error) {
    console.error('Load users failed:', error)
  } finally {
    userLoading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchKeyword.value = ''
  handleSearch()
}

const handleSizeChange = (val) => {
  pagination.limit = val
  loadData()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  loadData()
}

const handleViewDetail = (row) => {
  selectedLine.value = row
  showDetailDialog.value = true
}

const handleCreate = () => {
  isEdit.value = false
  form.production_line_name = ''
  form.production_line_loc = ''
  form.production_line_manager = ''
  showEditDialog.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  form.production_line_name = row.production_line_name
  form.production_line_loc = row.production_line_loc
  form.production_line_manager = row.production_line_manager
  showEditDialog.value = true
}

const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate(async (valid) => {
      if (valid) {
        loading.value = true
        if (isEdit.value) {
          await productionLineService.update(selectedLine.value.production_line_id, form)
          ElMessage.success('更新成功')
        } else {
          await productionLineService.create(form)
          ElMessage.success('创建成功')
        }
        showEditDialog.value = false
        loadData()
      }
    })
  } catch (error) {
    console.error('Save production line failed:', error)
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这条生产线吗？', '确认删除', {
      type: 'warning'
    })
    await productionLineService.delete(row.production_line_id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete production line failed:', error)
    }
  }
}

loadData()
</script>

<style scoped>
.production-lines-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.result-list {
  margin-top: 16px;
}

.pagination-wrapper {
  margin-top: 16px;
  text-align: right;
}

.empty-state {
  padding: 40px 0;
}
</style>
