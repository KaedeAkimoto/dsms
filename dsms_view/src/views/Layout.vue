<template>
  <div class="layout-container">
    <el-container>
      <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
        <div class="logo">
          <h1 v-show="!isCollapse">缺陷检测管理系统</h1>
          <span v-show="isCollapse">D</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="el-menu-vertical"
          :collapse="isCollapse"
          :router="true"
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <template #title>首页</template>
          </el-menu-item>
          <el-menu-item index="/profile">
            <el-icon><User /></el-icon>
            <template #title>个人中心</template>
          </el-menu-item>
          <el-sub-menu index="/system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-sub-menu index="/system/users">
              <template #title>用户管理</template>
              <el-menu-item index="/users">用户总览</el-menu-item>
              <el-menu-item index="/users/search">用户查找</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="/system/roles">
              <template #title>角色管理</template>
              <el-menu-item index="/roles">角色总览</el-menu-item>
              <el-menu-item index="/roles/search">角色查找</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="/system/departments">
              <template #title>部门管理</template>
              <el-menu-item index="/departments">部门总览</el-menu-item>
              <el-menu-item index="/departments/search">部门查找</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="/system/titles">
              <template #title>职称管理</template>
              <el-menu-item index="/titles">职称总览</el-menu-item>
              <el-menu-item index="/titles/search">职称查找</el-menu-item>
            </el-sub-menu>
          </el-sub-menu>
          <el-sub-menu index="/device">
            <template #title>
              <el-icon><Monitor /></el-icon>
              <span>设备管理</span>
            </template>
            <el-sub-menu index="/device/list">
              <template #title>设备列表</template>
              <el-menu-item index="/devices">设备总览</el-menu-item>
              <el-menu-item index="/devices/list">设备列表</el-menu-item>
              <el-menu-item index="/devices/search">设备查找</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="/device/history">
              <template #title>设备历史</template>
              <el-menu-item index="/devices/history/overview">状态总览</el-menu-item>
              <el-menu-item index="/devices/history">历史状态</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="/device/production">
              <template #title>生产线</template>
              <el-menu-item index="/production-lines">生产线总览</el-menu-item>
              <el-menu-item index="/production-lines/search">生产线查找</el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/devices/approval">设备审批</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/quality">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>质量管理</span>
            </template>
            <el-sub-menu index="/quality/detections">
              <template #title>检测记录</template>
              <el-menu-item index="/detections">检测总览</el-menu-item>
              <el-menu-item index="/detections/stats">检测统计</el-menu-item>
              <el-menu-item index="/detections/defect-list">缺陷详情列表</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="/quality/reviews">
              <template #title>审查任务</template>
              <el-menu-item index="/reviews">审查总览</el-menu-item>
            </el-sub-menu>
          </el-sub-menu>
          <el-sub-menu index="/message">
            <template #title>
              <el-icon><ChatDotRound /></el-icon>
              <span>消息中心</span>
              <span v-if="unreadCount > 0" class="new-dot"></span>
            </template>
            <el-menu-item index="/messages">
              <template #title>
                <span>我的消息</span>
                <span v-if="userUnreadCount > 0" class="unread-badge">{{ userUnreadCount > 99 ? '99+' : userUnreadCount }}</span>
              </template>
            </el-menu-item>
            <el-menu-item index="/announcements">
              <template #title>
                <span>公告管理</span>
                <span v-if="announcementUnreadCount > 0" class="unread-badge">{{ announcementUnreadCount > 99 ? '99+' : announcementUnreadCount }}</span>
              </template>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/system-functions">
            <template #title>
              <el-icon><FolderOpened /></el-icon>
              <span>系统功能</span>
            </template>
            <el-menu-item index="/audit-logs">审计日志</el-menu-item>
            <el-menu-item index="/export">数据导出</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="route.meta.parent">
                {{ route.meta.parent }}
              </el-breadcrumb-item>
              <el-breadcrumb-item v-if="route.meta.title">
                {{ route.meta.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-avatar :size="32" icon="UserFilled" />
                <span class="username">{{ authStore.user?.real_name || '用户' }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-main class="main">
          <RouterView v-slot="{ Component }">
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
          </RouterView>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter, RouterView } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { sseService } from '../services/sse'
import { messageService } from '../services/message'
import {
  HomeFilled,
  User,
  Setting,
  Monitor,
  DataAnalysis,
  ChatDotRound,
  Document,
  Fold,
  Expand,
  ArrowDown,
  FolderOpened
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)
const unreadCount = ref(0)
const userUnreadCount = ref(0)
const announcementUnreadCount = ref(0)

const activeMenu = computed(() => route.path)

const cachedViews = computed(() => {
  return route.meta.keepAlive ? route.name : ''
})

const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      sseService.disconnect()
      authStore.logout()
      router.push('/login')
    }).catch(() => {})
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

