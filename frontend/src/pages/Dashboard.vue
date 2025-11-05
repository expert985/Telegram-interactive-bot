<template>
  <div class="dashboard">
    <h2 class="page-title">数据概览</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(99, 102, 241, 0.1)">
            <el-icon :size="32" color="#6366f1"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">今日会话</div>
            <div class="stat-value">{{ stats.todayConversations || 0 }}</div>
            <div class="stat-change positive">+12% 较昨日</div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(16, 185, 129, 0.1)">
            <el-icon :size="32" color="#10b981"><Message /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">消息总数</div>
            <div class="stat-value">{{ stats.totalMessages || 0 }}</div>
            <div class="stat-change positive">+5.2% 较昨日</div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(245, 158, 11, 0.1)">
            <el-icon :size="32" color="#f59e0b"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">安全拦截</div>
            <div class="stat-value">{{ stats.blockedThreats || 0 }}</div>
            <div class="stat-change negative">-8.1% 较昨日</div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(59, 130, 246, 0.1)">
            <el-icon :size="32" color="#3b82f6"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">在线客服</div>
            <div class="stat-value">{{ stats.onlineAgents || 0 }}<span class="total-agents">/10</span></div>
            <div class="stat-change">实时</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>消息趋势（7天）</span>
              <el-radio-group v-model="chartType" size="small">
                <el-radio-button label="hour">小时</el-radio-button>
                <el-radio-button label="day">天</el-radio-button>
                <el-radio-button label="week">周</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="messageChartRef" style="height: 320px"></div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>威胁分布</span>
          </template>
          <div ref="threatChartRef" style="height: 320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card class="activity-card">
          <template #header>
            <span>最近会话</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in recentConversations"
              :key="index"
              :timestamp="item.time"
              placement="top"
            >
              <div class="timeline-content">
                <div class="user-name">{{ item.userName }}</div>
                <div class="message-preview">{{ item.message }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="activity-card">
          <template #header>
            <span>安全事件</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(alert, index) in recentAlerts"
              :key="index"
              :timestamp="alert.time"
              :type="getThreatType(alert.level)"
              placement="top"
            >
              <div class="timeline-content">
                <div class="threat-title">{{ alert.type }}</div>
                <div class="threat-desc">{{ alert.description }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ChatDotRound, Message, Warning, User } from '@element-plus/icons-vue'

// 统计数据
const stats = ref({
  todayConversations: 156,
  totalMessages: 2843,
  blockedThreats: 47,
  onlineAgents: 3
})

// 图表类型
const chartType = ref('day')

// 图表实例
const messageChartRef = ref<HTMLElement>()
const threatChartRef = ref<HTMLElement>()

// 最近会话
const recentConversations = ref([
  { time: '2分钟前', userName: '用户_123456', message: '我想咨询一下你们的产品...' },
  { time: '5分钟前', userName: '用户_789012', message: '订单发货了吗？' },
  { time: '10分钟前', userName: '用户_345678', message: '感谢你的帮助！' }
])

// 最近安全事件
const recentAlerts = ref([
  { time: '1分钟前', level: 'HIGH', type: '垃圾广告', description: '检测到用户发送大量广告链接' },
  { time: '3分钟前', level: 'MEDIUM', type: '频繁消息', description: '用户消息频率超过限制' },
  { time: '7分钟前', level: 'CRITICAL', type: '钓鱼链接', description: '检测到钓鱼网站链接' }
])

// 获取威胁类型
function getThreatType(level: string) {
  const typeMap: Record<string, any> = {
    'LOW': 'success',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'CRITICAL': 'danger'
  }
  return typeMap[level] || 'info'
}

// 初始化消息趋势图
function initMessageChart() {
  if (!messageChartRef.value) return

  const chart = echarts.init(messageChartRef.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(26, 31, 46, 0.9)',
      borderColor: '#2a3142',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['总消息', '安全拦截'],
      textStyle: { color: '#9ca3af' }
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
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      axisLine: { lineStyle: { color: '#2a3142' } },
      axisLabel: { color: '#9ca3af' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2a3142' } },
      axisLabel: { color: '#9ca3af' },
      splitLine: { lineStyle: { color: '#2a3142' } }
    },
    series: [
      {
        name: '总消息',
        type: 'line',
        smooth: true,
        data: [320, 432, 401, 534, 590, 530, 610],
        itemStyle: { color: '#6366f1' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0)' }
          ])
        }
      },
      {
        name: '安全拦截',
        type: 'line',
        smooth: true,
        data: [12, 25, 18, 32, 28, 21, 35],
        itemStyle: { color: '#f59e0b' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 158, 11, 0.3)' },
            { offset: 1, color: 'rgba(245, 158, 11, 0)' }
          ])
        }
      }
    ]
  }

  chart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => chart.resize())
}

// 初始化威胁分布图
function initThreatChart() {
  if (!threatChartRef.value) return

  const chart = echarts.init(threatChartRef.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(26, 31, 46, 0.9)',
      borderColor: '#2a3142',
      textStyle: { color: '#fff' }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: { color: '#9ca3af' }
    },
    series: [
      {
        name: '威胁类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#1a1f2e',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
            color: '#fff'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 45, name: '垃圾广告', itemStyle: { color: '#f59e0b' } },
          { value: 25, name: '恶意链接', itemStyle: { color: '#ef4444' } },
          { value: 18, name: '钓鱼攻击', itemStyle: { color: '#dc2626' } },
          { value: 12, name: '频率超限', itemStyle: { color: '#f97316' } }
        ]
      }
    ]
  }

  chart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => chart.resize())
}

onMounted(() => {
  initMessageChart()
  initThreatChart()
})

onUnmounted(() => {
  window.removeEventListener('resize', () => {})
})
</script>

<style scoped lang="scss">
.dashboard {
  .page-title {
    margin-bottom: 24px;
    color: var(--safeline-text-primary);
    font-size: 24px;
    font-weight: 600;
  }

  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: linear-gradient(135deg, var(--safeline-bg-secondary) 0%, var(--safeline-bg-tertiary) 100%);
    border: 1px solid var(--safeline-border-color);
    border-radius: var(--safeline-radius-lg);
    transition: all 0.3s ease;

    &:hover {
      border-color: var(--safeline-primary);
      box-shadow: var(--safeline-shadow-lg);
      transform: translateY(-2px);
    }

    .stat-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 64px;
      height: 64px;
      border-radius: var(--safeline-radius-md);
    }

    .stat-info {
      flex: 1;

      .stat-label {
        font-size: 14px;
        color: var(--safeline-text-secondary);
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--safeline-text-primary);

        .total-agents {
          font-size: 16px;
          color: var(--safeline-text-tertiary);
        }
      }

      .stat-change {
        font-size: 12px;
        margin-top: 4px;

        &.positive {
          color: var(--safeline-success);
        }

        &.negative {
          color: var(--safeline-danger);
        }
      }
    }
  }

  .chart-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .activity-card {
    .timeline-content {
      .user-name,
      .threat-title {
        font-weight: 600;
        color: var(--safeline-text-primary);
        margin-bottom: 4px;
      }

      .message-preview,
      .threat-desc {
        font-size: 13px;
        color: var(--safeline-text-secondary);
      }
    }
  }
}
</style>
