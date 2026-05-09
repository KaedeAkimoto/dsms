import api from '../utils/api'

export const reviewService = {
  getTasks(params) {
    return api.get('/review-tasks', { params })
  },

  getById(review_task_id) {
    return api.get(`/review-tasks/${review_task_id}`)
  },

  create(data) {
    return api.post('/review-tasks', data)
  },

  update(review_task_id, data) {
    return api.put(`/review-tasks/${review_task_id}`, data)
  },

  approve(review_task_id, data) {
    return api.put(`/review-tasks/${review_task_id}/approve`, data)
  },

  reject(review_task_id, data) {
    return api.put(`/review-tasks/${review_task_id}/reject`, data)
  }
}