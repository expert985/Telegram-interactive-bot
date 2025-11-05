/**
 * WebSocket 客户端封装
 * 用于实时消息推送和客服聊天
 */

export enum WebSocketEvent {
  // 消息事件
  NEW_MESSAGE = 'new_message',
  MESSAGE_SENT = 'message_sent',

  // 会话事件
  CONVERSATION_ASSIGNED = 'conversation_assigned',
  CONVERSATION_CLOSED = 'conversation_closed',
  SESSION_LOCKED = 'session_locked',
  SESSION_UNLOCKED = 'session_unlocked',

  // 安全事件
  SECURITY_ALERT = 'security_alert',
  THREAT_DETECTED = 'threat_detected',
  USER_BANNED = 'user_banned',

  // 统计事件
  STATS_UPDATE = 'stats_update',

  // 系统事件
  AGENT_STATUS = 'agent_status',
  TYPING = 'typing'
}

export interface WebSocketMessage {
  event: WebSocketEvent
  data: any
  timestamp: number
}

export interface WebSocketConfig {
  url: string
  reconnectInterval?: number
  reconnectAttempts?: number
  heartbeatInterval?: number
}

export type MessageHandler = (message: WebSocketMessage) => void
export type ErrorHandler = (error: Event) => void
export type StatusHandler = (connected: boolean) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private config: Required<WebSocketConfig>
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private reconnectCount = 0

  private messageHandlers: Map<WebSocketEvent, MessageHandler[]> = new Map()
  private errorHandlers: ErrorHandler[] = []
  private statusHandlers: StatusHandler[] = []

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 3000,
      reconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config
    }
  }

  /**
   * 连接 WebSocket
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('[WebSocket] 已经连接')
      return
    }

    try {
      console.log('[WebSocket] 正在连接...', this.config.url)
      this.ws = new WebSocket(this.config.url)

      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
    } catch (error) {
      console.error('[WebSocket] 连接失败:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.clearTimers()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.notifyStatus(false)
  }

  /**
   * 发送消息
   */
  send(event: WebSocketEvent, data: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] 未连接，无法发送消息')
      return
    }

    const message: WebSocketMessage = {
      event,
      data,
      timestamp: Date.now()
    }

    try {
      this.ws.send(JSON.stringify(message))
      console.log('[WebSocket] 发送消息:', message)
    } catch (error) {
      console.error('[WebSocket] 发送消息失败:', error)
    }
  }

  /**
   * 注册消息处理器
   */
  on(event: WebSocketEvent, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, [])
    }

    this.messageHandlers.get(event)!.push(handler)

    // 返回取消注册函数
    return () => {
      const handlers = this.messageHandlers.get(event)
      if (handlers) {
        const index = handlers.indexOf(handler)
        if (index > -1) {
          handlers.splice(index, 1)
        }
      }
    }
  }

  /**
   * 注册错误处理器
   */
  onError(handler: ErrorHandler): void {
    this.errorHandlers.push(handler)
  }

  /**
   * 注册状态变化处理器
   */
  onStatusChange(handler: StatusHandler): void {
    this.statusHandlers.push(handler)
  }

  /**
   * 获取连接状态
   */
  get connected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  /**
   * 处理连接打开
   */
  private handleOpen(): void {
    console.log('[WebSocket] ✅ 连接成功')
    this.reconnectCount = 0
    this.startHeartbeat()
    this.notifyStatus(true)
  }

  /**
   * 处理收到消息
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      console.log('[WebSocket] 收到消息:', message)

      // 心跳响应
      if (message.event === 'pong' as WebSocketEvent) {
        return
      }

      // 调用对应的消息处理器
      const handlers = this.messageHandlers.get(message.event)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message)
          } catch (error) {
            console.error('[WebSocket] 消息处理器异常:', error)
          }
        })
      }
    } catch (error) {
      console.error('[WebSocket] 解析消息失败:', error)
    }
  }

  /**
   * 处理错误
   */
  private handleError(event: Event): void {
    console.error('[WebSocket] ❌ 错误:', event)
    this.errorHandlers.forEach(handler => {
      try {
        handler(event)
      } catch (error) {
        console.error('[WebSocket] 错误处理器异常:', error)
      }
    })
  }

  /**
   * 处理连接关闭
   */
  private handleClose(): void {
    console.log('[WebSocket] 连接已关闭')
    this.clearTimers()
    this.notifyStatus(false)
    this.scheduleReconnect()
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.clearHeartbeat()

    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ event: 'ping', timestamp: Date.now() }))
      }
    }, this.config.heartbeatInterval)
  }

  /**
   * 清除心跳定时器
   */
  private clearHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectCount >= this.config.reconnectAttempts) {
      console.error('[WebSocket] 超过最大重连次数，停止重连')
      return
    }

    if (this.reconnectTimer !== null) {
      return // 已经在重连中
    }

    this.reconnectCount++
    const delay = this.config.reconnectInterval * Math.min(this.reconnectCount, 5)

    console.log(`[WebSocket] 将在 ${delay}ms 后重连 (第 ${this.reconnectCount} 次)`)

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  /**
   * 清除所有定时器
   */
  private clearTimers(): void {
    this.clearHeartbeat()

    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  /**
   * 通知状态变化
   */
  private notifyStatus(connected: boolean): void {
    this.statusHandlers.forEach(handler => {
      try {
        handler(connected)
      } catch (error) {
        console.error('[WebSocket] 状态处理器异常:', error)
      }
    })
  }
}

/**
 * 创建 WebSocket 客户端实例
 */
export function createWebSocketClient(config: WebSocketConfig): WebSocketClient {
  return new WebSocketClient(config)
}
