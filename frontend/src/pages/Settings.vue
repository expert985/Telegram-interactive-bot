<template>
  <div class="settings-page">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">系统设置</h2>
        <p class="page-description">配置系统参数、SafeLine 防护规则和通知选项</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Select" @click="saveAllSettings" :loading="saving">
          保存设置
        </el-button>
        <el-button :icon="Refresh" @click="loadSettings">重置</el-button>
      </div>
    </div>

    <!-- Settings Tabs -->
    <el-card class="settings-card">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- General Settings -->
        <el-tab-pane label="常规设置" name="general">
          <div class="settings-section">
            <h3 class="section-title">基础配置</h3>
            <el-form
              ref="generalFormRef"
              :model="generalSettings"
              label-width="140px"
              size="default"
            >
              <el-form-item label="系统名称">
                <el-input
                  v-model="generalSettings.systemName"
                  placeholder="Telegram 客服系统"
                  clearable
                />
              </el-form-item>

              <el-form-item label="系统描述">
                <el-input
                  v-model="generalSettings.systemDescription"
                  type="textarea"
                  :rows="3"
                  placeholder="简短描述您的客服系统..."
                />
              </el-form-item>

              <el-form-item label="时区">
                <el-select
                  v-model="generalSettings.timezone"
                  placeholder="选择时区"
                  filterable
                >
                  <el-option
                    v-for="tz in timezones"
                    :key="tz.value"
                    :label="tz.label"
                    :value="tz.value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="语言">
                <el-select v-model="generalSettings.language" placeholder="选择语言">
                  <el-option label="简体中文" value="zh-CN" />
                  <el-option label="English" value="en-US" />
                  <el-option label="繁體中文" value="zh-TW" />
                </el-select>
              </el-form-item>

              <el-form-item label="日期格式">
                <el-select v-model="generalSettings.dateFormat">
                  <el-option label="YYYY-MM-DD" value="YYYY-MM-DD" />
                  <el-option label="DD/MM/YYYY" value="DD/MM/YYYY" />
                  <el-option label="MM/DD/YYYY" value="MM/DD/YYYY" />
                </el-select>
              </el-form-item>

              <el-form-item label="启用自动回复">
                <el-switch
                  v-model="generalSettings.autoReply"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="自动回复延迟">
                <el-slider
                  v-model="generalSettings.autoReplyDelay"
                  :min="0"
                  :max="10"
                  :step="0.5"
                  show-stops
                  :marks="{ 0: '即时', 5: '5秒', 10: '10秒' }"
                  :disabled="!generalSettings.autoReply"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- SafeLine Security Settings -->
        <el-tab-pane name="safeline">
          <template #label>
            <span>
              <el-icon style="vertical-align: middle"><Lock /></el-icon>
              SafeLine 防护
            </span>
          </template>

          <div class="settings-section">
            <h3 class="section-title">SafeLine API 配置</h3>
            <el-form
              ref="safelineFormRef"
              :model="safelineSettings"
              label-width="160px"
            >
              <el-alert
                title="SafeLine 防护说明"
                type="info"
                :closable="false"
                style="margin-bottom: 20px"
              >
                SafeLine 是一个强大的 Web 应用防火墙，可以保护您的 Telegram 客服系统免受恶意攻击。
              </el-alert>

              <el-form-item label="SafeLine API URL">
                <el-input
                  v-model="safelineSettings.apiUrl"
                  placeholder="https://safeline-api.example.com"
                />
              </el-form-item>

              <el-form-item label="API Token">
                <el-input
                  v-model="safelineSettings.apiToken"
                  type="password"
                  placeholder="输入 SafeLine API Token"
                  show-password
                />
              </el-form-item>

              <el-form-item label="启用 SafeLine">
                <el-switch
                  v-model="safelineSettings.enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-divider />

              <h3 class="section-title">防护规则</h3>

              <el-form-item label="SQL 注入防护">
                <el-switch
                  v-model="safelineSettings.rules.sqlInjection"
                  :disabled="!safelineSettings.enabled"
                />
              </el-form-item>

              <el-form-item label="XSS 攻击防护">
                <el-switch
                  v-model="safelineSettings.rules.xss"
                  :disabled="!safelineSettings.enabled"
                />
              </el-form-item>

              <el-form-item label="CSRF 防护">
                <el-switch
                  v-model="safelineSettings.rules.csrf"
                  :disabled="!safelineSettings.enabled"
                />
              </el-form-item>

              <el-form-item label="DDoS 防护">
                <el-switch
                  v-model="safelineSettings.rules.ddos"
                  :disabled="!safelineSettings.enabled"
                />
              </el-form-item>

              <el-form-item label="恶意 Bot 识别">
                <el-switch
                  v-model="safelineSettings.rules.botDetection"
                  :disabled="!safelineSettings.enabled"
                />
              </el-form-item>

              <el-divider />

              <h3 class="section-title">威胁阈值</h3>

              <el-form-item label="请求频率限制">
                <el-input-number
                  v-model="safelineSettings.thresholds.rateLimit"
                  :min="1"
                  :max="1000"
                  :step="10"
                  :disabled="!safelineSettings.enabled"
                />
                <span class="input-suffix">请求/分钟</span>
              </el-form-item>

              <el-form-item label="威胁得分阈值">
                <el-slider
                  v-model="safelineSettings.thresholds.threatScore"
                  :min="0"
                  :max="100"
                  :marks="{ 0: '宽松', 50: '中等', 100: '严格' }"
                  :disabled="!safelineSettings.enabled"
                />
              </el-form-item>

              <el-form-item label="IP 封禁时长">
                <el-input-number
                  v-model="safelineSettings.thresholds.banDuration"
                  :min="1"
                  :max="1440"
                  :step="10"
                  :disabled="!safelineSettings.enabled"
                />
                <span class="input-suffix">分钟</span>
              </el-form-item>

              <el-form-item label="动作模式">
                <el-radio-group
                  v-model="safelineSettings.action"
                  :disabled="!safelineSettings.enabled"
                >
                  <el-radio value="monitor">监控模式（仅记录）</el-radio>
                  <el-radio value="block">拦截模式（阻止威胁）</el-radio>
                  <el-radio value="challenge">挑战模式（验证码）</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Notification Settings -->
        <el-tab-pane name="notification">
          <template #label>
            <span>
              <el-icon style="vertical-align: middle"><Bell /></el-icon>
              通知设置
            </span>
          </template>

          <div class="settings-section">
            <h3 class="section-title">通知渠道</h3>
            <el-form
              ref="notificationFormRef"
              :model="notificationSettings"
              label-width="160px"
            >
              <el-form-item label="启用邮件通知">
                <el-switch
                  v-model="notificationSettings.email.enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item
                label="SMTP 服务器"
                v-if="notificationSettings.email.enabled"
              >
                <el-input
                  v-model="notificationSettings.email.smtpServer"
                  placeholder="smtp.example.com"
                />
              </el-form-item>

              <el-form-item label="SMTP 端口" v-if="notificationSettings.email.enabled">
                <el-input-number v-model="notificationSettings.email.smtpPort" :min="1" :max="65535" />
              </el-form-item>

              <el-form-item
                label="发件邮箱"
                v-if="notificationSettings.email.enabled"
              >
                <el-input
                  v-model="notificationSettings.email.fromAddress"
                  placeholder="noreply@example.com"
                />
              </el-form-item>

              <el-form-item
                label="收件邮箱"
                v-if="notificationSettings.email.enabled"
              >
                <el-input
                  v-model="notificationSettings.email.toAddress"
                  placeholder="admin@example.com"
                />
              </el-form-item>

              <el-divider />

              <el-form-item label="启用 Webhook">
                <el-switch
                  v-model="notificationSettings.webhook.enabled"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item
                label="Webhook URL"
                v-if="notificationSettings.webhook.enabled"
              >
                <el-input
                  v-model="notificationSettings.webhook.url"
                  placeholder="https://your-webhook.example.com/notify"
                />
              </el-form-item>

              <el-form-item
                label="Webhook Secret"
                v-if="notificationSettings.webhook.enabled"
              >
                <el-input
                  v-model="notificationSettings.webhook.secret"
                  type="password"
                  placeholder="用于验证 Webhook 请求的密钥"
                  show-password
                />
              </el-form-item>

              <el-divider />

              <h3 class="section-title">通知事件</h3>

              <el-form-item label="新消息通知">
                <el-switch v-model="notificationSettings.events.newMessage" />
              </el-form-item>

              <el-form-item label="安全威胁通知">
                <el-switch v-model="notificationSettings.events.securityThreat" />
              </el-form-item>

              <el-form-item label="系统错误通知">
                <el-switch v-model="notificationSettings.events.systemError" />
              </el-form-item>

              <el-form-item label="账号状态变化">
                <el-switch v-model="notificationSettings.events.accountStatus" />
              </el-form-item>

              <el-form-item label="性能告警">
                <el-switch v-model="notificationSettings.events.performanceAlert" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- WebSocket Settings -->
        <el-tab-pane name="websocket">
          <template #label>
            <span>
              <el-icon style="vertical-align: middle"><Connection /></el-icon>
              WebSocket
            </span>
          </template>

          <div class="settings-section">
            <h3 class="section-title">WebSocket 连接配置</h3>
            <el-form
              ref="websocketFormRef"
              :model="websocketSettings"
              label-width="180px"
            >
              <el-form-item label="WebSocket 服务器">
                <el-input
                  v-model="websocketSettings.serverUrl"
                  placeholder="ws://localhost:8000/ws"
                />
              </el-form-item>

              <el-form-item label="自动重连">
                <el-switch
                  v-model="websocketSettings.autoReconnect"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="重连间隔">
                <el-input-number
                  v-model="websocketSettings.reconnectInterval"
                  :min="1"
                  :max="60"
                  :step="1"
                  :disabled="!websocketSettings.autoReconnect"
                />
                <span class="input-suffix">秒</span>
              </el-form-item>

              <el-form-item label="最大重连次数">
                <el-input-number
                  v-model="websocketSettings.maxReconnectAttempts"
                  :min="1"
                  :max="100"
                  :step="1"
                  :disabled="!websocketSettings.autoReconnect"
                />
              </el-form-item>

              <el-form-item label="心跳间隔">
                <el-input-number
                  v-model="websocketSettings.heartbeatInterval"
                  :min="5"
                  :max="60"
                  :step="5"
                />
                <span class="input-suffix">秒</span>
              </el-form-item>

              <el-form-item label="连接超时">
                <el-input-number
                  v-model="websocketSettings.connectionTimeout"
                  :min="5"
                  :max="120"
                  :step="5"
                />
                <span class="input-suffix">秒</span>
              </el-form-item>

              <el-form-item label="消息缓冲区大小">
                <el-input-number
                  v-model="websocketSettings.bufferSize"
                  :min="10"
                  :max="1000"
                  :step="10"
                />
                <span class="input-suffix">条消息</span>
              </el-form-item>

              <el-form-item label="启用压缩">
                <el-switch
                  v-model="websocketSettings.compression"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Advanced Settings -->
        <el-tab-pane name="advanced">
          <template #label>
            <span>
              <el-icon style="vertical-align: middle"><Setting /></el-icon>
              高级设置
            </span>
          </template>

          <div class="settings-section">
            <h3 class="section-title">性能优化</h3>
            <el-form
              ref="advancedFormRef"
              :model="advancedSettings"
              label-width="180px"
            >
              <el-form-item label="启用缓存">
                <el-switch
                  v-model="advancedSettings.performance.cache"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="缓存过期时间">
                <el-input-number
                  v-model="advancedSettings.performance.cacheExpiration"
                  :min="1"
                  :max="1440"
                  :step="10"
                  :disabled="!advancedSettings.performance.cache"
                />
                <span class="input-suffix">分钟</span>
              </el-form-item>

              <el-form-item label="并发连接数限制">
                <el-input-number
                  v-model="advancedSettings.performance.maxConnections"
                  :min="10"
                  :max="10000"
                  :step="10"
                />
              </el-form-item>

              <el-form-item label="请求队列大小">
                <el-input-number
                  v-model="advancedSettings.performance.queueSize"
                  :min="10"
                  :max="1000"
                  :step="10"
                />
              </el-form-item>

              <el-divider />

              <h3 class="section-title">日志配置</h3>

              <el-form-item label="日志级别">
                <el-select v-model="advancedSettings.logging.level">
                  <el-option label="调试 (DEBUG)" value="debug" />
                  <el-option label="信息 (INFO)" value="info" />
                  <el-option label="警告 (WARNING)" value="warning" />
                  <el-option label="错误 (ERROR)" value="error" />
                  <el-option label="严重 (CRITICAL)" value="critical" />
                </el-select>
              </el-form-item>

              <el-form-item label="启用文件日志">
                <el-switch
                  v-model="advancedSettings.logging.fileLogging"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="日志文件路径" v-if="advancedSettings.logging.fileLogging">
                <el-input
                  v-model="advancedSettings.logging.filePath"
                  placeholder="/var/log/telegram-bot.log"
                />
              </el-form-item>

              <el-form-item label="日志保留天数">
                <el-input-number
                  v-model="advancedSettings.logging.retentionDays"
                  :min="1"
                  :max="365"
                  :step="1"
                />
                <span class="input-suffix">天</span>
              </el-form-item>

              <el-form-item label="记录敏感信息">
                <el-switch
                  v-model="advancedSettings.logging.logSensitiveData"
                  active-text="是"
                  inactive-text="否"
                />
                <el-text type="warning" size="small" style="margin-left: 12px">
                  警告：启用后可能泄露敏感数据
                </el-text>
              </el-form-item>

              <el-divider />

              <h3 class="section-title">数据库</h3>

              <el-form-item label="启用连接池">
                <el-switch
                  v-model="advancedSettings.database.pooling"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="连接池大小">
                <el-input-number
                  v-model="advancedSettings.database.poolSize"
                  :min="5"
                  :max="100"
                  :step="5"
                  :disabled="!advancedSettings.database.pooling"
                />
              </el-form-item>

              <el-form-item label="最大溢出连接数">
                <el-input-number
                  v-model="advancedSettings.database.maxOverflow"
                  :min="0"
                  :max="100"
                  :step="5"
                  :disabled="!advancedSettings.database.pooling"
                />
              </el-form-item>

              <el-form-item label="连接超时">
                <el-input-number
                  v-model="advancedSettings.database.timeout"
                  :min="5"
                  :max="120"
                  :step="5"
                />
                <span class="input-suffix">秒</span>
              </el-form-item>

              <el-divider />

              <h3 class="section-title">开发者选项</h3>

              <el-form-item label="调试模式">
                <el-switch
                  v-model="advancedSettings.developer.debugMode"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="显示性能指标">
                <el-switch
                  v-model="advancedSettings.developer.showPerformanceMetrics"
                />
              </el-form-item>

              <el-form-item label="启用 SQL 日志">
                <el-switch v-model="advancedSettings.developer.sqlLogging" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- Action Buttons (Fixed at bottom on mobile) -->
    <div class="action-bar">
      <el-button type="default" size="large" @click="resetToDefaults">
        恢复默认设置
      </el-button>
      <el-button type="primary" size="large" :loading="saving" @click="saveAllSettings">
        保存所有设置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Select,
  Refresh,
  Lock,
  Bell,
  Connection,
  Setting
} from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// State
const activeTab = ref('general')
const saving = ref(false)

