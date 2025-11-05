# -*- coding: utf-8 -*-
"""
SQLAlchemy ORM 模型（MySQL 版本）
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime,
    Boolean, Enum, DECIMAL, JSON, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ==================== 1. Account 模型 ====================
class Account(Base):
    """账号表（Bot Token / Userbot）"""
    __tablename__ = 'accounts'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 账号类型
    type = Column(Enum('bot', 'userbot'), nullable=False, comment='账号类型')
    status = Column(Integer, nullable=False, default=1, comment='状态: 1=正常 0=禁用 -1=异常')

    # Bot Token 字段
    bot_token = Column(String(255), unique=True, comment='Bot Token')
    bot_username = Column(String(100), comment='Bot 用户名')

    # Userbot 字段
    tg_id = Column(BigInteger, unique=True, comment='Telegram 用户 ID')
    phone = Column(String(20), comment='手机号')
    username = Column(String(100), comment='用户名')
    first_name = Column(String(100), comment='名')
    last_name = Column(String(100), comment='姓')

    # Session 配置
    session_string = Column(Text, comment='Pyrogram Session String')
    session_type = Column(String(20), default='pyrogram', comment='Session 类型')

    # API 配置
    api_id = Column(Integer, default=6, comment='Telegram API ID')
    api_hash = Column(String(100), default='eb06d4abfb49dc3eeb1aeb98ae0f581e', comment='API Hash')

    # 设备信息
    device_model = Column(String(100), comment='设备型号')
    system_version = Column(String(50), comment='系统版本')
    app_version = Column(String(50), comment='应用版本')
    lang_code = Column(String(10), default='zh-hans', comment='语言代码')

    # 代理配置（JSON）
    proxy = Column(JSON, comment='代理配置')

    # 健康状态
    is_online = Column(Boolean, default=False, comment='是否在线')
    last_check_at = Column(DateTime, comment='最后检查时间')
    error_count = Column(Integer, default=0, comment='错误次数')
    last_error = Column(Text, comment='最后错误信息')

    # 流量控制
    flood_wait_until = Column(DateTime, comment='FloodWait 解除时间')
    daily_message_count = Column(Integer, default=0, comment='今日消息数')

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 索引
    __table_args__ = (
        Index('idx_type', 'type'),
        Index('idx_status', 'status'),
        Index('idx_tg_id', 'tg_id'),
        Index('idx_is_online', 'is_online'),
    )


# ==================== 2. Admin 模型 ====================
class Admin(Base):
    """管理员/客服表"""
    __tablename__ = 'admins'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    nickname = Column(String(100), nullable=False, comment='昵称')
    role = Column(Enum('admin', 'agent'), default='agent', comment='角色')

    # 在线状态
    status = Column(Enum('online', 'offline', 'busy'), default='offline', comment='在线状态')
    last_active_at = Column(DateTime, comment='最后活跃时间')

    # 权限（JSON 数组）
    permissions = Column(JSON, comment='权限列表')

    # 统计
    total_conversations = Column(Integer, default=0, comment='总会话数')
    avg_response_time = Column(Integer, default=0, comment='平均响应时间（秒）')
    satisfaction_rate = Column(DECIMAL(3, 2), default=0.00, comment='满意度评分')

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    conversations = relationship("Conversation", back_populates="assigned_agent", foreign_keys='Conversation.assigned_agent_id')
    statistics = relationship("Statistic", back_populates="agent", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_role', 'role'),
        Index('idx_status', 'status'),
    )


# ==================== 3. Conversation 模型 ====================
class Conversation(Base):
    """会话表"""
    __tablename__ = 'conversations'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 用户信息
    user_id = Column(BigInteger, unique=True, nullable=False, comment='Telegram 用户 ID')
    username = Column(String(100), comment='用户名')
    first_name = Column(String(100), comment='名')
    last_name = Column(String(100), comment='姓')

    # 会话状态
    status = Column(Enum('waiting', 'active', 'closed'), default='waiting', comment='会话状态')

    # 分配的客服
    assigned_agent_id = Column(BigInteger, ForeignKey('admins.id', ondelete='SET NULL'), comment='分配的客服 ID')
    assigned_agent_name = Column(String(100), comment='客服昵称')
    assigned_at = Column(DateTime, comment='分配时间')

    # 会话锁定
    locked_by = Column(BigInteger, ForeignKey('admins.id', ondelete='SET NULL'), comment='锁定客服 ID')
    locked_at = Column(DateTime, comment='锁定时间')
    lock_expires_at = Column(DateTime, comment='锁定过期时间')

    # 标签和备注
    tags = Column(JSON, comment='标签')
    notes = Column(Text, comment='备注')

    # 统计
    message_count = Column(Integer, default=0, comment='消息数量')
    unread_count = Column(Integer, default=0, comment='未读消息数')
    last_message_at = Column(DateTime, comment='最后消息时间')
    last_message_preview = Column(String(200), comment='最后消息预览')

    # 来源
    source = Column(String(50), default='direct', comment='来源')

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    assigned_agent = relationship("Admin", back_populates="conversations", foreign_keys=[assigned_agent_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_assigned_agent', 'assigned_agent_id'),
        Index('idx_locked_by', 'locked_by'),
        Index('idx_last_message_at', 'last_message_at'),
    )


# ==================== 4. Message 模型 ====================
class Message(Base):
    """消息表"""
    __tablename__ = 'messages'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    conversation_id = Column(BigInteger, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, comment='会话 ID')
    direction = Column(Enum('incoming', 'outgoing'), nullable=False, comment='方向')

    # 发送者
    from_user_id = Column(BigInteger, comment='发送者 ID')
    from_username = Column(String(100), comment='发送者用户名')
    from_type = Column(Enum('user', 'agent', 'bot'), nullable=False, comment='发送者类型')

    # 接收者
    to_user_id = Column(BigInteger, comment='接收者 ID')
    to_type = Column(String(20), comment='接收者类型')

    # 消息内容
    content_type = Column(Enum('text', 'photo', 'video', 'document', 'voice', 'sticker', 'animation', 'location', 'contact'), nullable=False, comment='消息类型')
    text = Column(Text, comment='文本内容')
    caption = Column(Text, comment='媒体说明')

    # 媒体文件（JSON）
    media = Column(JSON, comment='媒体文件信息')

    # Telegram 消息 ID
    tg_message_id = Column(BigInteger, comment='Telegram 消息 ID')
    chat_id = Column(BigInteger, comment='聊天 ID')

    # 引用消息
    reply_to_message_id = Column(BigInteger, comment='引用的消息 ID')

    # 状态
    is_read = Column(Boolean, default=False, comment='是否已读')
    is_deleted = Column(Boolean, default=False, comment='是否已删除')

    # 发送账号
    sent_via_account_id = Column(BigInteger, ForeignKey('accounts.id', ondelete='SET NULL'), comment='发送账号 ID')

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')

    # 关系
    conversation = relationship("Conversation", back_populates="messages")

    # 索引
    __table_args__ = (
        Index('idx_conversation', 'conversation_id'),
        Index('idx_direction', 'direction'),
        Index('idx_from_user', 'from_user_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_is_read', 'is_read'),
    )


# ==================== 5. Keyword 模型 ====================
class Keyword(Base):
    """关键词表"""
    __tablename__ = 'keywords'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    keyword = Column(String(200), nullable=False, comment='关键词')
    match_type = Column(Enum('exact', 'contains', 'regex'), default='contains', comment='匹配方式')
    enabled = Column(Boolean, default=True, comment='是否启用')

    # 触发动作（JSON）
    action = Column(JSON, nullable=False, comment='触发动作配置')

    # 监听范围
    listen_scope = Column(Enum('all', 'groups', 'private'), default='all', comment='监听范围')
    group_ids = Column(JSON, comment='指定群组 ID 列表')

    # 统计
    trigger_count = Column(Integer, default=0, comment='触发次数')
    last_triggered_at = Column(DateTime, comment='最后触发时间')

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 索引
    __table_args__ = (
        Index('idx_keyword', 'keyword'),
        Index('idx_enabled', 'enabled'),
        Index('idx_match_type', 'match_type'),
    )


# ==================== 6. QuickReply 模型 ====================
class QuickReply(Base):
    """快捷回复表"""
    __tablename__ = 'quick_replies'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    title = Column(String(100), nullable=False, comment='标题')
    shortcut = Column(String(50), unique=True, nullable=False, comment='快捷码')
    content = Column(Text, nullable=False, comment='回复内容')
    media = Column(JSON, comment='附带媒体')
    category = Column(String(50), default='通用', comment='分类')

    # 统计
    usage_count = Column(Integer, default=0, comment='使用次数')

    # 创建者
    created_by = Column(BigInteger, ForeignKey('admins.id', ondelete='SET NULL'), comment='创建者 ID')

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 索引
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_created_by', 'created_by'),
    )


# ==================== 7. Statistic 模型 ====================
class Statistic(Base):
    """统计表"""
    __tablename__ = 'statistics'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    date = Column(DateTime, nullable=False, comment='统计日期')
    agent_id = Column(BigInteger, ForeignKey('admins.id', ondelete='CASCADE'), comment='客服 ID')

    # 消息统计
    messages_sent = Column(Integer, default=0, comment='发送消息数')
    messages_received = Column(Integer, default=0, comment='接收消息数')

    # 会话统计
    conversations_handled = Column(Integer, default=0, comment='处理会话数')
    conversations_closed = Column(Integer, default=0, comment='关闭会话数')
    avg_response_time = Column(Integer, default=0, comment='平均响应时间（秒）')

    # 关键词统计
    keyword_triggers = Column(Integer, default=0, comment='关键词触发次数')

    # 在线时长
    online_minutes = Column(Integer, default=0, comment='在线时长（分钟）')

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    agent = relationship("Admin", back_populates="statistics")

    # 索引
    __table_args__ = (
        Index('uk_date_agent', 'date', 'agent_id', unique=True),
        Index('idx_date', 'date'),
        Index('idx_agent', 'agent_id'),
    )


# ==================== 8. Blacklist 模型（可选）====================
class Blacklist(Base):
    """黑名单表"""
    __tablename__ = 'blacklist'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(BigInteger, unique=True, nullable=False, comment='Telegram 用户 ID')
    username = Column(String(100), comment='用户名')
    reason = Column(Text, comment='封禁原因')

    blocked_by = Column(BigInteger, ForeignKey('admins.id', ondelete='SET NULL'), comment='封禁操作者 ID')
    blocked_at = Column(DateTime, default=func.now(), comment='封禁时间')
    expires_at = Column(DateTime, comment='解封时间')

    # 索引
    __table_args__ = (
        Index('idx_expires_at', 'expires_at'),
    )


# ==================== 9. AuditLog 模型（可选）====================
class AuditLog(Base):
    """操作日志表"""
    __tablename__ = 'audit_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    admin_id = Column(BigInteger, ForeignKey('admins.id', ondelete='SET NULL'), comment='操作者 ID')
    action = Column(String(50), nullable=False, comment='操作类型')
    resource_type = Column(String(50), nullable=False, comment='资源类型')
    resource_id = Column(BigInteger, comment='资源 ID')
    details = Column(JSON, comment='详细信息')

    ip_address = Column(String(45), comment='IP 地址')
    user_agent = Column(Text, comment='User Agent')

    created_at = Column(DateTime, default=func.now(), comment='创建时间')

    # 索引
    __table_args__ = (
        Index('idx_admin', 'admin_id'),
        Index('idx_action', 'action'),
        Index('idx_created_at', 'created_at'),
    )
