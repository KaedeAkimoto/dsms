import { ref } from 'vue'
import { ElNotification } from 'element-plus'

const SSE_URL = import.meta.env.VITE_SSE_URL || 'http://localhost:8001/api/v1/sse'

let controller = null
let reconnectTimer = null
let reconnectAttempts = 0
const maxReconnectAttempts = 10
let reader = null

const messageHandlers = []

export const isConnected = ref(false)

export const sseService = {
  connect(userId) {
    if (!userId) return

    if (controller) {
      this.disconnect()
    }

    const token = localStorage.getItem('access_token')
    controller = new AbortController()
    this.doConnect(`${SSE_URL}/connect`, token, userId)
  },

  async doConnect(url, token, userId) {
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream'
        },
        signal: controller.signal
      })

      if (!response.ok) {
        isConnected.value = false
        this.tryReconnect(userId)
        return
      }

      isConnected.value = true
      reconnectAttempts = 0

      reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        while (buffer.includes('\n\n')) {
          const index = buffer.indexOf('\n\n')
          const eventData = buffer.substring(0, index)
          buffer = buffer.substring(index + 2)

          if (eventData.startsWith('data: ')) {
            const jsonString = eventData.substring(6)
            try {
              const message = JSON.parse(jsonString)
              this.handleMessage(message)
            } catch (error) {
              console.error('SSE message parse error:', error)
            }
          }
        }
      }

      isConnected.value = false
      this.tryReconnect(userId)

    } catch (error) {
      if (error.name !== 'AbortError') {
        isConnected.value = false
        this.tryReconnect(userId)
      }
    }
  },

  tryReconnect(userId) {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++
      const delay = Math.min(Math.pow(2, reconnectAttempts) * 1000, 30000)
      
      reconnectTimer = setTimeout(() => {
        const token = localStorage.getItem('access_token')
        this.doConnect(`${SSE_URL}/connect`, token, userId)
      }, delay)
    }
  },

  disconnect() {
    if (controller) {
      controller.abort()
      controller = null
    }
    
    if (reader) {
      reader.cancel()
      reader = null
    }
    
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    
    isConnected.value = false
    reconnectAttempts = 0
  },

  handleMessage(message) {
    const { type } = message

    switch (type) {
      case 'heartbeat':
        break
      case 'device_status_alert':
        this.handleDeviceStatusAlert(message)
        break
      case 'system_message':
        this.handleSystemMessage(message)
        break
      case 'user_message':
        this.handleUserMessage(message)
        break
    }

    messageHandlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('SSE handler error:', error)
      }
    })
  },

  handleDeviceStatusAlert(message) {
    const { device_name, status, status_description, message: content } = message
    
    ElNotification({
      title: '🚨 设备状态异常',
      message: content || `${device_name} - ${status_description}`,
      type: status === 'fault' ? 'error' : 'warning',
      duration: 10000,
      position: 'top-right'
    })

    this.triggerMessageRefresh()
  },

  handleSystemMessage(message) {
    ElNotification({
      title: '📢 系统通知',
      message: message.content || message.data?.content || '系统消息',
      type: 'info',
      duration: 6000,
      position: 'top-right'
    })

    this.triggerMessageRefresh()
  },

  handleUserMessage(message) {
    ElNotification({
      title: '💬 新消息',
      message: message.content || message.data?.content || '新消息',
      type: 'info',
      duration: 8000,
      position: 'top-right'
    })

    this.triggerMessageRefresh()
  },

  triggerMessageRefresh() {
    const event = new Event('dsms_message_refresh')
    window.dispatchEvent(event)
  },

  onMessage(handler) {
    messageHandlers.push(handler)
    return () => {
      const index = messageHandlers.indexOf(handler)
      if (index > -1) {
        messageHandlers.splice(index, 1)
      }
    }
  }
}

export default sseService
