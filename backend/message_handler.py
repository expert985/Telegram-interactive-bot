# -*- coding: utf-8 -*-
"""
Telegram 消息处理器
处理双向消息转发、关键词监听、自动回复
"""
import asyncio
import logging
import re
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message as PyroMessage
from telegram import Update, Bot, Message as TelegramMessage
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters as tg_filters, ContextTypes
)

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from account_manager import get_account_manager

logger = logging.getLogger(__name__)


class MessageProcessor:
    """消息处理核心"""

    def __init__(self, mongo_uri: str, redis_client):
        self.mongo_client = AsyncIOMotorClient(mongo_uri)
        self.db = self.mongo_client['telegram_customer']
        self.redis = redis_client

        # Collections
        self.conversations = self.db['conversations']
        self.messages = self.db['messages']
        self.keywords = self.db['keywords']
        self.quick_replies = self.db['quick_replies']
        self.statistics = self.db['statistics']

        # WebSocket 连接池（用于实时推送到前端）
        self.ws_connections: Dict[str, list] = {}  # agent_id -> [websockets]

        logger.info("消息处理器初始化完成")

    # ==================== 用户消息处理 ====================

    async def handle_user_message(self, message: PyroMessage, client: Client):
        """
        处理用户发来的消息（通过 Userbot 监听或 Bot 接收）
        """
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else None
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""

        # 1. 查找或创建会话
        conversation = await self.conversations.find_one({"user_id": user_id})

        if not conversation:
            # 创建新会话
            conversation = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "status": "waiting",  # waiting | active | closed
                "assigned_agent_id": None,
                "assigned_agent_name": None,
                "message_count": 0,
                "unread_count": 0,
                "tags": [],
                "notes": "",
                "source": "direct",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            result = await self.conversations.insert_one(conversation)
            conversation['_id'] = result.inserted_id

            logger.info(f"创建新会话: User {user_id} ({username})")

        # 2. 保存消息到数据库
        message_doc = await self._save_message(
            conversation_id=conversation['_id'],
            direction="incoming",
            from_user_id=user_id,
            from_username=username,
            from_type="user",
            content_type=self._get_content_type(message),
            text=message.text or message.caption,
            media=await self._extract_media(message),
            tg_message_id=message.id,
            chat_id=message.chat.id
        )

        # 3. 更新会话统计
        await self.conversations.update_one(
            {"_id": conversation['_id']},
            {
                "$inc": {"message_count": 1, "unread_count": 1},
                "$set": {
                    "last_message_at": datetime.now(),
                    "last_message_preview": message.text[:50] if message.text else "[媒体消息]",
                    "updated_at": datetime.now()
                }
            }
        )

        # 4. 检查关键词触发
        if message.text:
            await self._check_keywords(message, conversation)

        # 5. WebSocket 推送到前端（实时通知客服）
        await self._push_to_frontend(conversation, message_doc)

        logger.info(f"处理用户消息: {user_id} -> {message.text[:30] if message.text else '[媒体]'}")

    # ==================== 客服消息处理 ====================

    async def handle_agent_message(
        self,
        conversation_id: str,
        agent_id: str,
        agent_name: str,
        content_type: str,
        text: Optional[str] = None,
        media: Optional[dict] = None
    ) -> dict:
        """
        处理客服发送的消息（从 Web 后台）
        """
        # 1. 获取会话信息
        conversation = await self.conversations.find_one({"_id": ObjectId(conversation_id)})
        if not conversation:
            return {"success": False, "error": "会话不存在"}

        user_id = conversation['user_id']

        # 2. 获取可用的账号（优先使用 Bot，如果没有则用 Userbot）
        account_mgr = get_account_manager()
        bot = account_mgr.get_next_bot()
        userbot = None

        if not bot:
            userbot = account_mgr.get_next_userbot()
            if not userbot:
                return {"success": False, "error": "没有可用的发送账号"}

        # 3. 发送消息到 Telegram
        try:
            if bot:
                # 使用 Bot 发送
                if content_type == "text":
                    tg_message = await bot.send_message(
                        chat_id=user_id,
                        text=text
                    )
                elif content_type == "photo":
                    tg_message = await bot.send_photo(
                        chat_id=user_id,
                        photo=media['file_id'],
                        caption=text
                    )
                elif content_type == "video":
                    tg_message = await bot.send_video(
                        chat_id=user_id,
                        video=media['file_id'],
                        caption=text
                    )
                elif content_type == "document":
                    tg_message = await bot.send_document(
                        chat_id=user_id,
                        document=media['file_id'],
                        caption=text
                    )
                else:
                    return {"success": False, "error": f"不支持的消息类型: {content_type}"}

            else:
                # 使用 Userbot 发送
                if content_type == "text":
                    tg_message = await userbot.send_message(
                        chat_id=user_id,
                        text=text
                    )
                elif content_type == "photo":
                    tg_message = await userbot.send_photo(
                        chat_id=user_id,
                        photo=media['file_id'],
                        caption=text
                    )
                elif content_type == "video":
                    tg_message = await userbot.send_video(
                        chat_id=user_id,
                        video=media['file_id'],
                        caption=text
                    )
                elif content_type == "document":
                    tg_message = await userbot.send_document(
                        chat_id=user_id,
                        document=media['file_id'],
                        caption=text
                    )
                else:
                    return {"success": False, "error": f"不支持的消息类型: {content_type}"}

            # 4. 保存消息到数据库
            message_doc = await self._save_message(
                conversation_id=ObjectId(conversation_id),
                direction="outgoing",
                from_user_id=int(agent_id),
                from_username=agent_name,
                from_type="agent",
                to_user_id=user_id,
                to_type="user",
                content_type=content_type,
                text=text,
                media=media,
                tg_message_id=tg_message.id if hasattr(tg_message, 'id') else tg_message.message_id,
                chat_id=user_id
            )

            # 5. 更新会话
            await self.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "status": "active",
                        "assigned_agent_id": ObjectId(agent_id),
                        "assigned_agent_name": agent_name,
                        "last_message_at": datetime.now(),
                        "last_message_preview": text[:50] if text else "[媒体消息]",
                        "updated_at": datetime.now()
                    },
                    "$inc": {"message_count": 1}
                }
            )

            logger.info(f"客服消息已发送: {agent_name} -> User {user_id}")

            return {
                "success": True,
                "message_id": str(message_doc['_id']),
                "tg_message_id": tg_message.id if hasattr(tg_message, 'id') else tg_message.message_id
            }

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 关键词监听 ====================

    async def _check_keywords(self, message: PyroMessage, conversation: dict):
        """检查消息是否触发关键词"""
        if not message.text:
            return

        # 获取所有启用的关键词
        keywords = await self.keywords.find({"enabled": True}).to_list(None)

        for kw in keywords:
            keyword = kw['keyword']
            match_type = kw['match_type']

            # 匹配检测
            is_matched = False
            if match_type == "exact":
                is_matched = message.text.lower() == keyword.lower()
            elif match_type == "contains":
                is_matched = keyword.lower() in message.text.lower()
            elif match_type == "regex":
                is_matched = bool(re.search(keyword, message.text, re.IGNORECASE))

            if not is_matched:
                continue

            # 触发关键词动作
            action = kw['action']
            logger.info(f"关键词触发: '{keyword}' by User {message.from_user.id}")

            # 更新触发统计
            await self.keywords.update_one(
                {"_id": kw['_id']},
                {
                    "$inc": {"trigger_count": 1},
                    "$set": {"last_triggered_at": datetime.now()}
                }
            )

            # 执行动作
            if action['type'] == 'auto_reply':
                # 自动回复
                reply_text = action['reply_text'].replace("{keyword}", keyword)

                account_mgr = get_account_manager()
                bot = account_mgr.get_next_bot()

                if bot:
                    try:
                        await bot.send_message(
                            chat_id=message.from_user.id,
                            text=reply_text
                        )
                        logger.info(f"自动回复已发送: {keyword}")
                    except Exception as e:
                        logger.error(f"自动回复失败: {e}")

            # 自动私信
            if action.get('auto_dm'):
                dm_message = action['dm_message'].replace("{keyword}", keyword)

                account_mgr = get_account_manager()
                userbot = account_mgr.get_next_userbot()

                if userbot:
                    try:
                        await userbot.send_message(
                            chat_id=message.from_user.id,
                            text=dm_message
                        )
                        logger.info(f"自动私信已发送: {keyword}")
                    except Exception as e:
                        logger.error(f"自动私信失败: {e}")

            # 通知客服
            if action.get('notify_agents'):
                await self._push_keyword_alert(kw, message, conversation)

    # ==================== 会话锁定 ====================

    async def lock_conversation(self, conversation_id: str, agent_id: str, duration: int = 300) -> dict:
        """
        锁定会话（防止多个客服同时回复）
        duration: 锁定时长（秒），默认 5 分钟
        """
        conversation = await self.conversations.find_one({"_id": ObjectId(conversation_id)})

        if not conversation:
            return {"success": False, "error": "会话不存在"}

        # 检查是否已被其他客服锁定
        if conversation.get('locked_by') and conversation.get('lock_expires_at'):
            if conversation['lock_expires_at'] > datetime.now():
                if str(conversation['locked_by']) != agent_id:
                    return {
                        "success": False,
                        "error": f"会话已被 {conversation.get('locked_by_name', '其他客服')} 锁定"
                    }

        # 锁定会话
        lock_expires_at = datetime.now() + timedelta(seconds=duration)

        await self.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$set": {
                    "locked_by": ObjectId(agent_id),
                    "locked_at": datetime.now(),
                    "lock_expires_at": lock_expires_at
                }
            }
        )

        logger.info(f"会话已锁定: {conversation_id} by {agent_id}")

        return {"success": True, "lock_expires_at": lock_expires_at}

    async def unlock_conversation(self, conversation_id: str, agent_id: str) -> dict:
        """解锁会话"""
        conversation = await self.conversations.find_one({"_id": ObjectId(conversation_id)})

        if not conversation:
            return {"success": False, "error": "会话不存在"}

        # 只有锁定者可以解锁
        if conversation.get('locked_by') and str(conversation['locked_by']) != agent_id:
            return {"success": False, "error": "无权解锁"}

        await self.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$unset": {
                    "locked_by": "",
                    "locked_at": "",
                    "lock_expires_at": ""
                }
            }
        )

        logger.info(f"会话已解锁: {conversation_id}")

        return {"success": True}

    # ==================== 辅助方法 ====================

    async def _save_message(self, **kwargs) -> dict:
        """保存消息到数据库"""
        message_doc = {
            "conversation_id": kwargs.get('conversation_id'),
            "direction": kwargs.get('direction'),
            "from_user_id": kwargs.get('from_user_id'),
            "from_username": kwargs.get('from_username'),
            "from_type": kwargs.get('from_type'),
            "to_user_id": kwargs.get('to_user_id'),
            "to_type": kwargs.get('to_type'),
            "content_type": kwargs.get('content_type'),
            "text": kwargs.get('text'),
            "caption": kwargs.get('caption'),
            "media": kwargs.get('media'),
            "tg_message_id": kwargs.get('tg_message_id'),
            "chat_id": kwargs.get('chat_id'),
            "reply_to_message_id": kwargs.get('reply_to_message_id'),
            "is_read": False,
            "is_deleted": False,
            "sent_via_account_id": kwargs.get('sent_via_account_id'),
            "created_at": datetime.now()
        }

        result = await self.messages.insert_one(message_doc)
        message_doc['_id'] = result.inserted_id

        return message_doc

    def _get_content_type(self, message: PyroMessage) -> str:
        """获取消息类型"""
        if message.text:
            return "text"
        elif message.photo:
            return "photo"
        elif message.video:
            return "video"
        elif message.document:
            return "document"
        elif message.voice:
            return "voice"
        elif message.sticker:
            return "sticker"
        else:
            return "unknown"

    async def _extract_media(self, message: PyroMessage) -> Optional[dict]:
        """提取媒体信息"""
        if message.photo:
            return {
                "file_id": message.photo.file_id,
                "file_unique_id": message.photo.file_unique_id,
                "file_size": message.photo.file_size,
                "width": message.photo.width,
                "height": message.photo.height
            }
        elif message.video:
            return {
                "file_id": message.video.file_id,
                "file_unique_id": message.video.file_unique_id,
                "file_size": message.video.file_size,
                "duration": message.video.duration,
                "width": message.video.width,
                "height": message.video.height
            }
        elif message.document:
            return {
                "file_id": message.document.file_id,
                "file_unique_id": message.document.file_unique_id,
                "file_size": message.document.file_size,
                "file_name": message.document.file_name,
                "mime_type": message.document.mime_type
            }
        elif message.voice:
            return {
                "file_id": message.voice.file_id,
                "file_unique_id": message.voice.file_unique_id,
                "file_size": message.voice.file_size,
                "duration": message.voice.duration
            }

        return None

    async def _push_to_frontend(self, conversation: dict, message_doc: dict):
        """推送消息到前端 WebSocket"""
        # TODO: 实现 WebSocket 推送
        pass

    async def _push_keyword_alert(self, keyword: dict, message: PyroMessage, conversation: dict):
        """推送关键词触发提醒到前端"""
        # TODO: 实现 WebSocket 推送
        pass


# 全局单例
message_processor: Optional[MessageProcessor] = None


def get_message_processor() -> MessageProcessor:
    """获取消息处理器实例"""
    global message_processor
    if message_processor is None:
        raise RuntimeError("消息处理器未初始化")
    return message_processor


async def init_message_processor(mongo_uri: str, redis_client):
    """初始化消息处理器"""
    global message_processor
    message_processor = MessageProcessor(mongo_uri, redis_client)
    return message_processor
