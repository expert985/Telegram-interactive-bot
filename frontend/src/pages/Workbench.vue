<template>
  <div class="workbench">
    <div class="workbench-container">
      <!-- 左侧：会话列表 -->
      <div class="conversation-list">
        <div class="list-header">
          <h3>会话列表</h3>
          <el-badge :value="unreadCount" :hidden="unreadCount === 0">
            <el-button size="small" :icon="Refresh" @click="refreshConversations">
              刷新
            </el-button>
          </el-badge>
        </div>

        <div class="list-search">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户或消息..."
            :prefix-icon="Search"
            clearable
          />
        </div>

        <div class="list-filter">
          <el-radio-group v-model="filterStatus" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="unread">未读</el-radio-button>
            <el-radio-button label="locked">锁定</el-radio-button>
          </el-radio-group>
        </div>

        <el-scrollbar class="list-scrollbar">
          <div
            v-for="conv in filteredConversations"
            :key="conv.id"
            class="conversation-item"
            :class="{
              active: currentConversation?.id === conv.id,
              unread: conv.unread_count > 0,
              locked: conv.is_locked
            }"
            @click="selectConversation(conv)"
          >
            <el-avatar :size="48" :src="conv.user_avatar">
              <el-icon><User /></el-icon>
            </el-avatar>

            <div class="item-content">
              <div class="item-header">
                <span class="user-name">{{ conv.user_name || `用户_${conv.user_id}` }}</span>
                <span class="time">{{ formatTime(conv.last_message_time) }}</span>
              </div>

              <div class="item-body">
                <span class="last-message">{{ conv.last_message }}</span>
                <el-badge
                  v-if="conv.unread_count > 0"
                  :value="conv.unread_count"
                  type="danger"
                />
              </div>

              <div class="item-footer">
                <el-tag v-if="conv.is_locked" type="warning" size="small">
                  <el-icon><Lock /></el-icon>
                  {{ conv.locked_by === agentId ? '我正在回复' : `${conv.locked_by} 正在回复` }}
                </el-tag>

                <el-tag
                  v-if="conv.risk_level"
                  :type="getRiskTagType(conv.risk_level)"
                  size="small"
                >
                  {{ conv.risk_level }}
                </el-tag>
              </div>
            </div>
          </div>

          <el-empty v-if="filteredConversations.length === 0" description="暂无会话" />
        </el-scrollbar>
      </div>

      <!-- 中间：聊天窗口 -->
      <div class="chat-window">
        <template v-if="currentConversation">
          <!-- 聊天头部 -->
          <div class="chat-header">
            <div class="header-left">
              <el-avatar :size="40" :src="currentConversation.user_avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="header-info">
                <div class="user-name">{{ currentConversation.user_name || `用户_${currentConversation.user_id}` }}</div>
                <div class="user-status">
                  <el-icon :size="10" color="#10b981"><CircleFilled /></el-icon>
                  <span>在线</span>
                </div>
              </div>
            </div>

            <div class="header-right">
              <el-tag
                v-if="currentConversation.is_locked && currentConversation.locked_by !== agentId"
                type="warning"
              >
                <el-icon><Lock /></el-icon>
                {{ currentConversation.locked_by }} 正在回复
              </el-tag>

              <el-button-group>
                <el-button :icon="RefreshRight" @click="loadMessages">刷新</el-button>
                <el-button :icon="Close" @click="closeConversation">关闭会话</el-button>
              </el-button-group>
            </div>
          </div>

          <!-- 消息列表 -->
          <el-scrollbar ref="messageScrollbar" class="message-list">
            <div class="message-container">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="message-item"
                :class="msg.direction"
              >
                <div v-if="msg.direction === 'incoming'" class="message-avatar">
                  <el-avatar :size="36" :src="currentConversation.user_avatar">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                </div>

                <div class="message-content">
                  <div class="message-info">
                    <span class="sender-name">
                      {{ msg.direction === 'incoming' ? currentConversation.user_name : '我' }}
                    </span>
                    <span class="message-time">{{ formatMessageTime(msg.created_at) }}</span>
                  </div>

                  <div class="message-bubble">
                    <div v-if="msg.content_type === 'text'" class="text-content">
                      {{ msg.content }}
                    </div>

                    <div v-else-if="msg.content_type === 'image'" class="image-content">
                      <el-image :src="msg.file_url" fit="cover" />
                    </div>

                    <div v-else-if="msg.content_type === 'file'" class="file-content">
                      <el-icon><Document /></el-icon>
                      <span>{{ msg.file_name }}</span>
                    </div>

                    <!-- 安全提示 -->
                    <div v-if="msg.threat_detected" class="threat-warning">
                      <el-icon><Warning /></el-icon>
                      <span>{{ msg.threat_reason }}</span>
                    </div>
                  </div>
                </div>

                <div v-if="msg.direction === 'outgoing'" class="message-avatar">
                  <el-avatar :size="36">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                </div>
              </div>

              <!-- 对方正在输入提示 -->
              <div v-if="isTyping" class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-text">对方正在输入...</span>
              </div>
            </div>
          </el-scrollbar>

          <!-- 输入框 -->
          <div class="chat-input">
            <div class="input-toolbar">
              <el-button-group>
                <el-button :icon="Picture" @click="sendImage">图片</el-button>
                <el-button :icon="Paperclip" @click="sendFile">文件</el-button>
                <el-button :icon="ChatLineSquare" @click="showQuickReplies">快捷回复</el-button>
              </el-button-group>
            </div>

            <div class="input-area">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
                @keydown.enter.exact.prevent="sendMessage"
                @input="handleTyping"
              />
            </div>

            <div class="input-actions">
              <el-button type="primary" :icon="Promotion" @click="sendMessage">
                发送消息
              </el-button>
            </div>
          </div>
        </template>

        <el-empty v-else description="请选择一个会话" />
      </div>

      <!-- 右侧：用户信息 -->
      <div class="user-info-panel">
        <template v-if="currentConversation">
          <div class="panel-header">
            <h3>用户信息</h3>
          </div>

          <div class="panel-content">
            <!-- 基本信息 -->
            <el-card class="info-card">
              <template #header>
                <span>基本信息</span>
              </template>

              <div class="info-item">
                <label>用户 ID:</label>
                <span>{{ currentConversation.user_id }}</span>
              </div>

              <div class="info-item">
                <label>用户名:</label>
                <span>{{ currentConversation.user_name || '未设置' }}</span>
              </div>

              <div class="info-item">
                <label>首次联系:</label>
                <span>{{ formatDate(currentConversation.created_at) }}</span>
              </div>

              <div class="info-item">
                <label>消息数:</label>
                <span>{{ currentConversation.message_count || 0 }}</span>
              </div>
            </el-card>

            <!-- 安全评分 -->
            <el-card class="info-card security-card">
              <template #header>
                <span>安全评分</span>
              </template>

              <div class="security-score">
                <el-progress
                  type="dashboard"
                  :percentage="currentConversation.security_score || 100"
                  :color="getScoreColor(currentConversation.security_score || 100)"
                >
                  <template #default="{ percentage }">
                    <span class="score-text">{{ percentage }}</span>
                  </template>
                </el-progress>
              </div>

              <div class="risk-level">
                <label>风险等级:</label>
                <el-tag
                  :type="getRiskTagType(currentConversation.risk_level || 'LOW')"
                  size="large"
                  class="risk-tag"
                >
                  {{ currentConversation.risk_level || 'LOW' }}
                </el-tag>
              </div>

              <div v-if="currentConversation.risk_factors" class="risk-factors">
                <label>风险因素:</label>
                <el-tag
                  v-for="(factor, index) in currentConversation.risk_factors"
                  :key="index"
                  type="warning"
                  size="small"
                  class="factor-tag"
                >
                  {{ factor }}
                </el-tag>
              </div>
            </el-card>

            <!-- 操作按钮 -->
            <div class="panel-actions">
              <el-button
                type="danger"
                :icon="CircleClose"
                @click="banUser"
              >
                封禁用户
              </el-button>

              <el-button
                type="warning"
                :icon="Warning"
                @click="reportThreat"
              >
                举报威胁
              </el-button>
            </div>
          </div>
        </template>

        <el-empty v-else description="请选择一个会话" />
      </div>
    </div>

    <!-- 快捷回复对话框 -->
    <el-dialog
      v-model="quickReplyDialogVisible"
      title="快捷回复"
      width="700px"
      :close-on-click-modal="false"
    >
      <div class="quick-reply-dialog">
        <div class="dialog-search">
          <el-input
            v-model="quickReplySearch"
            placeholder="搜索快捷回复..."
            :prefix-icon="Search"
            clearable
          />
        </div>

        <div class="category-tabs">
          <el-radio-group v-model="selectedCategory" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button
              v-for="category in replyCategories"
              :key="category"
              :label="category"
            >
              {{ category }}
            </el-radio-button>
          </el-radio-group>
        </div>

        <el-scrollbar height="400px" class="reply-list">
          <div
            v-for="reply in filteredQuickReplies"
            :key="reply.id"
            class="reply-item"
            @click="useQuickReply(reply)"
          >
            <div class="reply-header">
              <div class="reply-title">
                <span class="title-text">{{ reply.title }}</span>
                <el-tag size="small" type="info">{{ reply.shortcut }}</el-tag>
              </div>
              <el-tag size="small">{{ reply.category }}</el-tag>
            </div>
            <div class="reply-content">{{ reply.content }}</div>
            <div class="reply-footer">
              <span class="usage-count">使用次数: {{ reply.usage_count || 0 }}</span>
            </div>
          </div>

          <el-empty v-if="filteredQuickReplies.length === 0" description="暂无快捷回复" />
        </el-scrollbar>

        <div class="dialog-tip">
          💡 提示：点击快捷回复即可插入到输入框
        </div>
      </div>

      <template #footer>
        <el-button @click="quickReplyDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="manageQuickReplies">
          管理快捷回复
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useWebSocketStore } from '@/stores/websocket'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Search,
  Refresh,
  Lock,
  CircleFilled,
  RefreshRight,
  Close,
  Document,
  Warning,
  Picture,
  Paperclip,
  ChatLineSquare,
  Promotion,
  CircleClose
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

