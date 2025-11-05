# MySQL 8.0.36 版本使用指南

## 📋 为什么选择 MySQL？

相比 MongoDB，MySQL 8.0.36 有以下优势：

- ✅ **更成熟稳定**：经过数十年验证的关系型数据库
- ✅ **JSON 支持**：MySQL 8.0+ 原生支持 JSON 字段，灵活性不输 NoSQL
- ✅ **事务支持**：ACID 特性，数据一致性更强
- ✅ **性能优异**：优化的查询性能和索引机制
- ✅ **易于管理**：丰富的管理工具（PHPMyAdmin、DBeaver 等）
- ✅ **更熟悉**：大多数开发者更熟悉 SQL 语法

---

## 🏗️ 数据库设计

### 核心表结构

| 表名 | 用途 | 主要字段 |
|------|------|---------|
| `accounts` | TG 账号配置 | type, bot_token, tg_id, session_string |
| `admins` | 管理员/客服 | username, password_hash, role, status |
| `conversations` | 用户会话 | user_id, status, assigned_agent_id, locked_by |
| `messages` | 消息记录 | conversation_id, direction, content_type, text |
| `keywords` | 关键词规则 | keyword, match_type, action (JSON) |
| `quick_replies` | 快捷回复 | shortcut, content, category |
| `statistics` | 统计数据 | date, agent_id, messages_sent, conversations_handled |
| `blacklist` | 黑名单 | user_id, reason, blocked_by |
| `audit_logs` | 操作日志 | admin_id, action, resource_type, details (JSON) |

### JSON 字段的使用

MySQL 8.0 原生支持 JSON，用于存储灵活的数据结构：

```sql
-- 代理配置（accounts 表）
proxy: {
  "enabled": true,
  "type": "socks5",
  "host": "127.0.0.1",
  "port": 1080,
  "username": "user",
  "password": "pass"
}

-- 关键词动作（keywords 表）
action: {
  "type": "auto_reply",
  "reply_text": "您好！...",
  "auto_dm": true,
  "dm_message": "...",
  "notify_agents": true
}

-- 标签（conversations 表）
tags: ["新用户", "VIP", "产品咨询"]

-- 权限（admins 表）
permissions: ["chat", "keyword", "account", "admin"]
```

---

## 🚀 快速开始

### 方式 1: Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/expert985/Telegram-interactive-bot.git
cd Telegram-interactive-bot

# 2. 配置环境变量
cp .env.example .env
nano .env  # 修改 MySQL 密码等配置

# 3. 启动所有服务（MySQL + Redis + 后端）
docker-compose up -d

# 4. 查看日志
docker-compose logs -f mysql  # 查看 MySQL 日志
docker-compose logs -f backend  # 查看后端日志

# 5. 检查 MySQL 是否启动成功
docker-compose exec mysql mysql -u telegram -ptelegram123 -e "SHOW DATABASES;"
```

**首次启动时，MySQL 会自动执行 `database/schema.sql` 创建所有表！**

### 方式 2: 本地 MySQL 服务器

如果你已经有 MySQL 8.0.36 服务器：

```bash
# 1. 创建数据库并导入表结构
mysql -u root -p < database/schema.sql

# 2. 配置环境变量
cp .env.example .env
nano .env

# 修改为你的 MySQL 配置：
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=telegram
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=telegram_customer

# 3. 安装依赖并启动后端
cd backend
pip install -r requirements.txt
python database.py  # 测试连接
python main.py  # 启动 API 服务
```

---

## 📊 数据库管理

### 连接数据库

#### 命令行连接

```bash
# Docker 方式
docker-compose exec mysql mysql -u telegram -ptelegram123 telegram_customer

# 本地方式
mysql -u telegram -ptelegram123 telegram_customer
```

#### 图形化工具连接

推荐使用以下工具：

**1. DBeaver（推荐）**
- 下载：https://dbeaver.io/
- 配置：
  - Host: localhost
  - Port: 3306
  - Database: telegram_customer
  - Username: telegram
  - Password: telegram123

**2. PHPMyAdmin**
```bash
# 使用 Docker 快速启动 PHPMyAdmin
docker run --name phpmyadmin -d --link telegram_customer_mysql:db \
  -p 8080:80 phpmyadmin/phpmyadmin

# 访问: http://localhost:8080
# 用户名: telegram
# 密码: telegram123
```

**3. MySQL Workbench**
- 下载：https://dev.mysql.com/downloads/workbench/
- 适合 MySQL 专业管理

### 常用 SQL 命令

#### 查看所有表

```sql
SHOW TABLES;

