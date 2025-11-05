<template>
  <div class="monitor-page">
    <div class="page-header">
      <h2 class="page-title">📊 实时监控中心</h2>
      <div class="header-actions">
        <el-tag :type="wsConnected ? 'success' : 'danger'" size="large">
          <el-icon><Connection /></el-icon>
          {{ wsConnected ? 'WebSocket 已连接' : 'WebSocket 断开' }}
        </el-tag>
        <el-button @click="refreshStats" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 关键指标卡片 -->
    <div class="metrics-grid">
      <el-card class="metric-card">
        <div class="metric-header">
          <el-icon :size="32" color="var(--safeline-primary)"><Message /></el-icon>
          <span class="metric-label">实时消息流</span>
        </div>
        <div class="metric-value">{{ realtimeStats.messages_per_minute }}/分钟</div>
        <div class="metric-trend">
          <el-icon :color="realtimeStats.message_trend > 0 ? '#67c23a' : '#f56c6c'">
            <CaretTop v-if="realtimeStats.message_trend > 0" />
            <CaretBottom v-else />
          </el-icon>
          <span>{{ Math.abs(realtimeStats.message_trend) }}%</span>
        </div>
      </el-card>

      <el-card class="metric-card">
        <div class="metric-header">
          <el-icon :size="32" color="#67c23a"><User /></el-icon>
          <span class="metric-label">在线客服</span>
        </div>
        <div class="metric-value">{{ wsStats.online_agents?.length || 0 }}</div>
        <div class="metric-subtitle">总计 {{ wsStats.online_count || 0 }} 个连接</div>
      </el-card>

      <el-card class="metric-card">
        <div class="metric-header">
          <el-icon :size="32" color="#e6a23c"><ChatLineRound /></el-icon>
          <span class="metric-label">活跃会话</span>
        </div>
        <div class="metric-value">{{ wsStats.active_conversations || 0 }}</div>
        <div class="metric-subtitle">{{ wsStats.locked_conversations || 0 }} 个已锁定</div>
      </el-card>

      <el-card class="metric-card">
        <div class="metric-header">
          <el-icon :size="32" color="#f56c6c"><Warning /></el-icon>
          <span class="metric-label">实时威胁</span>
        </div>
        <div class="metric-value threat-count">{{ realtimeStats.threats_last_hour || 0 }}</div>
        <div class="metric-subtitle">最近1小时</div>
      </el-card>
    </div>

    <!-- 主内容区 -->
    <el-row :gutter="16" class="content-row">
      <!-- 左侧：实时消息流 -->
      <el-col :span="12">
        <el-card class="realtime-messages">
          <template #header>
            <div class="card-header">
              <span>📨 实时消息流</span>
              <el-switch v-model="autoScroll" active-text="自动滚动" />
            </div>
          </template>

          <div class="message-stream" ref="messageStreamRef">
            <div
              v-for="msg in realtimeMessages"
              :key="msg.id"
              class="stream-message"
              :class="{ 'threat-message': msg.threat_detected }"
            >
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              <div class="message-info">
                <el-tag :type="msg.direction === 'incoming' ? 'primary' : 'success'" size="small">
                  {{ msg.direction === 'incoming' ? '接收' : '发送' }}
                </el-tag>
                <span class="message-from">用户 {{ msg.user_id }}</span>
                <el-tag v-if="msg.threat_detected" type="danger" size="small">
                  🚨 威胁
                </el-tag>
              </div>
              <div class="message-text">{{ msg.text || '[媒体消息]' }}</div>
              <div v-if="msg.threat_detected" class="threat-reason">
                ⚠️ {{ msg.threat_reason }}
              </div>
            </div>
            <div v-if="realtimeMessages.length === 0" class="empty-placeholder">
              <el-empty description="暂无消息" />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：系统状态 -->
      <el-col :span="12">
        <!-- WebSocket 连接统计 -->
        <el-card class="websocket-stats">
          <template #header>
            <span>🔌 WebSocket 连接状态</span>
          </template>

          <div class="stats-list">
            <div class="stat-item">
              <span class="stat-label">在线客服</span>
              <el-tag type="success">{{ wsStats.online_count || 0 }}</el-tag>
            </div>
            <div class="stat-item">
              <span class="stat-label">活跃会话房间</span>
              <el-tag type="primary">{{ wsStats.active_conversations || 0 }}</el-tag>
            </div>
            <div class="stat-item">
              <span class="stat-label">锁定会话</span>
              <el-tag type="warning">{{ wsStats.locked_conversations || 0 }}</el-tag>
            </div>
          </div>

          <el-divider />

          <div class="online-agents">
            <div class="section-title">在线客服列表</div>
            <div class="agent-list">
              <el-tag
                v-for="agent in wsStats.online_agents"
                :key="agent"
                type="success"
                effect="plain"
                class="agent-tag"
              >
                <el-icon><User /></el-icon>
                {{ agent }}
              </el-tag>
              <div v-if="!wsStats.online_agents?.length" class="empty-text">
                暂无在线客服
              </div>
            </div>
          </div>
        </el-card>

        <!-- 实时威胁监控 -->
        <el-card class="threat-monitor" style="margin-top: 16px">
          <template #header>
            <span>🚨 实时威胁监控</span>
          </template>

          <div class="threat-stream">
            <div
              v-for="threat in recentThreats"
              :key="threat.id"
              class="threat-item"
              :class="`threat-${threat.level.toLowerCase()}`"
            >
              <div class="threat-header">
                <el-tag :type="getThreatType(threat.level)" size="small">
                  {{ threat.level }}
                </el-tag>
                <span class="threat-time">{{ formatTime(threat.timestamp) }}</span>
              </div>
              <div class="threat-content">
                <div class="threat-user">用户: {{ threat.user_id }}</div>
                <div class="threat-reason">{{ threat.reason }}</div>
              </div>
            </div>
            <div v-if="recentThreats.length === 0" class="empty-text">
              <el-icon><SuccessFilled /></el-icon>
              暂无威胁检测
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 流量图表 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📈 消息流量趋势</span>
              <el-radio-group v-model="chartTimeRange" size="small">
                <el-radio-button label="1h">1小时</el-radio-button>
                <el-radio-button label="6h">6小时</el-radio-button>
                <el-radio-button label="24h">24小时</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="messageChartRef" style="width: 100%; height: 300px"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🛡️ 威胁检测统计</span>
          </template>
          <div ref="threatChartRef" style="width: 100%; height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 性能指标 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <span>⚡ 系统性能指标</span>
      </template>

      <el-row :gutter="24">
        <el-col :span="6">
          <div class="performance-item">
            <div class="perf-label">消息处理延迟</div>
            <div class="perf-value">{{ performanceMetrics.avg_latency }}ms</div>
            <el-progress
              :percentage="Math.min((performanceMetrics.avg_latency / 1000) * 100, 100)"
              :color="getLatencyColor(performanceMetrics.avg_latency)"
              :show-text="false"
            />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="performance-item">
            <div class="perf-label">WebSocket 心跳</div>
            <div class="perf-value">{{ performanceMetrics.heartbeat_interval }}ms</div>
            <el-tag :type="performanceMetrics.heartbeat_interval < 5000 ? 'success' : 'warning'" size="small">
              {{ performanceMetrics.heartbeat_interval < 5000 ? '正常' : '延迟' }}
            </el-tag>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="performance-item">
            <div class="perf-label">消息队列长度</div>
            <div class="perf-value">{{ performanceMetrics.queue_length }}</div>
            <el-progress
              :percentage="Math.min((performanceMetrics.queue_length / 100) * 100, 100)"
              :color="getQueueColor(performanceMetrics.queue_length)"
              :show-text="false"
            />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="performance-item">
            <div class="perf-label">系统健康度</div>
            <div class="perf-value">{{ performanceMetrics.health_score }}%</div>
            <el-progress
              :percentage="performanceMetrics.health_score"
              :color="getHealthColor(performanceMetrics.health_score)"
              :show-text="false"
            />
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useWebSocketStore } from '@/stores/websocket'
import { storeToRefs } from 'pinia'
import * as echarts from 'echarts'
import {
  Connection,
  Refresh,
  Message,
  User,
  ChatLineRound,
  Warning,
  CaretTop,
  CaretBottom,
  SuccessFilled
} from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// WebSocket Store
const wsStore = useWebSocketStore()
const { connected: wsConnected, recentMessages } = storeToRefs(wsStore)