// WebSocket Store
const wsStore = useWebSocketStore()

// 当前客服 ID (TODO: 从登录状态获取)
const agentId = ref('agent_001')

// 会话列表
const conversations = ref<any[]>([
  {
    id: '1',
    user_id: 123456,
    user_name: '张三',
    user_avatar: '',
    last_message: '你好，我想咨询一下你们的产品...',
    last_message_time: new Date().toISOString(),
    unread_count: 2,
    is_locked: false,
    locked_by: null,
    risk_level: 'LOW',
    security_score: 95,
    message_count: 15,
    created_at: '2025-01-01T10:00:00Z'
  },
  {
    id: '2',
    user_id: 789012,
    user_name: '李四',
    user_avatar: '',
    last_message: '订单发货了吗？',
    last_message_time: new Date(Date.now() - 300000).toISOString(),
    unread_count: 0,
    is_locked: true,
    locked_by: 'agent_002',
    risk_level: 'MEDIUM',
    security_score: 75,
    risk_factors: ['频繁消息', '包含敏感词'],
    message_count: 8,
    created_at: '2025-01-02T14:30:00Z'
  },
  {
    id: '3',
    user_id: 345678,
    user_name: '王五',
    user_avatar: '',
    last_message: '点击这个链接领取福利 http://malicious.com',
    last_message_time: new Date(Date.now() - 600000).toISOString(),
    unread_count: 1,
    is_locked: false,
    locked_by: null,
    risk_level: 'CRITICAL',
    security_score: 30,
    risk_factors: ['恶意链接', '垃圾广告', '钓鱼攻击'],
    message_count: 3,
    created_at: '2025-01-03T09:15:00Z'
  }
])

