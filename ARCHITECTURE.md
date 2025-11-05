# Telegram 客服系统架构文档

## 📐 项目结构

```
Telegram-interactive-bot/
├── backend/                          # 后端服务
│   ├── main.py                       # FastAPI 主程序（API 路由）
│   ├── account_manager.py            # 账号管理器（Bot + Userbot）
│   ├── message_handler.py            # 消息处理器（双向转发、关键词）
│   ├── account_login.py              # 交互式登录模块
│   ├── requirements.txt              # Python 依赖
│   └── Dockerfile                    # 后端 Docker 镜像
│
├── frontend/                         # 前端服务（待开发）
│   ├── src/
│   │   ├── views/                    # 页面组件
│   │   │   ├── Login.vue            # 登录页
│   │   │   ├── Dashboard.vue        # 仪表盘
│   │   │   ├── Conversations.vue    # 会话列表
│   │   │   ├── Chat.vue             # 聊天界面
│   │   │   ├── Accounts.vue         # 账号管理
│   │   │   ├── Keywords.vue         # 关键词管理
│   │   │   └── Settings.vue         # 系统设置
│   │   ├── components/              # 组件
│   │   ├── api/                     # API 调用封装
│   │   └── store/                   # Vuex 状态管理
│   ├── Dockerfile
│   └── package.json
│
├── nginx/                            # Nginx 配置
│   ├── nginx.conf                    # 反向代理配置
│   └── ssl/                          # SSL 证书目录（可选）
│
├── interactive-bot/                  # 原项目代码（保留）
│   ├── __main__.py
│   ├── __init__.py
│   └── utils.py
│
├── db/                               # 原项目数据库模型
│   ├── model.py
│   └── database.py
│
├── .env.example                      # 环境变量示例
├── docker-compose.yml                # Docker Compose 配置
├── DEPLOYMENT.md                     # 部署指南
├── ARCHITECTURE.md                   # 本文档
└── README.md                         # 项目说明
```

---

## 🏗️ 系统架构图

### 整体架构

```
┌────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  Telegram 用户 ←→ Bot/Userbot ←→ 客服后台                     │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                      前端层 (Vue 3)                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ 登录页面  │ 会话列表  │ 聊天界面  │ 账号管理  │ 关键词   │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│                    HTTP/WebSocket                           │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                   后端层 (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API 路由层                                            │  │
│  │  - 认证 (/api/auth/*)                                 │  │
│  │  - 账号 (/api/accounts/*)                             │  │
│  │  - 会话 (/api/conversations/*)                        │  │
│  │  - 关键词 (/api/keywords/*)                           │  │
│  │  - WebSocket (/ws/{agent_id})                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  业务逻辑层                                            │  │
│  │  - AccountManager: 账号池管理                         │  │
│  │  - MessageProcessor: 消息处理和转发                   │  │
│  │  - AccountLoginManager: 交互式登录                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                  Telegram 账号层                             │
│  ┌──────────────────┬──────────────────┐                    │
│  │  Bot 池 (1-100)  │ Userbot 池 (1-100)│                   │
│  │  python-telegram │    Pyrogram      │                    │
│  │      -bot        │                  │                    │
│  └──────────────────┴──────────────────┘                    │
│           负载均衡（轮询/随机）                               │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                    数据层                                    │
│  ┌──────────────────┬──────────────────┐                    │
│  │  MongoDB         │     Redis        │                    │
│  │  - accounts      │  - 消息队列       │                    │
│  │  - admins        │  - 会话缓存       │                    │
│  │  - conversations │  - 实时状态       │                    │
│  │  - messages      │                  │                    │
│  │  - keywords      │                  │                    │
│  └──────────────────┴──────────────────┘                    │
└────────────────────────────────────────────────────────────┘
```

---

## 🔄 核心流程

### 1. 用户消息处理流程

```
用户发送消息
    ↓
Telegram API
    ↓
Bot/Userbot 接收 (account_manager)
    ↓
MessageProcessor.handle_user_message()
    ↓
├─ 保存消息到 MongoDB
├─ 创建/更新会话
├─ 检查关键词触发
│  └─ 触发自动回复/私信
├─ 更新统计数据
└─ WebSocket 推送到前端
    ↓
客服看到消息
```

### 2. 客服回复流程

