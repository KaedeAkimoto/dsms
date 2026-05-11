import api from '../utils/api'
import axios from 'axios'

// 创建一个不使用拦截器的axios实例用于文件下载
const downloadApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加token
downloadApi.interceptors.request.use(
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

export const exportService = {
  getExportTables() {
    return api.get('/export/tables')
  },
  
  exportTable(tableName, format = 'json') {
    return downloadApi.get(`/export/${tableName}`, {
      responseType: 'blob',
      params: { format }
    })
  },
  
  exportAllTables(format = 'json') {
    return downloadApi.get('/export/all', {
      responseType: 'blob',
      params: { format }
    })
  }
}