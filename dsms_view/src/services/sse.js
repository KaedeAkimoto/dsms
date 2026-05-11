import { ref } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'

const SSE_URL = import.meta.env.VITE_SSE_URL || 'http://localhost:8001/api/v1/sse'

let eventSource = null
let reconnectTimer = null
let reconnectAttempts = 0
const maxReconnectAttempts = 10

// 消息处理回调列表
const messageHandlers = []

export const isConnected = ref(false)

export const sseService = {
  /**
   * 连接SSE
   * @param {string} userId - 用户ID
   */
  connect(userId) {
    if (!userId) {
      console.warn('User ID is required to connect SSE')
      return
    }

    // 如果已有连接，先关闭
    if (eventSource) {
      this.disconnect()
    }

    const token = localStorage.getItem('access_token')
    const url = `${SSE_URL}/connect?user_id=${userId}&token=${token}`

    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      console.log('SSE connected')
      isConnected.value = true
      reconnectAttempts = 0
    }

    eventSource.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      isConnected.value = false

      // 自动重连
      if (eventSource.readyState === EventSource.CLOSED) {
        this.tryReconnect(userId)
      }
    }
  },

  /**
   * 尝试重连
   */
  tryReconnect(userId) {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++
      const delay = Math.min(Math.pow(2, reconnectAttempts) * 1000, 30000)
      console.log(`SSE reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`)
      
      reconnectTimer = setTimeout(() => {
        this.connect(userId)
      }, delay)
    } else {
      console.error('Max SSE reconnect attempts reached')
    }
  },

  /**
   * 断开SSE连接
   */
  disconnect() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    isConnected.value = false
  },

  /**
   * 处理接收到的消息
   * @param {object} message - 消息对象
   */
  handleMessage(message) {
    console.log('Received SSE message:', message)

    const { type } = message

    switch (type) {
      case 'heartbeat':
        // 心跳包，不需要处理
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
      default:
        console.log('Unknown SSE message type:', type)
    }

    // 通知所有注册的回调
    messageHandlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('Error in SSE message handler:', error)
      }
    })
  },

  /**
   * 处理设备状态告警
   */
  handleDeviceStatusAlert(message) {
    const { device_name, status, status_description, message: content } = message
    
    // 显示通知
    ElNotification({
      title: '🚨 设备状态异常',
      message: content || `${device_name} - ${status_description}`,
      type: status === 'fault' ? 'error' : 'warning',
      duration: 10000,
      position: 'top-right'
    })

    // 触发刷新消息事件
    this.triggerMessageRefresh()
  },

  /**
   * 处理系统消息
   */
  handleSystemMessage(message) {
    ElNotification({
      title: '📢 系统通知',
      message: message.content,
      type: 'info',
      duration: 6000,
      position: 'top-right'
    })

    this.triggerMessageRefresh()
  },

  /**
   * 处理用户消息
   */
  handleUserMessage(message) {
    ElNotification({
      title: '💬 新消息',
      message: message.content,
      type: 'info',
      duration: 8000,
      position: 'top-right'
    })

    this.triggerMessageRefresh()
  },

  /**
   * 触发消息刷新事件
   */
  triggerMessageRefresh() {
    const event = new Event('dsms_message_refresh')
    window.dispatchEvent(event)
  },

  /**
   * 注册消息处理回调
   * @param {function} handler - 消息处理函数
   * @returns {function} - 取消注册的函数
   */
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
