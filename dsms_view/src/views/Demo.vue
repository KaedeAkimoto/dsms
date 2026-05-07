<template>
  <div class="demo-container">
    <div class="demo-header">
      <h2>缺陷检测演示</h2>
      <p>实时视频流缺陷检测演示页面</p>
    </div>

    <div class="demo-content">
      <div class="video-section">
        <div class="video-wrapper">
          <video ref="videoRef" autoplay playsinline muted></video>
          <div v-if="!isConnected" class="connection-overlay">
            <div class="status-indicator offline"></div>
            <span>未连接</span>
          </div>
          <div v-else class="connection-overlay connected">
            <div class="status-indicator online"></div>
            <span>已连接</span>
          </div>
        </div>
        <div class="video-controls">
          <el-button 
            @click="toggleCamera" 
            :disabled="isProcessing"
            :loading="isProcessing"
          >
            {{ isCameraOn ? '关闭摄像头' : '开启摄像头' }}
          </el-button>
          <el-button 
            @click="toggleDetection" 
            :disabled="(!isCameraOn && !isVideoMode) || !isConnected"
            :type="isDetecting ? 'primary' : ''"
          >
            {{ isDetecting ? '停止检测' : '开始检测' }}
          </el-button>
          <el-button @click="resetStats">重置统计</el-button>
          <el-button @click="disconnect" v-if="isConnected">断开连接</el-button>
          <el-button @click="selectVideo">
            {{ isVideoMode ? '切换到摄像头' : '上传视频' }}
          </el-button>
          <input 
            ref="videoInputRef" 
            type="file" 
            accept="video/*" 
            style="display: none" 
            @change="handleVideoSelect"
          >
        </div>
        
        <div class="frame-rate-control">
          <label>上传帧率</label>
          <el-slider 
            v-model="frameRate" 
            :min="1" 
            :max="30" 
            :step="1"
            :disabled="isDetecting"
            class="frame-rate-slider"
          />
          <span class="frame-rate-value">{{ frameRate }} FPS</span>
        </div>

        <div class="preview-section">
          <h3>检测预览</h3>
          <div class="preview-wrapper" v-if="previewImage">
            <img :src="previewImage" alt="检测结果" class="preview-image">
            <canvas ref="previewCanvasRef" class="preview-canvas"></canvas>
            <div class="preview-info">
              <span class="preview-frame">帧 ID: {{ currentFrameId }}</span>
              <span class="preview-time">{{ formatTime(lastResult?.timestamp) }}</span>
            </div>
          </div>
          <div v-else class="no-preview">
            <p>等待检测结果...</p>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="stats-card">
          <h3>实时统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ stats.frameCount }}</span>
              <span class="stat-label">处理帧数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.fps.toFixed(1) }}</span>
              <span class="stat-label">FPS</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.totalDefects }}</span>
              <span class="stat-label">检测缺陷数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.defectRate }}%</span>
              <span class="stat-label">缺陷率</span>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <h3>缺陷类型分布</h3>
          <div class="chart-container">
            <div v-if="Object.keys(defectTypeStats).length > 0">
              <div v-for="(count, type) in sortedDefectTypeStats" :key="type" class="bar-item">
                <span class="bar-label">{{ type }}</span>
                <div class="bar-wrapper">
                  <div class="bar-fill" :style="{ width: getBarWidth(count) + '%' }"></div>
                </div>
                <span class="bar-count">{{ getBarPercentage(count) }}%</span>
              </div>
            </div>
            <div v-else class="no-chart-data">
              <p>暂无数据</p>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <h3>置信度曲线</h3>
          <div ref="confidenceChartRef" class="chart-container"></div>
          <div class="percentile-info">
            <span class="percentile-label">80%缺陷置信度大于:</span>
            <span class="percentile-value">{{ percentile80 }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const videoRef = ref(null)
const logRef = ref(null)
const videoInputRef = ref(null)
const confidenceChartRef = ref(null)

let confidenceChartInstance = null

const isConnected = ref(false)
const isCameraOn = ref(false)
const isVideoMode = ref(false)
const isDetecting = ref(false)
const isProcessing = ref(false)
const frameRate = ref(5) // 上传帧率，单位：帧/秒

let ws = null
let mediaStream = null
let animationId = null
let frameId = 0
let heartbeatTimer = null
let lastSendTime = 0
let fpsLastTime = 0
let fpsFrameCount = 0

const stats = reactive({
  frameCount: 0,
  fps: 0,
  totalDefects: 0,
  defectFrameCount: 0, // 有缺陷的帧数
  defectRate: 0
})

const defectTypeStats = reactive({}) // 缺陷类型统计 { typeName: count }
const confidenceData = ref(new Array(101).fill(0)) // 置信度0-100%的缺陷计数
const percentile80 = ref(0) // 80%分位数置信度

const lastResult = ref(null)
const logs = ref([])

const previewImage = ref('') // 预览图片
const currentFrameId = ref(0) // 当前帧ID
const previewCanvasRef = ref(null) // 预览画布引用

const getBarWidth = (count) => {
  const maxCount = Math.max(...Object.values(defectTypeStats), 1)
  return (count / maxCount) * 100
}

const getBarPercentage = (count) => {
  const total = Object.values(defectTypeStats).reduce((sum, val) => sum + val, 0)
  return total > 0 ? ((count / total) * 100).toFixed(1) : 0
}

const sortedDefectTypeStats = computed(() => {
  return Object.entries(defectTypeStats)
    .sort((a, b) => b[1] - a[1])
    .reduce((acc, [type, count]) => {
      acc[type] = count
      return acc
    }, {})
})

const addLog = (message, type = 'info') => {
  const now = new Date()
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  logs.value.push({ time: timeStr, message, type })
  setTimeout(() => {
    if (logRef.value) {
      logRef.value.scrollTop = logRef.value.scrollHeight
    }
  }, 100)
}

const connectWebSocket = () => {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1'
  const wsProtocol = apiBaseUrl.startsWith('https') ? 'wss://' : 'ws://'
  const wsBaseUrl = apiBaseUrl.replace(/^https?:\/\//, '').replace('/api/v1', '')
  const wsUrl = `${wsProtocol}${wsBaseUrl}/api/v1/ws/detection/demo`
  
  addLog(`正在连接 WebSocket: ${wsUrl}`, 'info')
  
  if (ws && ws.readyState === WebSocket.OPEN) {
    addLog('关闭现有连接', 'info')
    ws.close()
  }
  
  try {
    ws = new WebSocket(wsUrl)
    console.log('WebSocket 对象已创建，readyState:', ws.readyState)
    
    ws.onopen = () => {
      isConnected.value = true
      addLog('WebSocket 连接已建立', 'success')
      
      // 启动心跳机制，每10秒发送一次ping
      startHeartbeat()
    }

    ws.onmessage = (event) => {
      console.log('WebSocket 收到消息:', event.data)
      try {
        const data = JSON.parse(event.data)
        handleMessage(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onerror = (error) => {
      addLog(`WebSocket 错误: ${error.message || '未知错误'}`, 'error')
    }

    ws.onclose = (event) => {
      isConnected.value = false
      addLog(`WebSocket 连接已断开 (代码: ${event.code}, 原因: ${event.reason || '无'})`, 'error')
      
      // 自动重连机制
      if (event.code !== 1000) { // 1000 是正常关闭
        addLog('尝试重新连接...', 'info')
        setTimeout(() => {
          connectWebSocket()
        }, 3000)
      }
    }
    
  } catch (e) {
    addLog(`创建连接失败: ${e.message}`, 'error')
  }
}

const handleMessage = (message) => {
  switch (message.type) {
    case 'detection_result':
      lastResult.value = message
      stats.frameCount++
      
      // 计算FPS
      const now = Date.now()
      fpsFrameCount++
      if (now - fpsLastTime >= 1000) { // 每1秒计算一次FPS
        stats.fps = fpsFrameCount
        fpsFrameCount = 0
        fpsLastTime = now
      }
      
      if (message.has_defect) {
        stats.totalDefects += message.detect_count
        stats.defectFrameCount++ // 增加有缺陷的帧数
        
        // 更新缺陷类型统计
        if (message.detections) {
          message.detections.forEach(det => {
            const typeName = det.class_name || det.name || 'unknown'
            if (defectTypeStats[typeName]) {
              defectTypeStats[typeName]++
            } else {
              defectTypeStats[typeName] = 1
            }
          })
        }
      }
      
      // 更新当前帧ID
      if (message.frame_id !== undefined) {
        currentFrameId.value = message.frame_id
      }
      
      // 更新置信度分布数据（每1%一个数据点）
      if (message.detections) {
        message.detections.forEach(det => {
          const confidence = det.confidence || 0
          const percentIndex = Math.min(Math.floor(confidence * 100), 100)
          confidenceData.value[percentIndex]++
        })
        updateConfidenceChart()
      }
      
      // 缺陷率 = 有缺陷的帧数 / 总帧数 × 100%
      stats.defectRate = stats.frameCount > 0 ? ((stats.defectFrameCount / stats.frameCount) * 100).toFixed(1) : 0
      
      // 在预览画布上绘制检测结果
      drawPreviewDetections(message.detections)
      break
    case 'stats':
      stats.fps = message.fps
      break
    case 'error':
      addLog(`错误: ${message.message}`, 'error')
      break
    case 'pong':
      break
    default:
      addLog(`未知消息类型: ${message.type}`, 'info')
  }
}

const drawPreviewDetections = (detections) => {
  const canvas = previewCanvasRef.value
  const img = document.querySelector('.preview-image')
  const video = videoRef.value
  
  if (!canvas || !img || !video) {
    console.log('绘制条件不满足:', { canvas: !!canvas, img: !!img, video: !!video })
    return
  }

  // 使用图片的实际渲染尺寸
  const rect = img.getBoundingClientRect()
  const displayWidth = rect.width
  const displayHeight = rect.height
  
  // 设置画布大小与显示尺寸一致
  canvas.width = displayWidth
  canvas.height = displayHeight

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  if (!detections || detections.length === 0) {
    console.log('没有检测结果')
    return
  }

  // 计算缩放比例（检测框坐标是相对于原始视频尺寸的）
  const scaleX = displayWidth / video.videoWidth
  const scaleY = displayHeight / video.videoHeight

  console.log('绘制检测结果:', detections.length, '个缺陷')
  console.log('缩放比例:', scaleX, scaleY)
  console.log('视频尺寸:', video.videoWidth, video.videoHeight)
  console.log('显示尺寸:', displayWidth, displayHeight)

  detections.forEach((det, index) => {
    const x = (det.x || det.bbox?.[0] || 0) * scaleX
    const y = (det.y || det.bbox?.[1] || 0) * scaleY
    const width = (det.width || det.bbox?.[2] || 0) * scaleX
    const height = (det.height || det.bbox?.[3] || 0) * scaleY
    const className = det.class_name || det.name || 'defect'
    const confidence = det.confidence || 0

    console.log(`缺陷 ${index + 1}: ${className}, 位置: (${x}, ${y}), 大小: ${width}x${height}`)

    ctx.strokeStyle = '#ef4444'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, width, height)

    ctx.fillStyle = '#ef4444'
    ctx.font = 'bold 12px Arial'
    ctx.fillText(`${className} ${(confidence * 100).toFixed(1)}%`, x, y - 5)
  })
}

const selectVideo = () => {
  if (isVideoMode.value) {
    stopVideo()
    isVideoMode.value = false
    return
  }
  videoInputRef.value?.click()
}

const handleVideoSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  
  const url = URL.createObjectURL(file)
  const video = videoRef.value
  if (!video) return
  
  video.src = url
  video.loop = false
  
  isVideoMode.value = true
  isCameraOn.value = false
  
  video.onloadedmetadata = () => {
    addLog(`已加载视频: ${file.name}`, 'info')
  }
  
  video.onended = () => {
    addLog('视频播放完毕', 'info')
    stopDetection()
  }
}

const stopVideo = () => {
  const video = videoRef.value
  if (video) {
    video.pause()
    video.src = ''
    video.load()
  }
  isVideoMode.value = false
  isDetecting.value = false
}

const toggleCamera = async () => {
  if (isCameraOn.value) {
    stopCamera()
    return
  }

  try {
    isProcessing.value = true
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoRef.value.srcObject = mediaStream
    isCameraOn.value = true
    addLog('摄像头已开启', 'success')
  } catch (error) {
    addLog(`无法访问摄像头: ${error.message}`, 'error')
    console.error('Camera error:', error)
  } finally {
    isProcessing.value = false
  }
}

const stopCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  isCameraOn.value = false
  isDetecting.value = false
  addLog('摄像头已关闭', 'info')
}

const toggleDetection = () => {
  if (isDetecting.value) {
    stopDetection()
    return
  }

  if (!isConnected.value) {
    connectWebSocket()
  }
  isDetecting.value = true
  addLog('开始实时检测', 'success')
  
  if (isVideoMode.value && videoRef.value) {
    videoRef.value.play()
  }
  
  startDetectionLoop()
}

const stopDetection = () => {
  isDetecting.value = false
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (isVideoMode.value && videoRef.value) {
    videoRef.value.pause()
  }
  addLog('停止检测', 'info')
}

const startDetectionLoop = () => {
  if (!isDetecting.value || !ws || ws.readyState !== WebSocket.OPEN) return

  const now = Date.now()
  const interval = 1000 / frameRate.value // 计算每帧间隔（毫秒）
  
  // 检查是否应该发送这一帧
  if (now - lastSendTime >= interval) {
    const video = videoRef.value
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)
    
    // 保存预览图片
    previewImage.value = canvas.toDataURL('image/jpeg', 0.8)
    
    const imageData = canvas.toDataURL('image/jpeg', 0.5).split(',')[1]
    
    ws.send(JSON.stringify({
      type: 'image',
      data: imageData,
      frame_id: frameId++
    }))
    
    lastSendTime = now
  }

  animationId = requestAnimationFrame(startDetectionLoop)
}

const resetStats = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'reset_stats' }))
  }
  stats.frameCount = 0
  stats.fps = 0
  stats.totalDefects = 0
  stats.defectFrameCount = 0 // 重置有缺陷的帧数
  stats.defectRate = 0
  fpsLastTime = Date.now()
  fpsFrameCount = 0
  
  // 重置缺陷类型统计
  Object.keys(defectTypeStats).forEach(key => {
    delete defectTypeStats[key]
  })
  
  // 重置置信度分布数据
  confidenceData.value = new Array(101).fill(0)
  updateConfidenceChart()
  
  lastResult.value = null
  addLog('统计数据已重置', 'info')
}