// 状态
const loading = ref(false)
const autoScroll = ref(true)
const chartTimeRange = ref('1h')

// 统计数据
const wsStats = reactive<any>({
  online_agents: [],
  online_count: 0,
  active_conversations: 0,
  locked_conversations: 0
})

const realtimeStats = reactive({
  messages_per_minute: 0,
  message_trend: 0,
  threats_last_hour: 0
})

const performanceMetrics = reactive({
  avg_latency: 45,
  heartbeat_interval: 3000,
  queue_length: 0,
  health_score: 98
})

// 实时消息流
const realtimeMessages = ref<any[]>([])
const recentThreats = ref<any[]>([])

// 图表引用
const messageStreamRef = ref<HTMLElement>()
const messageChartRef = ref<HTMLElement>()
const threatChartRef = ref<HTMLElement>()

// 图表数据
const messageFlowData = reactive({
  timestamps: [] as string[],
  incoming: [] as number[],
  outgoing: [] as number[]
})

const threatStatsData = reactive({
  low: 0,
  medium: 0,
  high: 0,
  critical: 0
})

// 刷新统计
const refreshStats = async () => {
  loading.value = true
  try {
    // 获取 WebSocket 统计
    const { data } = await axios.get(`${API_BASE}/ws/stats`)
    Object.assign(wsStats, data)

    // 获取安全统计
    const securityData = await axios.get(`${API_BASE}/api/security/statistics/today`)
    if (securityData.data.success) {
      realtimeStats.threats_last_hour = securityData.data.stats.threat_high + securityData.data.stats.threat_critical || 0
    }

    // 模拟实时数据（实际应该从 WebSocket 获取）
    updateRealtimeMetrics()
  } catch (error) {
    console.error('刷新统计失败:', error)
  } finally {
    loading.value = false
  }
}