```
客服在后台发送消息
    ↓
前端 WebSocket/HTTP
    ↓
MessageProcessor.handle_agent_message()
    ↓
├─ 检查会话状态
├─ 选择可用账号（Bot 优先）
└─ 发送消息到 Telegram
    ↓
Telegram API
    ↓
用户收到消息
    ↓
保存消息记录到 MongoDB
```

### 3. TG 号登录流程

```
客服输入手机号
    ↓
POST /api/accounts/userbot/start
    ↓
AccountLoginManager.start_login()
    ↓
Pyrogram 发送验证码
    ↓
Telegram 发送验证码到手机
    ↓
客服输入验证码
    ↓
POST /api/accounts/userbot/code
    ↓
AccountLoginManager.submit_code()
    ↓
验证成功？
├─ 是 → 导出 session_string → 保存到数据库 → 完成
└─ 否 → 需要二次密码？
    ├─ 是 → 客服输入密码 → POST /api/accounts/userbot/password
    └─ 否 → 需要邮箱验证？
        └─ 是 → 输入邮箱验证码
```

### 4. 关键词监听流程

```
用户发送消息（包含关键词）
    ↓
MessageProcessor._check_keywords()
    ↓
遍历所有启用的关键词规则
    ↓
匹配类型判断
├─ exact: 精确匹配
├─ contains: 包含匹配
└─ regex: 正则匹配
    ↓
触发动作
├─ auto_reply: 自动回复
├─ auto_dm: 自动私信
└─ notify_agents: 通知客服
    ↓
更新触发统计
```

### 5. 会话锁定流程

```
客服 A 点击会话
    ↓
POST /api/conversations/{id}/lock
    ↓
MessageProcessor.lock_conversation()
    ↓
检查是否已被锁定
├─ 未锁定 → 锁定给客服 A（5 分钟）
└─ 已锁定 → 返回错误（显示锁定者）
    ↓
客服 A 可以回复
    ↓
其他客服看到「客服 A 正在回复中」
    ↓
5 分钟后自动解锁（或手动解锁）
```

---

## 📊 数据库设计

### MongoDB Collections

#### 1. accounts（账号表）

```javascript
{
  _id: ObjectId,
  type: "bot" | "userbot",         // 账号类型
  status: 1 | 0 | -1,              // 1=正常 0=禁用 -1=异常

  // Bot 类型字段
  bot_token: String,
  bot_username: String,

  // Userbot 类型字段
  tg_id: Number,
  phone: String,
  username: String,
  first_name: String,
  session_string: String,          // Pyrogram session
  session_type: "pyrogram",

  // API 配置
  api_id: Number,
  api_hash: String,

  // 代理配置
  proxy: {
    enabled: Boolean,
    type: "socks5" | "http",
    host: String,
    port: Number,
    username: String,
    password: String
  },

  // 健康状态
  is_online: Boolean,
  last_check_at: Date,
  error_count: Number,
  last_error: String,

  created_at: Date,
  updated_at: Date
}
```

#### 2. admins（管理员表）

```javascript
{
  _id: ObjectId,
  username: String,
  password_hash: String,           // bcrypt 加密
  nickname: String,
  role: "admin" | "agent",         // 角色

  status: "online" | "offline" | "busy",
  permissions: Array,              // 权限列表

  // 统计
  total_conversations: Number,
  avg_response_time: Number,
  satisfaction_rate: Number,

  last_active_at: Date,
  created_at: Date
}
```

#### 3. conversations（会话表）

```javascript
{
  _id: ObjectId,
  user_id: Number,                 // TG user id
  username: String,
  first_name: String,
  last_name: String,

  status: "waiting" | "active" | "closed",

  // 分配的客服
  assigned_agent_id: ObjectId,
  assigned_agent_name: String,
  assigned_at: Date,

  // 会话锁定
  locked_by: ObjectId,
  locked_at: Date,
  lock_expires_at: Date,

  // 统计
  message_count: Number,
  unread_count: Number,
  last_message_at: Date,
  last_message_preview: String,

  tags: Array,
  notes: String,
  source: String,

  created_at: Date,
  updated_at: Date
}
```

#### 4. messages（消息表）

