# -*- coding: utf-8 -*-
"""
TG 威胁情报监控系统
全局监控 Telegram 消息，收集威胁数据，构建威胁情报库
"""
import asyncio
import logging
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
from collections import defaultdict

from pyrogram import Client, filters
from pyrogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ==================== 威胁情报采集器 ====================

class ThreatIntelligenceCollector:
    """
    威胁情报采集器
    主动监控 TG 群组/频道消息，收集威胁数据
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

        # 监控的群组/频道列表
        self.monitored_chats: Set[int] = set()

        # 威胁数据缓存
        self.threat_cache = {
            'spam_users': set(),        # 垃圾用户集合
            'phishing_links': set(),     # 钓鱼链接集合
            'malicious_domains': set(),  # 恶意域名集合
            'suspicious_patterns': []    # 可疑模式列表
        }

        # 统计数据
        self.stats = {
            'messages_monitored': 0,
            'threats_detected': 0,
            'users_flagged': 0,
            'groups_monitored': 0
        }

    async def add_monitor_chat(self, chat_id: int, chat_type: str = 'group'):
        """
        添加监控的群组/频道

        Args:
            chat_id: 群组/频道 ID
            chat_type: 类型（group, channel, supergroup）
        """
        self.monitored_chats.add(chat_id)
        self.stats['groups_monitored'] = len(self.monitored_chats)

        logger.info(f"添加监控: Chat {chat_id} ({chat_type})")

        # 保存到数据库
        await self.db.execute("""
            INSERT INTO monitored_chats (chat_id, chat_type, added_at)
            VALUES (:chat_id, :chat_type, :added_at)
            ON DUPLICATE KEY UPDATE chat_type = :chat_type
        """, {
            'chat_id': chat_id,
            'chat_type': chat_type,
            'added_at': datetime.now()
        })
        await self.db.commit()

    async def remove_monitor_chat(self, chat_id: int):
        """移除监控"""
        if chat_id in self.monitored_chats:
            self.monitored_chats.remove(chat_id)
            self.stats['groups_monitored'] = len(self.monitored_chats)

            await self.db.execute("""
                DELETE FROM monitored_chats WHERE chat_id = :chat_id
            """, {'chat_id': chat_id})
            await self.db.commit()

            logger.info(f"移除监控: Chat {chat_id}")

    async def process_message(self, message: Message) -> Optional[dict]:
        """
        处理监控到的消息

        Returns:
            威胁信息（如果检测到）
        """
        self.stats['messages_monitored'] += 1

        # 只处理监控的群组
        if message.chat.id not in self.monitored_chats:
            return None

        threat_info = None

        # 1. 检测垃圾消息
        if await self._is_spam_message(message):
            threat_info = await self._record_spam_threat(message)

        # 2. 检测钓鱼链接
        elif await self._is_phishing_message(message):
            threat_info = await self._record_phishing_threat(message)

        # 3. 检测恶意用户行为
        elif await self._is_malicious_behavior(message):
            threat_info = await self._record_malicious_user(message)

        if threat_info:
            self.stats['threats_detected'] += 1
            logger.warning(f"[威胁情报] 检测到威胁: {threat_info['type']} | User {message.from_user.id}")

        return threat_info

    async def _is_spam_message(self, message: Message) -> bool:
        """检测是否为垃圾消息"""
        if not message.text:
            return False

        # 使用消息防护引擎检测
        from .message_protection import get_protection_engine

        engine = get_protection_engine()
        result = await engine.check_message({
            'text': message.text,
            'user_id': message.from_user.id
        })

        return result.is_blocked and 'spam' in result.matched_rules

    async def _is_phishing_message(self, message: Message) -> bool:
        """检测是否为钓鱼消息"""
        if not message.text:
            return False

        from .message_protection import get_protection_engine

        engine = get_protection_engine()
        result = await engine.check_message({
            'text': message.text,
            'user_id': message.from_user.id
        })

        return result.is_blocked and ('phishing' in result.matched_rules or 'malicious_link' in result.matched_rules)

    async def _is_malicious_behavior(self, message: Message) -> bool:
        """检测是否为恶意行为"""
        user_id = message.from_user.id

        # 检查用户消息频率（1分钟内超过10条）
        recent_messages = await self._get_recent_message_count(user_id, seconds=60)
        if recent_messages > 10:
            return True

        # 检查内容重复率
        similarity = await self._calculate_message_similarity(user_id, message.text)
        if similarity > 0.9:
            return True

        return False

    async def _record_spam_threat(self, message: Message) -> dict:
        """记录垃圾消息威胁"""
        user_id = message.from_user.id

        # 添加到威胁缓存
        self.threat_cache['spam_users'].add(user_id)

        # 保存到数据库
        threat_data = {
            'user_id': user_id,
            'username': message.from_user.username,
            'threat_type': 'spam',
            'severity': 7,
            'evidence': {
                'message': message.text[:200],
                'chat_id': message.chat.id,
                'message_id': message.id
            },
            'source': 'global_monitor',
            'detected_at': datetime.now()
        }

        await self._save_threat_intelligence(threat_data)
        self.stats['users_flagged'] += 1

        return threat_data

    async def _record_phishing_threat(self, message: Message) -> dict:
        """记录钓鱼威胁"""
        user_id = message.from_user.id

        # 提取链接
        from .message_protection import LinkScanner
        scanner = LinkScanner()
        links = scanner.extract_links(message.text)

        # 添加到威胁缓存
        for link in links:
            self.threat_cache['phishing_links'].add(link)

            # 提取域名
            import re
            domain_match = re.search(r'https?://([^/]+)', link)
            if domain_match:
                self.threat_cache['malicious_domains'].add(domain_match.group(1))

        # 保存到数据库
        threat_data = {
            'user_id': user_id,
            'username': message.from_user.username,
            'threat_type': 'phishing',
            'severity': 9,
            'evidence': {
                'message': message.text[:200],
                'links': links,
                'chat_id': message.chat.id,
                'message_id': message.id
            },
            'source': 'global_monitor',
            'detected_at': datetime.now()
        }

        await self._save_threat_intelligence(threat_data)
        self.stats['users_flagged'] += 1

        return threat_data

    async def _record_malicious_user(self, message: Message) -> dict:
        """记录恶意用户"""
        user_id = message.from_user.id

        # 保存到数据库
        threat_data = {
            'user_id': user_id,
            'username': message.from_user.username,
            'threat_type': 'malicious_behavior',
            'severity': 6,
            'evidence': {
                'message': message.text[:200] if message.text else '',
                'chat_id': message.chat.id,
                'message_id': message.id,
                'reason': '异常行为（高频/重复消息）'
            },
            'source': 'global_monitor',
            'detected_at': datetime.now()
        }

        await self._save_threat_intelligence(threat_data)
        self.stats['users_flagged'] += 1

        return threat_data

    async def _save_threat_intelligence(self, threat_data: dict):
        """保存威胁情报到数据库"""
        await self.db.execute("""
            INSERT INTO threat_intelligence
            (user_id, username, threat_type, severity, evidence, source, detected_at)
            VALUES (:user_id, :username, :threat_type, :severity, :evidence, :source, :detected_at)
        """, threat_data)
        await self.db.commit()

    async def _get_recent_message_count(self, user_id: int, seconds: int = 60) -> int:
        """获取用户最近的消息数量"""
        since = datetime.now() - timedelta(seconds=seconds)

        result = await self.db.execute("""
            SELECT COUNT(*) as count
            FROM user_behavior_logs
            WHERE user_id = :user_id AND created_at >= :since
        """, {'user_id': user_id, 'since': since})

        row = result.fetchone()
        return row['count'] if row else 0

    async def _calculate_message_similarity(self, user_id: int, text: str) -> float:
        """计算消息相似度"""
        # 获取用户最近的消息
        result = await self.db.execute("""
            SELECT metadata->>'$.text' as text
            FROM user_behavior_logs
            WHERE user_id = :user_id AND action = 'send_message'
            ORDER BY created_at DESC
            LIMIT 5
        """, {'user_id': user_id})

        recent_messages = [row['text'] for row in result.fetchall() if row['text']]

        if not recent_messages:
            return 0.0

        # 简单的相似度计算（可以使用更复杂的算法）
        max_similarity = 0.0
        for msg in recent_messages:
            # 计算文本相似度（这里使用简单的包含关系）
            if text and msg:
                similarity = len(set(text) & set(msg)) / len(set(text) | set(msg))
                max_similarity = max(max_similarity, similarity)

        return max_similarity

    def get_threat_cache(self) -> dict:
        """获取威胁缓存数据"""
        return {
            'spam_users_count': len(self.threat_cache['spam_users']),
            'phishing_links_count': len(self.threat_cache['phishing_links']),
            'malicious_domains_count': len(self.threat_cache['malicious_domains']),
            'spam_users': list(self.threat_cache['spam_users'])[:100],  # 最多返回100个
            'phishing_links': list(self.threat_cache['phishing_links'])[:100],
            'malicious_domains': list(self.threat_cache['malicious_domains'])[:100]
        }

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()


# ==================== 威胁情报查询服务 ====================

class ThreatIntelligenceService:
    """威胁情报查询服务"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def check_user(self, user_id: int) -> dict:
        """
        检查用户是否在威胁情报库中

        Returns:
            {
                'is_threat': bool,
                'threat_level': int,  # 0-10
                'threat_types': list,
                'last_detected': datetime,
                'detection_count': int
            }
        """
        result = await self.db.execute("""
            SELECT threat_type, severity, detected_at, COUNT(*) as count
            FROM threat_intelligence
            WHERE user_id = :user_id
            GROUP BY threat_type, severity, detected_at
            ORDER BY detected_at DESC
        """, {'user_id': user_id})

        threats = result.fetchall()

        if not threats:
            return {
                'is_threat': False,
                'threat_level': 0,
                'threat_types': [],
                'last_detected': None,
                'detection_count': 0
            }

        # 计算威胁等级（最高严重程度）
        max_severity = max(t['severity'] for t in threats)

        # 提取威胁类型
        threat_types = list(set(t['threat_type'] for t in threats))

        # 最后检测时间
        last_detected = max(t['detected_at'] for t in threats)

        # 检测次数
        detection_count = sum(t['count'] for t in threats)

        return {
            'is_threat': True,
            'threat_level': max_severity,
            'threat_types': threat_types,
            'last_detected': last_detected,
            'detection_count': detection_count
        }

    async def check_link(self, url: str) -> dict:
        """
        检查链接是否在威胁情报库中

        Returns:
            {
                'is_malicious': bool,
                'threat_type': str,
                'severity': int,
                'detected_count': int
            }
        """
        # 提取域名
        import re
        domain_match = re.search(r'https?://([^/]+)', url)
        domain = domain_match.group(1) if domain_match else url

        result = await self.db.execute("""
            SELECT threat_type, severity, COUNT(*) as count
            FROM threat_intelligence
            WHERE evidence->'$.links' LIKE :pattern
            GROUP BY threat_type, severity
            ORDER BY severity DESC
            LIMIT 1
        """, {'pattern': f'%{domain}%'})

        threat = result.fetchone()

        if not threat:
            return {
                'is_malicious': False,
                'threat_type': None,
                'severity': 0,
                'detected_count': 0
            }

        return {
            'is_malicious': True,
            'threat_type': threat['threat_type'],
            'severity': threat['severity'],
            'detected_count': threat['count']
        }

    async def get_user_reputation_score(self, user_id: int) -> int:
        """
        获取用户信誉分（0-100）

        100 = 完全可信
        0 = 完全不可信
        """
        score = 100

        # 检查威胁情报
        threat_info = await self.check_user(user_id)

        if threat_info['is_threat']:
            # 根据威胁等级扣分
            score -= threat_info['threat_level'] * 5

            # 根据检测次数扣分
            score -= min(threat_info['detection_count'] * 2, 30)

        # 检查黑名单
        result = await self.db.execute("""
            SELECT COUNT(*) as count FROM blacklist WHERE user_id = :user_id
        """, {'user_id': user_id})

        blacklist_count = result.fetchone()['count']
        if blacklist_count > 0:
            score -= 40

        return max(0, min(100, score))

    async def get_top_threats(self, limit: int = 100) -> List[dict]:
        """获取威胁排行榜"""
        result = await self.db.execute("""
            SELECT
                user_id,
                username,
                threat_type,
                MAX(severity) as max_severity,
                COUNT(*) as detection_count,
                MAX(detected_at) as last_detected
            FROM threat_intelligence
            WHERE detected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY user_id, username, threat_type
            ORDER BY max_severity DESC, detection_count DESC
            LIMIT :limit
        """, {'limit': limit})

        return [dict(row) for row in result.fetchall()]

    async def get_threat_statistics(self, days: int = 7) -> dict:
        """获取威胁统计（最近N天）"""
        since = datetime.now() - timedelta(days=days)

        result = await self.db.execute("""
            SELECT
                threat_type,
                COUNT(*) as count,
                AVG(severity) as avg_severity
            FROM threat_intelligence
            WHERE detected_at >= :since
            GROUP BY threat_type
        """, {'since': since})

        stats = {row['threat_type']: {
            'count': row['count'],
            'avg_severity': float(row['avg_severity'])
        } for row in result.fetchall()}

        # 总威胁数
        total = sum(s['count'] for s in stats.values())

        return {
            'total_threats': total,
            'threats_by_type': stats,
            'period_days': days
        }


