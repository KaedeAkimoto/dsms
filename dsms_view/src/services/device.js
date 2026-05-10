import api from '../utils/api'

export const deviceService = {
  getList(params) {
    return api.get('/devices', { params })
  },

  getById(device_id) {
    return api.get(`/devices/${device_id}`)
  },

  create(data) {
    return api.post('/devices', data)
  },

  update(device_id, data) {
    return api.put(`/devices/${device_id}`, data)
  },

  delete(device_id) {
    return api.delete(`/devices/${device_id}`)
  },

  generateToken(device_id) {
    return api.post(`/devices/${device_id}/token`)
  },

  getToken(device_id) {
    return api.get(`/devices/${device_id}/token`)
  },

  batchGenerateTokens(device_ids) {
    return api.post('/devices/tokens/batch-generate', { device_ids })
  },

  exportTokens() {
    return api.get('/devices/tokens/export', { responseType: 'blob' })
  },

  getHistory(device_id, params) {
    return api.get(`/devices/${device_id}/history`, { params })
  },

  getProductionLines(params) {
    return api.get('/device-production-lines', { params })
  },

  createProductionLine(data) {
    return api.post('/device-production-lines', data)
  },

  updateProductionLine(production_line_id, data) {
    return api.put(`/device-production-lines/${production_line_id}`, data)
  },

  deleteProductionLine(production_line_id) {
    return api.delete(`/device-production-lines/${production_line_id}`)
  },

  getApprovals() {
    return api.get('/device-approvals')
  },

  createApproval(data) {
    return api.post('/device-approvals', data)
  },

  approve(device_approval_id, approved) {
    return api.put(`/device-approvals/${device_approval_id}?approved=${approved}`)
  },

  search(params) {
    return api.get('/devices/list/search', { params })
  },

  getByType(device_type, params) {
    return api.get(`/devices/query/by-type/${device_type}`, { params })
  },

  getStatusStats() {
    return api.get('/devices/query/status-stats')
  },

  getStatusHistory(device_id) {
    return api.get(`/device-status-history/${device_id}`)
  }
}
