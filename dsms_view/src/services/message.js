import api from '../utils/api'

const messageCache = {
  loaded: false,
  systemMessages: [],
  receivedMessages: [],
  sentMessages: [],
  announcementLoaded: false,
  announcements: []
}

export const messageService = {
  getCache() {
    return messageCache
  },

  setSystemMessages(messages) {
    messageCache.systemMessages = messages
  },

  setReceivedMessages(messages) {
    messageCache.receivedMessages = messages
  },

  setSentMessages(messages) {
    messageCache.sentMessages = messages
  },

  setLoaded(loaded = true) {
    messageCache.loaded = loaded
  },

  getMessages(params) {
    return api.get('/messages', { params })
  },

  getMyMessages(params) {
    return api.get('/system-messages/my', { params })
  },

  getReceivedMessages(params) {
    return api.get('/user-messages/received', { params })
  },

  getSentMessages(params) {
    return api.get('/user-messages/sent', { params })
  },

  getById(message_id) {
    return api.get(`/user-messages/${message_id}`)
  },

  create(data) {
    return api.post('/user-messages', data)
  },

  sendMessage(data) {
    return api.post('/user-messages', data)
  },

  delete(message_id) {
    return api.delete(`/user-messages/${message_id}`)
  },

  markAsRead(message_id) {
    return api.put(`/user-messages/${message_id}/read`)
  },

  markMessageAsRead(message_id) {
    return api.put(`/user-messages/${message_id}/read`)
  },

  markSystemMessageAsRead(msg_id) {
    return api.put(`/system-messages/${msg_id}/read`)
  },

  markAllSystemMessagesAsRead() {
    return api.put('/system-messages/my/read-all')
  },

  markAllAsRead() {
    return api.put('/user-messages/read-all')
  },

  markAllReceivedAsRead() {
    return api.put('/user-messages/received/read-all')
  },

  getUnreadCount() {
    return api.get('/user-messages/unread/count')
  },

  getAnnouncements(params) {
    return api.get('/announcements', { params })
  },

  getMyAnnouncements(params) {
    return api.get('/announcements/my', { params })
  },

  getAnnouncementById(announcement_id) {
    return api.get(`/announcements/${announcement_id}`)
  },

  createAnnouncement(data) {
    return api.post('/announcements', data)
  },

  updateAnnouncement(announcement_id, data) {
    return api.put(`/announcements/${announcement_id}`, data)
  },

  getAnnouncementCache() {
    return messageCache
  },

  setAnnouncements(announcements) {
    messageCache.announcements = announcements
  },

  setAnnouncementLoaded(loaded = true) {
    messageCache.announcementLoaded = loaded
  },

  deleteAnnouncement(announcement_id) {
    return api.delete(`/announcements/${announcement_id}`)
  },

  markAnnouncementAsRead(announcement_id) {
    return api.put(`/announcements/${announcement_id}/read`)
  },

  getAnnouncementReaders(announcement_id) {
    return api.get(`/announcements/${announcement_id}/readers`)
  },

  getAnnouncementReadStatus(announcement_id) {
    return api.get(`/announcements/${announcement_id}/read-status`)
  },

  connectSSE() {
    return new EventSource(`${import.meta.env.VITE_API_BASE_URL}/sse/connect`)
  },

  sendSSE(user_id, data) {
    return api.post(`/sse/send/${user_id}`, data)
  }
}
