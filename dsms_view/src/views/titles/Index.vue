<template>
  <div class="titles-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>职称管理</span>
          <el-button type="primary" @click="showCreateDialog = true">创建职称</el-button>
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
          <el-table-column prop="title_id" label="职称ID" width="100" />
          <el-table-column prop="title_name" label="职称名称" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="showCreateDialog" title="创建职称" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="职称名称" prop="title_name">
          <el-input v-model="createForm.title_name" placeholder="请输入职称名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑职称" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="职称名称" prop="title_name">
          <el-input v-model="editForm.title_name" placeholder="请输入职称名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { titleService } from '../../services/user'

const loading = ref(false)
const tableData = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const createForm = reactive({
  title_name: ''
})

const editForm = reactive({
  title_id: null,
  title_name: ''
})

const createRules = {
  title_name: [{ required: true, message: '请输入职称名称', trigger: 'blur' }]
}

const editRules = {
  title_name: [{ required: true, message: '请输入职称名称', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await titleService.getList({
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    })
    tableData.value = res.data.titles || []
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('Load titles failed:', error)
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
        await titleService.create({
          title_name: createForm.title_name
        })
        ElMessage.success('职称创建成功')
        showCreateDialog.value = false
        createForm.title_name = ''
        loadData()
      } catch (error) {
        console.error('Create title failed:', error)
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleEdit = (row) => {
  editForm.title_id = row.title_id
  editForm.title_name = row.title_name
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        await titleService.update(editForm.title_id, {
          title_name: editForm.title_name
        })
        ElMessage.success('职称更新成功')
        showEditDialog.value = false
        loadData()
      } catch (error) {
        console.error('Update title failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除职称 ${row.title_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await titleService.delete(row.title_id)
    ElMessage.success('职称删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete title failed:', error)
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.titles-container {
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
</style>
