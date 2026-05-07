<template>
  <div class="messages-container">
    <el-card style="height: 100%; display: flex; flex-direction: column;">
      <template #header>
        <div class="card-header">
          <span>我的消息</span>
          <el-button type="primary" size="small" @click="handleMarkAllAsRead">
            全部标为已读
          </el-button>
        </div>
      </template>

      <div class="message-list" v-loading="loading">
        <div
          v-for="item in conversationList"
          :key="item.key"
          class="message-item"
          :class="{ unread: item.unreadCount > 0 }"
          @click="handleViewConversation(item)"
        >
          <div class="avatar" @click.stop="item.type !== 'system' && handleViewUserDetail(item.user_id)">
            <el-icon v-if="item.type === 'system'"><Warning /></el-icon>
            <el-icon v-else><User /></el-icon>
          </div>
          <div class="content-wrapper">
            <div class="header">
              <span class="sender">
                {{ item.name }}
              </span>
              <span class="time">{{ item.latestTime }}</span>
            </div>
            <div class="message-preview">
              {{ item.latestContent }}
            </div>
          </div>
          <div v-if="item.unreadCount > 0" class="unread-badge">
            {{ item.unreadCount > 99 ? '99+' : item.unreadCount }}
          </div>
        </div>

        <div v-if="conversationList.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无消息" />
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="showChatDialog"
      :title="currentConversation.name || '聊天'"
      width="600px"
      class="chat-dialog"
      @closed="handleChatClosed"
    >
      <div class="chat-messages" ref="chatMessagesRef">
        <div
          v-for="(msg, index) in sortedMessages"
          :key="msg.msg_id"
          class="message-bubble"
          :class="getMessageBubbleClass(msg)"
        >
          <div class="bubble-avatar" v-if="!isSystemMessage(msg)" @click="handleViewUserDetailFromMsg(msg)">
            <el-icon><User /></el-icon>
          </div>
          <div class="bubble-content">
            <div class="bubble-header">
              <span class="bubble-sender">
                {{ getMessageSenderName(msg) }}
              </span>
              <span class="bubble-time">{{ msg.created_at }}</span>
            </div>
            <div class="bubble-text">{{ msg.content }}</div>
            <div class="bubble-footer" v-if="!isSystemMessage(msg)">
              <el-tag v-if="msg.status === 'unread'" type="warning" size="small">未读</el-tag>
              <el-tag v-else type="success" size="small">已读</el-tag>
            </div>
          </div>
        </div>
      </div>
      <div class="chat-input" v-if="currentConversation.type === 'user'">
        <el-input
          v-model="newMessageContent"
          placeholder="输入消息内容..."
          class="message-input"
          @keyup.enter="handleSendMessage"
        />
        <el-button type="primary" @click="handleSendMessage" :disabled="!newMessageContent.trim()">发送</el-button>
      </div>
      <template #footer>
        <el-button @click="showChatDialog = false">关闭</el-button>
        <el-button v-if="hasUnreadMessages" type="primary" @click="handleMarkConversationAsRead">
          标记已读
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showUserDetailDialog" title="用户详情" width="500px">
      <el-form :model="viewUserForm" label-width="100px">
        <el-form-item label="用户ID">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input v-model="viewUserForm.user_id" disabled style="flex: 1;" />
            <el-button @click="copyToClipboard(viewUserForm.user_id, '用户ID')">复制</el-button>
          </div>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="viewUserForm.user_name" disabled />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="viewUserForm.real_name" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="viewUserForm.email" disabled />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="viewUserForm.phone" disabled />
        </el-form-item>
        <el-form-item label="工号">
          <div style="display: flex; gap: 8px; width: 100%;">
            <el-input v-model="viewUserForm.employee_id" disabled style="flex: 1;" />
            <el-button @click="copyToClipboard(viewUserForm.employee_id, '工号')">复制</el-button>
          </div>
        </el-form-item>
        <el-form-item label="角色">
          <el-input v-model="viewUserForm.role_name" disabled />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="viewUserForm.department_name" disabled />
        </el-form-item>
        <el-form-item label="职称">
          <el-input v-model="viewUserForm.title_name" disabled />
        </el-form-item>
        <el-form-item label="最后登录">
          <el-input v-model="viewUserForm.last_login" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUserDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'Messages' })
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning, User, ChatDotRound } from '@element-plus/icons-vue'
import { messageService } from '../../services/message'
import { userService, departmentService, titleService, roleService } from '../../services/user'
import { formatDateTime } from '../../utils/date'