const startHeartbeat = () => {
  stopHeartbeat()
  heartbeatTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 10000) // 每10秒发送一次心跳
}

const stopHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

const disconnect = () => {
  stopHeartbeat()
  if (ws) {
    ws.close()
    ws = null
  }
  isConnected.value = false
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

const initConfidenceChart = () => {
  if (!confidenceChartRef.value) return
  
  confidenceChartInstance = echarts.init(confidenceChartRef.value)
  
  const option = {
    grid: {
      left: '5%',
      right: '5%',
      top: '10%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      name: '置信度(%)',
      nameLocation: 'center',
      nameGap: 30,
      nameTextStyle: {
        color: '#e5e7eb',
        fontSize: 12
      },
      data: Array.from({ length: 101 }, (_, i) => i),
      axisLabel: {
        color: '#e5e7eb',
        fontSize: 11,
        interval: 9,
        formatter: (value) => value + '%'
      },
      axisLine: {
        lineStyle: { color: '#4b5563' }
      },
      axisTick: {
        lineStyle: { color: '#4b5563' }
      }
    },
    yAxis: {
      type: 'value',
      name: '缺陷占比(%)',
      nameLocation: 'center',
      nameGap: 40,
      nameTextStyle: {
        color: '#e5e7eb',
        fontSize: 12
      },
      axisLabel: {
        color: '#e5e7eb',
        fontSize: 11,
        formatter: (value) => value + '%'
      },
      axisLine: {
        lineStyle: { color: '#4b5563' }
      },
      axisTick: {
        lineStyle: { color: '#4b5563' }
      },
      splitLine: {
        lineStyle: { color: '#374151', type: 'dashed' }
      }
    },
    series: [{
      type: 'line',
      data: new Array(101).fill(0),
      smooth: true,
      symbol: 'none',
      lineStyle: {
        color: '#10b981',
        width: 2
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(16, 185, 129, 0.4)' },
          { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
        ])
      }
    }],
    tooltip: {
      trigger: 'axis',
      formatter: (params) => `置信度: ${params[0].axisValue}%<br/>占比: ${params[0].value}%`
    }
  }
  
  confidenceChartInstance.setOption(option)
}