// 当前选中的会话
const currentConversation = ref<any>(null)

// 消息列表
const messages = ref<any[]>([])

// 输入框内容
const inputMessage = ref('')

// 搜索关键词
const searchKeyword = ref('')

// 筛选状态
const filterStatus = ref('all')

// 正在输入状态
const isTyping = ref(false)

// 消息滚动容器
const messageScrollbar = ref<any>(null)

// 快捷回复相关
const quickReplyDialogVisible = ref(false)
const quickReplySearch = ref('')
const selectedCategory = ref('all')
const quickReplies = ref<any[]>([])
const replyCategories = ref<string[]>([])

// 未读消息数
const unreadCount = computed(() => {
  return conversations.value.reduce((sum, conv) => sum + conv.unread_count, 0)
})

// 过滤后的快捷回复列表
const filteredQuickReplies = computed(() => {
  let result = quickReplies.value

  // 分类过滤
  if (selectedCategory.value !== 'all') {
    result = result.filter(reply => reply.category === selectedCategory.value)
  }

  // 搜索过滤
  if (quickReplySearch.value) {
    const keyword = quickReplySearch.value.toLowerCase()
    result = result.filter(reply =>
      reply.title?.toLowerCase().includes(keyword) ||
      reply.content?.toLowerCase().includes(keyword) ||
      reply.shortcut?.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 过滤后的会话列表
const filteredConversations = computed(() => {
  let result = conversations.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(conv =>
      conv.user_name?.toLowerCase().includes(keyword) ||
      conv.last_message?.toLowerCase().includes(keyword)
    )
  }

  // 状态过滤
  if (filterStatus.value === 'unread') {
    result = result.filter(conv => conv.unread_count > 0)
  } else if (filterStatus.value === 'locked') {
    result = result.filter(conv => conv.is_locked)
  }

  return result
})

// 刷新会话列表
function refreshConversations() {
  // TODO: 从 API 获取会话列表
  ElMessage.success('会话列表已刷新')
}

// 选择会话
async function selectConversation(conv: any) {
  currentConversation.value = conv

  // 清除未读数
  conv.unread_count = 0

  // 加载消息
  await loadMessages()

  // 加入会话房间
  wsStore.send('join_conversation' as any, {
    conversation_id: conv.id
  })

  // 锁定会话
  wsStore.send('lock_conversation' as any, {
    conversation_id: conv.id
  })
}

// 加载消息
async function loadMessages() {
  if (!currentConversation.value) return

  // TODO: 从 API 获取消息列表
  messages.value = [
    {
      id: '1',
      direction: 'incoming',
      content_type: 'text',
      content: '你好，我想咨询一下你们的产品...',
      created_at: '2025-01-05T10:00:00Z',
      threat_detected: false
    },
    {
      id: '2',
      direction: 'outgoing',
      content_type: 'text',
      content: '您好！很高兴为您服务，请问有什么可以帮到您的？',
      created_at: '2025-01-05T10:01:00Z',
      threat_detected: false
    },
    {
      id: '3',
      direction: 'incoming',
      content_type: 'text',
      content: '我想了解一下价格',
      created_at: '2025-01-05T10:02:00Z',
      threat_detected: false
    }
  ]

  // 滚动到底部
  await nextTick()
  scrollToBottom()
}

// 发送消息
async function sendMessage() {
  if (!inputMessage.value.trim() || !currentConversation.value) return

  const message = {
    id: `${Date.now()}`,
    direction: 'outgoing',
    content_type: 'text',
    content: inputMessage.value,
    created_at: new Date().toISOString(),
    threat_detected: false
  }

  messages.value.push(message)

  // 通过 WebSocket 发送
  wsStore.send('send_message' as any, {
    conversation_id: currentConversation.value.id,
    content: inputMessage.value,
    content_type: 'text'
  })

  // 清空输入框
  inputMessage.value = ''

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 解锁会话
  wsStore.send('unlock_conversation' as any, {
    conversation_id: currentConversation.value.id
  })
}

// 处理输入（触发正在输入事件）
let typingTimeout: any = null
function handleTyping() {
  if (!currentConversation.value) return

  // 发送正在输入事件
  wsStore.send('typing' as any, {
    conversation_id: currentConversation.value.id
  })

  // 清除之前的定时器
  if (typingTimeout) {
    clearTimeout(typingTimeout)
  }

  // 3秒后自动取消
  typingTimeout = setTimeout(() => {
    isTyping.value = false
  }, 3000)
}

// 关闭会话
async function closeConversation() {
  if (!currentConversation.value) return

  const result = await ElMessageBox.confirm(
    '确定要关闭这个会话吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).catch(() => false)

  if (result) {
    // 离开会话房间
    wsStore.send('leave_conversation' as any, {
      conversation_id: currentConversation.value.id
    })

    currentConversation.value = null
    messages.value = []

    ElMessage.success('会话已关闭')
  }
}

// 发送图片
function sendImage() {
  ElMessage.info('图片发送功能开发中...')
}

// 发送文件
function sendFile() {
  ElMessage.info('文件发送功能开发中...')
}

// 显示快捷回复
async function showQuickReplies() {
  quickReplyDialogVisible.value = true

  // 如果还没加载，则加载快捷回复
  if (quickReplies.value.length === 0) {
    await loadQuickReplies()
  }
}

// 加载快捷回复列表
async function loadQuickReplies() {
  try {
    // TODO: 替换为真实 API 调用
    // const { data } = await axios.get('/api/quick_replies')
    // quickReplies.value = data

    // 模拟数据
    quickReplies.value = [
      {
        id: 1,
        title: '欢迎语',
        shortcut: '/welcome',
        content: '您好！欢迎咨询，我是客服小助手，很高兴为您服务。请问有什么可以帮助您的吗？',
        category: '问候',
        usage_count: 156
      },
      {
        id: 2,
        title: '工作时间',
        shortcut: '/hours',
        content: '我们的工作时间是：周一至周五 9:00-18:00，周末及节假日休息。如有紧急问题，请留言，我们会在工作时间内尽快回复您。',
        category: '常用',
        usage_count: 89
      },
      {
        id: 3,
        title: '产品介绍',
        shortcut: '/product',
        content: '我们提供多款优质产品，包括基础版、专业版和企业版。每个版本都有不同的功能特点，可根据您的需求选择。您可以访问我们的官网了解详情。',
        category: '产品',
        usage_count: 124
      },
      {
        id: 4,
        title: '价格咨询',
        shortcut: '/price',
        content: '感谢您对价格的关注。我们的产品定价根据版本和功能有所不同，具体价格如下：\n- 基础版：99元/月\n- 专业版：299元/月\n- 企业版：请联系商务洽谈\n\n如需详细报价，请提供您的联系方式。',
        category: '产品',
        usage_count: 201
      },
      {
        id: 5,
        title: '售后支持',
        shortcut: '/support',
        content: '我们提供7x24小时的售后技术支持。如遇到问题，您可以：\n1. 联系在线客服（工作时间）\n2. 发送邮件到 support@example.com\n3. 拨打服务热线：400-xxx-xxxx\n\n我们会尽快为您解决问题！',
        category: '售后',
        usage_count: 67
      },
      {
        id: 6,
        title: '退款政策',
        shortcut: '/refund',
        content: '我们的退款政策如下：\n- 购买后7天内，无理由退款\n- 7-30天内，扣除20%手续费后退款\n- 超过30天，不支持退款\n\n如需办理退款，请提供订单号和退款原因。',
        category: '售后',
        usage_count: 43
      },
      {
        id: 7,
        title: '感谢语',
        shortcut: '/thanks',
        content: '非常感谢您的咨询！如果还有其他问题，随时欢迎您联系我们。祝您生活愉快！',
        category: '问候',
        usage_count: 178
      },
      {
        id: 8,
        title: '稍等片刻',
        shortcut: '/wait',
        content: '好的，请稍等片刻，我马上为您查询/处理。',
        category: '常用',
        usage_count: 312
      },
      {
        id: 9,
        title: '转人工',
        shortcut: '/human',
        content: '好的，我会为您转接到人工客服。请稍候...',
        category: '常用',
        usage_count: 56
      },
      {
        id: 10,
        title: '留下联系方式',
        shortcut: '/contact',
        content: '为了更好地为您服务，能否留下您的联系方式（手机号或邮箱）？我们的专属客服会尽快与您联系。',
        category: '常用',
        usage_count: 92
      }
    ]

    // 提取分类
    const categories = new Set(quickReplies.value.map(r => r.category))
    replyCategories.value = Array.from(categories)
  } catch (error) {
    ElMessage.error('加载快捷回复失败')
    console.error(error)
  }
}

// 使用快捷回复
function useQuickReply(reply: any) {
  // 插入到输入框
  inputMessage.value = reply.content

  // 关闭对话框
  quickReplyDialogVisible.value = false

  // TODO: 更新使用次数
  // await axios.post(`/api/quick_replies/${reply.id}/use`)

  ElMessage.success(`已插入快捷回复：${reply.title}`)
}

// 管理快捷回复
function manageQuickReplies() {
  quickReplyDialogVisible.value = false
  ElMessage.info('快捷回复管理功能开发中...')
  // TODO: 跳转到快捷回复管理页面或打开管理对话框
}

// 封禁用户
async function banUser() {
  if (!currentConversation.value) return

  const result = await ElMessageBox.confirm(
    `确定要封禁用户 ${currentConversation.value.user_name || currentConversation.value.user_id} 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    }
  ).catch(() => false)

  if (result) {
    // TODO: 调用封禁 API
    ElMessage.success('用户已封禁')
  }
}

// 举报威胁
async function reportThreat() {
  ElMessage.info('举报威胁功能开发中...')
}

// 滚动到底部
function scrollToBottom() {
  if (messageScrollbar.value) {
    const scrollElement = messageScrollbar.value.$refs.wrapRef
    scrollElement.scrollTop = scrollElement.scrollHeight
  }
}

// 格式化时间
function formatTime(time: string) {
  return dayjs(time).fromNow()
}

function formatMessageTime(time: string) {
  return dayjs(time).format('HH:mm')
}

function formatDate(time: string) {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 获取风险标签类型
function getRiskTagType(level: string) {
  const typeMap: Record<string, any> = {
    'LOW': 'success',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'CRITICAL': 'danger'
  }
  return typeMap[level] || 'info'
}

// 获取评分颜色
function getScoreColor(score: number) {
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

// 监听 WebSocket 新消息
watch(() => wsStore.recentMessages, (newMessages) => {
  if (newMessages.length > 0 && currentConversation.value) {
    const latestMessage = newMessages[0]

    // 如果是当前会话的消息，添加到消息列表
    if (latestMessage.conversation_id === currentConversation.value.id) {
      messages.value.push({
        id: latestMessage.id,
        direction: 'incoming',
        content_type: latestMessage.content_type || 'text',
        content: latestMessage.content,
        created_at: latestMessage.timestamp,
        threat_detected: latestMessage.threat_detected
      })

      scrollToBottom()
    }
  }
}, { deep: true })

onMounted(() => {
  // TODO: 加载会话列表
})

onUnmounted(() => {
  // 离开所有会话
  if (currentConversation.value) {
    wsStore.send('leave_conversation' as any, {
      conversation_id: currentConversation.value.id
    })
  }
})
</script>

<style scoped lang="scss">
.workbench {
  height: calc(100vh - 60px - 48px); // 减去头部和内边距

  .workbench-container {
    display: grid;
    grid-template-columns: 320px 1fr 300px;
    gap: 0;
    height: 100%;
    background: var(--safeline-bg-primary);
  }

  // 会话列表
  .conversation-list {
    display: flex;
    flex-direction: column;
    background: var(--safeline-bg-secondary);
    border-right: 1px solid var(--safeline-border-color);

    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      border-bottom: 1px solid var(--safeline-border-color);

      h3 {
        margin: 0;
        font-size: 16px;
        color: var(--safeline-text-primary);
      }
    }

    .list-search {
      padding: 12px 16px;
      border-bottom: 1px solid var(--safeline-border-color);
    }

    .list-filter {
      padding: 12px 16px;
      border-bottom: 1px solid var(--safeline-border-color);
    }

    .list-scrollbar {
      flex: 1;
      overflow: hidden;
    }

    .conversation-item {
      display: flex;
      gap: 12px;
      padding: 12px 16px;
      cursor: pointer;
      border-bottom: 1px solid var(--safeline-border-color);
      transition: background 0.2s;

      &:hover {
        background: var(--safeline-bg-hover);
      }

      &.active {
        background: var(--safeline-bg-tertiary);
        border-left: 3px solid var(--safeline-primary);
      }

      &.unread {
        background: rgba(99, 102, 241, 0.05);
      }

      .item-content {
        flex: 1;
        min-width: 0;

        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;

          .user-name {
            font-weight: 600;
            color: var(--safeline-text-primary);
          }

          .time {
            font-size: 12px;
            color: var(--safeline-text-tertiary);
          }
        }

        .item-body {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          .last-message {
            flex: 1;
            font-size: 13px;
            color: var(--safeline-text-secondary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }

        .item-footer {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
      }
    }
  }

  // 聊天窗口
  .chat-window {
    display: flex;
    flex-direction: column;
    background: var(--safeline-bg-primary);

    .chat-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: var(--safeline-bg-secondary);
      border-bottom: 1px solid var(--safeline-border-color);

      .header-left {
        display: flex;
        align-items: center;
        gap: 12px;

        .header-info {
          .user-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--safeline-text-primary);
          }

          .user-status {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: var(--safeline-text-secondary);
            margin-top: 2px;
          }
        }
      }

      .header-right {
        display: flex;
        gap: 12px;
        align-items: center;
      }
    }

    .message-list {
      flex: 1;
      padding: 20px;

      .message-container {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .message-item {
        display: flex;
        gap: 12px;

        &.incoming {
          justify-content: flex-start;
        }

        &.outgoing {
          justify-content: flex-end;

          .message-content {
            align-items: flex-end;

            .message-bubble {
              background: var(--safeline-primary);
              color: #fff;
            }
          }
        }

        .message-avatar {
          flex-shrink: 0;
        }

        .message-content {
          display: flex;
          flex-direction: column;
          gap: 4px;
          max-width: 60%;

          .message-info {
            display: flex;
            gap: 8px;
            align-items: center;
            font-size: 12px;
            color: var(--safeline-text-tertiary);

            .sender-name {
              font-weight: 600;
            }
          }

          .message-bubble {
            padding: 12px 16px;
            border-radius: var(--safeline-radius-lg);
            background: var(--safeline-bg-secondary);
            color: var(--safeline-text-primary);
            word-wrap: break-word;

            .threat-warning {
              display: flex;
              align-items: center;
              gap: 6px;
              margin-top: 8px;
              padding: 6px 10px;
              background: rgba(239, 68, 68, 0.1);
              border: 1px solid var(--safeline-danger);
              border-radius: var(--safeline-radius-sm);
              font-size: 12px;
              color: var(--safeline-danger);
            }
          }
        }
      }

      .typing-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        padding-left: 48px;

        .typing-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--safeline-text-tertiary);
          animation: typing 1.4s infinite;

          &:nth-child(2) {
            animation-delay: 0.2s;
          }

          &:nth-child(3) {
            animation-delay: 0.4s;
          }
        }

        .typing-text {
          font-size: 12px;
          color: var(--safeline-text-tertiary);
        }
      }

      @keyframes typing {
        0%, 60%, 100% {
          opacity: 0.3;
          transform: scale(0.8);
        }
        30% {
          opacity: 1;
          transform: scale(1);
        }
      }
    }

    .chat-input {
      border-top: 1px solid var(--safeline-border-color);
      background: var(--safeline-bg-secondary);

      .input-toolbar {
        padding: 12px 20px;
        border-bottom: 1px solid var(--safeline-border-color);
      }

      .input-area {
        padding: 12px 20px;
      }

      .input-actions {
        padding: 0 20px 12px;
        display: flex;
        justify-content: flex-end;
      }
    }
  }

  // 用户信息面板
  .user-info-panel {
    display: flex;
    flex-direction: column;
    background: var(--safeline-bg-secondary);
    border-left: 1px solid var(--safeline-border-color);

    .panel-header {
      padding: 16px;
      border-bottom: 1px solid var(--safeline-border-color);

      h3 {
        margin: 0;
        font-size: 16px;
        color: var(--safeline-text-primary);
      }
    }

    .panel-content {
      flex: 1;
      padding: 16px;
      overflow-y: auto;

      .info-card {
        margin-bottom: 16px;

        .info-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid var(--safeline-border-color);

          &:last-child {
            border-bottom: none;
          }

          label {
            color: var(--safeline-text-secondary);
            font-size: 13px;
          }

          span {
            color: var(--safeline-text-primary);
            font-size: 13px;
          }
        }

        &.security-card {
          .security-score {
            display: flex;
            justify-content: center;
            padding: 20px 0;

            .score-text {
              font-size: 24px;
              font-weight: 700;
            }
          }

          .risk-level {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;

            label {
              color: var(--safeline-text-secondary);
            }

            .risk-tag {
              font-weight: 600;
            }
          }

          .risk-factors {
            label {
              display: block;
              color: var(--safeline-text-secondary);
              margin-bottom: 8px;
            }

            .factor-tag {
              margin-right: 6px;
              margin-bottom: 6px;
            }
          }
        }
      }

      .panel-actions {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 16px;

        .el-button {
          width: 100%;
        }
      }
    }
  }
}

// 快捷回复对话框样式
.quick-reply-dialog {
  .dialog-search {
    margin-bottom: 16px;
  }

  .category-tabs {
    margin-bottom: 16px;

    :deep(.el-radio-group) {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
  }

  .reply-list {
    .reply-item {
      padding: 12px;
      margin-bottom: 8px;
      background: var(--safeline-bg-secondary);
      border-radius: 8px;
      border: 1px solid var(--safeline-border);
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        background: var(--safeline-bg-primary);
        border-color: var(--safeline-primary);
        transform: translateX(4px);
      }

      .reply-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .reply-title {
          display: flex;
          align-items: center;
          gap: 8px;

          .title-text {
            font-size: 14px;
            font-weight: 600;
            color: var(--safeline-text-primary);
          }
        }
      }

      .reply-content {
        font-size: 13px;
        color: var(--safeline-text-secondary);
        line-height: 1.6;
        margin-bottom: 8px;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .reply-footer {
        display: flex;
        justify-content: flex-end;

        .usage-count {
          font-size: 12px;
          color: var(--safeline-text-secondary);
        }
      }
    }
  }

  .dialog-tip {
    margin-top: 16px;
    padding: 8px 12px;
    background: rgba(99, 102, 241, 0.1);
    border-radius: 4px;
    font-size: 13px;
    color: var(--safeline-primary);
    text-align: center;
  }
}
</style>
