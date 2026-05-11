import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/users/Index.vue'),
        meta: { title: '用户总览', parent: '系统管理' }
      },
      {
        path: 'users/search',
        name: 'UsersSearch',
        component: () => import('../views/users/Search.vue'),
        meta: { title: '用户查找', parent: '系统管理' }
      },
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('../views/roles/Index.vue'),
        meta: { title: '角色总览', parent: '系统管理' }
      },
      {
        path: 'roles/search',
        name: 'RolesSearch',
        component: () => import('../views/roles/Search.vue'),
        meta: { title: '角色查找', parent: '系统管理' }
      },
      {
        path: 'departments',
        name: 'Departments',
        component: () => import('../views/departments/Index.vue'),
        meta: { title: '部门总览', parent: '系统管理' }
      },
      {
        path: 'departments/search',
        name: 'DepartmentsSearch',
        component: () => import('../views/departments/Search.vue'),
        meta: { title: '部门查找', parent: '系统管理' }
      },
      {
        path: 'titles',
        name: 'Titles',
        component: () => import('../views/titles/Index.vue'),
        meta: { title: '职称总览', parent: '系统管理' }
      },
      {
        path: 'titles/search',
        name: 'TitlesSearch',
        component: () => import('../views/titles/Search.vue'),
        meta: { title: '职称查找', parent: '系统管理' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('../views/devices/CardView.vue'),
        meta: { title: '设备总览', parent: '设备管理' }
      },
      {
        path: 'devices/list',
        name: 'DevicesList',
        component: () => import('../views/devices/Index.vue'),
        meta: { title: '设备列表', parent: '设备管理' }
      },
      {
        path: 'devices/search',
        name: 'DevicesSearch',
        component: () => import('../views/devices/Search.vue'),
        meta: { title: '设备查找', parent: '设备管理' }
      },
      {
        path: 'devices/history',
        name: 'DeviceHistory',
        component: () => import('../views/devices/History.vue'),
        meta: { title: '历史状态', parent: '设备管理' }
      },
      {
        path: 'devices/history/overview',
        name: 'DeviceHistoryOverview',
        component: () => import('../views/devices/HistoryOverview.vue'),
        meta: { title: '状态总览', parent: '设备管理' }
      },
      {
        path: 'devices/approval',
        name: 'DeviceApproval',
        component: () => import('../views/devices/Approval.vue'),
        meta: { title: '设备审批', parent: '设备管理' }
      },
      {
        path: 'production-lines',
        name: 'ProductionLines',
        component: () => import('../views/productionLines/Index.vue'),
        meta: { title: '生产线总览', parent: '设备管理' }
      },
      {
        path: 'production-lines/search',
        name: 'ProductionLinesSearch',
        component: () => import('../views/productionLines/Search.vue'),
        meta: { title: '生产线查找', parent: '设备管理' }
      },
      {
        path: 'detections',
        name: 'Detections',
        component: () => import('../views/detections/Index.vue'),
        meta: { title: '检测记录', parent: '质量管理' }
      },
      {
        path: 'detections/stats',
        name: 'DetectionStats',
        component: () => import('../views/detections/Stats.vue'),
        meta: { title: '检测统计', parent: '质量管理' }
      },
      {
        path: 'detections/defect-list',
        name: 'DefectList',
        component: () => import('../views/detections/DefectList.vue'),
        meta: { title: '缺陷详情列表', parent: '质量管理' }
      },
      {
        path: 'detections/defect-detail/:recordBatchId',
        name: 'DefectDetail',
        component: () => import('../views/detections/DefectDetail.vue'),
        meta: { title: '缺陷详情', parent: '质量管理' }
      },
      {
        path: 'reviews',
        name: 'Reviews',
        component: () => import('../views/reviews/Index.vue'),
        meta: { title: '审查总览', parent: '质量管理' }
      },
      {
        path: 'messages',
        name: 'Messages',
        component: () => import('../views/messages/Index.vue'),
        meta: { title: '我的消息', parent: '消息中心', keepAlive: true }
      },
      {
        path: 'announcements',
        name: 'Announcements',
        component: () => import('../views/announcements/Index.vue'),
        meta: { title: '公告管理', parent: '消息中心', keepAlive: true }
      },
      {
        path: 'audit-logs',
        name: 'AuditLogs',
        component: () => import('../views/audit/Index.vue'),
        meta: { title: '审计日志', parent: '系统功能' }
      },
      {
        path: 'export',
        name: 'Export',
        component: () => import('../views/export/Index.vue'),
        meta: { title: '数据导出', parent: '系统功能' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '个人中心' }
      }
    ]
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/demo',
    name: 'Demo',
    component: () => import('../views/Demo.vue'),
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, from) => {
  if (to.meta.requiresAuth !== false) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      return '/login'
    }
  }

  if (to.path === '/login') {
    const token = localStorage.getItem('access_token')
    if (token) {
      return '/dashboard'
    }
  }

  return true
})

export default router
