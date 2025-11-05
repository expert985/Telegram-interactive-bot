# Telegram 智能客服系统（增强版）

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

**一个功能强大的 Telegram 客服系统，支持 Bot Token 和 TG 协议号混合管理**

[English](./README.en.md) | [部署指南](./DEPLOYMENT.md) | [架构文档](./ARCHITECTURE.md)

</div>

---

## 🎯 项目简介

这是基于原 [Telegram-interactive-bot](https://github.com/MiHaKun/Telegram-interactive-bot) 项目的**全面升级版本**，在保留原有优秀特性的基础上，增加了以下重磅功能：

### 🆕 新增核心功能

- ✅ **混合账号支持**：同时支持 Bot Token 和 TG 协议号（Userbot），最多各 100 个
- ✅ **交互式登录**：手机号 + 验证码 + 二次密码完整验证流程
- ✅ **Web 后台管理**：基于 Vue 3 的现代化管理界面
- ✅ **关键词智能监听**：自动检测关键词并触发回复/私信
- ✅ **多客服协作**：会话锁定机制，防止多客服同时回复
- ✅ **快捷回复模板**：预设常用回复，提高工作效率
- ✅ **实时消息推送**：WebSocket 实时通知，零延迟
- ✅ **数据统计分析**：客服工作量、响应时间等报表

### 💡 原项目优秀特性（保留）

- ✅ 子论坛隔离：每个用户独立对话空间
- ✅ 双向消息转发：用户 ↔ 客服完整通信
- ✅ 多客服支持：团队协作，分担压力
- ✅ 完整历史记录：保留所有沟通记录
- ✅ 媒体消息支持：图片、视频、文件等

---

## 📸 系统截图

> **注意**：前端界面正在开发中，以下为设计预览

| 登录页面 | 会话列表 |
|---------|---------|
| ![登录](https://via.placeholder.com/400x300?text=Login+Page) | ![会话](https://via.placeholder.com/400x300?text=Conversations) |

| 聊天界面 | 账号管理 |
|---------|---------|
| ![聊天](https://via.placeholder.com/400x300?text=Chat+Interface) | ![账号](https://via.placeholder.com/400x300?text=Account+Management) |

---

## 🏗️ 系统架构

```
用户层 (Telegram 用户)
      ↕
账号层 (Bot Token + TG 协议号池)
      ↕
后端层 (FastAPI + WebSocket)
      ↕
前端层 (Vue 3 + Element Plus)
      ↕
数据层 (MongoDB + Redis)
```

详细架构请查看 [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## ⚡ 快速开始

### 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 4GB RAM（推荐）
- 稳定的网络连接

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/expert985/Telegram-interactive-bot.git
cd Telegram-interactive-bot

# 2. 配置环境变量
cp .env.example .env
nano .env  # 修改必要的配置

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 访问系统

- **前端管理界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 创建管理员账号

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "nickname": "管理员",
    "role": "admin"
  }'
```

详细部署说明请查看 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📋 功能对比

| 功能 | 原版本 | 增强版 |
|-----|--------|--------|
| Bot Token 支持 | ✅ 单个 | ✅ 多个（1-100） |
| TG 协议号支持 | ❌ | ✅ 多个（1-100） |
| 交互式登录 | ❌ | ✅ 手机号+验证码+2FA |
| Web 后台 | ❌ | ✅ 现代化管理界面 |
| 关键词监听 | ❌ | ✅ 支持自动回复/私信 |
| 多客服管理 | ✅ 基础 | ✅ 会话锁定机制 |
| 快捷回复 | ❌ | ✅ 模板系统 |
| 实时推送 | ❌ | ✅ WebSocket |
| 数据统计 | ❌ | ✅ 完整报表 |
| 历史搜索 | ❌ | ✅ 全文搜索 |
| 用户标签 | ❌ | ✅ 分类管理 |

---

## 🔧 添加账号教程

### 添加 Bot Token 账号

1. 找 [@BotFather](https://t.me/BotFather) 创建机器人
2. 获取 Bot Token
3. 在后台「账号管理」中添加 Token
4. 系统自动验证并连接

### 添加 TG 协议号（Userbot）

#### 方式 1：在线登录（推荐）

1. 进入后台「账号管理」
2. 点击「添加 TG 号」
3. 输入手机号（国际格式：+8613800138000）
4. 输入收到的验证码
5. 如果有二次密码，输入密码
6. 登录成功！

#### 方式 2：导入 Session String

如果你已有 Pyrogram 或 Telethon 的 Session String：

1. 点击「导入 Session」
2. 粘贴 Session String
3. 选择类型（Pyrogram / Telethon）
4. 确认导入

---

## 💻 开发指南

### 项目结构

```
Telegram-interactive-bot/
├── backend/              # 后端（FastAPI）
│   ├── main.py          # API 主程序
│   ├── account_manager.py   # 账号管理器
│   ├── message_handler.py   # 消息处理器
│   └── account_login.py     # 交互式登录
│
├── frontend/            # 前端（Vue 3）- 开发中
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   └── api/        # API 封装
│   └── package.json
│
├── interactive-bot/     # 原项目代码（保留）
├── nginx/               # Nginx 配置
├── docker-compose.yml   # Docker Compose
└── DEPLOYMENT.md        # 部署指南
```

### 本地开发

#### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### 前端开发（待开发）

```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 安全说明

### 重要提示

1. **修改默认密钥**：生产环境必须修改 `.env` 中的 `JWT_SECRET`
2. **使用 HTTPS**：生产环境务必配置 SSL 证书
3. **限制访问**：建议使用防火墙限制后台访问 IP
4. **定期备份**：定期备份 MongoDB 数据库

### 数据安全

- JWT Token 认证
- 密码 bcrypt 加密
- Session String 加密存储（待实现）
- API 频率限制（待实现）

---

## 📊 性能特性

- **账号负载均衡**：自动轮询分配账号
- **健康检查**：定期检测账号状态
- **消息队列**：Redis 异步处理
- **缓存优化**：关键数据 Redis 缓存
- **数据库索引**：优化查询性能

---

## 🎁 功能亮点

### 1. 智能关键词监听

```yaml
关键词: "价格"
匹配方式: 包含
触发动作:
  - 自动回复: "我们的产品价格..."
  - 自动私信: "您好，我看到您询问了价格"
  - 通知客服: 是
```

### 2. 会话锁定机制

- 客服接入会话时自动锁定（默认 5 分钟）
- 其他客服看到「客服 A 正在回复中」提示
- 防止多客服同时回复造成混乱

### 3. 快捷回复模板

```
输入: /price
展开: 我们的产品价格如下：
      基础版：99元
      高级版：199元
      企业版：299元
      如有疑问请随时联系！
```

### 4. 实时统计报表

- 每日消息数量
- 平均响应时间
- 会话处理量
- 客服工作时长
- 关键词触发次数

---

## 🐛 常见问题

### 1. 无法连接 MongoDB

```bash
# 检查容器状态
docker-compose ps

# 重启 MongoDB
docker-compose restart mongo
```

### 2. TG 号登录失败

- 确认手机号格式正确（+国家代码）
- 验证码有 5 分钟时效
- 多次失败会被 Telegram 限制

### 3. 消息发送失败

- 检查账号是否在线
- Bot 无法主动给未交互用户发消息
- 查看后端日志获取详细错误

更多问题请查看 [DEPLOYMENT.md](./DEPLOYMENT.md#常见问题)

---

## 🛣️ 开发路线图

### v2.0（当前版本）

- [x] 后端 API 完整实现
- [x] 混合账号支持
- [x] 交互式登录
- [x] 关键词监听
- [x] Docker 部署

### v2.1（计划中）

- [ ] Vue 3 前端界面
- [ ] WebSocket 实时推送
- [ ] 文件上传功能
- [ ] 移动端适配

### v2.2（计划中）

- [ ] AI 辅助回复
- [ ] 多语言翻译
- [ ] 用户满意度评分
- [ ] 工作报表导出

### v3.0（未来）

- [ ] WhatsApp 集成
- [ ] Discord 集成
- [ ] 插件系统
- [ ] 多租户支持

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8（Python）
- 遵循 ESLint 规则（JavaScript）
- 提交前运行测试

---

## 💖 致谢

### 原作者

本项目基于 [@MrMiHa](https://t.me/MrMiHa) 的 [Telegram-interactive-bot](https://github.com/MiHaKun/Telegram-interactive-bot) 项目改进。

感谢米哈同学提供的优秀基础框架！

### 技术栈

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Pyrogram](https://docs.pyrogram.org/) - Telegram MTProto API 客户端
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram Bot API 封装
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI 组件库
- [MongoDB](https://www.mongodb.com/) - NoSQL 数据库
- [Redis](https://redis.io/) - 内存数据库

---

## 📄 开源协议

本项目基于 Apache License 2.0 开源协议。

使用本项目即表示您同意：
- 保留原作者版权信息
- 修改后的版本需注明修改内容
- 不得用于违法用途

详见 [LICENSE](./LICENSE) 文件。

---

## 📞 联系方式

- **原作者**: [@MrMiHa](https://t.me/MrMiHa)
- **讨论群组**: https://t.me/DeveloperTeamGroup
- **Issue 反馈**: https://github.com/expert985/Telegram-interactive-bot/issues

---

## ⚠️ 免责声明

本项目仅供学习和合法商业用途。使用本项目：

- 请遵守 Telegram 使用条款
- 请遵守当地法律法规
- 不得用于发送垃圾信息
- 不得用于侵犯用户隐私

因违规使用导致的任何后果由使用者自行承担。

---

## 🌟 Star History

如果这个项目对你有帮助，请给个 Star ⭐️

[![Star History Chart](https://api.star-history.com/svg?repos=expert985/Telegram-interactive-bot&type=Date)](https://star-history.com/#expert985/Telegram-interactive-bot&Date)

---

<div align="center">

**Made with ❤️ by the community**

[⬆ 回到顶部](#telegram-智能客服系统增强版)

</div>
