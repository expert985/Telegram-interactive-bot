-- =========================================
-- Telegram 客服系统 MySQL 数据库设计
-- 版本: 2.0.0
-- MySQL 版本: 8.0.36+
-- =========================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS telegram_customer
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE telegram_customer;

-- =========================================
-- 1. accounts 表（TG 账号配置）
-- =========================================
CREATE TABLE IF NOT EXISTS accounts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 账号类型
    type ENUM('bot', 'userbot') NOT NULL COMMENT '账号类型',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1=正常 0=禁用 -1=异常',

    -- Bot Token 字段
    bot_token VARCHAR(255) DEFAULT NULL COMMENT 'Bot Token',
    bot_username VARCHAR(100) DEFAULT NULL COMMENT 'Bot 用户名',

    -- Userbot 字段
    tg_id BIGINT DEFAULT NULL COMMENT 'Telegram 用户 ID',
    phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
    username VARCHAR(100) DEFAULT NULL COMMENT '用户名',
    first_name VARCHAR(100) DEFAULT NULL COMMENT '名',
    last_name VARCHAR(100) DEFAULT NULL COMMENT '姓',

    -- Session 配置
    session_string TEXT DEFAULT NULL COMMENT 'Pyrogram Session String',
    session_type VARCHAR(20) DEFAULT 'pyrogram' COMMENT 'Session 类型: pyrogram/telethon',

    -- API 配置
    api_id INT DEFAULT 6 COMMENT 'Telegram API ID',
    api_hash VARCHAR(100) DEFAULT 'eb06d4abfb49dc3eeb1aeb98ae0f581e' COMMENT 'Telegram API Hash',

    -- 设备信息（Userbot）
    device_model VARCHAR(100) DEFAULT NULL COMMENT '设备型号',
    system_version VARCHAR(50) DEFAULT NULL COMMENT '系统版本',
    app_version VARCHAR(50) DEFAULT NULL COMMENT '应用版本',
    lang_code VARCHAR(10) DEFAULT 'zh-hans' COMMENT '语言代码',

    -- 代理配置（JSON 格式）
    proxy JSON DEFAULT NULL COMMENT '代理配置',

    -- 健康状态
    is_online BOOLEAN DEFAULT FALSE COMMENT '是否在线',
    last_check_at DATETIME DEFAULT NULL COMMENT '最后检查时间',
    error_count INT DEFAULT 0 COMMENT '错误次数',
    last_error TEXT DEFAULT NULL COMMENT '最后错误信息',

    -- 流量控制
    flood_wait_until DATETIME DEFAULT NULL COMMENT 'FloodWait 解除时间',
    daily_message_count INT DEFAULT 0 COMMENT '今日消息数',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_tg_id (tg_id),
    INDEX idx_is_online (is_online),
    UNIQUE KEY uk_bot_token (bot_token),
    UNIQUE KEY uk_tg_id (tg_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账号表';

-- =========================================
-- 2. admins 表（管理员/客服）
-- =========================================
CREATE TABLE IF NOT EXISTS admins (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    username VARCHAR(50) NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    nickname VARCHAR(100) NOT NULL COMMENT '昵称',
    role ENUM('admin', 'agent') DEFAULT 'agent' COMMENT '角色',

    -- 在线状态
    status ENUM('online', 'offline', 'busy') DEFAULT 'offline' COMMENT '在线状态',
    last_active_at DATETIME DEFAULT NULL COMMENT '最后活跃时间',

    -- 权限（JSON 数组）
    permissions JSON DEFAULT NULL COMMENT '权限列表',

    -- 统计
    total_conversations INT DEFAULT 0 COMMENT '总会话数',
    avg_response_time INT DEFAULT 0 COMMENT '平均响应时间（秒）',
    satisfaction_rate DECIMAL(3,2) DEFAULT 0.00 COMMENT '满意度评分',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    UNIQUE KEY uk_username (username),
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

-- =========================================
-- 3. conversations 表（会话）
-- =========================================
CREATE TABLE IF NOT EXISTS conversations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 用户信息
    user_id BIGINT NOT NULL COMMENT 'Telegram 用户 ID',
    username VARCHAR(100) DEFAULT NULL COMMENT '用户名',
    first_name VARCHAR(100) DEFAULT NULL COMMENT '名',
    last_name VARCHAR(100) DEFAULT NULL COMMENT '姓',

    -- 会话状态
    status ENUM('waiting', 'active', 'closed') DEFAULT 'waiting' COMMENT '会话状态',

    -- 分配的客服
    assigned_agent_id BIGINT UNSIGNED DEFAULT NULL COMMENT '分配的客服 ID',
    assigned_agent_name VARCHAR(100) DEFAULT NULL COMMENT '客服昵称',
    assigned_at DATETIME DEFAULT NULL COMMENT '分配时间',

    -- 会话锁定
    locked_by BIGINT UNSIGNED DEFAULT NULL COMMENT '锁定客服 ID',
    locked_at DATETIME DEFAULT NULL COMMENT '锁定时间',
    lock_expires_at DATETIME DEFAULT NULL COMMENT '锁定过期时间',

    -- 标签和备注（JSON 数组）
    tags JSON DEFAULT NULL COMMENT '标签',
    notes TEXT DEFAULT NULL COMMENT '备注',

    -- 统计
    message_count INT DEFAULT 0 COMMENT '消息数量',
    unread_count INT DEFAULT 0 COMMENT '未读消息数',
    last_message_at DATETIME DEFAULT NULL COMMENT '最后消息时间',
    last_message_preview VARCHAR(200) DEFAULT NULL COMMENT '最后消息预览',

    -- 来源
    source VARCHAR(50) DEFAULT 'direct' COMMENT '来源: direct/keyword_trigger/manual',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    UNIQUE KEY uk_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_assigned_agent (assigned_agent_id),
    INDEX idx_locked_by (locked_by),
    INDEX idx_last_message_at (last_message_at),

    -- 外键
    FOREIGN KEY (assigned_agent_id) REFERENCES admins(id) ON DELETE SET NULL,
    FOREIGN KEY (locked_by) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';

-- =========================================
-- 4. messages 表（消息记录）
-- =========================================
CREATE TABLE IF NOT EXISTS messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    conversation_id BIGINT UNSIGNED NOT NULL COMMENT '会话 ID',
    direction ENUM('incoming', 'outgoing') NOT NULL COMMENT '方向: incoming=来自用户 outgoing=发给用户',

    -- 发送者
    from_user_id BIGINT DEFAULT NULL COMMENT '发送者 ID',
    from_username VARCHAR(100) DEFAULT NULL COMMENT '发送者用户名',
    from_type ENUM('user', 'agent', 'bot') NOT NULL COMMENT '发送者类型',

    -- 接收者
    to_user_id BIGINT DEFAULT NULL COMMENT '接收者 ID',
    to_type VARCHAR(20) DEFAULT NULL COMMENT '接收者类型',

    -- 消息内容
    content_type ENUM('text', 'photo', 'video', 'document', 'voice', 'sticker', 'animation', 'location', 'contact') NOT NULL COMMENT '消息类型',
    text TEXT DEFAULT NULL COMMENT '文本内容',
    caption TEXT DEFAULT NULL COMMENT '媒体说明',

    -- 媒体文件（JSON 格式）
    media JSON DEFAULT NULL COMMENT '媒体文件信息',

    -- Telegram 消息 ID
    tg_message_id BIGINT DEFAULT NULL COMMENT 'Telegram 消息 ID',
    chat_id BIGINT DEFAULT NULL COMMENT '聊天 ID',

    -- 引用消息
    reply_to_message_id BIGINT UNSIGNED DEFAULT NULL COMMENT '引用的消息 ID',

    -- 状态
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否已删除',

    -- 发送账号
    sent_via_account_id BIGINT UNSIGNED DEFAULT NULL COMMENT '发送账号 ID',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_conversation (conversation_id),
    INDEX idx_direction (direction),
    INDEX idx_from_user (from_user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_read (is_read),

    -- 外键
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sent_via_account_id) REFERENCES accounts(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- =========================================
-- 5. keywords 表（关键词规则）
-- =========================================
CREATE TABLE IF NOT EXISTS keywords (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    keyword VARCHAR(200) NOT NULL COMMENT '关键词',
    match_type ENUM('exact', 'contains', 'regex') DEFAULT 'contains' COMMENT '匹配方式',
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',

    -- 触发动作（JSON 格式）
    action JSON NOT NULL COMMENT '触发动作配置',

    -- 监听范围
    listen_scope ENUM('all', 'groups', 'private') DEFAULT 'all' COMMENT '监听范围',
    group_ids JSON DEFAULT NULL COMMENT '指定群组 ID 列表',

    -- 统计
    trigger_count INT DEFAULT 0 COMMENT '触发次数',
    last_triggered_at DATETIME DEFAULT NULL COMMENT '最后触发时间',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    INDEX idx_keyword (keyword),
    INDEX idx_enabled (enabled),
    INDEX idx_match_type (match_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键词表';

-- =========================================
-- 6. quick_replies 表（快捷回复）
-- =========================================
CREATE TABLE IF NOT EXISTS quick_replies (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    title VARCHAR(100) NOT NULL COMMENT '标题',
    shortcut VARCHAR(50) NOT NULL COMMENT '快捷码（如 /price）',
    content TEXT NOT NULL COMMENT '回复内容',
    media JSON DEFAULT NULL COMMENT '附带媒体',
    category VARCHAR(50) DEFAULT '通用' COMMENT '分类',

    -- 统计
    usage_count INT DEFAULT 0 COMMENT '使用次数',

    -- 创建者
    created_by BIGINT UNSIGNED DEFAULT NULL COMMENT '创建者 ID',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    UNIQUE KEY uk_shortcut (shortcut),
    INDEX idx_category (category),
    INDEX idx_created_by (created_by),

    -- 外键
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='快捷回复表';

-- =========================================
-- 7. statistics 表（统计数据）
-- =========================================
CREATE TABLE IF NOT EXISTS statistics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    date DATE NOT NULL COMMENT '统计日期',
    agent_id BIGINT UNSIGNED DEFAULT NULL COMMENT '客服 ID（NULL 表示全局统计）',

    -- 消息统计
    messages_sent INT DEFAULT 0 COMMENT '发送消息数',
    messages_received INT DEFAULT 0 COMMENT '接收消息数',

    -- 会话统计
    conversations_handled INT DEFAULT 0 COMMENT '处理会话数',
    conversations_closed INT DEFAULT 0 COMMENT '关闭会话数',
    avg_response_time INT DEFAULT 0 COMMENT '平均响应时间（秒）',

    -- 关键词统计
    keyword_triggers INT DEFAULT 0 COMMENT '关键词触发次数',

    -- 在线时长
    online_minutes INT DEFAULT 0 COMMENT '在线时长（分钟）',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    UNIQUE KEY uk_date_agent (date, agent_id),
    INDEX idx_date (date),
    INDEX idx_agent (agent_id),

    -- 外键
    FOREIGN KEY (agent_id) REFERENCES admins(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统计表';

-- =========================================
-- 8. user_tags 表（用户标签，可选）
-- =========================================
CREATE TABLE IF NOT EXISTS user_tags (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT NOT NULL COMMENT 'Telegram 用户 ID',
    tag VARCHAR(50) NOT NULL COMMENT '标签',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    UNIQUE KEY uk_user_tag (user_id, tag),
    INDEX idx_tag (tag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户标签表';

-- =========================================
-- 9. blacklist 表（黑名单，可选）
-- =========================================
CREATE TABLE IF NOT EXISTS blacklist (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT NOT NULL COMMENT 'Telegram 用户 ID',
    username VARCHAR(100) DEFAULT NULL COMMENT '用户名',
    reason TEXT DEFAULT NULL COMMENT '封禁原因',

    blocked_by BIGINT UNSIGNED DEFAULT NULL COMMENT '封禁操作者 ID',
    blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '封禁时间',
    expires_at DATETIME DEFAULT NULL COMMENT '解封时间（NULL 为永久）',

    -- 索引
    UNIQUE KEY uk_user_id (user_id),
    INDEX idx_expires_at (expires_at),

    -- 外键
    FOREIGN KEY (blocked_by) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='黑名单表';

-- =========================================
-- 10. audit_logs 表（操作日志，可选）
-- =========================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    admin_id BIGINT UNSIGNED DEFAULT NULL COMMENT '操作者 ID',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型',
    resource_id BIGINT UNSIGNED DEFAULT NULL COMMENT '资源 ID',
    details JSON DEFAULT NULL COMMENT '详细信息',

    ip_address VARCHAR(45) DEFAULT NULL COMMENT 'IP 地址',
    user_agent TEXT DEFAULT NULL COMMENT 'User Agent',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_admin (admin_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),

    -- 外键
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- =========================================
-- 初始化数据
-- =========================================

-- 创建默认管理员（密码：admin123）
-- 注意：生产环境请修改密码！
INSERT INTO admins (username, password_hash, nickname, role, permissions, status) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eBVEVZNE3F4i', '系统管理员', 'admin',
 '["chat", "keyword", "account", "admin"]', 'offline');

-- =========================================
-- 视图（方便查询）
-- =========================================

-- 会话列表视图（包含客服信息）
CREATE OR REPLACE VIEW v_conversations AS
SELECT
    c.id,
    c.user_id,
    c.username,
    c.first_name,
    c.last_name,
    c.status,
    c.assigned_agent_id,
    c.assigned_agent_name,
    a.status as agent_status,
    c.locked_by,
    c.lock_expires_at,
    CASE
        WHEN c.lock_expires_at IS NOT NULL AND c.lock_expires_at > NOW() THEN TRUE
        ELSE FALSE
    END as is_locked,
    c.message_count,
    c.unread_count,
    c.last_message_at,
    c.last_message_preview,
    c.tags,
    c.created_at,
    c.updated_at
FROM conversations c
LEFT JOIN admins a ON c.assigned_agent_id = a.id;

-- 统计视图（今日统计）
CREATE OR REPLACE VIEW v_today_stats AS
SELECT
    agent_id,
    messages_sent,
    messages_received,
    conversations_handled,
    conversations_closed,
    avg_response_time,
    online_minutes
FROM statistics
WHERE date = CURDATE();

-- =========================================
-- 数据库初始化完成
-- =========================================