// Timezones list
const timezones = [
  { label: 'UTC+8 北京', value: 'Asia/Shanghai' },
  { label: 'UTC+0 伦敦', value: 'Europe/London' },
  { label: 'UTC-5 纽约', value: 'America/New_York' },
  { label: 'UTC-8 洛杉矶', value: 'America/Los_Angeles' },
  { label: 'UTC+9 东京', value: 'Asia/Tokyo' },
  { label: 'UTC+1 柏林', value: 'Europe/Berlin' }
]

// General Settings
const generalSettings = reactive({
  systemName: 'Telegram 客服系统',
  systemDescription: 'SafeLine 防护版客服系统',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  dateFormat: 'YYYY-MM-DD',
  autoReply: true,
  autoReplyDelay: 2
})

// SafeLine Settings
const safelineSettings = reactive({
  apiUrl: '',
  apiToken: '',
  enabled: true,
  rules: {
    sqlInjection: true,
    xss: true,
    csrf: true,
    ddos: true,
    botDetection: true
  },
  thresholds: {
    rateLimit: 100,
    threatScore: 70,
    banDuration: 60
  },
  action: 'block' as 'monitor' | 'block' | 'challenge'
})

// Notification Settings
const notificationSettings = reactive({
  email: {
    enabled: false,
    smtpServer: '',
    smtpPort: 587,
    fromAddress: '',
    toAddress: ''
  },
  webhook: {
    enabled: false,
    url: '',
    secret: ''
  },
  events: {
    newMessage: true,
    securityThreat: true,
    systemError: true,
    accountStatus: true,
    performanceAlert: false
  }
})

