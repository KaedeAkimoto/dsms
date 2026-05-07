import api from '../utils/api'

export const productionLineService = {
  getList(params) {
    return api.get('/device-production-lines', { params })
  },

  search(params) {
    return api.get('/device-production-lines/search', { params })
  },

  getById(production_line_id) {
    return api.get(`/device-production-lines/${production_line_id}`)
  },

  create(data) {
    return api.post('/device-production-lines', {
      production_line_name: data.production_line_name,
      production_line_loc: data.production_line_loc,
      production_line_manager: data.production_line_manager
    })
  },

  update(production_line_id, data) {
    return api.put(`/device-production-lines/${production_line_id}`, {
      production_line_name: data.production_line_name,
      production_line_loc: data.production_line_loc,
      production_line_manager: data.production_line_manager
    })
  },

  delete(production_line_id) {
    return api.delete(`/device-production-lines/${production_line_id}`)
  },

  getDevices(production_line_id) {
    return api.get(`/devices/query/by-production-line/${production_line_id}`, { params: { limit: 1000 } })
  }
}