const updateConfidenceChart = () => {
  if (!confidenceChartInstance) return
  
  const total = confidenceData.value.reduce((sum, count) => sum + count, 0)
  const percentageData = confidenceData.value.map(count => 
    total > 0 ? Number((count / total * 100).toFixed(2)) : 0
  )
  
  // 计算80%缺陷置信度大于的值（从高到低累计）
  if (total > 0) {
    const target = total * 0.8
    let cumulative = 0
    for (let i = 100; i >= 0; i--) {
      cumulative += confidenceData.value[i]
      if (cumulative >= target) {
        percentile80.value = i
        break
      }
    }
  } else {
    percentile80.value = 0
  }
  
  confidenceChartInstance.setOption({
    series: [{
      data: percentageData
    }]
  })
}

onMounted(() => {
  addLog('演示页面已加载', 'info')
  connectWebSocket()
  initConfidenceChart()
})

onUnmounted(() => {
  stopDetection()
  stopCamera()
  disconnect()
  if (confidenceChartInstance) {
    confidenceChartInstance.dispose()
    confidenceChartInstance = null
  }
})
</script>

<style scoped>
.demo-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 20px;
}

.demo-header {
  text-align: center;
  margin-bottom: 20px;
  color: white;
}

.demo-header h2 {
  font-size: 28px;
  margin-bottom: 8px;
}