```javascript
{
  _id: ObjectId,
  conversation_id: ObjectId,
  direction: "incoming" | "outgoing",

  from_user_id: Number,
  from_username: String,
  from_type: "user" | "agent" | "bot",

  to_user_id: Number,
  to_type: String,

  content_type: "text" | "photo" | "video" | "document",
  text: String,
  caption: String,

  media: {
    file_id: String,
    file_unique_id: String,
    file_size: Number,
    ...
  },

  tg_message_id: Number,
  chat_id: Number,

  is_read: Boolean,
  is_deleted: Boolean,

  created_at: Date
}
```

#### 5. keywords（关键词表）

```javascript
{
  _id: ObjectId,
  keyword: String,
  match_type: "exact" | "contains" | "regex",
  enabled: Boolean,

  action: {
    type: "auto_reply",
    reply_text: String,
    reply_media: Array,
    auto_dm: Boolean,
    dm_message: String,
    notify_agents: Boolean
  },

  listen_scope: "all" | "groups" | "private",
  group_ids: Array,

  trigger_count: Number,
  last_triggered_at: Date,

  created_at: Date,
  updated_at: Date
}
```

### Redis 数据结构

```
# 会话锁定
conversation_lock:{conversation_id} = {agent_id}
TTL: 300 秒

# 消息队列
message_queue:incoming = [...]  # 用户发来的消息
message_queue:outgoing = [...]  # 待发送的消息

# 在线客服
online_agents = Set({agent_id1, agent_id2, ...})

# 未读消息计数
unread_count:{agent_id} = Number

# 关键词缓存
keywords_cache = JSON
TTL: 3600 秒
```

---

## 🔌 API 接口文档

### 认证相关

#### POST /api/auth/register
创建管理员账号

**请求**:
```json
{
  "username": "admin",
  "password": "admin123",
  "nickname": "管理员",
  "role": "admin"
}
```

**响应**:
```json
{
  "success": true,
  "admin_id": "xxx",
  "username": "admin"
}
```

#### POST /api/auth/login
登录

**请求**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### GET /api/auth/me
获取当前用户信息

**Headers**: `Authorization: Bearer {token}`

**响应**:
```json
{
  "id": "xxx",
  "username": "admin",
  "nickname": "管理员",
  "role": "admin",
  "status": "online",
  "permissions": ["chat", "keyword", "account"]
}
```

### 账号管理

#### GET /api/accounts
获取所有账号列表

**响应**:
```json
[
  {
    "id": "xxx",
    "type": "bot",
    "status": 1,
    "username": "mycustomer_bot",
    "is_online": true,
    "last_check_at": "2025-11-05T10:00:00",
    "created_at": "2025-11-01T10:00:00"
  },
  {
    "id": "yyy",
    "type": "userbot",
    "status": 1,
    "username": "myaccount",
    "tg_id": 123456789,
    "phone": "+8613800138000",
    "is_online": true
  }
]
```

#### POST /api/accounts/bot
添加 Bot Token 账号

**请求**:
```json
{
  "bot_token": "7126xxxxx:AAxxxxxxxxx"
}
```

#### POST /api/accounts/userbot/start
开始 Userbot 登录（步骤1：发送验证码）

**请求**:
```json
{
  "phone": "+8613800138000",
  "api_id": 6,
  "api_hash": "eb06d4abfb49dc3eeb1aeb98ae0f581e",
  "proxy": null
}
```

**响应**:
```json
{
  "success": true,
  "session_id": "uuid",
  "status": "code_required",
  "message": "验证码已发送到 +8613800138000"
}
```

#### POST /api/accounts/userbot/code
提交验证码（步骤2）

**请求**:
```json
{
  "session_id": "uuid",
  "code": "12345"
}
```

**响应**:
```json
// 成功
{
  "success": true,
  "status": "success",
  "session_string": "xxx",
  "user_info": {...},
  "account_id": "xxx"
}

// 需要二次密码
{
  "success": true,
  "status": "password_required",
  "message": "需要输入二次验证密码",
  "hint": "my_password_hint"
}
```

#### POST /api/accounts/userbot/password
提交二次密码（步骤3）

**请求**:
```json
{
  "session_id": "uuid",
  "password": "my_2fa_password"
}
```

#### DELETE /api/accounts/{account_id}
删除账号

### 会话管理

#### GET /api/conversations
获取会话列表

