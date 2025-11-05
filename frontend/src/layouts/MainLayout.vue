<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside width="240px" class="sidebar">
      <!-- Logo 区域 -->
      <div class="logo-container">
        <el-icon :size="32" color="#6366f1">
          <Shield />
        </el-icon>
        <div class="logo-text">
          <div class="title">Telegram 客服</div>
          <div class="subtitle">SafeLine 防护</div>
        </div>
      </div>

      <!-- 菜单 -->
      <el-menu
        :default-active="currentRoute"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </el-menu-item>

        <el-menu-item index="/protection">
          <el-icon><Shield /></el-icon>
          <span>防护控制台</span>
        </el-menu-item>

        <el-menu-item index="/workbench">
          <el-icon><ChatDotRound /></el-icon>
          <span>客服工作台</span>
          <el-badge
            v-if="unreadCount > 0"
            :value="unreadCount"
            class="badge"
          />
        </el-menu-item>

        <el-menu-item index="/threat">
          <el-icon><Warning /></el-icon>
          <span>威胁情报</span>
          <el-badge
            v-if="alertCount > 0"
            :value="alertCount"
            class="badge"
            type="danger"
          />
        </el-menu-item>

        <el-menu-item index="/monitor">
          <el-icon><Monitor /></el-icon>
          <span>实时监控</span>
          <span v-if="wsConnected" class="status-dot online"></span>
        </el-menu-item>

        <el-menu-item index="/accounts">
          <el-icon><User /></el-icon>
          <span>账号管理</span>
        </el-menu-item>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>

      <!-- 底部信息 -->
      <div class="sidebar-footer">
        <div class="version">v0.6.0-beta</div>
        <div class="status">
          <el-icon :size="10" :color="wsConnected ? '#10b981' : '#ef4444'">
            <CircleFilled />
          </el-icon>
          <span>{{ wsConnected ? '已连接' : '未连接' }}</span>
        </div>
      </div>
    </el-aside>

    <!-- 主内容区域 -->
    <el-container class="main-container">
      <!-- 顶部导航栏 -->
      <el-header height="60px" class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- WebSocket 状态指示器 -->
          <div class="ws-status" :class="{ connected: wsConnected }">
            <el-icon class="animate-pulse">
              <Connection />
            </el-icon>
            <span>{{ wsConnected ? '实时在线' : '离线' }}</span>
          </div>

          <!-- 通知 -->
          <el-badge :value="alertCount" :hidden="alertCount === 0">
            <el-button circle>
              <el-icon><Bell /></el-icon>
            </el-button>
          </el-badge>

          <!-- 用户信息 -->
          <el-dropdown>
            <div class="user-info">
              <el-avatar :size="36" src="/avatar.png">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">管理员</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人设置</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useWebSocketStore } from '@/stores/websocket'
import {
  DataAnalysis,
  Shield,
  ChatDotRound,
  Warning,
  Monitor,
  User,
  Setting,
  Connection,
  Bell,
  CircleFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const wsStore = useWebSocketStore()

// 当前路由
const currentRoute = computed(() => route.path)

// 当前页面标题
const currentPageTitle = computed(() => {
  return (route.meta.title as string) || '未知页面'
})

// WebSocket 连接状态
const wsConnected = computed(() => wsStore.connected)

// 未读消息数
const unreadCount = computed(() => wsStore.recentMessages.length)

// 安全告警数
const alertCount = computed(() => wsStore.securityAlerts.length)

// 退出登录
function handleLogout() {
  // TODO: 实现退出登录逻辑
  localStorage.removeItem('token')
  window.location.href = '/login'
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
  width: 100vw;
}

.sidebar {
  display: flex;
  flex-direction: column;
  background-color: var(--safeline-bg-secondary);
  border-right: 1px solid var(--safeline-border-color);

  .logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px;
    border-bottom: 1px solid var(--safeline-border-color);

    .logo-text {
      .title {
        font-size: 16px;
        font-weight: 700;
        color: var(--safeline-text-primary);
        line-height: 1.2;
      }

      .subtitle {
        font-size: 12px;
        color: var(--safeline-text-tertiary);
      }
    }
  }

  .sidebar-menu {
    flex: 1;
    border-right: none;
    padding: 10px 0;

    .badge {
      margin-left: auto;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-left: auto;

      &.online {
        background-color: var(--safeline-success);
        box-shadow: 0 0 8px var(--safeline-success);
      }
    }
  }

  .sidebar-footer {
    padding: 16px;
    border-top: 1px solid var(--safeline-border-color);
    text-align: center;

    .version {
      font-size: 12px;
      color: var(--safeline-text-tertiary);
      margin-bottom: 8px;
    }

    .status {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-size: 12px;
      color: var(--safeline-text-secondary);
    }
  }
}

.main-container {
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background-color: var(--safeline-bg-secondary);
  border-bottom: 1px solid var(--safeline-border-color);

  .header-left {
    flex: 1;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;

    .ws-status {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: var(--safeline-radius-md);
      background-color: var(--safeline-bg-tertiary);
      color: var(--safeline-text-tertiary);
      font-size: 13px;

      &.connected {
        color: var(--safeline-success);
        background-color: rgba(16, 185, 129, 0.1);
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;

      .username {
        color: var(--safeline-text-primary);
        font-size: 14px;
      }

      &:hover {
        opacity: 0.8;
      }
    }
  }
}

.main-content {
  padding: 24px;
  overflow-y: auto;
}
</style>
