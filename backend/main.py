# -*- coding: utf-8 -*-
"""
FastAPI 后端主程序
提供 RESTful API 和 WebSocket 接口
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import redis.asyncio as aioredis
import jwt
import bcrypt

# 导入自定义模块
from account_manager import init_account_manager, get_account_manager
from message_handler import init_message_processor, get_message_processor
from account_login import get_account_login_manager
from websocket_handler import handle_websocket, get_connection_manager
from database import init_mysql, close_mysql, execute_raw_sql
import api_security

# ==================== 配置 ====================

# 从环境变量读取配置
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== 应用生命周期 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的操作"""
    logger.info("🚀 正在启动应用...")

    # 启动时初始化
    global mongo_client, db, redis_client

    # 连接 MySQL
    try:
        await init_mysql()
        logger.info("✅ MySQL 已连接")
    except Exception as e:
        logger.warning(f"⚠️ MySQL 连接失败: {e}")
        logger.info("将使用 MongoDB 作为主数据库")

    # 连接 MongoDB
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client['telegram_customer']
    logger.info("✅ MongoDB 已连接")

    # 连接 Redis
    redis_client = await aioredis.from_url(REDIS_URL)
    logger.info("✅ Redis 已连接")

    # 初始化账号管理器
    await init_account_manager(MONGO_URI)
    logger.info("✅ 账号管理器已初始化")

    # 初始化消息处理器
    await init_message_processor(MONGO_URI, redis_client)
    logger.info("✅ 消息处理器已初始化")

    logger.info("✅ 应用启动完成！")

    yield

    # 关闭时清理
    logger.info("正在关闭应用...")

    # 关闭所有账号连接
    account_mgr = get_account_manager()
    await account_mgr.close_all()

    # 关闭数据库连接
    await close_mysql()
    mongo_client.close()
    await redis_client.close()

    logger.info("应用已关闭")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="Telegram Customer Service API",
    description="Telegram 客服系统后端 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置（允许前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含安全 API 路由
app.include_router(api_security.router)

# HTTP Bearer 认证
security = HTTPBearer()

# ==================== Pydantic Models ====================


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminCreate(BaseModel):
    username: str
    password: str
    nickname: str
    role: str = "agent"  # admin | agent


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BotAccountAdd(BaseModel):
    bot_token: str


class UserbotAccountAdd(BaseModel):
    session_string: str
    session_type: str = "pyrogram"  # pyrogram | telethon
    api_id: int = 6
    api_hash: str = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
    proxy: Optional[dict] = None


class UserbotLoginStart(BaseModel):
    phone: str
    api_id: Optional[int] = 6
    api_hash: Optional[str] = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
    proxy: Optional[dict] = None


class UserbotLoginCode(BaseModel):
    session_id: str
    code: str


class UserbotLoginPassword(BaseModel):
    session_id: str
    password: str


class SendMessage(BaseModel):
    conversation_id: str
    content_type: str  # text | photo | video | document
    text: Optional[str] = None
    media: Optional[dict] = None


class KeywordCreate(BaseModel):
    keyword: str
    match_type: str = "contains"  # exact | contains | regex
    enabled: bool = True
    action: dict


class QuickReplyCreate(BaseModel):
    title: str
    shortcut: str
    content: str
    media: Optional[List[dict]] = []
    category: Optional[str] = "通用"


# ==================== 认证依赖 ====================


def create_access_token(data: dict) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 JWT Token 并返回当前管理员"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        admin_id = payload.get("sub")

        if admin_id is None:
            raise HTTPException(status_code=401, detail="无效的认证凭证")

        # 从数据库查询管理员
        admin = await db['admins'].find_one({"_id": ObjectId(admin_id)})

        if admin is None:
            raise HTTPException(status_code=401, detail="用户不存在")

        # 更新最后活跃时间
        await db['admins'].update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": {"last_active_at": datetime.now()}}
        )

        return admin

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="无法验证凭证")


# ==================== API 路由 ====================

# -------------------- 认证相关 --------------------


