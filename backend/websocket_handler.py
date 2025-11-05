# -*- coding: utf-8 -*-
"""
WebSocket 处理器
用于实时消息推送和客服聊天
"""
import json
import logging
from typing import Dict, Set, Optional, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class WebSocketEvent(str, Enum):
    """WebSocket 事件类型"""
    # 消息事件
    NEW_MESSAGE = "new_message"
    MESSAGE_SENT = "message_sent"

    # 会话事件
    CONVERSATION_ASSIGNED = "conversation_assigned"
    CONVERSATION_CLOSED = "conversation_closed"
    SESSION_LOCKED = "session_locked"
    SESSION_UNLOCKED = "session_unlocked"

    # 安全事件
    SECURITY_ALERT = "security_alert"
    THREAT_DETECTED = "threat_detected"
    USER_BANNED = "user_banned"

    # 统计事件
    STATS_UPDATE = "stats_update"

    # 系统事件
    AGENT_STATUS = "agent_status"
    TYPING = "typing"

    # 心跳
    PING = "ping"
    PONG = "pong"


class ConnectionManager:
    """
    WebSocket 连接管理器
    支持多客服、多会话的实时通信
    """

    def __init__(self):
        # 所有活跃连接 {agent_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # 会话房间 {conversation_id: Set[agent_id]}
        self.conversation_rooms: Dict[str, Set[str]] = {}

        # 客服状态 {agent_id: {"status": "online/busy/away", "current_conversation": "xxx"}}
        self.agent_status: Dict[str, dict] = {}

        # 会话锁定状态 {conversation_id: agent_id}
        self.conversation_locks: Dict[str, str] = {}

    async def connect(self, agent_id: str, websocket: WebSocket):
        """
        建立 WebSocket 连接

        Args:
            agent_id: 客服 ID
            websocket: WebSocket 连接对象
        """
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.agent_status[agent_id] = {
            "status": "online",
            "current_conversation": None,
            "connected_at": datetime.now().isoformat()
        }

        logger.info(f"✅ 客服 {agent_id} 已连接 WebSocket")

        # 通知其他客服
        await self.broadcast_agent_status(agent_id, "online")

    async def disconnect(self, agent_id: str):
        """
        断开 WebSocket 连接

        Args:
            agent_id: 客服 ID
        """
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]

        # 从所有会话房间中移除
        for room_agents in self.conversation_rooms.values():
            room_agents.discard(agent_id)

        # 解锁该客服锁定的会话
        locked_conversations = [
            conv_id for conv_id, locked_agent in self.conversation_locks.items()
            if locked_agent == agent_id
        ]
        for conv_id in locked_conversations:
            await self.unlock_conversation(conv_id)

        # 更新状态
        if agent_id in self.agent_status:
            self.agent_status[agent_id]["status"] = "offline"

        logger.info(f"❌ 客服 {agent_id} 已断开 WebSocket")

        # 通知其他客服
        await self.broadcast_agent_status(agent_id, "offline")

    async def join_conversation(self, agent_id: str, conversation_id: str):
        """
        客服加入会话房间

        Args:
            agent_id: 客服 ID
            conversation_id: 会话 ID
        """
        if conversation_id not in self.conversation_rooms:
            self.conversation_rooms[conversation_id] = set()

        self.conversation_rooms[conversation_id].add(agent_id)

        if agent_id in self.agent_status:
            self.agent_status[agent_id]["current_conversation"] = conversation_id

        logger.info(f"客服 {agent_id} 加入会话 {conversation_id}")

    async def leave_conversation(self, agent_id: str, conversation_id: str):
        """
        客服离开会话房间

        Args:
            agent_id: 客服 ID
            conversation_id: 会话 ID
        """
        if conversation_id in self.conversation_rooms:
            self.conversation_rooms[conversation_id].discard(agent_id)

            # 如果房间为空，删除房间
            if not self.conversation_rooms[conversation_id]:
                del self.conversation_rooms[conversation_id]

        if agent_id in self.agent_status:
            self.agent_status[agent_id]["current_conversation"] = None

        logger.info(f"客服 {agent_id} 离开会话 {conversation_id}")

    async def lock_conversation(self, conversation_id: str, agent_id: str):
        """
        锁定会话（表示某个客服正在回复）

        Args:
            conversation_id: 会话 ID
            agent_id: 客服 ID
        """
        self.conversation_locks[conversation_id] = agent_id

        # 通知会话房间内的其他客服
        await self.send_to_conversation(
            conversation_id,
            WebSocketEvent.SESSION_LOCKED,
            {
                "conversation_id": conversation_id,
                "locked_by": agent_id,
                "message": f"客服 {agent_id} 正在回复..."
            },
            exclude_agent=agent_id
        )

        logger.info(f"🔒 会话 {conversation_id} 已被客服 {agent_id} 锁定")

    async def unlock_conversation(self, conversation_id: str):
        """
        解锁会话

        Args:
            conversation_id: 会话 ID
        """
        if conversation_id in self.conversation_locks:
            agent_id = self.conversation_locks[conversation_id]
            del self.conversation_locks[conversation_id]

            # 通知会话房间内的所有客服
            await self.send_to_conversation(
                conversation_id,
                WebSocketEvent.SESSION_UNLOCKED,
                {
                    "conversation_id": conversation_id,
                    "unlocked_by": agent_id
                }
            )

            logger.info(f"🔓 会话 {conversation_id} 已解锁")

    async def send_personal_message(
        self,
        agent_id: str,
        event: WebSocketEvent,
        data: dict
    ):
        """
        发送消息给指定客服

        Args:
            agent_id: 客服 ID
            event: 事件类型
            data: 数据
        """
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]
            message = {
                "event": event.value,
                "data": data,
                "timestamp": datetime.now().timestamp()
            }

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"发送消息给客服 {agent_id} 失败: {e}")
                await self.disconnect(agent_id)

    async def send_to_conversation(
        self,
        conversation_id: str,
        event: WebSocketEvent,
        data: dict,
        exclude_agent: Optional[str] = None
    ):
        """
        发送消息给会话房间内的所有客服

        Args:
            conversation_id: 会话 ID
            event: 事件类型
            data: 数据
            exclude_agent: 排除的客服 ID（不发送给该客服）
        """
        if conversation_id not in self.conversation_rooms:
            return

        agents = self.conversation_rooms[conversation_id]

        for agent_id in agents:
            if exclude_agent and agent_id == exclude_agent:
                continue

            await self.send_personal_message(agent_id, event, data)

    async def broadcast(
        self,
        event: WebSocketEvent,
        data: dict,
        exclude_agents: Optional[List[str]] = None
    ):
        """
        广播消息给所有在线客服

        Args:
            event: 事件类型
            data: 数据
            exclude_agents: 排除的客服 ID 列表
        """
        exclude_agents = exclude_agents or []

        for agent_id in list(self.active_connections.keys()):
            if agent_id not in exclude_agents:
                await self.send_personal_message(agent_id, event, data)

    async def broadcast_agent_status(self, agent_id: str, status: str):
        """
        广播客服状态变化

        Args:
            agent_id: 客服 ID
            status: 状态（online/busy/away/offline）
        """
        await self.broadcast(
            WebSocketEvent.AGENT_STATUS,
            {
                "agent_id": agent_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            exclude_agents=[agent_id]
        )

    async def broadcast_new_message(
        self,
        conversation_id: str,
        message_data: dict
    ):
        """
        广播新消息（来自用户）

        Args:
            conversation_id: 会话 ID
            message_data: 消息数据
        """
        # 发送给会话房间内的所有客服
        await self.send_to_conversation(
            conversation_id,
            WebSocketEvent.NEW_MESSAGE,
            message_data
        )

        # 如果没有客服在该会话中，广播给所有在线客服（新会话提醒）
        if conversation_id not in self.conversation_rooms or not self.conversation_rooms[conversation_id]:
            await self.broadcast(
                WebSocketEvent.NEW_MESSAGE,
                message_data
            )

    async def broadcast_security_alert(self, alert_data: dict):
        """
        广播安全告警

        Args:
            alert_data: 告警数据
        """
        await self.broadcast(
            WebSocketEvent.SECURITY_ALERT,
            alert_data
        )

    async def broadcast_threat_detected(self, threat_data: dict):
        """
        广播威胁检测事件

        Args:
            threat_data: 威胁数据
        """
        await self.broadcast(
            WebSocketEvent.THREAT_DETECTED,
            threat_data
        )

    async def broadcast_stats_update(self, stats_data: dict):
        """
        广播统计数据更新

        Args:
            stats_data: 统计数据
        """
        await self.broadcast(
            WebSocketEvent.STATS_UPDATE,
            stats_data
        )

    def get_online_agents(self) -> List[str]:
        """获取所有在线客服 ID"""
        return list(self.active_connections.keys())

    def get_agent_count(self) -> int:
        """获取在线客服数量"""
        return len(self.active_connections)

    def is_conversation_locked(self, conversation_id: str) -> bool:
        """检查会话是否被锁定"""
        return conversation_id in self.conversation_locks

    def get_conversation_lock_agent(self, conversation_id: str) -> Optional[str]:
        """获取锁定会话的客服 ID"""
        return self.conversation_locks.get(conversation_id)


# 全局 ConnectionManager 实例
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """获取全局 ConnectionManager 实例"""
    global _connection_manager

    if _connection_manager is None:
        _connection_manager = ConnectionManager()

    return _connection_manager


# ==================== WebSocket 处理函数 ====================

async def handle_websocket(websocket: WebSocket, agent_id: str):
    """
    处理 WebSocket 连接

    Args:
        websocket: WebSocket 连接对象
        agent_id: 客服 ID
    """
    manager = get_connection_manager()

    try:
        # 建立连接
        await manager.connect(agent_id, websocket)

        # 发送欢迎消息
        await manager.send_personal_message(
            agent_id,
            WebSocketEvent.AGENT_STATUS,
            {
                "message": "WebSocket 连接成功",
                "agent_id": agent_id,
                "online_agents": manager.get_online_agents()
            }
        )

        # 消息循环
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                event = message.get("event")
                payload = message.get("data", {})

                # 处理心跳
                if event == WebSocketEvent.PING.value:
                    await manager.send_personal_message(
                        agent_id,
                        WebSocketEvent.PONG,
                        {"timestamp": datetime.now().timestamp()}
                    )
                    continue

                # 处理加入会话
                elif event == "join_conversation":
                    conversation_id = payload.get("conversation_id")
                    if conversation_id:
                        await manager.join_conversation(agent_id, conversation_id)

                # 处理离开会话
                elif event == "leave_conversation":
                    conversation_id = payload.get("conversation_id")
                    if conversation_id:
                        await manager.leave_conversation(agent_id, conversation_id)

                # 处理锁定会话
                elif event == "lock_conversation":
                    conversation_id = payload.get("conversation_id")
                    if conversation_id:
                        await manager.lock_conversation(conversation_id, agent_id)

                # 处理解锁会话
                elif event == "unlock_conversation":
                    conversation_id = payload.get("conversation_id")
                    if conversation_id:
                        await manager.unlock_conversation(conversation_id)

                # 处理发送消息（客服 → 用户）
                elif event == "send_message":
                    # TODO: 调用 message_handler 发送消息到 Telegram
                    conversation_id = payload.get("conversation_id")
                    content = payload.get("content")

                    logger.info(f"客服 {agent_id} 向会话 {conversation_id} 发送消息: {content}")

                    # 确认消息已发送
                    await manager.send_personal_message(
                        agent_id,
                        WebSocketEvent.MESSAGE_SENT,
                        {
                            "conversation_id": conversation_id,
                            "content": content,
                            "sent_at": datetime.now().isoformat()
                        }
                    )

                # 处理正在输入
                elif event == "typing":
                    conversation_id = payload.get("conversation_id")
                    if conversation_id:
                        await manager.send_to_conversation(
                            conversation_id,
                            WebSocketEvent.TYPING,
                            {
                                "agent_id": agent_id,
                                "conversation_id": conversation_id
                            },
                            exclude_agent=agent_id
                        )

                else:
                    logger.warning(f"未知事件类型: {event}")

            except json.JSONDecodeError:
                logger.error(f"无效的 JSON 数据: {data}")
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")

    except WebSocketDisconnect:
        logger.info(f"客服 {agent_id} 主动断开连接")
        await manager.disconnect(agent_id)

    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
        await manager.disconnect(agent_id)


# ==================== 辅助函数（供其他模块调用）====================

async def notify_new_message(conversation_id: str, message_data: dict):
    """
    通知新消息（供 message_handler 调用）

    Args:
        conversation_id: 会话 ID
        message_data: 消息数据
    """
    manager = get_connection_manager()
    await manager.broadcast_new_message(conversation_id, message_data)


async def notify_security_alert(alert_data: dict):
    """
    通知安全告警（供防护模块调用）

    Args:
        alert_data: 告警数据
    """
    manager = get_connection_manager()
    await manager.broadcast_security_alert(alert_data)


async def notify_threat_detected(threat_data: dict):
    """
    通知威胁检测（供防护模块调用）

    Args:
        threat_data: 威胁数据
    """
    manager = get_connection_manager()
    await manager.broadcast_threat_detected(threat_data)


async def update_stats(stats_data: dict):
    """
    更新统计数据（供统计模块调用）

    Args:
        stats_data: 统计数据
    """
    manager = get_connection_manager()
    await manager.broadcast_stats_update(stats_data)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket 处理器测试")
    print("=" * 60)

    manager = get_connection_manager()

    print(f"\n在线客服数: {manager.get_agent_count()}")
    print(f"在线客服列表: {manager.get_online_agents()}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
