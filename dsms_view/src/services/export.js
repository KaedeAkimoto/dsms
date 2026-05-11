import api from '../utils/api'

export const exportService = {
  getTableCounts() {
    return api.get('/export/counts')
  },
  
  exportTable(tableName) {
    return api.get(`/export/table/${tableName}`, {
      responseType: 'blob'
    })
  },
  
  exportAllTables() {
    return api.get('/export/all', {
      responseType: 'blob'
    })
  }
}