@app.post("/api/auth/login", response_model=Token)
async def login(admin_login: AdminLogin):
    """管理员登录"""
    admin = await db['admins'].find_one({"username": admin_login.username})

    if not admin:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not bcrypt.checkpw(admin_login.password.encode(), admin['password_hash'].encode()):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 生成 Token
    access_token = create_access_token({"sub": str(admin['_id'])})

    # 更新登录状态
    await db['admins'].update_one(
        {"_id": admin['_id']},
        {
            "$set": {
                "status": "online",
                "last_active_at": datetime.now()
            }
        }
    )

    return {"access_token": access_token}


@app.post("/api/auth/register")
async def register(admin_create: AdminCreate):
    """创建管理员账号（首次安装时使用）"""
    # 检查是否已存在
    existing = await db['admins'].find_one({"username": admin_create.username})
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 密码加密
    password_hash = bcrypt.hashpw(admin_create.password.encode(), bcrypt.gensalt()).decode()

    # 创建管理员
    admin = {
        "username": admin_create.username,
        "password_hash": password_hash,
        "nickname": admin_create.nickname,
        "role": admin_create.role,
        "status": "offline",
        "permissions": ["chat", "keyword", "account"],
        "total_conversations": 0,
        "avg_response_time": 0,
        "satisfaction_rate": 0,
        "created_at": datetime.now(),
        "last_active_at": datetime.now()
    }

    result = await db['admins'].insert_one(admin)

    return {
        "success": True,
        "admin_id": str(result.inserted_id),
        "username": admin_create.username
    }


@app.get("/api/auth/me")
async def get_me(current_admin: dict = Depends(get_current_admin)):
    """获取当前登录的管理员信息"""
    return {
        "id": str(current_admin['_id']),
        "username": current_admin['username'],
        "nickname": current_admin['nickname'],
        "role": current_admin['role'],
        "status": current_admin['status'],
        "permissions": current_admin.get('permissions', [])
    }


# -------------------- 账号管理 --------------------

@app.get("/api/accounts")
async def get_accounts(current_admin: dict = Depends(get_current_admin)):
    """获取所有账号列表"""
    accounts = await db['accounts'].find().to_list(None)

    return [
        {
            "id": str(acc['_id']),
            "type": acc['type'],
            "status": acc['status'],
            "username": acc.get('username') or acc.get('bot_username'),
            "tg_id": acc.get('tg_id'),
            "phone": acc.get('phone'),
            "is_online": acc.get('is_online', False),
            "last_check_at": acc.get('last_check_at'),
            "error_count": acc.get('error_count', 0),
            "created_at": acc.get('created_at')
        }
        for acc in accounts
    ]


@app.post("/api/accounts/bot")
async def add_bot_account(
    bot_account: BotAccountAdd,
    current_admin: dict = Depends(get_current_admin)
):
    """添加 Bot Token 账号"""
    account_mgr = get_account_manager()
    result = await account_mgr.add_bot_account(bot_account.bot_token)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@app.post("/api/accounts/userbot/start")