const loading = ref(false)
const cachedMessages = reactive({
  system: [],
  received: [],
  sent: []
})
const showChatDialog = ref(false)
const currentConversation = ref({})
const chatMessagesRef = ref(null)
const showUserDetailDialog = ref(false)
const newMessageContent = ref('')

const viewUserForm = reactive({
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

const userCache = ref({})
const roleMap = ref({})
const departmentMap = ref({})
const titleMap = ref({})

const formatUserName = (user) => {
  if (!user) return '未知用户'
  const userName = user.real_name || user.user_name || '未知用户'
  const deptName = user.department_name || '暂无部门'
  const titleName = user.title_name || '暂无职称'
  return `${userName}-${deptName}-${titleName}`
}

const conversationList = computed(() => {
  const conversations = {}
  
  if (cachedMessages.system.length > 0) {
    const systemMessages = cachedMessages.system
    const latestMsg = systemMessages.reduce((latest, msg) => 
      new Date(msg.created_at) > new Date(latest.created_at) ? msg : latest
    )
    const unreadCount = systemMessages.filter(msg => msg.status === 'unread').length
    
    conversations['system'] = {
      key: 'system',
      type: 'system',
      name: '系统',
      latestContent: latestMsg.content.length > 50 ? latestMsg.content.substring(0, 50) + '...' : latestMsg.content,
      latestTime: latestMsg.created_at,
      unreadCount,
      messages: systemMessages
    }
  }
  
  const userMessages = [...cachedMessages.received, ...cachedMessages.sent]
  userMessages.forEach(msg => {
    let userId
    let displayName
    
    if (msg.type === 'received') {
      userId = msg.send_user
      const user = userCache.value[userId]
      displayName = formatUserName(user)
    } else {
      userId = msg.receive_user
      const user = userCache.value[userId]
      displayName = formatUserName(user)
    }
    
    const key = `user-${userId}`
    
    if (!conversations[key]) {
      conversations[key] = {
        key,
        type: 'user',
        user_id: userId,
        name: displayName,
        latestContent: msg.content,
        latestTime: msg.created_at,
        unreadCount: (msg.type === 'received' && msg.status === 'unread') ? 1 : 0,
        messages: [msg]
      }
    } else {
      conversations[key].messages.push(msg)
      if (msg.created_at > conversations[key].latestTime) {
        conversations[key].latestContent = msg.content.length > 50 ? msg.content.substring(0, 50) + '...' : msg.content
        conversations[key].latestTime = msg.created_at
      }
      if (msg.type === 'received' && msg.status === 'unread') {
        conversations[key].unreadCount++
      }
    }
  })
  
  return Object.values(conversations).sort((a, b) => 
    new Date(b.latestTime) - new Date(a.latestTime)
  )
})

const sortedMessages = computed(() => {
  return [...(currentConversation.value.messages || [])].sort((a, b) => 
    new Date(a.created_at) - new Date(b.created_at)
  )
})

const hasUnreadMessages = computed(() => {
  return sortedMessages.value.some(msg => msg.type !== 'sent' && msg.status === 'unread')
})

const loadAllMessages = async () => {
  const cache = messageService.getCache()
  if (cache.loaded) {
    cachedMessages.system = [...cache.systemMessages]
    cachedMessages.received = [...cache.receivedMessages]
    cachedMessages.sent = [...cache.sentMessages]
    return
  }
  
  loading.value = true
  try {
    await Promise.all([
      loadAllTypeMessages('system'),
      loadAllTypeMessages('received'),
      loadAllTypeMessages('sent')
    ])
    
    messageService.setSystemMessages([...cachedMessages.system])
    messageService.setReceivedMessages([...cachedMessages.received])
    messageService.setSentMessages([...cachedMessages.sent])
    messageService.setLoaded()
  } catch (error) {
    console.error('Load messages failed:', error)
  } finally {
    loading.value = false
  }
}

const loadAllTypeMessages = async (type) => {
  let allMessages = []
  let skip = 0
  const limit = 1000
  
  try {
    let res
    if (type === 'system') {
      res = await messageService.getMyMessages({ skip: 0, limit })
    } else if (type === 'received') {
      res = await messageService.getReceivedMessages({ skip: 0, limit })
    } else {
      res = await messageService.getSentMessages({ skip: 0, limit })
    }
    
    allMessages = (res.data.messages || []).map(msg => ({
      ...msg,
      type,
      created_at: formatDateTime(msg.created_at)
    }))
    
    if (allMessages.length === limit) {
      let hasMore = true
      while (hasMore) {
        skip += limit
        let nextRes
        if (type === 'system') {
          nextRes = await messageService.getMyMessages({ skip, limit })
        } else if (type === 'received') {
          nextRes = await messageService.getReceivedMessages({ skip, limit })
        } else {
          nextRes = await messageService.getSentMessages({ skip, limit })
        }
        const nextMessages = (nextRes.data.messages || []).map(msg => ({
          ...msg,
          type,
          created_at: formatDateTime(msg.created_at)
        }))
        allMessages = allMessages.concat(nextMessages)
        hasMore = nextMessages.length === limit
      }
    }
    
    cachedMessages[type] = allMessages
  } catch (error) {
    console.error(`Load ${type} messages failed:`, error)
  }
}

const loadAllUsers = async () => {
  try {
    const allUsers = []
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
      
      allUsers.push(...users)
      skip += limit
      
      if (users.length < limit) {
        break
      }
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

const handleViewConversation = (conv) => {
  currentConversation.value = { ...conv }
  showChatDialog.value = true
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

const handleMarkSentMessagesAsRead = (msgId) => {
  const msgIndex = cachedMessages.sent.findIndex(m => m.msg_id === msgId)
  if (msgIndex !== -1) {
    cachedMessages.sent[msgIndex].status = 'read'
    messageService.setSentMessages([...cachedMessages.sent])
  }
}

const handleChatClosed = () => {
  currentConversation.value = {}
  newMessageContent.value = ''
}

const handleSendMessage = async () => {
  if (!newMessageContent.value.trim()) return
  
  const content = newMessageContent.value.trim()
  const receiveUserId = currentConversation.value.user_id
  
  try {
    const res = await messageService.sendMessage({
      receive_user: receiveUserId,
      content
    })
    
    const newMsg = {
      msg_id: (res.data.message && res.data.message.msg_id) || Date.now().toString(),
      send_user: (res.data.message && res.data.message.send_user) || '',
      receive_user: receiveUserId,
      content: content,
      type: 'sent',
      status: 'unread',
      created_at: formatDateTime(new Date().toISOString())
    }
    
    cachedMessages.sent.push(newMsg)
    messageService.setSentMessages([...cachedMessages.sent])
    
    if (currentConversation.value.key === `user-${receiveUserId}`) {
      currentConversation.value = {
        ...currentConversation.value,
        messages: [...currentConversation.value.messages, newMsg],
        latestContent: content.length > 50 ? content.substring(0, 50) + '...' : content,
        latestTime: newMsg.created_at
      }
    }
    
    ElMessage.success('消息发送成功')
    newMessageContent.value = ''
    
    nextTick(() => {
      if (chatMessagesRef.value) {
        chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
      }
    })
  } catch (error) {
    console.error('Send message failed:', error)
    ElMessage.error('消息发送失败')
  }
}

const isSystemMessage = (msg) => {
  return msg.type === 'system'
}

const getMessageBubbleClass = (msg) => {
  if (msg.type === 'system') {
    return 'system'
  } else if (msg.type === 'sent') {
    return 'right'
  } else {
    return 'left'
  }
}

const getMessageSenderName = (msg) => {
  if (msg.type === 'system') {
    return '系统'
  } else if (msg.type === 'received') {
    const user = userCache.value[msg.send_user]
    return formatUserName(user)
  } else {
    const user = userCache.value[msg.receive_user]
    return formatUserName(user)
  }
}

const handleViewUserDetail = async (userId) => {
  if (!userId) return
  
  let user = userCache.value[userId]
  
  if (!user) {
    try {
      const res = await userService.getById(userId)
      user = res.data.user
      if (user) {
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
        userCache.value[userId] = user
      }
    } catch (error) {
      console.error('Get user failed:', error)
      ElMessage.error('获取用户信息失败')
      return
    }
  }
  
  if (user) {
    viewUserForm.user_id = user.user_id || ''
    viewUserForm.user_name = user.user_name || ''
    viewUserForm.real_name = user.real_name || ''
    viewUserForm.email = user.email || ''
    viewUserForm.phone = user.phone || ''
    viewUserForm.employee_id = user.employee_id || ''
    viewUserForm.role_name = user.role_name || ''
    viewUserForm.department_name = user.department_name || ''
    viewUserForm.title_name = user.title_name || ''
    viewUserForm.last_login = user.last_login || ''
    showUserDetailDialog.value = true
  }
}

const handleViewUserDetailFromMsg = (msg) => {
  let userId
  if (msg.type === 'received') {
    userId = msg.send_user
  } else {
    userId = msg.receive_user
  }
  handleViewUserDetail(userId)
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

const handleMarkConversationAsRead = async () => {
  try {
    const unreadMessages = sortedMessages.value.filter(msg => msg.type !== 'sent' && msg.status === 'unread')
    for (const msg of unreadMessages) {
      if (msg.type === 'system') {
        await messageService.markSystemMessageAsRead(msg.msg_id)
      } else {
        await messageService.markMessageAsRead(msg.msg_id)
      }
    }
    ElMessage.success('标记已读成功')
    
    for (const msg of unreadMessages) {
      msg.status = 'read'
    }
    messageService.setLoaded(false)
    messageService.setSystemMessages([...cachedMessages.system])
    messageService.setReceivedMessages([...cachedMessages.received])
    messageService.setSentMessages([...cachedMessages.sent])
  } catch (error) {
    console.error('Mark conversation as read failed:', error)
  }
}

const handleMarkAllAsRead = async () => {
  try {
    await ElMessageBox.confirm('确定要将所有消息标记为已读吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    await Promise.all([
      messageService.markAllSystemMessagesAsRead(),
      messageService.markAllReceivedAsRead()
    ])
    ElMessage.success('全部标记已读成功')
    
    cachedMessages.system.forEach(msg => { msg.status = 'read' })
    cachedMessages.received.forEach(msg => { msg.status = 'read' })
    cachedMessages.sent.forEach(msg => { msg.status = 'read' })
    messageService.setLoaded(false)
    messageService.setSystemMessages([...cachedMessages.system])
    messageService.setReceivedMessages([...cachedMessages.received])
    messageService.setSentMessages([...cachedMessages.sent])
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Mark all as read failed:', error)
    }
  }
}

onMounted(async () => {
  if (cachedMessages.system.length === 0 && cachedMessages.received.length === 0 && cachedMessages.sent.length === 0) {
    await Promise.all([
      loadAllRoles(),
      loadAllDepartments(),
      loadAllTitles()
    ])
    await loadAllUsers()
    loadAllMessages()
  }
})
</script>

<style scoped>
.messages-container {
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
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.message-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 8px;
  position: relative;
}

.message-item:hover {
  background-color: #f5f7fa;
}

.message-item.unread {
  background-color: #ecf5ff;
}

.message-item.unread:hover {
  background-color: #d9ecff;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  flex-shrink: 0;
  cursor: pointer;
  transition: transform 0.2s;
}

.avatar:hover {
  transform: scale(1.1);
}

.content-wrapper {
  flex: 1;
  margin-left: 12px;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.sender {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.time {
  font-size: 12px;
  color: #909399;
}

.message-preview {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background-color: #f56c6c;
  color: white;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

.empty-state {
  padding: 60px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.chat-dialog .el-dialog__body) {
  padding: 0;
  height: 500px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f7fa;
}

.message-bubble {
  display: flex;
  margin-bottom: 16px;
}

.message-bubble.left {
  justify-content: flex-start;
}

.message-bubble.right {
  justify-content: flex-end;
}

.message-bubble.system {
  justify-content: center;
}

.bubble-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  flex-shrink: 0;
  cursor: pointer;
  transition: transform 0.2s;
}

.bubble-avatar:hover {
  transform: scale(1.1);
}

.message-bubble.right .bubble-avatar {
  order: 2;
  margin-left: 12px;
}

.message-bubble.left .bubble-avatar {
  margin-right: 12px;
}

.bubble-content {
  max-width: 70%;
}

.message-bubble.system .bubble-content {
  max-width: 90%;
}

.bubble-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  padding: 0 8px;
}

.message-bubble.right .bubble-header {
  flex-direction: row-reverse;
}

.bubble-sender {
  font-size: 12px;
  color: #909399;
}

.bubble-time {
  font-size: 11px;
  color: #c0c4cc;
}

.bubble-text {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-bubble.left .bubble-text {
  background-color: white;
  color: #303133;
  border-radius: 0 8px 8px 8px;
}

.message-bubble.right .bubble-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px 0 8px 8px;
}

.message-bubble.system .bubble-text {
  background-color: #e6a23c;
  color: white;
  text-align: center;
  border-radius: 8px;
  padding: 8px 16px;
}

.bubble-footer {
  margin-top: 4px;
  padding: 0 8px;
  display: flex;
  justify-content: flex-end;
}

.message-bubble.left .bubble-footer {
  justify-content: flex-start;
}

.message-bubble.system .bubble-footer {
  display: none;
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  background-color: white;
  border-top: 1px solid #e6e6e6;
}

.message-input {
  flex: 1;
}
</style>
