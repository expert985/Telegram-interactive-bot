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

    -- SafeLine 安全评分
    security_score INT DEFAULT 100 COMMENT '安全评分（0-100）',
    risk_level ENUM('safe', 'low', 'medium', 'high', 'critical') DEFAULT 'safe' COMMENT '风险等级',
    risk_factors JSON DEFAULT NULL COMMENT '风险因素列表',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    UNIQUE KEY uk_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_assigned_agent (assigned_agent_id),
    INDEX idx_locked_by (locked_by),
    INDEX idx_last_message_at (last_message_at),
    INDEX idx_risk_level (risk_level),
    INDEX idx_security_score (security_score),

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

    -- SafeLine 威胁检测
    threat_detected BOOLEAN DEFAULT FALSE COMMENT '是否检测到威胁',
    threat_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') DEFAULT NULL COMMENT '威胁等级',
    threat_reason VARCHAR(500) DEFAULT NULL COMMENT '威胁原因',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 索引
    INDEX idx_conversation (conversation_id),
    INDEX idx_direction (direction),
    INDEX idx_from_user (from_user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_read (is_read),
    INDEX idx_threat_detected (threat_detected),
    INDEX idx_threat_level (threat_level),

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
-- SafeLine 防护模块表
-- =========================================

-- =========================================
-- 11. security_events 表（安全事件）
-- =========================================
CREATE TABLE IF NOT EXISTS security_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 用户信息
    user_id BIGINT NOT NULL COMMENT 'Telegram 用户 ID',
    username VARCHAR(100) DEFAULT NULL COMMENT '用户名',

    -- 事件类型
    event_type VARCHAR(50) NOT NULL COMMENT '事件类型: message_blocked/rate_limited/behavior_anomaly/threat_detected',
    threat_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL COMMENT '威胁等级',

    -- 原因和证据
    reason VARCHAR(500) NOT NULL COMMENT '拦截/告警原因',
    evidence JSON DEFAULT NULL COMMENT '证据数据（消息内容、行为数据等）',

    -- 处理状态
    handled BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
    handled_by BIGINT UNSIGNED DEFAULT NULL COMMENT '处理人 ID',
    handled_at DATETIME DEFAULT NULL COMMENT '处理时间',
    handle_action VARCHAR(100) DEFAULT NULL COMMENT '处理动作',
    handle_notes TEXT DEFAULT NULL COMMENT '处理备注',

    -- 来源
    source VARCHAR(50) DEFAULT 'auto' COMMENT '来源: auto/manual/rule',
    rule_id BIGINT UNSIGNED DEFAULT NULL COMMENT '触发的规则 ID',

    -- 影响
    action_taken VARCHAR(100) DEFAULT NULL COMMENT '已采取的动作: blocked/warned/logged',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_threat_level (threat_level),
    INDEX idx_handled (handled),
    INDEX idx_created_at (created_at),
    INDEX idx_handled_by (handled_by),

    -- 外键
    FOREIGN KEY (handled_by) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='安全事件表';

-- =========================================
-- 12. user_behaviors 表（用户行为分析）
-- =========================================
CREATE TABLE IF NOT EXISTS user_behaviors (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 用户信息
    user_id BIGINT NOT NULL COMMENT 'Telegram 用户 ID',

    -- 行为维度（6 维）
    message_frequency DECIMAL(5,2) DEFAULT 0.00 COMMENT '消息频率分数（0-100）',
    content_diversity DECIMAL(5,2) DEFAULT 0.00 COMMENT '内容多样性分数（0-100）',
    time_pattern DECIMAL(5,2) DEFAULT 0.00 COMMENT '时间模式分数（0-100）',
    interaction_depth DECIMAL(5,2) DEFAULT 0.00 COMMENT '互动深度分数（0-100）',
    response_speed DECIMAL(5,2) DEFAULT 0.00 COMMENT '响应速度分数（0-100）',
    behavior_consistency DECIMAL(5,2) DEFAULT 0.00 COMMENT '行为一致性分数（0-100）',

    -- 综合评分
    risk_score INT DEFAULT 0 COMMENT '综合风险评分（0-100）',
    risk_level ENUM('safe', 'low', 'medium', 'high', 'critical') DEFAULT 'safe' COMMENT '风险等级',

    -- 异常标识
    is_anomaly BOOLEAN DEFAULT FALSE COMMENT '是否异常',
    anomaly_reasons JSON DEFAULT NULL COMMENT '异常原因列表',

    -- 统计数据
    total_messages INT DEFAULT 0 COMMENT '总消息数',
    spam_count INT DEFAULT 0 COMMENT '垃圾消息数',
    warning_count INT DEFAULT 0 COMMENT '警告次数',
    ban_count INT DEFAULT 0 COMMENT '封禁次数',

    -- 最近活动
    last_message_at DATETIME DEFAULT NULL COMMENT '最后消息时间',
    last_analyzed_at DATETIME DEFAULT NULL COMMENT '最后分析时间',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    UNIQUE KEY uk_user_id (user_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_risk_score (risk_score),
    INDEX idx_is_anomaly (is_anomaly),
    INDEX idx_last_analyzed (last_analyzed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户行为分析表';

-- =========================================
-- 13. protection_rules 表（防护规则配置）
-- =========================================
CREATE TABLE IF NOT EXISTS protection_rules (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 规则基本信息
    name VARCHAR(100) NOT NULL COMMENT '规则名称',
    description TEXT DEFAULT NULL COMMENT '规则描述',
    category ENUM('spam', 'phishing', 'malicious_link', 'rate_limit', 'behavior', 'custom') NOT NULL COMMENT '规则类别',

    -- 规则配置（JSON 格式）
    conditions JSON NOT NULL COMMENT '触发条件',
    actions JSON NOT NULL COMMENT '执行动作',

    -- 严重程度
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL COMMENT '严重程度',

    -- 状态
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    priority INT DEFAULT 50 COMMENT '优先级（0-100，越高越优先）',

    -- 统计
    trigger_count INT DEFAULT 0 COMMENT '触发次数',
    last_triggered_at DATETIME DEFAULT NULL COMMENT '最后触发时间',

    -- 创建者
    created_by BIGINT UNSIGNED DEFAULT NULL COMMENT '创建者 ID',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    INDEX idx_category (category),
    INDEX idx_enabled (enabled),
    INDEX idx_severity (severity),
    INDEX idx_priority (priority),
    INDEX idx_created_by (created_by),

    -- 外键
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='防护规则表';

-- =========================================
-- 14. threat_intelligence 表（威胁情报）
-- =========================================
CREATE TABLE IF NOT EXISTS threat_intelligence (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 威胁标识
    threat_type ENUM('malicious_ip', 'malicious_domain', 'malicious_hash', 'spam_pattern', 'phishing_url') NOT NULL COMMENT '威胁类型',
    threat_value VARCHAR(500) NOT NULL COMMENT '威胁值（IP/域名/哈希/模式）',

    -- 威胁级别
    threat_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL COMMENT '威胁等级',
    confidence DECIMAL(3,2) DEFAULT 0.50 COMMENT '置信度（0.00-1.00）',

    -- 来源
    source VARCHAR(100) DEFAULT 'internal' COMMENT '情报来源',
    source_url VARCHAR(500) DEFAULT NULL COMMENT '情报来源 URL',

    -- 描述
    description TEXT DEFAULT NULL COMMENT '威胁描述',
    tags JSON DEFAULT NULL COMMENT '标签列表',

    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否生效',
    expires_at DATETIME DEFAULT NULL COMMENT '过期时间',

    -- 统计
    hit_count INT DEFAULT 0 COMMENT '命中次数',
    last_hit_at DATETIME DEFAULT NULL COMMENT '最后命中时间',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    INDEX idx_threat_type (threat_type),
    INDEX idx_threat_value (threat_value(255)),
    INDEX idx_threat_level (threat_level),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at),
    INDEX idx_last_hit_at (last_hit_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='威胁情报表';

-- =========================================
-- 15. rate_limit_bans 表（频率限制封禁记录）
-- =========================================
CREATE TABLE IF NOT EXISTS rate_limit_bans (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 用户信息
    user_id BIGINT NOT NULL COMMENT 'Telegram 用户 ID',
    username VARCHAR(100) DEFAULT NULL COMMENT '用户名',

    -- 封禁类型
    ban_type ENUM('temporary', 'permanent') NOT NULL COMMENT '封禁类型',
    ban_reason VARCHAR(500) NOT NULL COMMENT '封禁原因',

    -- 触发信息
    trigger_type VARCHAR(50) NOT NULL COMMENT '触发类型: message_flood/request_flood',
    trigger_threshold INT NOT NULL COMMENT '触发阈值',
    actual_count INT NOT NULL COMMENT '实际次数',

    -- 封禁时间
    banned_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '封禁时间',
    expires_at DATETIME DEFAULT NULL COMMENT '解封时间（NULL=永久）',

    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否生效',

    -- 解封信息
    unbanned_at DATETIME DEFAULT NULL COMMENT '实际解封时间',
    unbanned_by BIGINT UNSIGNED DEFAULT NULL COMMENT '解封操作者 ID',
    unban_reason VARCHAR(500) DEFAULT NULL COMMENT '解封原因',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_ban_type (ban_type),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at),
    INDEX idx_unbanned_by (unbanned_by),

    -- 外键
    FOREIGN KEY (unbanned_by) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='频率限制封禁表';

-- =========================================
-- 16. protection_statistics 表（防护统计）
-- =========================================
CREATE TABLE IF NOT EXISTS protection_statistics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- 统计日期
    date DATE NOT NULL COMMENT '统计日期',

    -- 消息防护统计
    total_messages INT DEFAULT 0 COMMENT '总消息数',
    blocked_messages INT DEFAULT 0 COMMENT '拦截消息数',
    spam_detected INT DEFAULT 0 COMMENT '垃圾消息数',
    phishing_detected INT DEFAULT 0 COMMENT '钓鱼消息数',
    malicious_links INT DEFAULT 0 COMMENT '恶意链接数',

    -- 频率限制统计
    rate_limit_triggered INT DEFAULT 0 COMMENT '频率限制触发次数',
    temporary_bans INT DEFAULT 0 COMMENT '临时封禁次数',
    permanent_bans INT DEFAULT 0 COMMENT '永久封禁次数',

    -- 行为分析统计
    anomaly_detected INT DEFAULT 0 COMMENT '检测到的异常行为数',
    high_risk_users INT DEFAULT 0 COMMENT '高风险用户数',

    -- 威胁等级分布
    threat_low INT DEFAULT 0 COMMENT 'LOW 威胁数',
    threat_medium INT DEFAULT 0 COMMENT 'MEDIUM 威胁数',
    threat_high INT DEFAULT 0 COMMENT 'HIGH 威胁数',
    threat_critical INT DEFAULT 0 COMMENT 'CRITICAL 威胁数',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    UNIQUE KEY uk_date (date),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='防护统计表';

-- =========================================
-- 初始化数据
-- =========================================

-- 创建默认管理员（密码：admin123）
-- 注意：生产环境请修改密码！
INSERT INTO admins (username, password_hash, nickname, role, permissions, status) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eBVEVZNE3F4i', '系统管理员', 'admin',
 '["chat", "keyword", "account", "admin"]', 'offline');

-- 初始化默认防护规则
INSERT INTO protection_rules (name, description, category, conditions, actions, severity, enabled, priority) VALUES
-- 垃圾消息规则
('重复消息检测', '检测短时间内发送的重复消息', 'spam',
 '{"type": "duplicate_content", "time_window": 60, "threshold": 3}',
 '{"action": "warn", "message": "检测到重复消息"}',
 'MEDIUM', TRUE, 70),

('高频消息拦截', '拦截每分钟超过 10 条消息的用户', 'rate_limit',
 '{"type": "message_frequency", "limit": 10, "window": 60}',
 '{"action": "block", "duration": 300}',
 'HIGH', TRUE, 80),

-- 钓鱼检测规则
('可疑链接检测', '检测常见钓鱼域名和短链接', 'phishing',
 '{"type": "url_pattern", "patterns": ["bit.ly", "tinyurl.com", "goo.gl", "t.cn"]}',
 '{"action": "flag", "alert_agent": true}',
 'HIGH', TRUE, 90),

-- 恶意内容规则
('敏感词过滤', '过滤包含敏感词汇的消息', 'spam',
 '{"type": "keyword_match", "keywords": ["赌博", "诈骗", "博彩", "贷款"]}',
 '{"action": "block", "notify": true}',
 'CRITICAL', TRUE, 95),

('长消息检测', '检测超长消息（可能是垃圾信息）', 'spam',
 '{"type": "message_length", "max_length": 1000}',
 '{"action": "warn"}',
 'LOW', TRUE, 40);

-- 初始化威胁情报（示例）
INSERT INTO threat_intelligence (threat_type, threat_value, threat_level, confidence, source, description) VALUES
('phishing_url', 'bit.ly/scam*', 'HIGH', 0.85, 'internal', '已知钓鱼短链接模式'),
('spam_pattern', '.*博彩.*', 'CRITICAL', 0.95, 'internal', '博彩垃圾信息关键词'),
('spam_pattern', '.*加微信.*领取.*', 'MEDIUM', 0.75, 'internal', '诱导添加微信的垃圾信息');

-- 初始化今日防护统计（避免查询空结果）
INSERT INTO protection_statistics (date, total_messages, blocked_messages) VALUES
(CURDATE(), 0, 0);

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

-- SafeLine 安全事件视图（未处理的高危事件）
CREATE OR REPLACE VIEW v_unhandled_threats AS
SELECT
    se.id,
    se.user_id,
    se.username,
    se.event_type,
    se.threat_level,
    se.reason,
    se.action_taken,
    se.created_at,
    ub.risk_score,
    ub.risk_level
FROM security_events se
LEFT JOIN user_behaviors ub ON se.user_id = ub.user_id
WHERE se.handled = FALSE
  AND se.threat_level IN ('HIGH', 'CRITICAL')
ORDER BY se.threat_level DESC, se.created_at DESC;

-- 高风险用户视图
CREATE OR REPLACE VIEW v_high_risk_users AS
SELECT
    ub.user_id,
    c.username,
    c.first_name,
    c.last_name,
    ub.risk_score,
    ub.risk_level,
    ub.anomaly_reasons,
    ub.total_messages,
    ub.spam_count,
    ub.warning_count,
    ub.ban_count,
    c.security_score,
    c.risk_factors,
    ub.last_message_at,
    COUNT(se.id) as recent_violations
FROM user_behaviors ub
LEFT JOIN conversations c ON ub.user_id = c.user_id
LEFT JOIN security_events se ON ub.user_id = se.user_id
    AND se.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
WHERE ub.risk_level IN ('high', 'critical')
GROUP BY ub.user_id, c.username, c.first_name, c.last_name, ub.risk_score,
         ub.risk_level, ub.anomaly_reasons, ub.total_messages, ub.spam_count,
         ub.warning_count, ub.ban_count, c.security_score, c.risk_factors,
         ub.last_message_at
ORDER BY ub.risk_score DESC;

-- 今日防护统计视图
CREATE OR REPLACE VIEW v_today_protection_stats AS
SELECT
    date,
    total_messages,
    blocked_messages,
    ROUND((blocked_messages / NULLIF(total_messages, 0)) * 100, 2) as block_rate,
    spam_detected,
    phishing_detected,
    malicious_links,
    rate_limit_triggered,
    temporary_bans,
    permanent_bans,
    anomaly_detected,
    high_risk_users,
    (threat_low + threat_medium + threat_high + threat_critical) as total_threats,
    threat_low,
    threat_medium,
    threat_high,
    threat_critical
FROM protection_statistics
WHERE date = CURDATE();

-- =========================================
-- 数据库初始化完成
-- =========================================