**查询参数**:
- `status`: waiting | active | closed

**响应**:
```json
[
  {
    "id": "xxx",
    "user_id": 123456789,
    "username": "@user123",
    "first_name": "张三",
    "status": "waiting",
    "message_count": 5,
    "unread_count": 2,
    "last_message_at": "2025-11-05T10:00:00",
    "last_message_preview": "请问价格是多少？",
    "locked_by": null
  }
]
```

#### GET /api/conversations/{conversation_id}/messages
获取会话消息

#### POST /api/conversations/{conversation_id}/send
发送消息

**请求**:
```json
{
  "content_type": "text",
  "text": "您好，价格是 99 元"
}
```

#### POST /api/conversations/{conversation_id}/lock
锁定会话

#### POST /api/conversations/{conversation_id}/unlock
解锁会话

### 关键词管理

#### GET /api/keywords
获取关键词列表

#### POST /api/keywords
创建关键词

**请求**:
```json
{
  "keyword": "价格",
  "match_type": "contains",
  "enabled": true,
  "action": {
    "type": "auto_reply",
    "reply_text": "价格信息...",
    "auto_dm": true,
    "dm_message": "您好，我看到您询问了价格",
    "notify_agents": true
  }
}
```

#### PUT /api/keywords/{keyword_id}
更新关键词

#### DELETE /api/keywords/{keyword_id}
删除关键词

### WebSocket

#### WS /ws/{agent_id}
实时消息推送

**连接**: `ws://localhost:8000/ws/{agent_id}`

**接收消息格式**:
```json
{
  "type": "new_message",
  "conversation_id": "xxx",
  "message": {...}
}

{
  "type": "keyword_trigger",
  "keyword": "价格",
  "user_id": 123456789
}

{
  "type": "agent_status",
  "agent_id": "yyy",
  "status": "online"
}
```

---

## 🔒 安全性

### 认证机制

- JWT Token 认证
- Token 有效期：24 小时
- 密码使用 bcrypt 加密存储

### 会话管理

- 会话锁定机制（防止并发冲突）
- 自动解锁（超时 5 分钟）

### 数据安全

- 敏感数据（Session String）加密存储（待实现）
- API 使用 HTTPS（生产环境）
- WebSocket 连接验证

---

## 📈 性能优化

### 账号池负载均衡

- 轮询方式分配账号
- 自动剔除失效账号
- 健康检查机制

### 缓存策略

- Redis 缓存关键词规则
- Redis 缓存会话状态
- 消息队列异步处理

### 数据库优化

- MongoDB 索引优化
  - `accounts.type`
  - `accounts.status`
  - `conversations.user_id`
  - `conversations.status`
  - `messages.conversation_id`
  - `messages.created_at`

---

## 🚀 扩展性

### 横向扩展

- 支持多个后端实例（使用 Redis 共享状态）
- 账号池可分布在多个实例

### 功能扩展

- 插件系统（待开发）
- Webhook 支持
- 第三方集成（WhatsApp、Discord 等）

---

## 📝 待开发功能

### 前端

- [ ] Vue 3 前端界面
- [ ] 实时聊天组件
- [ ] 账号管理界面
- [ ] 关键词配置界面
- [ ] 数据统计看板

### 后端

- [ ] 文件上传和管理
- [ ] 图片/视频压缩
- [ ] 敏感词过滤
- [ ] AI 辅助回复
- [ ] 邮箱验证支持（Telethon）

### 功能

- [ ] 会话转接
- [ ] 用户标签系统
- [ ] 满意度评分
- [ ] 工作报表导出
- [ ] 多语言翻译

---

## 🎯 下一步计划

1. **前端开发**（Vue 3 + Element Plus）
2. **WebSocket 实时推送完善**
3. **文件上传功能**
4. **AI 辅助回复**（集成 OpenAI API）
5. **数据统计看板**
6. **移动端适配**

---

## 📞 技术栈总结

| 类别 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 前端框架 | Vue 3 + Element Plus（待开发） |
| 数据库 | MongoDB + Redis |
| Telegram | Pyrogram + python-telegram-bot |
| 认证 | JWT |
| 部署 | Docker + Docker Compose |
| 反向代理 | Nginx |

---

**文档版本**: 1.0.0
**最后更新**: 2025-11-05