.demo-header p {
  color: #aaa;
}

.demo-content {
  display: flex;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.video-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.preview-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
  color: white;
}

.preview-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 10px;
}

.preview-wrapper {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

.preview-image {
  width: 100%;
  height: auto;
  display: block;
}

.preview-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.preview-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.7);
  padding: 10px 15px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.preview-frame {
  color: #4ade80;
  font-weight: bold;
}

.preview-time {
  color: #9ca3af;
}

.no-preview {
  text-align: center;
  padding: 60px 0;
  color: #666;
}

.video-wrapper {
  position: relative;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
}

.video-wrapper video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.connection-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 8px 12px;
  border-radius: 20px;
  color: #fff;
  font-size: 12px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.offline {
  background: #ef4444;
}

.status-indicator.online {
  background: #22c55e;
}

.video-controls {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.video-controls button {
  flex: 1;
}

.frame-rate-control {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 15px;
  padding: 12px 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: white;
}

.frame-rate-control label {
  font-size: 14px;
  min-width: 70px;
}

.frame-rate-slider {
  flex: 1;
}

.frame-rate-value {
  min-width: 60px;
  text-align: right;
  font-weight: bold;
  color: #4ade80;
}

.info-section {
  width: 380px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stats-card, .chart-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
  color: white;
}

.stats-card h3, .chart-card h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #3b82f6;
}

.stat-label {
  font-size: 12px;
  color: #aaa;
}

.result-content {
  font-size: 14px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.result-info, .result-time {
  margin-bottom: 8px;
  color: #ccc;
}

.detection-list {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.detection-list h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
}

.detection-list ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.detection-list li {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.defect-type {
  color: #ef4444;
}

.defect-conf {
  color: #f59e0b;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar-label {
  min-width: 60px;
  font-size: 13px;
  color: #9ca3af;
}

.bar-wrapper {
  flex: 1;
  height: 12px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  transition: width 0.3s ease;
}

.bar-count {
  width: 50px;
  text-align: right;
  font-weight: bold;
  color: #4ade80;
}

.no-chart-data {
  text-align: center;
  padding: 30px 0;
  color: #666;
}

.chart-container {
  height: 200px;
  width: 100%;
}

.percentile-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #374151;
}

.percentile-label {
  color: #9ca3af;
  font-size: 14px;
}

.percentile-value {
  color: #10b981;
  font-size: 18px;
  font-weight: bold;
}

.log-content .warning .log-message {
  color: #f59e0b;
}

.log-content .error .log-message {
  color: #ef4444;
}
</style>