-- 输出:
-- +-----------------------------+
-- | Tables_in_telegram_customer |
-- +-----------------------------+
-- | accounts                    |
-- | admins                      |
-- | audit_logs                  |
-- | blacklist                   |
-- | conversations               |
-- | keywords                    |
-- | messages                    |
-- | quick_replies               |
-- | statistics                  |
-- | user_tags                   |
-- +-----------------------------+
```

#### 查看表结构

```sql
DESC accounts;  -- 查看 accounts 表结构
SHOW CREATE TABLE accounts;  -- 查看建表语句
```

#### 查询数据示例

```sql
-- 查看所有在线的账号
SELECT id, type, username, bot_username, is_online, last_check_at
FROM accounts
WHERE status = 1 AND is_online = TRUE;

-- 查看今日会话统计
SELECT
    a.nickname,
    s.messages_sent,
    s.conversations_handled,
    s.avg_response_time
FROM statistics s
JOIN admins a ON s.agent_id = a.id
WHERE s.date = CURDATE();

-- 查看未读消息数量
SELECT
    c.user_id,
    c.first_name,
    c.unread_count,
    c.last_message_at
FROM conversations c
WHERE c.unread_count > 0
ORDER BY c.last_message_at DESC;

-- JSON 字段查询示例
SELECT keyword, action->>'$.type' as action_type
FROM keywords
WHERE enabled = TRUE;
```

---

## 🔧 数据库操作

### 备份数据库

```bash
# 完整备份（包含数据）
docker-compose exec mysql mysqldump -u telegram -ptelegram123 \
  telegram_customer > backup_$(date +%Y%m%d_%H%M%S).sql

# 仅备份表结构（不含数据）
docker-compose exec mysql mysqldump -u telegram -ptelegram123 \
  --no-data telegram_customer > schema_backup.sql
```

### 恢复数据库

```bash
# 从备份文件恢复
docker-compose exec -T mysql mysql -u telegram -ptelegram123 \
  telegram_customer < backup_20250105_120000.sql
```

### 重置数据库

```bash
# ⚠️ 危险操作！会删除所有数据
docker-compose exec mysql mysql -u telegram -ptelegram123 -e "
  DROP DATABASE telegram_customer;
  CREATE DATABASE telegram_customer;
"

# 重新导入表结构
docker-compose exec -T mysql mysql -u telegram -ptelegram123 \
  telegram_customer < database/schema.sql
```

---

## 🛠️ SQLAlchemy ORM 使用

### 同步查询示例

```python
from database import get_db
from models import Admin, Conversation, Message

# 使用上下文管理器
with get_db() as db:
    # 查询所有管理员
    admins = db.query(Admin).filter_by(role='admin').all()

    # 查询特定会话
    conversation = db.query(Conversation).filter_by(user_id=123456789).first()

    # 复杂查询
    from sqlalchemy import func
    result = db.query(
        Conversation.status,
        func.count(Conversation.id).label('count')
    ).group_by(Conversation.status).all()

    for status, count in result:
        print(f"{status}: {count}")
```

### 异步查询示例

```python
from database import get_async_db
from models import Admin, Conversation
from sqlalchemy import select

async def get_admin_conversations(admin_id: int):
    async with get_async_db() as db:
        # 查询管理员的所有会话
        stmt = select(Conversation).where(
            Conversation.assigned_agent_id == admin_id
        )
        result = await db.execute(stmt)
        conversations = result.scalars().all()

        return conversations
```

### FastAPI 依赖注入

```python
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db_session
from models import Admin

app = FastAPI()

@app.get("/admins")
async def list_admins(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Admin))
    admins = result.scalars().all()
    return admins
```

---

## 📈 性能优化

### 索引优化

所有表已预设优化的索引：

```sql
-- 会话表索引
CREATE INDEX idx_status ON conversations(status);
CREATE INDEX idx_assigned_agent ON conversations(assigned_agent_id);
CREATE INDEX idx_last_message_at ON conversations(last_message_at);

-- 消息表索引
CREATE INDEX idx_conversation ON messages(conversation_id);
CREATE INDEX idx_created_at ON messages(created_at);
CREATE INDEX idx_is_read ON messages(is_read);
```

### 查询优化建议

```sql
-- ✅ 好的查询（使用索引）
SELECT * FROM conversations WHERE status = 'waiting';

-- ❌ 避免全表扫描
SELECT * FROM messages WHERE text LIKE '%关键词%';  -- 无法使用索引

