# -*- coding: utf-8 -*-
"""
Telegram 账号管理器
支持 Bot Token 和 Userbot (Pyrogram/Telethon) 混合管理
"""
import asyncio
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
import itertools

from pyrogram import Client
from pyrogram.errors import (
    AuthKeyUnregistered, UserDeactivatedBan,
    SessionRevoked, FloodWait
)
from telegram import Bot
from telegram.error import InvalidToken, NetworkError

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class AccountManager:
    """统一管理 Bot Token 和 Userbot 账号"""

    def __init__(self, mongo_uri: str):
        self.mongo_client = AsyncIOMotorClient(mongo_uri)
        self.db = self.mongo_client['telegram_customer']
        self.accounts_collection = self.db['accounts']

        # 活跃的客户端实例
        self.bot_clients: Dict[str, Bot] = {}  # account_id -> Bot
        self.userbot_clients: Dict[str, Client] = {}  # account_id -> Client

        # 账号池循环器（负载均衡）
        self.bot_pool = []
        self.userbot_pool = []
        self.bot_cycler = None
        self.userbot_cycler = None

        logger.info("账号管理器初始化完成")

    async def load_accounts(self):
        """从数据库加载所有可用账号"""
        accounts = await self.accounts_collection.find({"status": 1}).to_list(None)

        bot_accounts = [acc for acc in accounts if acc['type'] == 'bot']
        userbot_accounts = [acc for acc in accounts if acc['type'] == 'userbot']

        logger.info(f"加载账号: {len(bot_accounts)} 个 Bot, {len(userbot_accounts)} 个 Userbot")

        # 初始化 Bot 客户端
        for acc in bot_accounts:
            try:
                bot = Bot(token=acc['bot_token'])
                await bot.initialize()
                bot_info = await bot.get_me()

                self.bot_clients[str(acc['_id'])] = bot
                self.bot_pool.append(str(acc['_id']))

                # 更新数据库状态
                await self.accounts_collection.update_one(
                    {"_id": acc['_id']},
                    {
                        "$set": {
                            "bot_username": bot_info.username,
                            "is_online": True,
                            "last_check_at": datetime.now()
                        }
                    }
                )

                logger.info(f"✅ Bot @{bot_info.username} 已连接")

            except InvalidToken:
                logger.error(f"❌ Bot Token 无效: {acc.get('bot_token', '')[:20]}...")
                await self._mark_account_error(acc['_id'], "Invalid token")
            except Exception as e:
                logger.error(f"❌ Bot 初始化失败: {e}")
                await self._mark_account_error(acc['_id'], str(e))

        # 初始化 Userbot 客户端（Pyrogram）
        for acc in userbot_accounts:
            try:
                # 支持 Pyrogram 和 Telethon session
                if acc['session_type'] == 'pyrogram':
                    client = Client(
                        name=f"userbot_{acc['tg_id']}",
                        api_id=acc.get('api_id', 6),
                        api_hash=acc.get('api_hash', 'eb06d4abfb49dc3eeb1aeb98ae0f581e'),
                        session_string=acc['session_string'],
                        device_model=acc.get('device_model', 'PC'),
                        system_version=acc.get('system_version', 'Windows 10'),
                        app_version=acc.get('app_version', '4.9.1'),
                        lang_code=acc.get('lang_code', 'zh-hans'),
                        proxy=self._parse_proxy(acc.get('proxy'))
                    )

                    await client.start()
                    me = await client.get_me()

                    self.userbot_clients[str(acc['_id'])] = client
                    self.userbot_pool.append(str(acc['_id']))

                    # 取消敏感内容限制
                    try:
                        from pyrogram import raw
                        await client.invoke(
                            raw.functions.account.SetContentSettings(
                                sensitive_enabled=True
                            )
                        )
                    except:
                        pass

                    # 更新数据库状态
                    await self.accounts_collection.update_one(
                        {"_id": acc['_id']},
                        {
                            "$set": {
                                "username": me.username,
                                "first_name": me.first_name,
                                "is_online": True,
                                "last_check_at": datetime.now()
                            }
                        }
                    )

                    logger.info(f"✅ Userbot @{me.username} (ID: {me.id}) 已连接")

            except (AuthKeyUnregistered, UserDeactivatedBan, SessionRevoked) as e:
                logger.error(f"❌ Userbot 账号已失效: {acc['tg_id']}")
                await self.accounts_collection.update_one(
                    {"_id": acc['_id']},
                    {"$set": {"status": 0, "last_error": str(e)}}
                )
            except Exception as e:
                logger.error(f"❌ Userbot 初始化失败: {e}")
                await self._mark_account_error(acc['_id'], str(e))

        # 初始化循环器（负载均衡）
        if self.bot_pool:
            self.bot_cycler = itertools.cycle(self.bot_pool)
            logger.info(f"Bot 池已就绪: {len(self.bot_pool)} 个账号")

        if self.userbot_pool:
            self.userbot_cycler = itertools.cycle(self.userbot_pool)
            logger.info(f"Userbot 池已就绪: {len(self.userbot_pool)} 个账号")

    def _parse_proxy(self, proxy_config: Optional[dict]) -> Optional[dict]:
        """解析代理配置"""
        if not proxy_config or not proxy_config.get('enabled'):
            return None

        return {
            'scheme': proxy_config['type'],  # socks5 or http
            'hostname': proxy_config['host'],
            'port': proxy_config['port'],
            'username': proxy_config.get('username'),
            'password': proxy_config.get('password')
        }

    async def _mark_account_error(self, account_id, error_msg: str):
        """标记账号错误"""
        await self.accounts_collection.update_one(
            {"_id": account_id},
            {
                "$set": {
                    "is_online": False,
                    "last_error": error_msg,
                    "last_check_at": datetime.now()
                },
                "$inc": {"error_count": 1}
            }
        )

    def get_next_bot(self) -> Optional[Bot]:
        """获取下一个可用的 Bot（轮询）"""
        if not self.bot_cycler:
            logger.warning("没有可用的 Bot 账号")
            return None

        account_id = next(self.bot_cycler)
        return self.bot_clients.get(account_id)

    def get_next_userbot(self) -> Optional[Client]:
        """获取下一个可用的 Userbot（轮询）"""
        if not self.userbot_cycler:
            logger.warning("没有可用的 Userbot 账号")
            return None

        account_id = next(self.userbot_cycler)
        return self.userbot_clients.get(account_id)

    def get_bot_by_id(self, account_id: str) -> Optional[Bot]:
        """根据 ID 获取 Bot"""
        return self.bot_clients.get(account_id)

    def get_userbot_by_id(self, account_id: str) -> Optional[Client]:
        """根据 ID 获取 Userbot"""
        return self.userbot_clients.get(account_id)

    async def health_check(self):
        """健康检查：检测所有账号状态"""
        logger.info("开始健康检查...")

        # 检查 Bot
        for account_id, bot in self.bot_clients.items():
            try:
                await bot.get_me()
                await self.accounts_collection.update_one(
                    {"_id": account_id},
                    {
                        "$set": {
                            "is_online": True,
                            "last_check_at": datetime.now(),
                            "error_count": 0
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Bot 健康检查失败 ({account_id}): {e}")
                await self._mark_account_error(account_id, str(e))

        # 检查 Userbot
        for account_id, client in self.userbot_clients.items():
            try:
                await client.get_me()
                await self.accounts_collection.update_one(
                    {"_id": account_id},
                    {
                        "$set": {
                            "is_online": True,
                            "last_check_at": datetime.now(),
                            "error_count": 0
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Userbot 健康检查失败 ({account_id}): {e}")
                await self._mark_account_error(account_id, str(e))

        logger.info("健康检查完成")

    async def add_bot_account(self, bot_token: str) -> dict:
        """添加新的 Bot 账号"""
        try:
            bot = Bot(token=bot_token)
            await bot.initialize()
            bot_info = await bot.get_me()

            # 保存到数据库
            account = {
                "type": "bot",
                "status": 1,
                "bot_token": bot_token,
                "bot_username": bot_info.username,
                "is_online": True,
                "created_at": datetime.now(),
                "last_check_at": datetime.now()
            }

            result = await self.accounts_collection.insert_one(account)
            account_id = str(result.inserted_id)

            # 添加到客户端池
            self.bot_clients[account_id] = bot
            self.bot_pool.append(account_id)
            self.bot_cycler = itertools.cycle(self.bot_pool)

            logger.info(f"✅ 新增 Bot: @{bot_info.username}")

            return {
                "success": True,
                "account_id": account_id,
                "username": bot_info.username
            }

        except InvalidToken:
            return {"success": False, "error": "Bot Token 无效"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def add_userbot_account(
        self,
        session_string: str,
        session_type: str = "pyrogram",
        api_id: int = 6,
        api_hash: str = "eb06d4abfb49dc3eeb1aeb98ae0f581e",
        proxy: Optional[dict] = None
    ) -> dict:
        """添加新的 Userbot 账号"""
        try:
            client = Client(
                name=f"temp_{datetime.now().timestamp()}",
                api_id=api_id,
                api_hash=api_hash,
                session_string=session_string,
                proxy=self._parse_proxy(proxy)
            )

            await client.start()
            me = await client.get_me()

            # 保存到数据库
            account = {
                "type": "userbot",
                "status": 1,
                "tg_id": me.id,
                "phone": me.phone_number,
                "username": me.username,
                "first_name": me.first_name,
                "session_string": session_string,
                "session_type": session_type,
                "api_id": api_id,
                "api_hash": api_hash,
                "proxy": proxy,
                "is_online": True,
                "created_at": datetime.now(),
                "last_check_at": datetime.now()
            }

            result = await self.accounts_collection.insert_one(account)
            account_id = str(result.inserted_id)

            # 添加到客户端池
            self.userbot_clients[account_id] = client
            self.userbot_pool.append(account_id)
            self.userbot_cycler = itertools.cycle(self.userbot_pool)

            logger.info(f"✅ 新增 Userbot: @{me.username} (ID: {me.id})")

            return {
                "success": True,
                "account_id": account_id,
                "username": me.username,
                "tg_id": me.id
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def remove_account(self, account_id: str):
        """移除账号"""
        # 停止客户端
        if account_id in self.bot_clients:
            # Bot 不需要特别停止
            del self.bot_clients[account_id]
            self.bot_pool.remove(account_id)
            self.bot_cycler = itertools.cycle(self.bot_pool) if self.bot_pool else None

        if account_id in self.userbot_clients:
            client = self.userbot_clients[account_id]
            await client.stop()
            del self.userbot_clients[account_id]
            self.userbot_pool.remove(account_id)
            self.userbot_cycler = itertools.cycle(self.userbot_pool) if self.userbot_pool else None

        # 从数据库删除
        await self.accounts_collection.delete_one({"_id": account_id})

        logger.info(f"账号已移除: {account_id}")

    async def close_all(self):
        """关闭所有连接"""
        logger.info("正在关闭所有连接...")

        # 停止所有 Userbot
        for client in self.userbot_clients.values():
            try:
                await client.stop()
            except:
                pass

        # Bot 不需要特别停止

        self.mongo_client.close()
        logger.info("所有连接已关闭")


# 全局单例
account_manager: Optional[AccountManager] = None


def get_account_manager() -> AccountManager:
    """获取账号管理器实例"""
    global account_manager
    if account_manager is None:
        raise RuntimeError("账号管理器未初始化")
    return account_manager


async def init_account_manager(mongo_uri: str):
    """初始化账号管理器"""
    global account_manager
    account_manager = AccountManager(mongo_uri)
    await account_manager.load_accounts()
    return account_manager
