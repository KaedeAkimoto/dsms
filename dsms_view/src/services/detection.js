import api from '../utils/api'

export const detectionService = {
  getList(params) {
    return api.get('/detection-records', { params })
  },

  getById(detection_record_id) {
    return api.get(`/detection-records/${detection_record_id}`)
  },

  getDefectDetail(defect_details_id) {
    return api.get(`/defect-details/${defect_details_id}`)
  },

  create(data) {
    return api.post('/detection-records', data)
  },

  update(detection_record_id, data) {
    return api.put(`/detection-records/${detection_record_id}`, data)
  },

  delete(detection_record_id) {
    return api.delete(`/detection-records/${detection_record_id}`)
  },

  getByDevice(device_id, params) {
    return api.get(`/detection-records/device/${device_id}`, { params })
  },

  getByTime(start_time, end_time, params) {
    return api.get('/detection-records/by-time', { params: { start_time, end_time, ...params } })
  },

  getByDefectType(defect_type_id, params) {
    return api.get(`/detection-records/by-defect-type/${defect_type_id}`, { params })
  },

  getDefectStats(params) {
    return api.get('/detection/defect-stats', { params })
  },

  getStats(params) {
    return api.get('/detection/stats', { params })
  },

  getTrend(params) {
    return api.get('/detection/trend', { params })
  },

  getDefectTrend(params) {
    return api.get('/detection/defect-trend', { params })
  },

  getDefectTypes() {
    return api.get('/defect-types')
  },

  createDefectType(data) {
    return api.post('/defect-types', data)
  },

  updateDefectType(defect_type_id, data) {
    return api.put(`/defect-types/${defect_type_id}`, data)
  },

  deleteDefectType(defect_type_id) {
    return api.delete(`/defect-types/${defect_type_id}`)
  },

  runDemo() {
    return api.post('/detection/demo')
  }
}
