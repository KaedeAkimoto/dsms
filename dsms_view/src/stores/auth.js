import { defineStore } from 'pinia'
import api from '../utils/api'

const ROLE_ID_TO_NAME = {
  212: 'no_permission_user',
  213: 'normal_employee',
  214: 'device_admin',
  215: 'detection_monitor',
  216: 'hr_admin',
  217: 'senior_sys_admin',
  218: 'super_sys_admin'
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
    userRoleName: (state) => {
      if (!state.user) return null
      if (state.user.role_name) return state.user.role_name
      return ROLE_ID_TO_NAME[state.user.role_id] || null
    }
  },

  actions: {
    async login(user_name, password) {
      const response = await api.post('/auth/login', { user_name, password })
      const { access_token, user } = response.data

      const roleName = ROLE_ID_TO_NAME[user.role_id] || null
      const fullUser = { ...user, role_name: roleName }

      this.token = access_token
      this.user = fullUser
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('user', JSON.stringify(fullUser))
      return fullUser
    },

    async register(userData) {
      const response = await api.post('/auth/register', userData)
      return response.data
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    },

    async getCurrentUser() {
      const response = await api.get('/users/me')
      this.user = response.data
      localStorage.setItem('user', JSON.stringify(this.user))
      return this.user
    },

    async updateProfile(userData) {
      const response = await api.put('/users/me', userData)
      this.user = response.data
      localStorage.setItem('user', JSON.stringify(this.user))
      return response.data
    },

    async changePassword(old_password, new_password) {
      await api.put('/users/me/password', { old_password, new_password })
    }
  }
})
