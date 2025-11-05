/**
 * WebSocket 状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createWebSocketClient, WebSocketClient, WebSocketEvent } from '@/utils/websocket'
import { ElNotification } from 'element-plus'

export const useWebSocketStore = defineStore('websocket', () => {
  // WebSocket 客户端实例
  const client = ref<WebSocketClient | null>(null)

  // 连接状态
  const connected = ref(false)

  // 最新消息队列（用于显示通知）
  const recentMessages = ref<any[]>([])

  // 安全告警队列
  const securityAlerts = ref<any[]>([])

  // 统计数据
  const stats = ref<any>({})

  /**
   * 连接 WebSocket
   */
  function connect() {
    if (client.value) {
      console.warn('WebSocket 已经连接')
      return
    }

    // 获取 WebSocket URL（根据环境自动选择）
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = import.meta.env.DEV ? 'localhost:8000' : window.location.host
    const wsUrl = `${wsProtocol}//${wsHost}/ws`

    // 创建客户端
    client.value = createWebSocketClient({ url: wsUrl })

    // 注册状态变化处理
    client.value.onStatusChange((status) => {
      connected.value = status

      if (status) {
        ElNotification.success({
          title: 'WebSocket',
          message: '实时连接已建立',
          duration: 2000
        })
      } else {
        ElNotification.warning({
          title: 'WebSocket',
          message: '实时连接已断开',
          duration: 2000
        })
      }
    })

    // 注册消息处理器
    registerMessageHandlers()

    // 开始连接
    client.value.connect()
  }

  /**
   * 断开连接
   */
  function disconnect() {
    if (client.value) {
      client.value.disconnect()
      client.value = null
    }
    connected.value = false
  }

  /**
   * 发送消息
   */
  function send(event: WebSocketEvent, data: any) {
    if (!client.value || !connected.value) {
      console.warn('WebSocket 未连接，无法发送消息')
      return
    }

    client.value.send(event, data)
  }

  /**
   * 注册消息处理器
   */
  function registerMessageHandlers() {
    if (!client.value) return

    // 新消息通知
    client.value.on(WebSocketEvent.NEW_MESSAGE, (message) => {
      recentMessages.value.unshift(message.data)

      // 限制队列长度
      if (recentMessages.value.length > 50) {
        recentMessages.value.pop()
      }

      // 显示通知
      ElNotification.info({
        title: '新消息',
        message: `来自用户 ${message.data.user_name || message.data.user_id} 的消息`,
        duration: 3000
      })
    })

    // 安全告警
    client.value.on(WebSocketEvent.SECURITY_ALERT, (message) => {
      securityAlerts.value.unshift(message.data)

      // 限制队列长度
      if (securityAlerts.value.length > 100) {
        securityAlerts.value.pop()
      }

      // 根据威胁等级显示不同类型的通知
      const alertType = message.data.threat_level === 'CRITICAL' ? 'error' : 'warning'

      ElNotification[alertType]({
        title: '🚨 安全告警',
        message: message.data.reason || '检测到可疑行为',
        duration: 5000
      })
    })

    // 威胁检测
    client.value.on(WebSocketEvent.THREAT_DETECTED, (message) => {
      ElNotification.error({
        title: '⚠️ 威胁检测',
        message: `检测到 ${message.data.threat_type}: ${message.data.description}`,
        duration: 5000
      })
    })

    // 用户封禁
    client.value.on(WebSocketEvent.USER_BANNED, (message) => {
      ElNotification.warning({
        title: '🚫 用户封禁',
        message: `用户 ${message.data.user_id} 已被封禁`,
        duration: 3000
      })
    })

    // 统计更新
    client.value.on(WebSocketEvent.STATS_UPDATE, (message) => {
      stats.value = message.data
    })

    // 会话分配
    client.value.on(WebSocketEvent.CONVERSATION_ASSIGNED, (message) => {
      ElNotification.success({
        title: '新会话',
        message: `已分配给您一个新的客服会话`,
        duration: 3000
      })
    })

    // 会话锁定
    client.value.on(WebSocketEvent.SESSION_LOCKED, (message) => {
      console.log('会话已锁定:', message.data)
    })

    // 会话解锁
    client.value.on(WebSocketEvent.SESSION_UNLOCKED, (message) => {
      console.log('会话已解锁:', message.data)
    })

    // 客服状态变化
    client.value.on(WebSocketEvent.AGENT_STATUS, (message) => {
      console.log('客服状态:', message.data)
    })
  }

  /**
   * 清空告警队列
   */
  function clearAlerts() {
    securityAlerts.value = []
  }

  /**
   * 清空消息队列
   */
  function clearMessages() {
    recentMessages.value = []
  }

  return {
    // 状态
    connected,
    recentMessages,
    securityAlerts,
    stats,

    // 方法
    connect,
    disconnect,
    send,
    clearAlerts,
    clearMessages
  }
})