-- ✅ 使用全文索引（如果需要）
ALTER TABLE messages ADD FULLTEXT INDEX ft_text (text);
SELECT * FROM messages WHERE MATCH(text) AGAINST('关键词' IN NATURAL LANGUAGE MODE);
```

### 连接池配置

在 `backend/database.py` 中已配置：

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # 连接池大小
    max_overflow=40,  # 溢出连接数
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_pre_ping=True  # 连接前 ping 检测
)
```

---

## 🔍 常见问题

### 1. 连接失败：Access denied

```bash
# 错误: Access denied for user 'telegram'@'localhost'

# 解决方案1：检查密码
docker-compose exec mysql mysql -u root -proot123 -e "
  ALTER USER 'telegram'@'%' IDENTIFIED BY 'telegram123';
  FLUSH PRIVILEGES;
"

# 解决方案2：检查 .env 文件配置是否正确
```

### 2. 字符集问题

```sql
-- 检查数据库字符集
SHOW VARIABLES LIKE 'character%';

-- 修改表字符集（如果需要）
ALTER TABLE messages CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. JSON 字段查询

```sql
-- 查询 JSON 字段
SELECT * FROM accounts WHERE proxy->>'$.enabled' = 'true';

-- 更新 JSON 字段
UPDATE accounts
SET proxy = JSON_SET(proxy, '$.host', '127.0.0.1')
WHERE id = 1;

-- 提取 JSON 数组元素
SELECT tags->>'$[0]' as first_tag FROM conversations;
```

### 4. 连接数过多

```sql
-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看最大连接数
SHOW VARIABLES LIKE 'max_connections';

-- 增加最大连接数（已在 docker-compose.yml 配置为 500）
```

---

## 📚 视图（View）

系统已创建便捷视图：

### v_conversations（会话视图）

```sql
-- 查询会话列表（包含客服信息和锁定状态）
SELECT * FROM v_conversations
WHERE status = 'waiting'
ORDER BY last_message_at DESC;
```

### v_today_stats（今日统计视图）

```sql
-- 查询今日客服统计
SELECT * FROM v_today_stats;
```

---

## 🎯 迁移指南（从 MongoDB）

如果你之前使用的是 MongoDB 版本，迁移步骤：

### 1. 导出 MongoDB 数据

```javascript
// MongoDB 导出脚本
mongodump --db telegram_customer --out ./mongodb_backup
```

### 2. 转换数据格式

```python
# 编写迁移脚本（Python 示例）
from pymongo import MongoClient
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Account, Admin, Conversation, Message

# 连接 MongoDB
mongo_client = MongoClient('mongodb://localhost:27017')
mongo_db = mongo_client['telegram_customer']

# 连接 MySQL
db = SessionLocal()

# 迁移账号数据
for doc in mongo_db['accounts'].find():
    account = Account(
        type=doc['type'],
        status=doc.get('status', 1),
        bot_token=doc.get('bot_token'),
        tg_id=doc.get('tg_id'),
        # ... 其他字段
    )
    db.add(account)

db.commit()
db.close()
```

### 3. 验证数据

```sql
-- 检查记录数
SELECT 'accounts' as table_name, COUNT(*) as count FROM accounts
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'messages', COUNT(*) FROM messages;
```

---

## 🔐 安全建议

### 1. 修改默认密码

```sql
-- 生产环境必须修改密码！
ALTER USER 'telegram'@'%' IDENTIFIED BY 'your_strong_password_here';
FLUSH PRIVILEGES;
```

### 2. 限制访问 IP

```sql
-- 创建仅本地访问的用户
CREATE USER 'telegram_local'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON telegram_customer.* TO 'telegram_local'@'localhost';
```

### 3. 定期备份

```bash
# 设置 cron 定时备份（每天凌晨 2 点）
0 2 * * * /usr/local/bin/backup_mysql.sh
```

---

## 📞 技术支持

遇到 MySQL 相关问题：

1. 查看日志：`docker-compose logs mysql`
2. 连接测试：`python backend/database.py`
3. 提交 Issue：https://github.com/expert985/Telegram-interactive-bot/issues

---

## 📖 参考资料

- MySQL 8.0 官方文档：https://dev.mysql.com/doc/refman/8.0/en/
- SQLAlchemy 文档：https://docs.sqlalchemy.org/
- JSON 函数参考：https://dev.mysql.com/doc/refman/8.0/en/json-functions.html

---

**完成！现在你可以享受 MySQL 的稳定性和强大功能了！** 🎉
