<template>
  <div class="accounts-page">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">账号管理</h2>
        <p class="page-description">管理 Telegram Bot 和 Userbot 账号</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showAddBotDialog">
          添加 Bot 账号
        </el-button>
        <el-button type="success" :icon="User" @click="showAddUserbotDialog">
          添加 Userbot 账号
        </el-button>
        <el-button :icon="Refresh" @click="refreshAccounts">刷新</el-button>
      </div>
    </div>

    <!-- Statistics Cards -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="32" color="#409eff"><Avatar /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ totalAccounts }}</div>
              <div class="stat-label">总账号数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="32" color="#67c23a"><CircleCheck /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ onlineAccounts }}</div>
              <div class="stat-label">在线账号</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="32" color="#409eff"><Robot /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ botCount }}</div>
              <div class="stat-label">Bot 账号</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon :size="32" color="#67c23a"><User /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ userbotCount }}</div>
              <div class="stat-label">Userbot 账号</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Accounts Table -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>账号列表</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索账号..."
            :prefix-icon="Search"
            style="width: 300px"
            clearable
          />
        </div>
      </template>

      <el-table
        :data="filteredAccounts"
        style="width: 100%"
        :row-class-name="tableRowClassName"
        v-loading="loading"
      >
        <el-table-column type="index" label="#" width="60" />

        <el-table-column prop="name" label="账号名称" min-width="180">
          <template #default="{ row }">
            <div class="account-name">
              <el-avatar :size="32" :src="row.avatar">
                {{ row.name.charAt(0) }}
              </el-avatar>
              <div class="name-info">
                <div class="name">{{ row.name }}</div>
                <div class="username">@{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'bot' ? 'primary' : 'success'">
              {{ row.type === 'bot' ? 'Bot' : 'Userbot' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'online' ? 'success' : row.status === 'offline' ? 'info' : 'danger'"
              effect="dark"
            >
              <el-icon style="vertical-align: middle">
                <CircleCheck v-if="row.status === 'online'" />
                <CircleClose v-else-if="row.status === 'offline'" />
                <Warning v-else />
              </el-icon>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="phone" label="手机号" width="140">
          <template #default="{ row }">
            <span v-if="row.phone">{{ row.phone }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="messageCount" label="消息数" width="100" sortable />

        <el-table-column prop="lastActive" label="最后活跃" width="160">
          <template #default="{ row }">
            {{ formatTime(row.lastActive) }}
          </template>
        </el-table-column>

        <el-table-column prop="createdAt" label="添加时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'offline'"
              type="primary"
              size="small"
              :icon="VideoPlay"
              @click="connectAccount(row)"
            >
              连接
            </el-button>
            <el-button
              v-else-if="row.status === 'online'"
              type="info"
              size="small"
              :icon="VideoPause"
              @click="disconnectAccount(row)"
            >
              断开
            </el-button>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="deleteAccount(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredAccounts.length"
        />
      </div>
    </el-card>

    <!-- Add Bot Dialog -->
    <el-dialog
      v-model="addBotDialogVisible"
      title="添加 Bot 账号"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="botFormRef"
        :model="botForm"
        :rules="botFormRules"
        label-width="100px"
      >
        <el-alert
          title="如何获取 Bot Token？"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <template #default>
            <ol style="margin: 8px 0; padding-left: 20px">
              <li>在 Telegram 中搜索 @BotFather</li>
              <li>发送 /newbot 命令创建新 Bot</li>
              <li>按提示设置 Bot 名称和用户名</li>
              <li>复制 BotFather 返回的 Token</li>
            </ol>
          </template>
        </el-alert>

        <el-form-item label="Bot Token" prop="token">
          <el-input
            v-model="botForm.token"
            type="textarea"
            :rows="3"
            placeholder="例如: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="备注名称" prop="nickname">
          <el-input
            v-model="botForm.nickname"
            placeholder="可选，便于识别该账号"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addBotDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="botFormLoading"
          @click="submitBotForm"
        >
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- Add Userbot Dialog -->
    <el-dialog
      v-model="addUserbotDialogVisible"
      title="添加 Userbot 账号"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="userbotFormRef"
        :model="userbotForm"
        :rules="userbotFormRules"
        label-width="120px"
      >
        <el-alert
          title="什么是 Userbot？"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <template #default>
            <p style="margin: 8px 0">
              Userbot 是使用真实用户账号登录的机器人，可以执行更多操作（如主动发起对话）。
              需要您的 Telegram 账号 API ID、API Hash 和登录验证。
            </p>
          </template>
        </el-alert>

        <el-tabs v-model="userbotLoginMethod" style="margin-bottom: 20px">
          <el-tab-pane label="手机号登录" name="phone">
            <el-form-item label="API ID" prop="apiId">
              <el-input
                v-model="userbotForm.apiId"
                placeholder="从 my.telegram.org 获取"
              />
            </el-form-item>

            <el-form-item label="API Hash" prop="apiHash">
              <el-input
                v-model="userbotForm.apiHash"
                placeholder="从 my.telegram.org 获取"
              />
            </el-form-item>

            <el-form-item label="手机号" prop="phone">
              <el-input
                v-model="userbotForm.phone"
                placeholder="例如: +8613800138000"
              />
            </el-form-item>

            <el-alert
              v-if="userbotForm.requiresCode"
              title="需要验证码"
              type="warning"
              :closable="false"
              style="margin-bottom: 16px"
            >
              验证码已发送到您的 Telegram，请输入验证码继续登录。
            </el-alert>

            <el-form-item
              v-if="userbotForm.requiresCode"
              label="验证码"
              prop="code"
            >
              <el-input
                v-model="userbotForm.code"
                placeholder="输入收到的验证码"
              />
            </el-form-item>

            <el-form-item
              v-if="userbotForm.requiresPassword"
              label="两步验证密码"
              prop="password"
            >
              <el-input
                v-model="userbotForm.password"
                type="password"
                placeholder="如果启用了两步验证，请输入密码"
                show-password
              />
            </el-form-item>
          </el-tab-pane>

          <el-tab-pane label="Session String" name="session">
            <el-form-item label="Session String" prop="sessionString">
              <el-input
                v-model="userbotForm.sessionString"
                type="textarea"
                :rows="4"
                placeholder="粘贴已有的 Session String（从之前导出的会话）"
              />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>

        <el-form-item label="备注名称" prop="nickname">
          <el-input
            v-model="userbotForm.nickname"
            placeholder="可选，便于识别该账号"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addUserbotDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="userbotFormLoading"
          @click="submitUserbotForm"
        >
          {{ userbotForm.requiresCode || userbotForm.requiresPassword ? '验证登录' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  User,
  Refresh,
  Search,
  Delete,
  VideoPlay,
  VideoPause,
  Avatar,
  Robot,
  CircleCheck,
  CircleClose,
  Warning
} from '@element-plus/icons-vue'
import axios from 'axios'
import type { FormInstance, FormRules } from 'element-plus'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// State
const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// Accounts data
const accounts = ref<any[]>([])

// Statistics
const totalAccounts = computed(() => accounts.value.length)
const onlineAccounts = computed(() => accounts.value.filter(a => a.status === 'online').length)
const botCount = computed(() => accounts.value.filter(a => a.type === 'bot').length)
const userbotCount = computed(() => accounts.value.filter(a => a.type === 'userbot').length)

// Filtered accounts
const filteredAccounts = computed(() => {
  if (!searchQuery.value) return accounts.value

  const keyword = searchQuery.value.toLowerCase()
  return accounts.value.filter(account =>
    account.name?.toLowerCase().includes(keyword) ||
    account.username?.toLowerCase().includes(keyword) ||
    account.phone?.includes(keyword)
  )
})

// Add Bot Dialog
const addBotDialogVisible = ref(false)
const botFormRef = ref<FormInstance>()
const botFormLoading = ref(false)
const botForm = reactive({
  token: '',
  nickname: ''
})

const botFormRules: FormRules = {
  token: [
    { required: true, message: '请输入 Bot Token', trigger: 'blur' },
    { min: 20, message: 'Token 格式不正确', trigger: 'blur' }
  ]
}

// Add Userbot Dialog
const addUserbotDialogVisible = ref(false)
const userbotFormRef = ref<FormInstance>()
const userbotFormLoading = ref(false)
const userbotLoginMethod = ref('phone')
const userbotForm = reactive({
  apiId: '',
  apiHash: '',
  phone: '',
  code: '',
  password: '',
  sessionString: '',
  nickname: '',
  requiresCode: false,
  requiresPassword: false,
  tempSessionId: '' // For multi-step login
})

const userbotFormRules: FormRules = {
  apiId: [{ required: true, message: '请输入 API ID', trigger: 'blur' }],
  apiHash: [{ required: true, message: '请输入 API Hash', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^\+?[1-9]\d{1,14}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  sessionString: [{ required: true, message: '请输入 Session String', trigger: 'blur' }]
}

// Methods
const showAddBotDialog = () => {
  addBotDialogVisible.value = true
  botForm.token = ''
  botForm.nickname = ''
}

const showAddUserbotDialog = () => {
  addUserbotDialogVisible.value = true
  userbotLoginMethod.value = 'phone'
  Object.assign(userbotForm, {
    apiId: '',
    apiHash: '',
    phone: '',
    code: '',
    password: '',
    sessionString: '',
    nickname: '',
    requiresCode: false,
    requiresPassword: false,
    tempSessionId: ''
  })
}

const submitBotForm = async () => {
  if (!botFormRef.value) return

  try {
    await botFormRef.value.validate()
    botFormLoading.value = true

    const { data } = await axios.post(
      `${API_BASE}/api/accounts/bot`,
      {
        token: botForm.token,
        nickname: botForm.nickname || undefined
      },
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )

    ElMessage.success('Bot 账号添加成功！')
    addBotDialogVisible.value = false
    await refreshAccounts()
  } catch (error: any) {
    if (error.response) {
      ElMessage.error(error.response.data.detail || '添加失败')
    } else {
      ElMessage.error('添加失败，请检查网络连接')
    }
  } finally {
    botFormLoading.value = false
  }
}

const submitUserbotForm = async () => {
  if (!userbotFormRef.value) return

  try {
    // Validate based on login method
    if (userbotLoginMethod.value === 'phone') {
      await userbotFormRef.value.validateField(['apiId', 'apiHash', 'phone'])
    } else {
      await userbotFormRef.value.validateField(['sessionString'])
    }

    userbotFormLoading.value = true

    if (userbotLoginMethod.value === 'session') {
      // Session string login
      const { data } = await axios.post(
        `${API_BASE}/api/accounts/userbot/session`,
        {
          session_string: userbotForm.sessionString,
          nickname: userbotForm.nickname || undefined
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      )

      ElMessage.success('Userbot 账号添加成功！')
      addUserbotDialogVisible.value = false
      await refreshAccounts()
    } else {
      // Phone login
      if (!userbotForm.requiresCode && !userbotForm.requiresPassword) {
        // Step 1: Send code
        const { data } = await axios.post(
          `${API_BASE}/api/accounts/userbot/phone`,
          {
            api_id: userbotForm.apiId,
            api_hash: userbotForm.apiHash,
            phone: userbotForm.phone
          },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        )

        userbotForm.tempSessionId = data.session_id
        userbotForm.requiresCode = true
        ElMessage.info('验证码已发送，请查收')
      } else {
        // Step 2/3: Verify code and/or password
        const { data } = await axios.post(
          `${API_BASE}/api/accounts/userbot/verify`,
          {
            session_id: userbotForm.tempSessionId,
            code: userbotForm.code || undefined,
            password: userbotForm.password || undefined,
            nickname: userbotForm.nickname || undefined
          },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        )

        if (data.requires_password) {
          userbotForm.requiresPassword = true
          ElMessage.warning('需要输入两步验证密码')
        } else {
          ElMessage.success('Userbot 账号添加成功！')
          addUserbotDialogVisible.value = false
          await refreshAccounts()
        }
      }
    }
  } catch (error: any) {
    if (error.response) {
      ElMessage.error(error.response.data.detail || '操作失败')
    } else {
      ElMessage.error('操作失败，请检查网络连接')
    }
  } finally {
    userbotFormLoading.value = false
  }
}

const connectAccount = async (account: any) => {
  try {
    loading.value = true
    await axios.post(
      `${API_BASE}/api/accounts/${account.id}/connect`,
      {},
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )
    ElMessage.success(`${account.name} 连接成功`)
    await refreshAccounts()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '连接失败')
  } finally {
    loading.value = false
  }
}

const disconnectAccount = async (account: any) => {
  try {
    loading.value = true
    await axios.post(
      `${API_BASE}/api/accounts/${account.id}/disconnect`,
      {},
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )
    ElMessage.success(`${account.name} 已断开连接`)
    await refreshAccounts()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '断开失败')
  } finally {
    loading.value = false
  }
}

const deleteAccount = async (account: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除账号 "${account.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    loading.value = true
    await axios.delete(`${API_BASE}/api/accounts/${account.id}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })

    ElMessage.success('删除成功')
    await refreshAccounts()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  } finally {
    loading.value = false
  }
}

const refreshAccounts = async () => {
  try {
    loading.value = true
    const { data } = await axios.get(`${API_BASE}/api/accounts`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    accounts.value = data
  } catch (error: any) {
    ElMessage.error('加载账号列表失败')
  } finally {
    loading.value = false
  }
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    online: '在线',
    offline: '离线',
    error: '异常'
  }
  return statusMap[status] || status
}

const formatTime = (timestamp: number | string) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // Less than 1 minute
  if (diff < 60000) return '刚刚'
  // Less than 1 hour
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  // Less than 1 day
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  // Less than 7 days
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  return date.toLocaleDateString()
}

const tableRowClassName = ({ row }: { row: any }) => {
  if (row.status === 'error') return 'error-row'
  return ''
}

// Load accounts on mount
onMounted(() => {
  refreshAccounts()

  // Auto-refresh every 30 seconds
  const interval = setInterval(refreshAccounts, 30000)

  // Cleanup on unmount
  return () => clearInterval(interval)
})
</script>

<style scoped lang="scss">
.accounts-page {
  padding: 24px;

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

  .stats-row {
    margin-bottom: 24px;

    .stat-card {
      :deep(.el-card__body) {
        padding: 20px;
      }

      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;

        .stat-info {
          flex: 1;

          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--safeline-text-primary);
            line-height: 1.2;
          }

          .stat-label {
            margin-top: 4px;
            font-size: 13px;
            color: var(--safeline-text-secondary);
          }
        }
      }
    }
  }

  .table-card {
    :deep(.el-card__header) {
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color);
    }

    :deep(.el-card__body) {
      padding: 0;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
      color: var(--safeline-text-primary);
    }

    :deep(.el-table) {
      .account-name {
        display: flex;
        align-items: center;
        gap: 12px;

        .name-info {
          .name {
            font-weight: 500;
            color: var(--safeline-text-primary);
            margin-bottom: 2px;
          }

          .username {
            font-size: 12px;
            color: var(--safeline-text-secondary);
          }
        }
      }

      .text-muted {
        color: var(--safeline-text-secondary);
      }

      .error-row {
        background-color: rgba(245, 108, 108, 0.05);
      }
    }

    .pagination {
      padding: 16px 20px;
      display: flex;
      justify-content: flex-end;
      border-top: 1px solid var(--el-border-color);
    }
  }

  // Dialog styles
  :deep(.el-dialog) {
    .el-form-item__label {
      font-weight: 500;
    }

    .el-alert {
      ol {
        font-size: 13px;
        line-height: 1.6;
        color: var(--el-text-color-regular);
      }
    }
  }
}

// Responsive
@media (max-width: 768px) {
  .accounts-page {
    padding: 16px;

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

    .stats-row {
      :deep(.el-col) {
        margin-bottom: 12px;
      }
    }

    .card-header {
      flex-direction: column;
      gap: 12px;

      .el-input {
        width: 100% !important;
      }
    }
  }
}
</style>
