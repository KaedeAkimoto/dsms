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
    console.log('[SSE Service] 尝试连接SSE...')
    console.log('[SSE Service] 用户ID:', userId)
    
    if (!userId) {
      console.warn('[SSE Service] User ID is required to connect SSE')
      return
    }

    // 如果已有连接，先关闭
    if (eventSource) {
      console.log('[SSE Service] 已有连接，先断开')
      this.disconnect()
    }

    const token = localStorage.getItem('access_token')
    console.log('[SSE Service] Token exists:', !!token)
    
    const url = `${SSE_URL}/connect?user_id=${userId}&token=${token}`
    console.log('[SSE Service] SSE URL:', url)

    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      console.log('[SSE Service] ✅ SSE连接成功建立')
      isConnected.value = true
      reconnectAttempts = 0
    }

    eventSource.onmessage = (event) => {
      console.log('[SSE Service] 📥 接收到SSE消息')
      console.log('[SSE Service] 原始消息:', event.data)
      
      try {
        const message = JSON.parse(event.data)
        console.log('[SSE Service] 解析后的消息:', message)
        this.handleMessage(message)
      } catch (error) {
        console.error('[SSE Service] ❌ 解析SSE消息失败:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('[SSE Service] ❌ SSE错误:', error)
      console.error('[SSE Service] 错误详情:', error ? error.message || error : '未知错误')
      isConnected.value = false

      // 自动重连
      if (eventSource.readyState === EventSource.CLOSED) {
        console.log('[SSE Service] 连接已关闭，准备重连')
        this.tryReconnect(userId)
      }
    }

    eventSource.onclose = () => {
      console.log('[SSE Service] SSE连接已关闭')
      isConnected.value = false
    }
  },

  /**
   * 尝试重连
   */
  tryReconnect(userId) {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++
      const delay = Math.min(Math.pow(2, reconnectAttempts) * 1000, 30000)
      console.log(`[SSE Service] 🔄 重连中... (第${reconnectAttempts}/${maxReconnectAttempts}次，延迟${delay}ms)`)
      
      reconnectTimer = setTimeout(() => {
        this.connect(userId)
      }, delay)
    } else {
      console.error('[SSE Service] ❌ 达到最大重连次数')
    }
  },

  /**
   * 断开SSE连接
   */
  disconnect() {
    console.log('[SSE Service] 断开SSE连接')
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
    console.log('[SSE Service] 🎯 开始处理消息')
    console.log('[SSE Service] 消息类型:', message.type)
    console.log('[SSE Service] 消息内容:', message)

    const { type } = message

    switch (type) {
      case 'heartbeat':
        console.log('[SSE Service] 💓 收到心跳包')
        break
      case 'device_status_alert':
        console.log('[SSE Service] 🚨 收到设备状态告警')
        this.handleDeviceStatusAlert(message)
        break
      case 'system_message':
        console.log('[SSE Service] 📢 收到系统消息')
        this.handleSystemMessage(message)
        break
      case 'user_message':
        console.log('[SSE Service] 💬 收到用户消息')
        this.handleUserMessage(message)
        break
      default:
        console.log('[SSE Service] ⚠️ 未知消息类型:', type)
    }

    // 通知所有注册的回调
    console.log('[SSE Service] 通知注册的消息处理器，共', messageHandlers.length, '个')
    messageHandlers.forEach((handler, index) => {
      try {
        console.log('[SSE Service] 调用第', index + 1, '个消息处理器')
        handler(message)
      } catch (error) {
        console.error('[SSE Service] ❌ 消息处理器', index + 1, '执行失败:', error)
      }
    })
  },

  /**
   * 处理设备状态告警
   */
  handleDeviceStatusAlert(message) {
    const { device_name, status, status_description, message: content } = message
    console.log('[SSE Service] 设备状态告警详情:', { device_name, status, status_description, content })
    
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
    console.log('[SSE Service] 系统消息内容:', message.content)
    
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
    console.log('[SSE Service] 用户消息内容:', message.content)
    
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
    console.log('[SSE Service] 🔥 触发消息刷新事件: dsms_message_refresh')
    const event = new Event('dsms_message_refresh')
    window.dispatchEvent(event)
    console.log('[SSE Service] ✅ 消息刷新事件已派发')
  },

  /**
   * 注册消息处理回调
   * @param {function} handler - 消息处理函数
   * @returns {function} - 取消注册的函数
   */
  onMessage(handler) {
    console.log('[SSE Service] 注册新的消息处理器')
    messageHandlers.push(handler)
    return () => {
      const index = messageHandlers.indexOf(handler)
      if (index > -1) {
        messageHandlers.splice(index, 1)
      }
    }
  },

  /**
   * 获取当前连接状态
   */
  getStatus() {
    return {
      isConnected: isConnected.value,
      reconnectAttempts: reconnectAttempts,
      hasEventSource: !!eventSource,
      handlerCount: messageHandlers.length
    }
  },

  /**
   * 手动触发消息刷新（用于测试）
   */
  testRefresh() {
    console.log('[SSE Service] 🧪 测试触发消息刷新')
    this.triggerMessageRefresh()
  }
}

export default sseService