const loadUnreadCount = async () => {
  try {
    const [userRes, systemRes, announcementRes] = await Promise.all([
      messageService.getReceivedMessages({ status: 'unread', limit: 100 }),
      messageService.getMyMessages({ status: 'unread', limit: 100 }),
      messageService.getMyAnnouncements({ limit: 100 })
    ])
    
    const userUnread = userRes.data.total || 0
    const systemUnread = systemRes.data.total || 0
    userUnreadCount.value = userUnread + systemUnread
    
    const announcements = announcementRes.data.announcements || []
    let announcementUnread = 0
    for (const ann of announcements) {
      try {
        const statusRes = await messageService.getAnnouncementReadStatus(ann.announcement_id)
        if (statusRes.data.is_read !== true) {
          announcementUnread++
        }
      } catch (error) {
        announcementUnread++
      }
    }
    announcementUnreadCount.value = announcementUnread
    unreadCount.value = userUnreadCount.value + announcementUnreadCount.value
  } catch (error) {
    console.error('Load unread count failed:', error)
    userUnreadCount.value = 0
    announcementUnreadCount.value = 0
    unreadCount.value = 0
  }
}

onMounted(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  if (user.user_id) {
    sseService.connect(user.user_id)
  }
  loadUnreadCount()
  
  sseService.onMessage((message) => {
    if (message.type === 'user_message' || message.type === 'system_message') {
      userUnreadCount.value++
    } else if (message.type === 'announcement') {
      announcementUnreadCount.value++
    }
    unreadCount.value = userUnreadCount.value + announcementUnreadCount.value
  })
  
  window.addEventListener('announcement-confirmed', loadUnreadCount)
})

onUnmounted(() => {
  sseService.disconnect()
  window.removeEventListener('announcement-confirmed', loadUnreadCount)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.el-container {
  height: 100%;
  flex: 1;
}

.aside {
  background: #304156;
  transition: width 0.3s;
  overflow-y: auto;
  overflow-x: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #263445;
  color: white;
  font-size: 20px;
  font-weight: bold;
}

.logo h1, .logo span {
  margin: 0;
  font-size: 20px;
}

.el-menu-vertical {
  border-right: none;
  background: transparent;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 220px;
}

:deep(.el-menu) {
  background: transparent;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: #bfcbd9;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: #263445 !important;
}

:deep(.el-menu-item.is-active) {
  background: #409eff !important;
  color: white;
}

:deep(.el-sub-menu__title) {
  position: relative;
}

:deep(.new-dot) {
  position: absolute;
  top: 10px;
  right: 18px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
}

:deep(.unread-badge) {
  position: absolute;
  top: 8px;
  right: 20px;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #f56c6c;
  color: white;
  font-size: 12px;
  text-align: center;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  font-size: 14px;
}

.main {
  background: #f5f7fa;
  padding: 16px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

:deep(.router-view-container) {
  height: 100%;
}

:deep(.fade-enter-active),
:deep(.fade-leave-active) {
  transition: opacity 0.2s ease;
}

:deep(.fade-enter-from),
:deep(.fade-leave-to) {
  opacity: 0;
}
</style>
