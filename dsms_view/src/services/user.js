import api from '../utils/api'

export const userService = {
  getList(params) {
    return api.get('/users', { params })
  },

  getById(user_id) {
    return api.get(`/users/${user_id}`)
  },

  getByEmployeeId(employee_id) {
    return api.get('/users/employee', { params: { employee_id } })
  },

  search(params) {
    return api.get('/users/search', { params })
  },

  createBatch(users, default_role_id) {
    return api.post('/users/batch', { users, default_role_id })
  },

  update(user_id, data) {
    return api.put(`/users/${user_id}`, data)
  },

  resetPassword(user_id, new_password) {
    return api.put(`/users/${user_id}/password`, null, { params: { new_password } })
  },

  delete(user_id) {
    return api.delete(`/users/${user_id}`)
  },

  getCurrentUser() {
    return api.get('/users/me')
  },

  updateCurrentUser(data) {
    return api.put('/users/me', data)
  },

  changePassword(old_password, new_password) {
    return api.put('/users/me/password', { old_password, new_password })
  },

  getByDepartment(department_id, params) {
    return api.get(`/users/by-department/${department_id}`, { params })
  },

  getByTitle(title_id, params) {
    return api.get(`/users/by-title/${title_id}`, { params })
  },

  getByRole(role_id, params) {
    return api.get(`/users/by-role/${role_id}`, { params })
  }
}

export const roleService = {
  getList(params) {
    return api.get('/roles', { params })
  },

  getById(role_id) {
    return api.get(`/roles/${role_id}`)
  },

  create(data) {
    return api.post('/roles', data)
  },

  update(role_id, data) {
    return api.put(`/roles/${role_id}`, data)
  },

  delete(role_id) {
    return api.delete(`/roles/${role_id}`)
  }
}

export const departmentService = {
  getList(params) {
    return api.get('/departments', { params })
  },

  getById(department_id) {
    return api.get(`/departments/${department_id}`)
  },

  search(params) {
    return api.get('/departments/search', { params })
  },

  getTree() {
    return api.get('/departments/list/tree')
  },

  getChildren(department_id) {
    return api.get(`/departments/query/children/${department_id}`)
  },

  create(data) {
    return api.post('/departments', data)
  },

  update(department_id, data) {
    return api.put(`/departments/${department_id}`, data)
  },

  delete(department_id) {
    return api.delete(`/departments/${department_id}`)
  }
}

export const titleService = {
  getList(params) {
    return api.get('/titles', { params })
  },

  getById(title_id) {
    return api.get(`/titles/${title_id}`)
  },

  create(data) {
    return api.post('/titles', data)
  },

  update(title_id, data) {
    return api.put(`/titles/${title_id}`, data)
  },

  delete(title_id) {
    return api.delete(`/titles/${title_id}`)
  }
}
