# Telegram 智能客服系统 - 前端（SafeLine 风格）

基于 Vue 3 + TypeScript + Vite 的 Telegram 客服系统前端界面，采用 SafeLine WAF 的暗色主题设计风格。

## ✨ 技术栈

- **框架**: Vue 3.4+ (Composition API)
- **语言**: TypeScript 5.4+
- **构建工具**: Vite 5.1+
- **UI 框架**: Element Plus 2.6+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.3+
- **图表**: ECharts 5.5+
- **样式**: SCSS

## 🎨 设计风格

参考 [SafeLine WAF](https://github.com/chaitin/SafeLine) 的 UI 设计：
- 🌙 **暗色主题**: 深色背景 + 蓝紫色主色调
- 📊 **数据可视化**: ECharts 图表展示
- 🔔 **实时通知**: WebSocket 实时消息推送
- 🛡️ **安全中心**: 威胁情报、防护控制台

## 📁 项目结构

```
frontend/
├── src/
│   ├── assets/          # 静态资源
│   ├── components/      # 公共组件
│   ├── layouts/         # 布局组件
│   │   └── MainLayout.vue  # 主布局（侧边栏+顶栏）
│   ├── pages/           # 页面组件
│   │   ├── Dashboard.vue          # 数据概览
│   │   ├── Protection.vue         # 防护控制台
│   │   ├── Workbench.vue          # 客服工作台（实时消息）
│   │   ├── ThreatIntelligence.vue # 威胁情报
│   │   ├── Monitor.vue            # 实时监控
│   │   ├── Accounts.vue           # 账号管理
│   │   └── Settings.vue           # 系统设置
│   ├── router/          # 路由配置
│   ├── stores/          # Pinia 状态管理
│   │   └── websocket.ts  # WebSocket 状态
│   ├── styles/          # 全局样式
│   │   └── index.scss    # SafeLine 暗色主题
│   ├── types/           # TypeScript 类型定义
│   ├── utils/           # 工具函数
│   │   └── websocket.ts  # WebSocket 客户端封装
│   ├── App.vue          # 根组件
│   └── main.ts          # 入口文件
├── index.html           # HTML 模板
├── vite.config.ts       # Vite 配置
├── tsconfig.json        # TypeScript 配置
└── package.json         # 依赖配置
```

## 🚀 快速开始

### 安装依赖

```bash
npm install
# 或
pnpm install
# 或
yarn install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 🔌 WebSocket 实时通信

系统内置 WebSocket 客户端，支持以下实时事件：

### 消息事件
- `NEW_MESSAGE`: 新消息通知
- `MESSAGE_SENT`: 消息发送确认

### 会话事件
- `CONVERSATION_ASSIGNED`: 会话分配
- `CONVERSATION_CLOSED`: 会话关闭
- `SESSION_LOCKED`: 会话锁定（其他客服正在回复）
- `SESSION_UNLOCKED`: 会话解锁

### 安全事件
- `SECURITY_ALERT`: 安全告警
- `THREAT_DETECTED`: 威胁检测
- `USER_BANNED`: 用户封禁

### 统计事件
- `STATS_UPDATE`: 统计数据更新

### 使用示例

```typescript
import { useWebSocketStore } from '@/stores/websocket'

const wsStore = useWebSocketStore()

// 连接
wsStore.connect()

// 发送消息
wsStore.send(WebSocketEvent.MESSAGE_SENT, {
  conversation_id: '123',
  content: 'Hello!'
})

// 监听状态
watch(() => wsStore.connected, (connected) => {
  console.log('WebSocket 连接状态:', connected)
})
```

## 🎨 主题定制

所有主题变量定义在 `src/styles/index.scss`：

```scss
:root {
  /* 主色调 */
  --safeline-primary: #6366f1;

  /* 背景色 */
  --safeline-bg-primary: #0f1419;
  --safeline-bg-secondary: #1a1f2e;

  /* 文字色 */
  --safeline-text-primary: #ffffff;
  --safeline-text-secondary: #9ca3af;

  /* 威胁等级色 */
  --threat-low: #10b981;
  --threat-medium: #f59e0b;
  --threat-high: #f97316;
  --threat-critical: #dc2626;
}
```

## 📄 页面说明

### 1. 数据概览 (Dashboard)
- 实时统计卡片（会话数、消息数、拦截数、在线客服）
- 消息趋势图表（ECharts）
- 威胁分布饼图
- 最近会话和安全事件时间线

### 2. 防护控制台 (Protection)
🚧 开发中
- 防护规则配置
- 黑白名单管理
- 限流策略设置

### 3. 客服工作台 (Workbench) ⚡ 重点
🚧 开发中
- **实时消息列表**（WebSocket 推送）
- 会话管理
- 快捷回复
- 会话锁定状态显示
- 安全信息集成

### 4. 威胁情报 (ThreatIntelligence)
🚧 开发中
- 威胁数据库
- 用户风险评分
- 行为分析报告

### 5. 实时监控 (Monitor)
🚧 开发中
- WebSocket 连接状态监控
- 实时消息流量
- 安全事件流

### 6. 账号管理 (Accounts)
🚧 开发中
- Bot Token 管理
- Userbot 账号管理
- 交互式登录

### 7. 系统设置 (Settings)
🚧 开发中
- 系统配置
- 通知设置
- 管理员权限

## 🔧 开发配置

### Vite 代理

开发环境下，API 和 WebSocket 请求会自动代理到后端：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    },
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true
    }
  }
}
```

### 自动导入

已配置 Element Plus 组件和 Vue API 自动导入：
- 无需手动 import Element Plus 组件
- 无需手动 import `ref`, `computed` 等 Vue API

## 📊 完成度

```
总体进度: ████████░░░░░░░░░░░░ 40%

模块进度:
├─ 项目搭建        ████████████████████ 100%
├─ 主题样式        ████████████████████ 100%
├─ 布局组件        ████████████████████ 100%
├─ WebSocket       ████████████████████ 100%
├─ 数据概览        ████████████████████ 100%
├─ 防护控制台      ░░░░░░░░░░░░░░░░░░░░   0%
├─ 客服工作台      ░░░░░░░░░░░░░░░░░░░░   0%
├─ 威胁情报        ░░░░░░░░░░░░░░░░░░░░   0%
├─ 实时监控        ░░░░░░░░░░░░░░░░░░░░   0%
└─ 账号管理        ░░░░░░░░░░░░░░░░░░░░   0%
```

## 🔗 相关链接

- [SafeLine WAF](https://github.com/chaitin/SafeLine) - UI 设计参考
- [Vue 3 文档](https://cn.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/zh-CN/)
- [Vite 文档](https://cn.vitejs.dev/)
- [ECharts 文档](https://echarts.apache.org/zh/index.html)

## 📝 待办事项

- [ ] 完成客服工作台（实时消息）
- [ ] 完成防护控制台页面
- [ ] 完成威胁情报中心
- [ ] 完成实时监控面板
- [ ] 实现登录/注册功能
- [ ] API 接口集成
- [ ] 响应式适配（移动端）

---

**版本**: v0.6.0-beta
**最后更新**: 2025-11-05
