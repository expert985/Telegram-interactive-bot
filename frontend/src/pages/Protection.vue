<template>
  <div class="protection-page">
    <div class="page-header">
      <h2 class="page-title">🛡️ SafeLine 防护控制台</h2>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-icon" style="background: var(--safeline-primary-light)">
          <el-icon :size="24" color="var(--safeline-primary)"><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardData.unhandled_threats }}</div>
          <div class="stat-label">未处理威胁</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon" style="background: #fef0f0">
          <el-icon :size="24" color="#f56c6c"><UserFilled /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardData.high_risk_users }}</div>
          <div class="stat-label">高风险用户</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon" style="background: #fff7e6">
          <el-icon :size="24" color="#e6a23c"><Lock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardData.active_bans }}</div>
          <div class="stat-label">活跃封禁</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon" style="background: #f0f9ff">
          <el-icon :size="24" color="#409eff"><Operation /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ todayStats.blocked_messages || 0 }}</div>
          <div class="stat-label">今日拦截</div>
        </div>
      </el-card>
    </div>

    <!-- 主内容区域 -->
    <el-tabs v-model="activeTab" class="protection-tabs">
      <!-- 安全事件 -->
      <el-tab-pane label="安全事件" name="events">
        <div class="tab-header">
          <el-space>
            <el-select v-model="eventFilter.threat_level" placeholder="威胁等级" clearable style="width: 150px">
              <el-option label="低危" value="LOW" />
              <el-option label="中危" value="MEDIUM" />
              <el-option label="高危" value="HIGH" />
              <el-option label="严重" value="CRITICAL" />
            </el-select>
            <el-select v-model="eventFilter.event_type" placeholder="事件类型" clearable style="width: 180px">
              <el-option label="消息拦截" value="message_blocked" />
              <el-option label="频率限制" value="rate_limited" />
              <el-option label="行为异常" value="behavior_anomaly" />
              <el-option label="威胁检测" value="threat_detected" />
            </el-select>
            <el-select v-model="eventFilter.handled" placeholder="处理状态" clearable style="width: 150px">
              <el-option label="未处理" :value="false" />
              <el-option label="已处理" :value="true" />
            </el-select>
            <el-button type="primary" @click="loadSecurityEvents">查询</el-button>
          </el-space>
        </div>

        <el-table :data="securityEvents" style="width: 100%" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="user_id" label="用户ID" width="120" />
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column label="威胁等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getThreatLevelType(row.threat_level)" size="small">
                {{ getThreatLevelText(row.threat_level) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="事件类型" width="120">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ getEventTypeText(row.event_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="原因" min-width="200" show-overflow-tooltip />
          <el-table-column label="处理状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.handled ? 'success' : 'warning'" size="small">
                {{ row.handled ? '已处理' : '未处理' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="发生时间" width="180" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button v-if="!row.handled" type="primary" size="small" @click="handleSecurityEvent(row)">
                处理
              </el-button>
              <el-button type="info" size="small" @click="viewEventDetail(row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 防护规则 -->
      <el-tab-pane label="防护规则" name="rules">
        <div class="tab-header">
          <el-button type="primary" @click="showRuleDialog = true">
            <el-icon><Plus /></el-icon>
            添加规则
          </el-button>
        </div>

        <el-table :data="protectionRules" style="width: 100%" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="规则名称" width="180" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column label="类别" width="120">
            <template #default="{ row }">
              <el-tag :type="getRuleCategoryType(row.category)" size="small">
                {{ getRuleCategoryText(row.category) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="getThreatLevelType(row.severity)" size="small">
                {{ getThreatLevelText(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" width="100" />
          <el-table-column prop="trigger_count" label="触发次数" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.enabled"
                @change="toggleRule(row)"
                active-color="var(--safeline-primary)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="editRule(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 高风险用户 -->
      <el-tab-pane label="高风险用户" name="high-risk">
        <el-table :data="highRiskUsers" style="width: 100%" stripe>
          <el-table-column prop="user_id" label="用户ID" width="120" />
          <el-table-column label="用户名" width="150">
            <template #default="{ row }">
              <div class="user-info">
                <div class="username">{{ row.username || '未知' }}</div>
                <div class="name">{{ row.first_name }} {{ row.last_name }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="风险评分" width="150">
            <template #default="{ row }">
              <el-progress
                :percentage="row.risk_score"
                :color="getRiskScoreColor(row.risk_score)"
                :stroke-width="20"
              />
            </template>
          </el-table-column>
          <el-table-column label="风险等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getRiskLevelType(row.risk_level)" size="small">
                {{ getRiskLevelText(row.risk_level) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="spam_count" label="垃圾消息" width="100" />
          <el-table-column prop="warning_count" label="警告次数" width="100" />
          <el-table-column prop="ban_count" label="封禁次数" width="100" />
          <el-table-column prop="recent_violations" label="近期违规" width="100" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="viewUserBehavior(row)">
                查看详情
              </el-button>
              <el-button type="danger" size="small" @click="banUser(row)">
                封禁
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 威胁情报 -->
      <el-tab-pane label="威胁情报" name="intelligence">
        <div class="tab-header">
          <el-button type="primary" @click="showIntelDialog = true">
            <el-icon><Plus /></el-icon>
            添加情报
          </el-button>
        </div>

        <el-table :data="threatIntelligence" style="width: 100%" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column label="威胁类型" width="150">
            <template #default="{ row }">
              <el-tag type="warning" size="small">{{ getThreatTypeText(row.threat_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="threat_value" label="威胁值" min-width="200" show-overflow-tooltip />
          <el-table-column label="威胁等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getThreatLevelType(row.threat_level)" size="small">
                {{ getThreatLevelText(row.threat_level) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="{ row }">
              {{ (row.confidence * 100).toFixed(0) }}%
            </template>
          </el-table-column>
          <el-table-column prop="hit_count" label="命中次数" width="100" />
          <el-table-column prop="source" label="来源" width="120" />
          <el-table-column prop="created_at" label="创建时间" width="180" />
        </el-table>
      </el-tab-pane>

      <!-- 统计数据 -->
      <el-tab-pane label="统计数据" name="statistics">
        <div class="statistics-section">
          <el-card class="stats-detail">
            <template #header>
              <div class="card-header">
                <span>今日防护统计</span>
                <el-date-picker
                  v-model="statsDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  size="small"
                  @change="loadTrendData"
                />
              </div>
            </template>

            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-label">总消息数</div>
                <div class="stat-value-large">{{ todayStats.total_messages || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">拦截消息数</div>
                <div class="stat-value-large" style="color: #f56c6c">{{ todayStats.blocked_messages || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">拦截率</div>
                <div class="stat-value-large" style="color: #e6a23c">{{ todayStats.block_rate || 0 }}%</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">垃圾消息</div>
                <div class="stat-value-large">{{ todayStats.spam_detected || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">钓鱼消息</div>
                <div class="stat-value-large">{{ todayStats.phishing_detected || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">恶意链接</div>
                <div class="stat-value-large">{{ todayStats.malicious_links || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">频率限制触发</div>
                <div class="stat-value-large">{{ todayStats.rate_limit_triggered || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">临时封禁</div>
                <div class="stat-value-large">{{ todayStats.temporary_bans || 0 }}</div>
              </div>
            </div>
          </el-card>

          <!-- 趋势图表 -->
          <el-card class="trend-chart" v-if="trendData.length > 0">
            <template #header>
              <span>防护趋势</span>
            </template>
            <div ref="chartRef" style="width: 100%; height: 400px"></div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 处理安全事件对话框 -->
    <el-dialog v-model="handleEventDialogVisible" title="处理安全事件" width="600px">
      <el-form :model="handleEventForm" label-width="100px">
        <el-form-item label="处理动作">
          <el-select v-model="handleEventForm.handle_action" placeholder="选择处理动作">
            <el-option label="忽略" value="ignore" />
            <el-option label="警告用户" value="warn" />
            <el-option label="封禁用户" value="ban" />
            <el-option label="加入黑名单" value="blacklist" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input v-model="handleEventForm.handle_notes" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleEventDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitHandleEvent">确认</el-button>
      </template>
    </el-dialog>

    <!-- 添加规则对话框 -->
    <el-dialog v-model="showRuleDialog" title="添加防护规则" width="700px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称">
          <el-input v-model="ruleForm.name" placeholder="例如：敏感词过滤" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="ruleForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="ruleForm.category">
            <el-option label="垃圾消息" value="spam" />
            <el-option label="钓鱼检测" value="phishing" />
            <el-option label="恶意链接" value="malicious_link" />
            <el-option label="频率限制" value="rate_limit" />
            <el-option label="行为分析" value="behavior" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="ruleForm.severity">
            <el-option label="低危" value="LOW" />
            <el-option label="中危" value="MEDIUM" />
            <el-option label="高危" value="HIGH" />
            <el-option label="严重" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-slider v-model="ruleForm.priority" :min="0" :max="100" show-input />
        </el-form-item>
        <el-form-item label="条件配置">
          <el-input v-model="ruleForm.conditionsJson" type="textarea" :rows="4" placeholder='{"type": "keyword_match", "keywords": ["示例"]}' />
        </el-form-item>
        <el-form-item label="动作配置">
          <el-input v-model="ruleForm.actionsJson" type="textarea" :rows="4" placeholder='{"action": "block", "notify": true}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRule">确认</el-button>
      </template>
    </el-dialog>

    <!-- 添加威胁情报对话框 -->
    <el-dialog v-model="showIntelDialog" title="添加威胁情报" width="600px">
      <el-form :model="intelForm" label-width="100px">
        <el-form-item label="威胁类型">
          <el-select v-model="intelForm.threat_type">
            <el-option label="恶意IP" value="malicious_ip" />
            <el-option label="恶意域名" value="malicious_domain" />
            <el-option label="恶意哈希" value="malicious_hash" />
            <el-option label="垃圾模式" value="spam_pattern" />
            <el-option label="钓鱼URL" value="phishing_url" />
          </el-select>
        </el-form-item>
        <el-form-item label="威胁值">
          <el-input v-model="intelForm.threat_value" placeholder="例如：192.168.1.1 或 evil.com" />
        </el-form-item>
        <el-form-item label="威胁等级">
          <el-select v-model="intelForm.threat_level">
            <el-option label="低危" value="LOW" />
            <el-option label="中危" value="MEDIUM" />
            <el-option label="高危" value="HIGH" />
            <el-option label="严重" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="置信度">
          <el-slider v-model="intelForm.confidence" :min="0" :max="1" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="intelForm.source" placeholder="例如：manual, external_feed" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="intelForm.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showIntelDialog = false">取消</el-button>
        <el-button type="primary" @click="submitIntel">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Warning, UserFilled, Lock, Operation, Plus } from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 当前标签页
const activeTab = ref('events')

// 仪表盘数据
const dashboardData = reactive({
  unhandled_threats: 0,
  high_risk_users: 0,
  active_bans: 0
})

// 今日统计
const todayStats = reactive<any>({})

// 安全事件
const securityEvents = ref<any[]>([])
const eventFilter = reactive({
  threat_level: '',
  event_type: '',
  handled: undefined as boolean | undefined
})

// 防护规则
const protectionRules = ref<any[]>([])
const showRuleDialog = ref(false)
const ruleForm = reactive({
  name: '',
  description: '',
  category: 'spam',
  severity: 'MEDIUM',
  priority: 50,
  conditionsJson: '',
  actionsJson: ''
})

// 高风险用户
const highRiskUsers = ref<any[]>([])

// 威胁情报
const threatIntelligence = ref<any[]>([])
const showIntelDialog = ref(false)
const intelForm = reactive({
  threat_type: 'spam_pattern',
  threat_value: '',
  threat_level: 'MEDIUM',
  confidence: 0.75,
  source: 'manual',
  description: ''
})

// 处理事件对话框
const handleEventDialogVisible = ref(false)
const currentEvent = ref<any>(null)
const handleEventForm = reactive({
  handle_action: '',
  handle_notes: ''
})

// 统计趋势
const statsDateRange = ref<Date[]>([])
const trendData = ref<any[]>([])
const chartRef = ref<HTMLElement>()

// 刷新所有数据
const refreshData = async () => {
  await Promise.all([
    loadDashboard(),
    loadSecurityEvents(),
    loadProtectionRules(),
    loadHighRiskUsers(),
    loadThreatIntelligence(),
    loadTodayStats()
  ])
  ElMessage.success('数据已刷新')
}

// 加载仪表盘数据
const loadDashboard = async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/api/security/dashboard`)
    if (data.success) {
      Object.assign(dashboardData, data.dashboard)
    }
  } catch (error) {
    console.error('加载仪表盘失败:', error)
  }
}

// 加载今日统计
const loadTodayStats = async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/api/security/statistics/today`)
    if (data.success) {
      Object.assign(todayStats, data.stats)
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

// 加载安全事件
const loadSecurityEvents = async () => {
  try {
    const params: any = { limit: 100 }
    if (eventFilter.threat_level) params.threat_level = eventFilter.threat_level
    if (eventFilter.event_type) params.event_type = eventFilter.event_type
    if (eventFilter.handled !== undefined) params.handled = eventFilter.handled

    const { data } = await axios.get(`${API_BASE}/api/security/events`, { params })
    if (data.success) {
      securityEvents.value = data.events
    }
  } catch (error) {
    console.error('加载安全事件失败:', error)
  }
}

// 加载防护规则
const loadProtectionRules = async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/api/security/rules`)
    if (data.success) {
      protectionRules.value = data.rules
    }
  } catch (error) {
    console.error('加载防护规则失败:', error)
  }
}

// 加载高风险用户
const loadHighRiskUsers = async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/api/security/users/high-risk`, {
      params: { limit: 50 }
    })
    if (data.success) {
      highRiskUsers.value = data.users
    }
  } catch (error) {
    console.error('加载高风险用户失败:', error)
  }
}

// 加载威胁情报
const loadThreatIntelligence = async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/api/security/threat-intelligence`, {
      params: { limit: 100 }
    })
    if (data.success) {
      threatIntelligence.value = data.intelligence
    }
  } catch (error) {
    console.error('加载威胁情报失败:', error)
  }
}

// 加载趋势数据
const loadTrendData = async () => {
  try {
    const days = statsDateRange.value.length > 0 ?
      Math.ceil((statsDateRange.value[1].getTime() - statsDateRange.value[0].getTime()) / (1000 * 60 * 60 * 24)) : 7

    const { data } = await axios.get(`${API_BASE}/api/security/statistics/trend`, {
      params: { days }
    })

    if (data.success) {
      trendData.value = data.trend
      await nextTick()
      renderChart()
    }
  } catch (error) {
    console.error('加载趋势数据失败:', error)
  }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || trendData.value.length === 0) return

  const chart = echarts.init(chartRef.value)

  const dates = trendData.value.map(item => item.date)
  const totalMessages = trendData.value.map(item => item.total_messages)
  const blockedMessages = trendData.value.map(item => item.blocked_messages)
  const blockRate = trendData.value.map(item => item.block_rate)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'var(--safeline-primary)',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['总消息数', '拦截消息数', '拦截率(%)'],
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
      data: dates,
      axisLine: { lineStyle: { color: 'var(--safeline-border)' } }
    },
    yAxis: [
      {
        type: 'value',
        name: '消息数',
        axisLine: { lineStyle: { color: 'var(--safeline-border)' } }
      },
      {
        type: 'value',
        name: '拦截率(%)',
        max: 100,
        axisLine: { lineStyle: { color: 'var(--safeline-border)' } }
      }
    ],
    series: [
      {
        name: '总消息数',
        type: 'line',
        data: totalMessages,
        smooth: true,
        lineStyle: { color: 'var(--safeline-primary)' },
        itemStyle: { color: 'var(--safeline-primary)' }
      },
      {
        name: '拦截消息数',
        type: 'line',
        data: blockedMessages,
        smooth: true,
        lineStyle: { color: '#f56c6c' },
        itemStyle: { color: '#f56c6c' }
      },
      {
        name: '拦截率(%)',
        type: 'line',
        yAxisIndex: 1,
        data: blockRate,
        smooth: true,
        lineStyle: { color: '#e6a23c' },
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }

  chart.setOption(option)
}

// 处理安全事件
const handleSecurityEvent = (event: any) => {
  currentEvent.value = event
  handleEventDialogVisible.value = true
  handleEventForm.handle_action = ''
  handleEventForm.handle_notes = ''
}

// 提交处理事件
const submitHandleEvent = async () => {
  try {
    const { data } = await axios.post(
      `${API_BASE}/api/security/events/${currentEvent.value.id}/handle`,
      handleEventForm
    )

    if (data.success) {
      ElMessage.success('事件已处理')
      handleEventDialogVisible.value = false
      await loadSecurityEvents()
      await loadDashboard()
    }
  } catch (error) {
    ElMessage.error('处理失败')
  }
}

// 查看事件详情
const viewEventDetail = (event: any) => {
  ElMessageBox.alert(
    `<pre>${JSON.stringify(event.evidence, null, 2)}</pre>`,
    '事件详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  )
}

// 切换规则状态
const toggleRule = async (rule: any) => {
  try {
    await axios.put(`${API_BASE}/api/security/rules/${rule.id}/toggle`)
    ElMessage.success(`规则已${rule.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('操作失败')
    rule.enabled = !rule.enabled // 回滚状态
  }
}

// 编辑规则
const editRule = (rule: any) => {
  Object.assign(ruleForm, {
    ...rule,
    conditionsJson: JSON.stringify(rule.conditions, null, 2),
    actionsJson: JSON.stringify(rule.actions, null, 2)
  })
  showRuleDialog.value = true
}

// 提交规则
const submitRule = async () => {
  try {
    const payload = {
      ...ruleForm,
      conditions: JSON.parse(ruleForm.conditionsJson),
      actions: JSON.parse(ruleForm.actionsJson)
    }

    const { data } = await axios.post(`${API_BASE}/api/security/rules`, payload)

    if (data.success) {
      ElMessage.success('规则已添加')
      showRuleDialog.value = false
      await loadProtectionRules()
    }
  } catch (error) {
    ElMessage.error('添加失败，请检查JSON格式')
  }
}

// 提交威胁情报
const submitIntel = async () => {
  try {
    const { data } = await axios.post(`${API_BASE}/api/security/threat-intelligence`, intelForm)

    if (data.success) {
      ElMessage.success('威胁情报已添加')
      showIntelDialog.value = false
      await loadThreatIntelligence()
    }
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

// 查看用户行为
const viewUserBehavior = async (user: any) => {
  try {
    const { data } = await axios.get(`${API_BASE}/api/security/users/${user.user_id}/behavior`)
    if (data.success) {
      ElMessageBox.alert(
        `<pre>${JSON.stringify(data.behavior, null, 2)}</pre>`,
        '用户行为详情',
        {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '关闭'
        }
      )
    }
  } catch (error) {
    ElMessage.error('加载失败')
  }
}

// 封禁用户
const banUser = (user: any) => {
  ElMessageBox.confirm(`确定要封禁用户 ${user.username || user.user_id} 吗？`, '确认封禁', {
    type: 'warning'
  }).then(() => {
    ElMessage.success('封禁功能开发中...')
  })
}

// 工具函数：获取威胁等级类型
const getThreatLevelType = (level: string) => {
  const map: any = {
    'LOW': 'success',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'CRITICAL': 'danger'
  }
  return map[level] || 'info'
}

// 获取威胁等级文本
const getThreatLevelText = (level: string) => {
  const map: any = {
    'LOW': '低危',
    'MEDIUM': '中危',
    'HIGH': '高危',
    'CRITICAL': '严重'
  }
  return map[level] || level
}

// 获取事件类型文本
const getEventTypeText = (type: string) => {
  const map: any = {
    'message_blocked': '消息拦截',
    'rate_limited': '频率限制',
    'behavior_anomaly': '行为异常',
    'threat_detected': '威胁检测'
  }
  return map[type] || type
}

// 获取规则类别类型
const getRuleCategoryType = (category: string) => {
  const map: any = {
    'spam': 'warning',
    'phishing': 'danger',
    'malicious_link': 'danger',
    'rate_limit': 'info',
    'behavior': 'primary',
    'custom': 'success'
  }
  return map[category] || 'info'
}

// 获取规则类别文本
const getRuleCategoryText = (category: string) => {
  const map: any = {
    'spam': '垃圾消息',
    'phishing': '钓鱼检测',
    'malicious_link': '恶意链接',
    'rate_limit': '频率限制',
    'behavior': '行为分析',
    'custom': '自定义'
  }
  return map[category] || category
}

// 获取威胁类型文本
const getThreatTypeText = (type: string) => {
  const map: any = {
    'malicious_ip': '恶意IP',
    'malicious_domain': '恶意域名',
    'malicious_hash': '恶意哈希',
    'spam_pattern': '垃圾模式',
    'phishing_url': '钓鱼URL'
  }
  return map[type] || type
}

// 获取风险评分颜色
const getRiskScoreColor = (score: number) => {
  if (score >= 80) return '#f56c6c'
  if (score >= 60) return '#e6a23c'
  if (score >= 40) return '#409eff'
  return '#67c23a'
}

// 获取风险等级类型
const getRiskLevelType = (level: string) => {
  const map: any = {
    'safe': 'success',
    'low': 'info',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return map[level] || 'info'
}

// 获取风险等级文本
const getRiskLevelText = (level: string) => {
  const map: any = {
    'safe': '安全',
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险',
    'critical': '严重风险'
  }
  return map[level] || level
}

// 初始化
onMounted(async () => {
  await refreshData()
  await loadTrendData()
})
</script>

<style scoped lang="scss">
.protection-page {
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
  }

  .stats-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    margin-bottom: 24px;

    .stat-card {
      :deep(.el-card__body) {
        display: flex;
        align-items: center;
        padding: 20px;
      }

      .stat-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
      }

      .stat-content {
        flex: 1;

        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: var(--safeline-text-primary);
          line-height: 1;
          margin-bottom: 8px;
        }

        .stat-label {
          font-size: 14px;
          color: var(--safeline-text-secondary);
        }
      }
    }
  }

  .protection-tabs {
    background: var(--safeline-bg-secondary);
    border-radius: 8px;
    padding: 16px;

    .tab-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    :deep(.el-tabs__content) {
      color: var(--safeline-text-primary);
    }
  }

  .user-info {
    .username {
      font-weight: 600;
      color: var(--safeline-text-primary);
    }

    .name {
      font-size: 12px;
      color: var(--safeline-text-secondary);
      margin-top: 4px;
    }
  }

  .statistics-section {
    .stats-detail {
      margin-bottom: 24px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 24px;

        .stat-item {
          text-align: center;
          padding: 16px;
          background: var(--safeline-bg-primary);
          border-radius: 8px;

          .stat-label {
            font-size: 14px;
            color: var(--safeline-text-secondary);
            margin-bottom: 8px;
          }

          .stat-value-large {
            font-size: 32px;
            font-weight: 700;
            color: var(--safeline-text-primary);
          }
        }
      }
    }

    .trend-chart {
      :deep(.el-card__body) {
        padding: 16px;
      }
    }
  }
}
</style>
