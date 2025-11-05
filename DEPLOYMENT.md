# Telegram 客服系统部署指南

## 📋 目录

1. [系统架构](#系统架构)
2. [功能特性](#功能特性)
3. [环境要求](#环境要求)
4. [快速开始](#快速开始)
5. [详细配置](#详细配置)
6. [添加账号流程](#添加账号流程)
7. [常见问题](#常见问题)

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│  前端 (Vue 3)                                            │
│  - 管理员登录                                             │
│  - 账号管理（Bot/Userbot）                                │
│  - 实时聊天界面                                           │
│  - 关键词配置                                             │
└─────────────────────────────────────────────────────────┘
                         ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│  后端 (FastAPI)                                          │
│  - RESTful API                                           │
│  - WebSocket 实时通信                                     │
│  - 账号管理（混合 Bot + Userbot）                         │
│  - 消息处理和转发                                         │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│  Telegram 账号层                                         │
│  - Bot Token 池（1-100个）                               │
│  - Userbot 池（Pyrogram，1-100个）                       │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│  数据持久化                                               │
│  - MongoDB（会话、消息、配置）                             │
│  - Redis（缓存、消息队列）                                 │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ 功能特性

### 核心功能

- ✅ **混合账号支持**：同时支持 Bot Token 和 TG 协议号（Userbot）
- ✅ **多账号管理**：最多支持 100 个 Bot + 100 个 Userbot
- ✅ **交互式登录**：手机号 + 验证码 + 二次密码完整验证流程
- ✅ **实时聊天**：WebSocket 实时推送，客服与用户双向通信
- ✅ **关键词监听**：自动监听关键词并触发自动回复/私信
- ✅ **多客服管理**：会话锁定机制，防止多客服同时回复
- ✅ **快捷回复**：预设常用回复模板，提高效率
- ✅ **历史记录**：完整的消息历史和搜索功能
- ✅ **统计报表**：客服工作量、响应时间等数据分析

### 高级功能

- 🔄 **账号健康检查**：自动检测账号在线状态
- 🔒 **会话锁定**：客服接入会话时自动锁定（默认 5 分钟）
- 📊 **数据统计**：每日/每周/每月的客服工作报表
- 🏷️ **标签系统**：为会话添加标签便于分类管理
- 🔔 **实时通知**：新消息桌面通知、关键词触发提醒

---

## 🔧 环境要求

### 服务器配置

- **操作系统**: Linux (Ubuntu 20.04+ 推荐)
- **CPU**: 2 核心及以上
- **内存**: 4GB 及以上
- **硬盘**: 20GB 及以上
- **网络**: 稳定的网络连接，能够访问 Telegram API

### 软件依赖

- Docker >= 20.10
- Docker Compose >= 2.0
- (可选) Nginx - 如果需要自定义反向代理

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/expert985/Telegram-interactive-bot.git
cd Telegram-interactive-bot
```

### 2. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件（重要！）
nano .env
```

**必须修改的配置项**：

```env
# MongoDB 连接（如果使用外部 MongoDB）
MONGO_URI=mongodb://localhost:27017

# Redis 连接
REDIS_URL=redis://localhost:6379

# JWT 密钥（生产环境必须修改！）
JWT_SECRET=your-super-secret-key-here-change-me-!!!

# API 服务配置
API_HOST=0.0.0.0
API_PORT=8000

# 前端访问地址
FRONTEND_URL=http://localhost:3000
```

### 3. 启动服务

```bash
# 使用 Docker Compose 一键启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

启动成功后，服务将运行在：

- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 4. 创建管理员账号

第一次使用需要创建管理员账号：

```bash
# 方式 1: 使用 API 直接创建（推荐）
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "nickname": "管理员",
    "role": "admin"
  }'
```

或者通过前端界面首次访问时会提示创建管理员。

### 5. 登录后台

访问 http://localhost:3000，使用创建的账号登录。

---

## 📝 详细配置

### MongoDB 配置

#### 使用 Docker 内置 MongoDB（默认）

无需额外配置，Docker Compose 会自动启动 MongoDB 容器。

#### 使用外部 MongoDB

如果你有自己的 MongoDB 服务器：

```env
# .env 文件
MONGO_URI=mongodb://username:password@your-mongo-server:27017/telegram_customer
```

#### 使用 MongoDB Atlas（云数据库）

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/telegram_customer?retryWrites=true&w=majority
```

### Redis 配置

#### 使用 Docker 内置 Redis（默认）

无需额外配置。

#### 使用外部 Redis

```env
REDIS_URL=redis://your-redis-server:6379
# 如果有密码
REDIS_URL=redis://:password@your-redis-server:6379
```

### Nginx 反向代理（域名访问）

如果你希望通过域名访问（例如 `https://customer.yourdomain.com`）：

#### 1. 修改 Nginx 配置

编辑 `nginx/nginx.conf`，找到：

```nginx
server {
    listen 80;
    server_name _;  # 替换为你的域名
```

替换为：

```nginx
server {
    listen 80;
    server_name customer.yourdomain.com;  # 你的域名
```

#### 2. 配置 SSL 证书（HTTPS）

将 SSL 证书文件放到 `nginx/ssl/` 目录：

```
nginx/ssl/
├── cert.pem      # SSL 证书
└── key.pem       # 私钥
```

然后取消 `nginx.conf` 中 HTTPS 配置的注释。

#### 3. 重启 Nginx

```bash
docker-compose restart nginx
```

---

## 🔐 添加账号流程

### 添加 Bot Token 账号

#### 1. 创建 Telegram Bot

1. 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建机器人
3. 按提示设置机器人名称和用户名
4. 获得 Bot Token（格式：`7126xxxxx:AAxxxxxxxxx`）

#### 2. 在后台添加 Bot

1. 登录后台管理界面
2. 进入「账号管理」页面
3. 点击「添加 Bot 账号」
4. 粘贴 Bot Token
5. 点击「确认添加」

系统会自动验证 Token 并连接。

### 添加 TG 协议号（Userbot）

#### 方式 1: 在线登录（推荐）

1. 登录后台管理界面
2. 进入「账号管理」页面
3. 点击「添加 TG 号」
4. 按照以下步骤操作：

**步骤 1：输入手机号**
```
格式：国际格式
示例：+8613800138000
```

点击「发送验证码」后，Telegram 会向该手机号发送验证码。

**步骤 2：输入验证码**
```
输入收到的 5 位数字验证码
示例：12345
```

**步骤 3：输入二次密码（如果有）**
```
如果你的 Telegram 账号设置了二次验证密码，需要输入。
提示：系统会显示密码提示（如果有设置）
```

**步骤 4：邮箱验证（极少情况）**
```
某些情况下可能需要邮箱验证码。
输入收到的邮箱验证码即可。
```

登录成功后，系统会自动保存 Session，无需重复登录。

#### 方式 2: 导入 Session String

如果你已有 Pyrogram 或 Telethon 的 Session String：

1. 点击「导入 Session」
2. 粘贴 Session String
3. 选择类型（Pyrogram / Telethon）
4. 点击「确认导入」

---

## 🎯 使用教程

### 客服接入流程

1. **查看待处理会话**
   - 登录后台
   - 在「会话列表」中查看等待中的用户

2. **接入会话**
   - 点击会话进入聊天界面
   - 系统会自动锁定该会话（防止其他客服同时回复）

3. **回复用户**
   - 输入文字消息
   - 可上传图片、视频、文件等
   - 支持快捷回复（输入 `/` 触发）

4. **结束会话**
   - 点击「结束会话」按钮
   - 会话将标记为已关闭

### 关键词监听配置

1. **创建关键词规则**
   - 进入「关键词管理」
   - 点击「添加关键词」

2. **配置匹配方式**
   - **精确匹配**：完全相同才触发
   - **包含匹配**：消息中包含关键词即触发
   - **正则匹配**：使用正则表达式匹配

3. **设置触发动作**
   ```json
   {
     "type": "auto_reply",  // 自动回复
     "reply_text": "您好！我们的客服会尽快回复您。",
     "auto_dm": true,  // 是否自动私信
     "dm_message": "您好，我看到您发送了关键词【{keyword}】",
     "notify_agents": true  // 是否通知客服
   }
   ```

### 快捷回复使用

1. **创建快捷回复**
   - 进入「快捷回复」
   - 点击「添加模板」
   - 设置快捷码（例如 `/price`）
   - 编写回复内容

2. **使用快捷回复**
   - 在聊天界面输入快捷码
   - 例如输入 `/price` 自动展开为完整回复

---

## 🐛 常见问题

### 1. Bot Token 无效

**问题**：添加 Bot 时提示 "Invalid token"

**解决方案**：
- 检查 Token 格式是否正确（格式：`数字:字母数字`）
- 确认 Token 是从 @BotFather 获取的最新 Token
- Token 中不要有多余的空格

### 2. TG 号登录失败

**问题**：输入验证码后提示失败

**解决方案**：
- 确认手机号格式正确（必须包含 `+` 和国家代码）
- 验证码有时效性（约 5 分钟），过期需重新发送
- 如果多次失败，Telegram 可能会限制，请等待 24 小时后重试

### 3. 账号频繁掉线

**问题**：Userbot 账号显示离线

**解决方案**：
- 检查网络连接是否稳定
- 查看日志是否有错误信息：`docker-compose logs backend`
- 可能是账号被 Telegram 限制，请检查是否违反使用条款
- 尝试配置代理（如果在受限地区）

### 4. 消息发送失败

**问题**：发送消息时提示失败

**解决方案**：
- 检查账号是否在线
- 确认用户没有屏蔽机器人
- Bot 无法主动给用户发消息（除非用户先发过消息）
- 查看后端日志获取详细错误信息

### 5. MongoDB 连接失败

**问题**：启动时提示无法连接 MongoDB

**解决方案**：
```bash
# 检查 MongoDB 容器状态
docker-compose ps

# 重启 MongoDB
docker-compose restart mongo

# 查看 MongoDB 日志
docker-compose logs mongo
```

### 6. 前端无法访问

**问题**：浏览器无法打开前端页面

**解决方案**：
- 检查端口是否被占用：`netstat -tuln | grep 3000`
- 确认防火墙是否开放 3000 端口
- 查看前端日志：`docker-compose logs frontend`

---

## 🔄 升级和维护

### 更新系统

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

### 备份数据

```bash
# 备份 MongoDB 数据
docker exec telegram_customer_mongo mongodump --out /backup

# 复制备份到主机
docker cp telegram_customer_mongo:/backup ./mongodb_backup_$(date +%Y%m%d)

# 备份 Redis 数据
docker exec telegram_customer_redis redis-cli SAVE
docker cp telegram_customer_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### 恢复数据

```bash
# 恢复 MongoDB
docker exec -i telegram_customer_mongo mongorestore /backup

# 恢复 Redis
docker cp redis_backup.rdb telegram_customer_redis:/data/dump.rdb
docker-compose restart redis
```

---

## 📞 技术支持

如有问题，请提交 Issue：
https://github.com/expert985/Telegram-interactive-bot/issues

---

## 📄 许可证

本项目基于原项目 Apache License 2.0 开源协议。

---

## 🎉 完成！

现在你可以开始使用 Telegram 客服系统了！

**推荐操作顺序**：
1. ✅ 创建管理员账号
2. ✅ 添加至少 1 个 Bot Token 或 TG 号
3. ✅ 配置关键词规则（可选）
4. ✅ 创建快捷回复（可选）
5. ✅ 开始接待用户咨询

祝使用愉快！🚀
