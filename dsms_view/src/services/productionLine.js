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
      line_name: data.production_line_name,
      line_code: data.production_line_loc
    })
  },

  update(production_line_id, data) {
    return api.put(`/device-production-lines/${production_line_id}`, {
      line_name: data.production_line_name,
      line_code: data.production_line_loc
    })
  },

  delete(production_line_id) {
    return api.delete(`/device-production-lines/${production_line_id}`)
  },

  getDevices(production_line_id) {
    return api.get(`/devices/query/by-production-line/${production_line_id}`, { params: { limit: 1000 } })
  }
}