// 更新实时指标
const updateRealtimeMetrics = () => {
  // 计算每分钟消息数
  const now = Date.now()
  const oneMinuteAgo = now - 60000
  const messagesLastMinute = realtimeMessages.value.filter(
    msg => msg.timestamp > oneMinuteAgo
  ).length

  const prevCount = realtimeStats.messages_per_minute
  realtimeStats.messages_per_minute = messagesLastMinute

  // 计算趋势
  if (prevCount > 0) {
    realtimeStats.message_trend = Math.round(((messagesLastMinute - prevCount) / prevCount) * 100)
  }

  // 更新性能指标
  performanceMetrics.queue_length = realtimeMessages.value.length
  performanceMetrics.health_score = Math.max(100 - performanceMetrics.queue_length, 80)
}

// 监听 WebSocket 消息
watch(() => wsStore.recentMessages, (newMessages) => {
  if (newMessages.length > 0) {
    const latestMessage = newMessages[0]

    // 添加到实时消息流
    realtimeMessages.value.unshift({
      id: Date.now() + Math.random(),
      timestamp: Date.now(),
      ...latestMessage
    })

    // 限制消息数量
    if (realtimeMessages.value.length > 100) {
      realtimeMessages.value = realtimeMessages.value.slice(0, 100)
    }

    // 如果是威胁消息，添加到威胁列表
    if (latestMessage.threat_detected) {
      recentThreats.value.unshift({
        id: Date.now() + Math.random(),
        timestamp: Date.now(),
        user_id: latestMessage.user_id,
        level: latestMessage.threat_level || 'MEDIUM',
        reason: latestMessage.threat_reason || '检测到可疑行为'
      })

      // 更新威胁统计
      const level = (latestMessage.threat_level || 'MEDIUM').toLowerCase()
      if (level === 'low') threatStatsData.low++
      else if (level === 'medium') threatStatsData.medium++
      else if (level === 'high') threatStatsData.high++
      else if (level === 'critical') threatStatsData.critical++

      // 限制威胁数量
      if (recentThreats.value.length > 20) {
        recentThreats.value = recentThreats.value.slice(0, 20)
      }

      renderThreatChart()
    }

    // 自动滚动
    if (autoScroll.value) {
      nextTick(() => {
        if (messageStreamRef.value) {
          messageStreamRef.value.scrollTop = 0
        }
      })
    }

    // 更新消息流图表
    updateMessageFlowChart(latestMessage.direction)
  }
}, { deep: true })

