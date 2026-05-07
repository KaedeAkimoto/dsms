<template>
  <div class="departments-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>部门管理</span>
          <div class="header-actions">
            <el-button-group>
              <el-button :type="viewMode === 'table' ? 'primary' : 'default'" @click="viewMode = 'table'">表格视图</el-button>
              <el-button :type="viewMode === 'tree' ? 'primary' : 'default'" @click="switchToTree">树形视图</el-button>
            </el-button-group>
            <el-button type="primary" @click="showCreateDialog = true">创建部门</el-button>
          </div>
        </div>
      </template>

      <div v-if="viewMode === 'table'" class="table-wrapper">
        <el-table 
          :data="tableData" 
          v-loading="loading" 
          style="width: 100%;"
          height="100%"
          :header-cell-style="{ position: 'sticky', top: 0, zIndex: 1 }"
        >
          <el-table-column prop="department_id" label="部门ID" width="100" />
          <el-table-column prop="department_code" label="部门编码" width="120" />
          <el-table-column prop="department_name" label="部门名称" />
          <el-table-column prop="parent_id" label="上级部门ID" width="120" />
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="info" size="small" @click="handleView(row)">查看</el-button>
                <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
              </div>
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

      <div v-else class="tree-wrapper">
        <div class="tree-stats">
          <span>部门总数：{{ totalNodes }}</span>
        </div>
        <div class="tree-container" ref="treeContainer">
          <svg class="tree-svg" :width="svgWidth" :height="svgHeight">
            <g v-for="(link, index) in treeLinks" :key="'link-' + index">
              <path :d="link.path" class="tree-link" />
            </g>
          </svg>
          <div class="tree-nodes" :style="{ width: svgWidth + 'px', height: svgHeight + 'px' }">
            <div
              v-for="node in treeNodes"
              :key="node.id"
              class="tree-node-card"
              :style="{ left: node.x + 'px', top: node.y + 'px' }"
              @click="handleNodeClick(node.data)"
            >
              <div class="node-icon">
                <el-icon><OfficeBuilding /></el-icon>
              </div>
              <div class="node-info">
                <div class="node-name">{{ node.data.department_name }}</div>
                <div class="node-code">{{ node.data.department_code }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="showViewDialog" title="部门详情" width="500px">
      <el-descriptions :column="1" border v-if="viewData">
        <el-descriptions-item label="部门ID">{{ viewData.department_id }}</el-descriptions-item>
        <el-descriptions-item label="部门编码">{{ viewData.department_code }}</el-descriptions-item>
        <el-descriptions-item label="部门名称">{{ viewData.department_name }}</el-descriptions-item>
        <el-descriptions-item label="上级部门ID">{{ viewData.parent_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ viewData.created_at }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleEditFromView">编辑</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateDialog" title="创建部门" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="部门编码" prop="department_code">
          <el-input v-model="createForm.department_code" placeholder="请输入部门编码" />
        </el-form-item>
        <el-form-item label="部门名称" prop="department_name">
          <el-input v-model="createForm.department_name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="上级部门" prop="parent_id">
          <el-input-number v-model="createForm.parent_id" :min="0" placeholder="上级部门ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑部门" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="部门编码" prop="department_code">
          <el-input v-model="editForm.department_code" placeholder="请输入部门编码" />
        </el-form-item>
        <el-form-item label="部门名称" prop="department_name">
          <el-input v-model="editForm.department_name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="上级部门" prop="parent_id">
          <el-input-number v-model="editForm.parent_id" :min="0" />
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { OfficeBuilding } from '@element-plus/icons-vue'
import { departmentService } from '../../services/user'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const viewMode = ref('table')
const tableData = ref([])
const treeData = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showViewDialog = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const treeContainer = ref(null)

const viewData = ref(null)

const NODE_WIDTH = 160
const NODE_HEIGHT = 60
const LEVEL_HEIGHT = 100
const HORIZONTAL_SPACING = 40

const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0
})

const createForm = reactive({
  department_code: '',
  department_name: '',
  parent_id: null
})

const editForm = reactive({
  department_id: null,
  department_code: '',
  department_name: '',
  parent_id: null
})