// WebSocket Settings
const websocketSettings = reactive({
  serverUrl: 'ws://localhost:8000/ws',
  autoReconnect: true,
  reconnectInterval: 5,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30,
  connectionTimeout: 30,
  bufferSize: 100,
  compression: false
})

// Advanced Settings
const advancedSettings = reactive({
  performance: {
    cache: true,
    cacheExpiration: 60,
    maxConnections: 1000,
    queueSize: 100
  },
  logging: {
    level: 'info',
    fileLogging: true,
    filePath: '/var/log/telegram-bot.log',
    retentionDays: 30,
    logSensitiveData: false
  },
  database: {
    pooling: true,
    poolSize: 10,
    maxOverflow: 20,
    timeout: 30
  },
  developer: {
    debugMode: false,
    showPerformanceMetrics: false,
    sqlLogging: false
  }
})

// Load settings from backend
const loadSettings = async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/api/settings`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })

    // Merge loaded settings with defaults
    if (data.general) Object.assign(generalSettings, data.general)
    if (data.safeline) Object.assign(safelineSettings, data.safeline)
    if (data.notification) Object.assign(notificationSettings, data.notification)
    if (data.websocket) Object.assign(websocketSettings, data.websocket)
    if (data.advanced) Object.assign(advancedSettings, data.advanced)

    ElMessage.success('设置加载成功')
  } catch (error: any) {
    console.error('Failed to load settings:', error)
    // Use default settings if loading fails
  }
}

// Save all settings
const saveAllSettings = async () => {
  try {
    saving.value = true

    await axios.post(
      `${API_BASE}/api/settings`,
      {
        general: generalSettings,
        safeline: safelineSettings,
        notification: notificationSettings,
        websocket: websocketSettings,
        advanced: advancedSettings
      },
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )

    ElMessage.success('设置保存成功！')
  } catch (error: any) {
    if (error.response) {
      ElMessage.error(error.response.data.detail || '保存失败')
    } else {
      ElMessage.error('保存失败，请检查网络连接')
    }
  } finally {
    saving.value = false
  }
}

// Reset to default settings
const resetToDefaults = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要恢复所有设置到默认值吗？此操作不可撤销。',
      '确认重置',
      {
        confirmButtonText: '恢复默认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // Reset to defaults
    Object.assign(generalSettings, {
      systemName: 'Telegram 客服系统',
      systemDescription: 'SafeLine 防护版客服系统',
      timezone: 'Asia/Shanghai',
      language: 'zh-CN',
      dateFormat: 'YYYY-MM-DD',
      autoReply: true,
      autoReplyDelay: 2
    })

    Object.assign(safelineSettings, {
      apiUrl: '',
      apiToken: '',
      enabled: true,
      rules: {
        sqlInjection: true,
        xss: true,
        csrf: true,
        ddos: true,
        botDetection: true
      },
      thresholds: {
        rateLimit: 100,
        threatScore: 70,
        banDuration: 60
      },
      action: 'block'
    })

    ElMessage.success('已恢复默认设置')
  } catch (error) {
    // User cancelled
  }
}

// Load settings on mount
onMounted(() => {
  loadSettings()
})
</script>

<style scoped lang="scss">
.settings-page {
  padding: 24px;
  padding-bottom: 80px; // Space for fixed action bar

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;

    .page-title {
      margin: 0 0 8px 0;
      color: var(--safeline-text-primary);
      font-size: 24px;
      font-weight: 600;
    }

    .page-description {
      margin: 0;
      color: var(--safeline-text-secondary);
      font-size: 14px;
    }

    .header-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
  }

  .settings-card {
    :deep(.el-card__body) {
      padding: 0;
    }

    :deep(.el-tabs--border-card) {
      border: none;
      box-shadow: none;

      .el-tabs__header {
        background-color: var(--el-fill-color-light);
        border-bottom: 1px solid var(--el-border-color);
      }

      .el-tabs__content {
        padding: 24px;
      }
    }

    .settings-section {
      .section-title {
        margin: 0 0 20px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid var(--safeline-primary);
        color: var(--safeline-text-primary);
        font-size: 16px;
        font-weight: 600;
      }

      .el-form {
        max-width: 800px;

        .input-suffix {
          margin-left: 12px;
          color: var(--safeline-text-secondary);
          font-size: 13px;
        }

        :deep(.el-form-item__label) {
          font-weight: 500;
          color: var(--safeline-text-primary);
        }

        .el-divider {
          margin: 32px 0;
        }
      }
    }
  }

  .action-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px 24px;
    background: var(--el-bg-color);
    border-top: 1px solid var(--el-border-color);
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    z-index: 100;
  }
}

// Responsive
@media (max-width: 768px) {
  .settings-page {
    padding: 16px;
    padding-bottom: 80px;

    .page-header {
      flex-direction: column;
      align-items: stretch;

      .header-actions {
        justify-content: stretch;

        .el-button {
          flex: 1;
        }
      }
    }

    .settings-card {
      :deep(.el-tabs--border-card) {
        .el-tabs__content {
          padding: 16px;
        }
      }

      .settings-section {
        .el-form {
          :deep(.el-form-item__label) {
            text-align: left;
            width: 100% !important;
          }

          :deep(.el-form-item__content) {
            margin-left: 0 !important;
          }
        }
      }
    }

    .action-bar {
      padding: 12px 16px;

      .el-button {
        flex: 1;
      }
    }
  }
}
</style>