# ==================== 威胁监控启动器 ====================

class ThreatMonitorService:
    """威胁监控服务（长期运行）"""

    def __init__(self, userbot_accounts: List[Client], db_session: AsyncSession):
        self.accounts = userbot_accounts
        self.collector = ThreatIntelligenceCollector(db_session)
        self.is_running = False

    async def start(self):
        """启动威胁监控"""
        self.is_running = True

        logger.info("🚀 威胁监控服务启动")

        # 为每个 Userbot 注册消息处理器
        for client in self.accounts:
            @client.on_message()
            async def handle_message(client, message: Message):
                if self.is_running:
                    await self.collector.process_message(message)

            # 启动客户端
            await client.start()

        logger.info(f"✅ 已启动 {len(self.accounts)} 个监控账号")

        # 保持运行
        while self.is_running:
            await asyncio.sleep(60)

            # 每分钟输出统计
            stats = self.collector.get_stats()
            logger.info(f"[统计] 监控消息: {stats['messages_monitored']} | 检测威胁: {stats['threats_detected']}")

    async def stop(self):
        """停止威胁监控"""
        self.is_running = False

        for client in self.accounts:
            await client.stop()

        logger.info("威胁监控服务已停止")

    def add_monitor_chat(self, chat_id: int):
        """添加监控群组"""
        asyncio.create_task(self.collector.add_monitor_chat(chat_id))

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.collector.get_stats()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("威胁情报监控系统")
    print("=" * 60)
    print("功能：")
    print("- 全局监控 TG 群组/频道消息")
    print("- 自动检测垃圾消息、钓鱼链接、恶意行为")
    print("- 构建威胁情报库")
    print("- 提供威胁查询 API")
    print("=" * 60)