const createRules = {
  department_code: [{ required: true, message: '请输入部门编码', trigger: 'blur' }],
  department_name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const editRules = {
  department_code: [{ required: true, message: '请输入部门编码', trigger: 'blur' }],
  department_name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const treeNodes = computed(() => {
  const nodes = []
  const processNode = (data, depth = 0, startX = 0) => {
    if (!data) return 0
    
    const children = data.children || []
    let totalChildWidth = 0
    
    if (children.length > 0) {
      children.forEach(child => {
        totalChildWidth += processNode(child, depth + 1, startX + totalChildWidth)
      })
    }
    
    const nodeWidth = totalChildWidth > 0 ? totalChildWidth : NODE_WIDTH
    const x = startX + (nodeWidth - NODE_WIDTH) / 2
    const y = depth * LEVEL_HEIGHT
    
    nodes.push({
      id: data.department_id,
      x,
      y,
      data,
      children
    })
    
    if (children.length > 0) {
      let childX = startX
      children.forEach(child => {
        const childNode = nodes.find(n => n.id === child.department_id)
        if (childNode) {
          childNode.x = childX + (NODE_WIDTH - NODE_WIDTH) / 2
          childX += getSubtreeWidth(child)
        }
      })
    }
    
    return Math.max(nodeWidth, children.reduce((sum, c) => sum + getSubtreeWidth(c), 0))
  }
  
  let startX = 0
  treeData.value.forEach(rootNode => {
    const subtreeWidth = getSubtreeWidth(rootNode)
    processNode(rootNode, 0, startX)
    startX += subtreeWidth + HORIZONTAL_SPACING
  })
  
  return nodes
})

const treeLinks = computed(() => {
  const links = []
  
  const processLinks = (data) => {
    if (!data) return
    
    const parentNode = treeNodes.value.find(n => n.id === data.department_id)
    if (!parentNode) return
    
    const children = data.children || []
    children.forEach(child => {
      const childNode = treeNodes.value.find(n => n.id === child.department_id)
      if (childNode) {
        const parentCenterX = parentNode.x + NODE_WIDTH / 2
        const parentBottomY = parentNode.y + NODE_HEIGHT
        const childCenterX = childNode.x + NODE_WIDTH / 2
        const childTopY = childNode.y
        
        const midY = (parentBottomY + childTopY) / 2
        
        links.push({
          path: `M ${parentCenterX} ${parentBottomY} 
                L ${parentCenterX} ${midY} 
                L ${childCenterX} ${midY} 
                L ${childCenterX} ${childTopY}`
        })
      }
      processLinks(child)
    })
  }
  
  treeData.value.forEach(rootNode => {
    processLinks(rootNode)
  })
  
  return links
})

const svgWidth = computed(() => {
  if (treeNodes.value.length === 0) return 800
  const maxX = Math.max(...treeNodes.value.map(n => n.x)) + NODE_WIDTH
  return Math.max(maxX + 40, 800)
})

const svgHeight = computed(() => {
  if (treeNodes.value.length === 0) return 400
  const maxY = Math.max(...treeNodes.value.map(n => n.y)) + NODE_HEIGHT
  return Math.max(maxY + 40, 400)
})

const totalNodes = computed(() => {
  let count = 0
  const countNodes = (data) => {
    if (!data) return
    count++
    ;(data.children || []).forEach(countNodes)
  }
  treeData.value.forEach(countNodes)
  return count
})

function getSubtreeWidth(data) {
  if (!data || !data.children || data.children.length === 0) {
    return NODE_WIDTH + HORIZONTAL_SPACING
  }
  const childrenWidth = data.children.reduce((sum, child) => sum + getSubtreeWidth(child), 0)
  return Math.max(NODE_WIDTH, childrenWidth)
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await departmentService.getList({
      skip: (pagination.page - 1) * pagination.limit,
      limit: pagination.limit
    })
    const departments = res.data.departments || []
    for (const dept of departments) {
      dept.created_at = formatDateTime(dept.created_at)
    }
    tableData.value = departments
    pagination.total = res.data.total || 0
  } catch (error) {
    console.error('Load departments failed:', error)
  } finally {
    loading.value = false
  }
}

const loadTreeData = async () => {
  loading.value = true
  try {
    const res = await departmentService.getTree()
    treeData.value = res.data || []
  } catch (error) {
    console.error('Load tree data failed:', error)
    ElMessage.error('加载部门树形结构失败')
  } finally {
    loading.value = false
  }
}

const switchToTree = () => {
  viewMode.value = 'tree'
  if (treeData.value.length === 0) {
    loadTreeData()
  }
}

const handleNodeClick = async (data) => {
  try {
    const res = await departmentService.getById(data.department_id)
    viewData.value = {
      ...res.data,
      created_at: formatDateTime(res.data.created_at)
    }
    showViewDialog.value = true
  } catch (error) {
    console.error('Get department detail failed:', error)
    ElMessage.error('获取部门详情失败')
  }
}

const handleView = (row) => {
  viewData.value = {
    ...row,
    created_at: row.created_at
  }
  showViewDialog.value = true
}

const handleEditFromView = () => {
  showViewDialog.value = false
  handleEdit(viewData.value)
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
        await departmentService.create({
          department_code: createForm.department_code,
          department_name: createForm.department_name,
          parent_id: createForm.parent_id || undefined
        })
        ElMessage.success('部门创建成功')
        showCreateDialog.value = false
        createForm.department_code = ''
        createForm.department_name = ''
        createForm.parent_id = null
        loadData()
        if (viewMode.value === 'tree') {
          loadTreeData()
        }
      } catch (error) {
        console.error('Create department failed:', error)
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleEdit = (row) => {
  editForm.department_id = row.department_id
  editForm.department_code = row.department_code
  editForm.department_name = row.department_name
  editForm.parent_id = row.parent_id
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true
      try {
        await departmentService.update(editForm.department_id, {
          department_code: editForm.department_code,
          department_name: editForm.department_name,
          parent_id: editForm.parent_id || undefined
        })
        ElMessage.success('部门更新成功')
        showEditDialog.value = false
        loadData()
        if (viewMode.value === 'tree') {
          loadTreeData()
        }
      } catch (error) {
        console.error('Update department failed:', error)
      } finally {
        editLoading.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除部门 ${row.department_name} 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await departmentService.delete(row.department_id)
    ElMessage.success('部门删除成功')
    loadData()
    if (viewMode.value === 'tree') {
      loadTreeData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete department failed:', error)
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.departments-container {
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

.header-actions {
  display: flex;
  gap: 12px;
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

.tree-wrapper {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.tree-stats {
  padding: 8px 0 16px 0;
  font-size: 14px;
  color: #606266;
}

.tree-container {
  position: relative;
  min-height: 400px;
}

.tree-svg {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.tree-link {
  fill: none;
  stroke: #409eff;
  stroke-width: 2;
}

.tree-nodes {
  position: relative;
}

.tree-node-card {
  position: absolute;
  width: 160px;
  height: 60px;
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.tree-node-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.5);
}

.node-icon {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  flex-shrink: 0;
}

.node-icon .el-icon {
  color: #fff;
  font-size: 18px;
}

.node-info {
  overflow: hidden;
}

.node-name {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-code {
  color: rgba(255, 255, 255, 0.8);
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
