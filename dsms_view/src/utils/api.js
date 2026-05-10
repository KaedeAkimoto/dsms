import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

const isTokenExpired = (error) => {
  if (error.response) {
    const { status, data } = error.response
    if (status === 401) return true
    if (data && data.code === 401) return true
    if (data && (data.message?.includes('token') || data.message?.includes('登录') || data.message?.includes('过期'))) return true
  }
  if (error.message?.includes('timeout') || error.message?.includes('Network')) return false
  if (!error.response && error.request) return false
  return false
}

api.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200 && res.code !== 0 && res.code !== 201) {
      ElMessage.error(res.message || '请求失败')
      if (res.code === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401 || (data && data.code === 401)) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else if (status === 403) {
        ElMessage.error(data?.message || '权限不足')
      } else if (status === 404) {
        ElMessage.error(data?.message || '资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器错误')
      } else {
        ElMessage.error(data?.message || '请求失败')
      }
    } else if (error.request) {
      if (isTokenExpired(error)) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else {
        ElMessage.error('网络错误，请检查网络连接')
      }
    } else {
      ElMessage.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

export default api
