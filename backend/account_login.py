# -*- coding: utf-8 -*-
"""
Telegram 账号交互式登录模块
支持手机号 + 验证码 + 二次密码 + 邮箱验证
"""
import asyncio
import logging
import uuid
from typing import Optional, Dict
from datetime import datetime, timedelta
import hashlib

from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded, PhoneCodeInvalid,
    PhoneCodeExpired, PhoneNumberInvalid,
    PasswordHashInvalid
)

logger = logging.getLogger(__name__)


class LoginSession:
    """登录会话（保存登录状态）"""

    def __init__(self, session_id: str, phone: str):
        self.session_id = session_id
        self.phone = phone
        self.client: Optional[Client] = None
        self.phone_code_hash: Optional[str] = None
        self.status = "phone_sent"  # phone_sent | code_required | password_required | email_required | success | error
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(minutes=10)  # 10分钟过期

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


class AccountLoginManager:
    """账号登录管理器"""

    def __init__(self):
        # 存储活跃的登录会话
        self.login_sessions: Dict[str, LoginSession] = {}

        # 默认 API 凭证
        self.default_api_id = 6
        self.default_api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"

        logger.info("账号登录管理器初始化完成")

    async def start_login(
        self,
        phone: str,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        proxy: Optional[dict] = None
    ) -> dict:
        """
        步骤 1: 开始登录 - 发送验证码到手机

        Returns:
            {
                "success": True,
                "session_id": "uuid",
                "status": "code_required",
                "message": "验证码已发送到您的手机"
            }
        """
        # 清理过期会话
        self._cleanup_expired_sessions()

        # 生成唯一会话 ID
        session_id = str(uuid.uuid4())

        # 使用默认或自定义 API 凭证
        api_id = api_id or self.default_api_id
        api_hash = api_hash or self.default_api_hash

        try:
            # 创建 Pyrogram 客户端（使用内存会话）
            client = Client(
                name=f"login_{session_id}",
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone,
                in_memory=True,  # 不保存到文件
                proxy=self._parse_proxy(proxy)
            )

            await client.connect()

            # 发送验证码
            sent_code = await client.send_code(phone)

            # 创建登录会话
            login_session = LoginSession(session_id, phone)
            login_session.client = client
            login_session.phone_code_hash = sent_code.phone_code_hash
            login_session.status = "code_required"

            self.login_sessions[session_id] = login_session

            logger.info(f"验证码已发送: {phone} (Session: {session_id})")

            return {
                "success": True,
                "session_id": session_id,
                "status": "code_required",
                "message": f"验证码已发送到 {phone}"
            }

        except PhoneNumberInvalid:
            return {
                "success": False,
                "error": "手机号格式错误，请使用国际格式（如 +8613800138000）"
            }
        except Exception as e:
            logger.error(f"发送验证码失败: {e}")
            return {
                "success": False,
                "error": f"发送验证码失败: {str(e)}"
            }

    async def submit_code(self, session_id: str, code: str) -> dict:
        """
        步骤 2: 提交验证码

        Returns:
            成功（无二次密码）:
            {
                "success": True,
                "status": "success",
                "session_string": "xxx",
                "user_info": {...}
            }

            需要二次密码:
            {
                "success": True,
                "status": "password_required",
                "hint": "密码提示"
            }

            需要邮箱验证:
            {
                "success": True,
                "status": "email_required",
                "email_pattern": "a**@example.com"
            }
        """
        login_session = self.login_sessions.get(session_id)

        if not login_session:
            return {
                "success": False,
                "error": "会话不存在或已过期，请重新开始"
            }

        if login_session.is_expired():
            del self.login_sessions[session_id]
            return {
                "success": False,
                "error": "会话已过期，请重新开始"
            }

        client = login_session.client
        phone = login_session.phone
        phone_code_hash = login_session.phone_code_hash

        try:
            # 提交验证码
            await client.sign_in(phone, phone_code_hash, code)

            # 登录成功！获取用户信息
            me = await client.get_me()

            # 导出 session string
            session_string = await client.export_session_string()

            await client.disconnect()

            # 清理会话
            del self.login_sessions[session_id]

            logger.info(f"登录成功: @{me.username} (ID: {me.id})")

            return {
                "success": True,
                "status": "success",
                "session_string": session_string,
                "user_info": {
                    "id": me.id,
                    "username": me.username,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "phone": me.phone_number,
                    "is_premium": me.is_premium
                }
            }

        except SessionPasswordNeeded:
            # 需要二次验证密码
            login_session.status = "password_required"

            # 获取密码提示
            try:
                password_info = await client.get_password_hint()
                hint = password_info or "无提示"
            except:
                hint = "无提示"

            logger.info(f"需要二次密码: {phone}")

            return {
                "success": True,
                "status": "password_required",
                "message": "需要输入二次验证密码",
                "hint": hint
            }

        except PhoneCodeInvalid:
            return {
                "success": False,
                "error": "验证码错误"
            }

        except PhoneCodeExpired:
            del self.login_sessions[session_id]
            return {
                "success": False,
                "error": "验证码已过期，请重新开始"
            }

        except Exception as e:
            logger.error(f"提交验证码失败: {e}")

            # 检查是否需要邮箱验证
            if "email" in str(e).lower():
                login_session.status = "email_required"
                return {
                    "success": True,
                    "status": "email_required",
                    "message": "需要邮箱验证码"
                }

            return {
                "success": False,
                "error": f"验证失败: {str(e)}"
            }

    async def submit_password(self, session_id: str, password: str) -> dict:
        """
        步骤 3: 提交二次验证密码（如果需要）

        Returns:
            {
                "success": True,
                "status": "success",
                "session_string": "xxx",
                "user_info": {...}
            }
        """
        login_session = self.login_sessions.get(session_id)

        if not login_session:
            return {
                "success": False,
                "error": "会话不存在或已过期"
            }

        if login_session.status != "password_required":
            return {
                "success": False,
                "error": "当前不需要输入密码"
            }

        client = login_session.client

        try:
            # 提交二次密码
            await client.check_password(password)

            # 登录成功！
            me = await client.get_me()
            session_string = await client.export_session_string()

            await client.disconnect()

            # 清理会话
            del self.login_sessions[session_id]

            logger.info(f"登录成功（二次密码）: @{me.username} (ID: {me.id})")

            return {
                "success": True,
                "status": "success",
                "session_string": session_string,
                "user_info": {
                    "id": me.id,
                    "username": me.username,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "phone": me.phone_number,
                    "is_premium": me.is_premium
                }
            }

        except PasswordHashInvalid:
            return {
                "success": False,
                "error": "密码错误"
            }

        except Exception as e:
            logger.error(f"提交密码失败: {e}")
            return {
                "success": False,
                "error": f"验证失败: {str(e)}"
            }

    async def submit_email_code(self, session_id: str, email_code: str) -> dict:
        """
        步骤 4: 提交邮箱验证码（如果需要）

        注意：Pyrogram 目前对邮箱验证支持有限，可能需要使用 Telethon
        """
        login_session = self.login_sessions.get(session_id)

        if not login_session:
            return {
                "success": False,
                "error": "会话不存在或已过期"
            }

        # TODO: 实现邮箱验证码逻辑
        # Pyrogram 原生不支持，需要使用 raw API 或切换到 Telethon

        return {
            "success": False,
            "error": "邮箱验证暂未实现，请使用 Telethon"
        }

    async def cancel_login(self, session_id: str) -> dict:
        """取消登录"""
        login_session = self.login_sessions.get(session_id)

        if not login_session:
            return {
                "success": False,
                "error": "会话不存在"
            }

        # 断开客户端
        if login_session.client:
            try:
                await login_session.client.disconnect()
            except:
                pass

        # 删除会话
        del self.login_sessions[session_id]

        logger.info(f"登录已取消: {session_id}")

        return {
            "success": True,
            "message": "登录已取消"
        }

    def _parse_proxy(self, proxy_config: Optional[dict]) -> Optional[dict]:
        """解析代理配置"""
        if not proxy_config or not proxy_config.get('enabled'):
            return None

        return {
            'scheme': proxy_config['type'],
            'hostname': proxy_config['host'],
            'port': proxy_config['port'],
            'username': proxy_config.get('username'),
            'password': proxy_config.get('password')
        }

    def _cleanup_expired_sessions(self):
        """清理过期的登录会话"""
        expired = [
            sid for sid, session in self.login_sessions.items()
            if session.is_expired()
        ]

        for sid in expired:
            session = self.login_sessions[sid]
            if session.client:
                try:
                    asyncio.create_task(session.client.disconnect())
                except:
                    pass

            del self.login_sessions[sid]
            logger.info(f"清理过期会话: {sid}")

    def get_session_status(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        login_session = self.login_sessions.get(session_id)

        if not login_session:
            return None

        return {
            "session_id": session_id,
            "phone": login_session.phone,
            "status": login_session.status,
            "error_message": login_session.error_message,
            "expires_at": login_session.expires_at.isoformat()
        }


# 全局单例
account_login_manager: Optional[AccountLoginManager] = None


def get_account_login_manager() -> AccountLoginManager:
    """获取账号登录管理器"""
    global account_login_manager
    if account_login_manager is None:
        account_login_manager = AccountLoginManager()
    return account_login_manager
