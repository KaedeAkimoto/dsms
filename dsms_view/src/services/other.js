import api from '../utils/api'

export const auditService = {
  getLogs(params) {
    return api.get('/audit-logs/logs', { params })
  },

  getLogById(log_id) {
    return api.get(`/audit-logs/logs/${log_id}`)
  },

  getUserLogs(user_id, params) {
    return api.get(`/audit-logs/users/${user_id}/logs`, { params })
  }
}

export const exportService = {
  getTables() {
    return api.get('/export/tables')
  },

  exportAll() {
    return api.get('/export/all', { responseType: 'blob' })
  },

  exportTable(table_name) {
    return api.get(`/export/${table_name}`, { responseType: 'blob' })
  }
}

export const adminService = {
  refreshRoleCache() {
    return api.post('/admin/role-cache/refresh')
  },

  getApis() {
    return api.get('/admin/apis')
  }
}