async def start_userbot_login(
    login_data: UserbotLoginStart,
    current_admin: dict = Depends(get_current_admin)
):
    """步骤1：开始 Userbot 登录 - 发送验证码"""
    login_mgr = get_account_login_manager()

    result = await login_mgr.start_login(
        phone=login_data.phone,
        api_id=login_data.api_id,
        api_hash=login_data.api_hash,
        proxy=login_data.proxy
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@app.post("/api/accounts/userbot/code")
async def submit_userbot_code(
    code_data: UserbotLoginCode,
    current_admin: dict = Depends(get_current_admin)
):
    """步骤2：提交验证码"""
    login_mgr = get_account_login_manager()

    result = await login_mgr.submit_code(
        session_id=code_data.session_id,
        code=code_data.code
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    # 如果登录成功，保存账号到数据库
    if result['status'] == 'success':
        account_mgr = get_account_manager()
        user_info = result['user_info']

        save_result = await account_mgr.add_userbot_account(
            session_string=result['session_string'],
            session_type='pyrogram'
        )

        return {
            "success": True,
            "status": "success",
            "user_info": user_info,
            "account_id": save_result.get('account_id')
        }

    return result


@app.post("/api/accounts/userbot/password")
async def submit_userbot_password(
    password_data: UserbotLoginPassword,
    current_admin: dict = Depends(get_current_admin)
):
    """步骤3：提交二次密码"""
    login_mgr = get_account_login_manager()

    result = await login_mgr.submit_password(
        session_id=password_data.session_id,
        password=password_data.password
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    # 如果登录成功，保存账号
    if result['status'] == 'success':
        account_mgr = get_account_manager()
        user_info = result['user_info']

        save_result = await account_mgr.add_userbot_account(
            session_string=result['session_string'],
            session_type='pyrogram'
        )

        return {
            "success": True,
            "status": "success",
            "user_info": user_info,
            "account_id": save_result.get('account_id')
        }

    return result


@app.delete("/api/accounts/{account_id}")
async def remove_account(
    account_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """删除账号"""
    account_mgr = get_account_manager()
    await account_mgr.remove_account(account_id)

    return {"success": True, "message": "账号已删除"}


# -------------------- 会话管理 --------------------

@app.get("/api/conversations")
async def get_conversations(
    status: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin)
):
    """获取会话列表"""
    query = {}

    if status:
        query['status'] = status

    conversations = await db['conversations'].find(query).sort("updated_at", -1).limit(100).to_list(None)

    return [
        {
            "id": str(conv['_id']),
            "user_id": conv['user_id'],
            "username": conv.get('username'),
            "first_name": conv.get('first_name'),
            "last_name": conv.get('last_name'),
            "status": conv['status'],
            "assigned_agent_name": conv.get('assigned_agent_name'),
            "message_count": conv.get('message_count', 0),
            "unread_count": conv.get('unread_count', 0),
            "last_message_at": conv.get('last_message_at'),
            "last_message_preview": conv.get('last_message_preview'),
            "tags": conv.get('tags', []),
            "locked_by": str(conv['locked_by']) if conv.get('locked_by') else None,
            "created_at": conv.get('created_at'),
            # SafeLine 安全字段
            "security_score": conv.get('security_score', 100),
            "risk_level": conv.get('risk_level', 'safe'),
            "risk_factors": conv.get('risk_factors', [])
        }
        for conv in conversations
    ]


@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """获取会话的所有消息"""
    messages = await db['messages'].find(
        {"conversation_id": ObjectId(conversation_id)}
    ).sort("created_at", 1).to_list(None)

    # 标记为已读
    await db['messages'].update_many(
        {"conversation_id": ObjectId(conversation_id), "is_read": False},
        {"$set": {"is_read": True}}
    )

    # 更新会话未读数
    await db['conversations'].update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {"unread_count": 0}}
    )

    return [
        {
            "id": str(msg['_id']),
            "direction": msg['direction'],
            "from_user_id": msg.get('from_user_id'),
            "from_username": msg.get('from_username'),
            "from_type": msg.get('from_type'),
            "content_type": msg['content_type'],
            "text": msg.get('text'),
            "media": msg.get('media'),
            "is_read": msg.get('is_read', False),
            "created_at": msg.get('created_at'),
            # SafeLine 威胁检测字段
            "threat_detected": msg.get('threat_detected', False),
            "threat_level": msg.get('threat_level'),
            "threat_reason": msg.get('threat_reason')
        }
        for msg in messages
    ]


@app.post("/api/conversations/{conversation_id}/send")
async def send_message_to_user(
    conversation_id: str,
    message: SendMessage,
    current_admin: dict = Depends(get_current_admin)
):
    """发送消息给用户"""
    msg_processor = get_message_processor()

    result = await msg_processor.handle_agent_message(
        conversation_id=conversation_id,
        agent_id=str(current_admin['_id']),
        agent_name=current_admin['nickname'],
        content_type=message.content_type,
        text=message.text,
        media=message.media
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@app.post("/api/conversations/{conversation_id}/lock")
async def lock_conversation(
    conversation_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """锁定会话"""
    msg_processor = get_message_processor()

    result = await msg_processor.lock_conversation(
        conversation_id=conversation_id,
        agent_id=str(current_admin['_id'])
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@app.post("/api/conversations/{conversation_id}/unlock")
async def unlock_conversation(
    conversation_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """解锁会话"""
    msg_processor = get_message_processor()

    result = await msg_processor.unlock_conversation(
        conversation_id=conversation_id,
        agent_id=str(current_admin['_id'])
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


# -------------------- 关键词管理 --------------------

@app.get("/api/keywords")
async def get_keywords(current_admin: dict = Depends(get_current_admin)):
    """获取所有关键词"""
    keywords = await db['keywords'].find().to_list(None)

    return [
        {
            "id": str(kw['_id']),
            "keyword": kw['keyword'],
            "match_type": kw['match_type'],
            "enabled": kw['enabled'],
            "action": kw['action'],
            "trigger_count": kw.get('trigger_count', 0),
            "last_triggered_at": kw.get('last_triggered_at'),
            "created_at": kw.get('created_at')
        }
        for kw in keywords
    ]


@app.post("/api/keywords")
async def create_keyword(
    keyword_data: KeywordCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """创建关键词"""
    keyword = {
        "keyword": keyword_data.keyword,
        "match_type": keyword_data.match_type,
        "enabled": keyword_data.enabled,
        "action": keyword_data.action,
        "trigger_count": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = await db['keywords'].insert_one(keyword)

    return {
        "success": True,
        "keyword_id": str(result.inserted_id)
    }


@app.put("/api/keywords/{keyword_id}")
async def update_keyword(
    keyword_id: str,
    keyword_data: KeywordCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """更新关键词"""
    await db['keywords'].update_one(
        {"_id": ObjectId(keyword_id)},
        {
            "$set": {
                "keyword": keyword_data.keyword,
                "match_type": keyword_data.match_type,
                "enabled": keyword_data.enabled,
                "action": keyword_data.action,
                "updated_at": datetime.now()
            }
        }
    )

    return {"success": True}


@app.delete("/api/keywords/{keyword_id}")
async def delete_keyword(
    keyword_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """删除关键词"""
    await db['keywords'].delete_one({"_id": ObjectId(keyword_id)})

    return {"success": True}


# -------------------- 快捷回复 --------------------

@app.get("/api/quick_replies")
async def get_quick_replies(current_admin: dict = Depends(get_current_admin)):
    """获取所有快捷回复"""
    replies = await db['quick_replies'].find().to_list(None)

    return [
        {
            "id": str(reply['_id']),
            "title": reply['title'],
            "shortcut": reply['shortcut'],
            "content": reply['content'],
            "media": reply.get('media', []),
            "category": reply.get('category'),
            "usage_count": reply.get('usage_count', 0)
        }
        for reply in replies
    ]


@app.post("/api/quick_replies")
async def create_quick_reply(
    reply_data: QuickReplyCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """创建快捷回复"""
    reply = {
        "title": reply_data.title,
        "shortcut": reply_data.shortcut,
        "content": reply_data.content,
        "media": reply_data.media,
        "category": reply_data.category,
        "usage_count": 0,
        "created_by": current_admin['_id'],
        "created_at": datetime.now()
    }

    result = await db['quick_replies'].insert_one(reply)

    return {
        "success": True,
        "reply_id": str(result.inserted_id)
    }


# -------------------- WebSocket (实时通信) --------------------

@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket 连接（用于实时推送消息）

    功能:
    - 实时消息推送（用户 → 客服）
    - 会话管理（加入/离开会话房间）
    - 会话锁定（防止多客服同时回复）
    - 安全事件推送
    - 统计数据更新
    - 心跳保活

    Args:
        agent_id: 客服 ID
    """
    await handle_websocket(websocket, agent_id)


@app.get("/ws/stats")
async def get_websocket_stats():
    """获取 WebSocket 连接统计"""
    manager = get_connection_manager()

    return {
        "online_agents": manager.get_online_agents(),
        "online_count": manager.get_agent_count(),
        "active_conversations": len(manager.conversation_rooms),
        "locked_conversations": len(manager.conversation_locks)
    }


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn

    # 从环境变量读取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # 开发模式
        log_level="info"
    )