// 更新消息流图表数据
const updateMessageFlowChart = (direction: string) => {
  const now = new Date()
  const timeStr = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`

  // 如果时间戳不存在，添加
  if (!messageFlowData.timestamps.includes(timeStr)) {
    messageFlowData.timestamps.push(timeStr)
    messageFlowData.incoming.push(0)
    messageFlowData.outgoing.push(0)

    // 限制数据点数量
    if (messageFlowData.timestamps.length > 20) {
      messageFlowData.timestamps.shift()
      messageFlowData.incoming.shift()
      messageFlowData.outgoing.shift()
    }
  }

  // 更新对应方向的计数
  const index = messageFlowData.timestamps.length - 1
  if (direction === 'incoming') {
    messageFlowData.incoming[index]++
  } else {
    messageFlowData.outgoing[index]++
  }

  renderMessageChart()
}

// 渲染消息流图表
const renderMessageChart = () => {
  if (!messageChartRef.value) return

  const chart = echarts.init(messageChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'var(--safeline-primary)',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['接收消息', '发送消息'],
      textStyle: { color: 'var(--safeline-text-primary)' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: messageFlowData.timestamps,
      axisLine: { lineStyle: { color: 'var(--safeline-border)' } }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'var(--safeline-border)' } }
    },
    series: [
      {
        name: '接收消息',
        type: 'line',
        smooth: true,
        data: messageFlowData.incoming,
        lineStyle: { color: '#409eff' },
        areaStyle: { color: 'rgba(64, 158, 255, 0.2)' }
      },
      {
        name: '发送消息',
        type: 'line',
        smooth: true,
        data: messageFlowData.outgoing,
        lineStyle: { color: '#67c23a' },
        areaStyle: { color: 'rgba(103, 194, 58, 0.2)' }
      }
    ]
  }

  chart.setOption(option)
}

// 渲染威胁统计图表
const renderThreatChart = () => {
  if (!threatChartRef.value) return

  const chart = echarts.init(threatChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'var(--safeline-primary)',
      textStyle: { color: '#fff' }
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center',
      textStyle: { color: 'var(--safeline-text-primary)' }
    },
    series: [
      {
        name: '威胁等级',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: 'var(--safeline-bg-primary)',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: threatStatsData.low, name: '低危', itemStyle: { color: '#67c23a' } },
          { value: threatStatsData.medium, name: '中危', itemStyle: { color: '#e6a23c' } },
          { value: threatStatsData.high, name: '高危', itemStyle: { color: '#f56c6c' } },
          { value: threatStatsData.critical, name: '严重', itemStyle: { color: '#c62828' } }
        ]
      }
    ]
  }

  chart.setOption(option)
}

// 格式化时间
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

// 获取威胁类型
const getThreatType = (level: string) => {
  const map: any = {
    'LOW': 'success',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'CRITICAL': 'danger'
  }
  return map[level] || 'info'
}

// 获取延迟颜色
const getLatencyColor = (latency: number) => {
  if (latency < 100) return '#67c23a'
  if (latency < 500) return '#e6a23c'
  return '#f56c6c'
}

// 获取队列颜色
const getQueueColor = (length: number) => {
  if (length < 20) return '#67c23a'
  if (length < 50) return '#e6a23c'
  return '#f56c6c'
}

// 获取健康度颜色
const getHealthColor = (score: number) => {
  if (score >= 90) return '#67c23a'
  if (score >= 70) return '#e6a23c'
  return '#f56c6c'
}

// 定时更新
let updateInterval: any = null

onMounted(async () => {
  await refreshStats()

  // 渲染初始图表
  await nextTick()
  renderMessageChart()
  renderThreatChart()

  // 每5秒更新一次指标
  updateInterval = setInterval(() => {
    updateRealtimeMetrics()
    refreshStats()
  }, 5000)

  // 模拟一些初始数据
  for (let i = 0; i < 10; i++) {
    const timeStr = `${new Date().getHours()}:${(new Date().getMinutes() - i).toString().padStart(2, '0')}`
    messageFlowData.timestamps.unshift(timeStr)
    messageFlowData.incoming.unshift(Math.floor(Math.random() * 20))
    messageFlowData.outgoing.unshift(Math.floor(Math.random() * 15))
  }
  renderMessageChart()
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})
</script>

<style scoped lang="scss">
.monitor-page {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    .page-title {
      color: var(--safeline-text-primary);
      font-size: 24px;
      font-weight: 600;
      margin: 0;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    margin-bottom: 16px;

    .metric-card {
      :deep(.el-card__body) {
        padding: 20px;
      }

      .metric-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;

        .metric-label {
          font-size: 14px;
          color: var(--safeline-text-secondary);
          font-weight: 500;
        }
      }

      .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: var(--safeline-text-primary);
        line-height: 1;
        margin-bottom: 8px;

        &.threat-count {
          color: #f56c6c;
        }
      }

      .metric-subtitle {
        font-size: 12px;
        color: var(--safeline-text-secondary);
      }

      .metric-trend {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 14px;
        font-weight: 600;
      }
    }
  }

  .content-row {
    margin-bottom: 16px;
  }

  .realtime-messages {
    height: 500px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .message-stream {
      height: 420px;
      overflow-y: auto;
      padding-right: 8px;

      &::-webkit-scrollbar {
        width: 6px;
      }

      &::-webkit-scrollbar-thumb {
        background: var(--safeline-border);
        border-radius: 3px;
      }

      .stream-message {
        padding: 12px;
        margin-bottom: 8px;
        background: var(--safeline-bg-primary);
        border-radius: 8px;
        border-left: 3px solid var(--safeline-primary);

        &.threat-message {
          border-left-color: #f56c6c;
          background: rgba(245, 108, 108, 0.1);
        }

        .message-time {
          font-size: 12px;
          color: var(--safeline-text-secondary);
          margin-bottom: 6px;
        }

        .message-info {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;

          .message-from {
            font-size: 13px;
            color: var(--safeline-text-primary);
          }
        }

        .message-text {
          font-size: 14px;
          color: var(--safeline-text-primary);
          word-break: break-word;
        }

        .threat-reason {
          margin-top: 8px;
          padding: 8px;
          background: rgba(245, 108, 108, 0.1);
          border-radius: 4px;
          font-size: 12px;
          color: #f56c6c;
        }
      }

      .empty-placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
      }
    }
  }

  .websocket-stats {
    .stats-list {
      .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid var(--safeline-border);

        &:last-child {
          border-bottom: none;
        }

        .stat-label {
          font-size: 14px;
          color: var(--safeline-text-secondary);
        }
      }
    }

    .online-agents {
      .section-title {
        font-size: 14px;
        color: var(--safeline-text-secondary);
        margin-bottom: 12px;
      }

      .agent-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .agent-tag {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .empty-text {
          font-size: 13px;
          color: var(--safeline-text-secondary);
          font-style: italic;
        }
      }
    }
  }

  .threat-monitor {
    .threat-stream {
      max-height: 300px;
      overflow-y: auto;

      &::-webkit-scrollbar {
        width: 6px;
      }

      &::-webkit-scrollbar-thumb {
        background: var(--safeline-border);
        border-radius: 3px;
      }

      .threat-item {
        padding: 12px;
        margin-bottom: 8px;
        background: var(--safeline-bg-primary);
        border-radius: 6px;
        border-left: 3px solid #e6a23c;

        &.threat-high {
          border-left-color: #f56c6c;
        }

        &.threat-critical {
          border-left-color: #c62828;
          background: rgba(198, 40, 40, 0.1);
        }

        .threat-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          .threat-time {
            font-size: 12px;
            color: var(--safeline-text-secondary);
          }
        }

        .threat-content {
          .threat-user {
            font-size: 13px;
            color: var(--safeline-text-primary);
            margin-bottom: 4px;
          }

          .threat-reason {
            font-size: 12px;
            color: var(--safeline-text-secondary);
          }
        }
      }

      .empty-text {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 20px;
        color: var(--safeline-text-secondary);
        font-size: 14px;
      }
    }
  }

  .performance-item {
    text-align: center;

    .perf-label {
      font-size: 13px;
      color: var(--safeline-text-secondary);
      margin-bottom: 8px;
    }

    .perf-value {
      font-size: 24px;
      font-weight: 700;
      color: var(--safeline-text-primary);
      margin-bottom: 8px;
    }
  }
}
</style>
