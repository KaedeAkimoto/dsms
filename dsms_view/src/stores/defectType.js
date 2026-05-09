import { defineStore } from 'pinia'
import api from '../utils/api'

export const useDefectTypeStore = defineStore('defectType', {
  state: () => ({
    defectTypes: [],
    cacheTime: null,
    cacheExpireMs: 30 * 60 * 1000
  }),

  getters: {
    getDefectNameById: (state) => (defectTypeId) => {
      const found = state.defectTypes.find(dt => dt.defect_type_id === defectTypeId)
      return found ? found.defect_type_name : null
    },

    getDefectTypeMap: (state) => {
      const map = {}
      state.defectTypes.forEach(dt => {
        map[dt.defect_type_id] = dt.defect_type_name
      })
      return map
    },

    isCacheValid: (state) => {
      if (!state.cacheTime) return false
      return Date.now() - state.cacheTime < state.cacheExpireMs
    }
  },

  actions: {
    async loadDefectTypes() {
      if (this.isCacheValid && this.defectTypes.length > 0) {
        return this.defectTypes
      }

      try {
        const response = await api.get('/defect-types')
        this.defectTypes = response.data || []
        this.cacheTime = Date.now()
        return this.defectTypes
      } catch (error) {
        console.error('Failed to load defect types:', error)
        return this.defectTypes
      }
    },

    async getDefectName(defectTypeId) {
      if (!this.isCacheValid || this.defectTypes.length === 0) {
        await this.loadDefectTypes()
      }
      return this.getDefectNameById(defectTypeId)
    },

    clearCache() {
      this.defectTypes = []
      this.cacheTime = null
    }
  }
})