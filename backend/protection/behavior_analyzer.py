# -*- coding: utf-8 -*-
"""
用户行为分析模块
分析用户行为模式，识别异常和风险
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ==================== 行为特征类 ====================

class BehaviorProfile:
    """用户行为画像"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.risk_score = 0  # 风险评分 0-100
        self.risk_level = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
        self.risk_factors = []  # 风险因素列表
        self.behavior_patterns = {}  # 行为模式
        self.anomalies = []  # 异常行为列表

    def calculate_risk_level(self):
        """计算风险等级"""
        if self.risk_score >= 80:
            self.risk_level = "CRITICAL"
        elif self.risk_score >= 60:
            self.risk_level = "HIGH"
        elif self.risk_score >= 40:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "LOW"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "behavior_patterns": self.behavior_patterns,
            "anomalies": self.anomalies
        }


# ==================== 用户行为分析器 ====================

class BehaviorAnalyzer:
    """用户行为分析器"""

    def __init__(self, redis_client: aioredis.Redis, db_session: AsyncSession):
        self.redis = redis_client
        self.db = db_session

        # 行为阈值配置
        self.thresholds = {
            'message_rate_per_minute': 10,      # 每分钟消息数
            'message_rate_per_hour': 100,       # 每小时消息数
            'similarity_threshold': 0.8,        # 内容相似度阈值
            'link_ratio_threshold': 0.3,        # 链接占比阈值
            'special_char_ratio': 0.5,          # 特殊字符占比
            'night_activity_threshold': 0.7,    # 夜间活跃占比
        }

    async def analyze_user(self, user_id: int, time_window: int = 3600) -> BehaviorProfile:
        """
        分析用户行为

        Args:
            user_id: 用户 ID
            time_window: 分析时间窗口（秒），默认 1 小时

        Returns:
            BehaviorProfile: 用户行为画像
        """
        profile = BehaviorProfile(user_id)

        # 1. 消息频率分析
        await self._analyze_message_frequency(user_id, profile, time_window)

        # 2. 内容相似度分析
        await self._analyze_content_similarity(user_id, profile)

        # 3. 链接行为分析
        await self._analyze_link_behavior(user_id, profile)

        # 4. 活跃时间分析
        await self._analyze_activity_time(user_id, profile)

        # 5. 机器人行为检测
        await self._detect_bot_behavior(user_id, profile)

        # 6. 历史违规分析
        await self._analyze_violation_history(user_id, profile)

        # 计算最终风险等级
        profile.calculate_risk_level()

        # 保存分析结果到 Redis（缓存 1 小时）
        await self._cache_profile(profile)

        logger.info(
            f"[行为分析] User {user_id} | "
            f"风险评分: {profile.risk_score} | "
            f"等级: {profile.risk_level} | "
            f"因素: {len(profile.risk_factors)}"
        )

        return profile

    async def _analyze_message_frequency(
        self,
        user_id: int,
        profile: BehaviorProfile,
        time_window: int
    ):
        """消息频率分析"""

        # 获取时间窗口内的消息数
        minute_count = await self._get_message_count(user_id, window=60)
        hour_count = await self._get_message_count(user_id, window=3600)

        profile.behavior_patterns['messages_per_minute'] = minute_count
        profile.behavior_patterns['messages_per_hour'] = hour_count

        # 每分钟消息数检测
        if minute_count > self.thresholds['message_rate_per_minute']:
            profile.risk_score += 30
            profile.risk_factors.append(
                f"高频消息（{minute_count}条/分钟）"
            )
            profile.anomalies.append({
                'type': 'high_frequency',
                'value': minute_count,
                'threshold': self.thresholds['message_rate_per_minute']
            })

        # 每小时消息数检测
        if hour_count > self.thresholds['message_rate_per_hour']:
            profile.risk_score += 20
            profile.risk_factors.append(
                f"消息量异常（{hour_count}条/小时）"
            )

    async def _analyze_content_similarity(self, user_id: int, profile: BehaviorProfile):
        """内容相似度分析"""

        # 获取用户最近的消息内容
        recent_messages = await self._get_recent_messages(user_id, limit=10)

        if len(recent_messages) < 2:
            return

        # 计算消息之间的相似度
        similarities = []
        for i in range(len(recent_messages) - 1):
            similarity = self._calculate_text_similarity(
                recent_messages[i]['text'],
                recent_messages[i + 1]['text']
            )
            similarities.append(similarity)

        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            profile.behavior_patterns['content_similarity'] = avg_similarity

            if avg_similarity > self.thresholds['similarity_threshold']:
                profile.risk_score += 40
                profile.risk_factors.append(
                    f"重复内容刷屏（相似度: {avg_similarity:.2%}）"
                )
                profile.anomalies.append({
                    'type': 'content_repetition',
                    'value': avg_similarity,
                    'threshold': self.thresholds['similarity_threshold']
                })

    async def _analyze_link_behavior(self, user_id: int, profile: BehaviorProfile):
        """链接行为分析"""

        recent_messages = await self._get_recent_messages(user_id, limit=20)

        if not recent_messages:
            return

        # 统计包含链接的消息比例
        messages_with_links = 0
        total_links = 0

        for msg in recent_messages:
            text = msg.get('text', '')
            if not text:
                continue

            # 简单检测链接
            if 'http://' in text or 'https://' in text or 't.me/' in text:
                messages_with_links += 1
                # 统计链接数量
                total_links += text.count('http://') + text.count('https://') + text.count('t.me/')

        link_ratio = messages_with_links / len(recent_messages)
        profile.behavior_patterns['link_ratio'] = link_ratio
        profile.behavior_patterns['total_links'] = total_links

        # 链接占比过高
        if link_ratio > self.thresholds['link_ratio_threshold']:
            profile.risk_score += 35
            profile.risk_factors.append(
                f"频繁发送链接（{link_ratio:.0%} 消息含链接）"
            )
            profile.anomalies.append({
                'type': 'excessive_links',
                'value': link_ratio,
                'threshold': self.thresholds['link_ratio_threshold']
            })

    async def _analyze_activity_time(self, user_id: int, profile: BehaviorProfile):
        """活跃时间分析"""

        # 获取用户消息的时间分布
        time_distribution = await self._get_activity_time_distribution(user_id)

        if not time_distribution:
            return

        # 统计夜间活跃时间（0-6点）
        night_activity = sum(
            time_distribution.get(hour, 0)
            for hour in range(0, 6)
        )

        total_activity = sum(time_distribution.values())

        if total_activity > 0:
            night_ratio = night_activity / total_activity
            profile.behavior_patterns['night_activity_ratio'] = night_ratio

            # 夜间活跃异常（可能是机器人）
            if night_ratio > self.thresholds['night_activity_threshold']:
                profile.risk_score += 25
                profile.risk_factors.append(
                    f"夜间活跃异常（{night_ratio:.0%} 在 0-6 点）"
                )

    async def _detect_bot_behavior(self, user_id: int, profile: BehaviorProfile):
        """机器人行为检测"""

        # 检测规律性发送（固定时间间隔）
        message_intervals = await self._get_message_intervals(user_id, limit=10)

        if len(message_intervals) >= 5:
            # 计算间隔的标准差
            import statistics
            try:
                std_dev = statistics.stdev(message_intervals)
                avg_interval = statistics.mean(message_intervals)

                profile.behavior_patterns['message_interval_std'] = std_dev
                profile.behavior_patterns['message_interval_avg'] = avg_interval

                # 间隔过于规律（标准差很小）
                if std_dev < 5 and avg_interval < 60:  # 标准差 < 5 秒，平均间隔 < 60 秒
                    profile.risk_score += 50
                    profile.risk_factors.append(
                        f"疑似机器人行为（消息间隔规律: ±{std_dev:.1f}秒）"
                    )
                    profile.anomalies.append({
                        'type': 'bot_like_behavior',
                        'value': std_dev,
                        'avg_interval': avg_interval
                    })
            except:
                pass

    async def _analyze_violation_history(self, user_id: int, profile: BehaviorProfile):
        """历史违规分析"""

        # 查询历史违规记录
        result = await self.db.execute("""
            SELECT COUNT(*) as count, MAX(created_at) as last_violation
            FROM security_events
            WHERE user_id = :user_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """, {'user_id': user_id})

        row = result.fetchone()

        if row and row['count'] > 0:
            violation_count = row['count']
            profile.behavior_patterns['violation_count'] = violation_count
            profile.behavior_patterns['last_violation'] = row['last_violation']

            # 根据违规次数增加风险分
            profile.risk_score += min(violation_count * 10, 40)
            profile.risk_factors.append(
                f"历史违规记录（{violation_count} 次）"
            )

    # ==================== 辅助方法 ====================

    async def _get_message_count(self, user_id: int, window: int = 60) -> int:
        """获取时间窗口内的消息数"""
        key = f"user_messages:{user_id}"

        # 使用 Redis 有序集合统计
        now = datetime.now().timestamp()
        count = await self.redis.zcount(key, now - window, now)

        return count

    async def _get_recent_messages(self, user_id: int, limit: int = 10) -> List[dict]:
        """获取用户最近的消息"""
        result = await self.db.execute("""
            SELECT text, created_at
            FROM messages
            WHERE from_user_id = :user_id
            AND text IS NOT NULL
            ORDER BY created_at DESC
            LIMIT :limit
        """, {'user_id': user_id, 'limit': limit})

        return [dict(row) for row in result.fetchall()]

    async def _get_activity_time_distribution(self, user_id: int) -> Dict[int, int]:
        """获取用户活跃时间分布"""
        result = await self.db.execute("""
            SELECT HOUR(created_at) as hour, COUNT(*) as count
            FROM messages
            WHERE from_user_id = :user_id
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY HOUR(created_at)
        """, {'user_id': user_id})

        return {row['hour']: row['count'] for row in result.fetchall()}

    async def _get_message_intervals(self, user_id: int, limit: int = 10) -> List[float]:
        """获取消息时间间隔"""
        result = await self.db.execute("""
            SELECT created_at
            FROM messages
            WHERE from_user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """, {'user_id': user_id, 'limit': limit})

        timestamps = [row['created_at'] for row in result.fetchall()]

        if len(timestamps) < 2:
            return []

        # 计算相邻消息的时间间隔（秒）
        intervals = []
        for i in range(len(timestamps) - 1):
            interval = (timestamps[i] - timestamps[i + 1]).total_seconds()
            intervals.append(abs(interval))

        return intervals

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        if not text1 or not text2:
            return 0.0

        # 使用 Jaccard 相似度
        set1 = set(text1)
        set2 = set(text2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    async def _cache_profile(self, profile: BehaviorProfile):
        """缓存用户行为画像"""
        key = f"behavior_profile:{profile.user_id}"
        await self.redis.setex(
            key,
            3600,  # 1 小时过期
            str(profile.to_dict())
        )

    async def get_cached_profile(self, user_id: int) -> Optional[BehaviorProfile]:
        """获取缓存的行为画像"""
        key = f"behavior_profile:{user_id}"
        data = await self.redis.get(key)

        if data:
            # 从缓存恢复
            import ast
            profile_dict = ast.literal_eval(data.decode())

            profile = BehaviorProfile(user_id)
            profile.risk_score = profile_dict['risk_score']
            profile.risk_level = profile_dict['risk_level']
            profile.risk_factors = profile_dict['risk_factors']
            profile.behavior_patterns = profile_dict['behavior_patterns']
            profile.anomalies = profile_dict['anomalies']

            return profile

        return None


# ==================== 行为监控器 ====================

class BehaviorMonitor:
    """行为监控器（后台任务）"""

    def __init__(self, analyzer: BehaviorAnalyzer, check_interval: int = 300):
        self.analyzer = analyzer
        self.check_interval = check_interval  # 检查间隔（秒）
        self.is_running = False

    async def start(self):
        """启动监控"""
        self.is_running = True
        logger.info("🚀 行为监控器已启动")

        while self.is_running:
            try:
                # 获取活跃用户列表
                active_users = await self._get_active_users()

                logger.info(f"[行为监控] 检查 {len(active_users)} 个活跃用户")

                # 并发分析用户行为
                tasks = [
                    self.analyzer.analyze_user(user_id)
                    for user_id in active_users
                ]

                profiles = await asyncio.gather(*tasks, return_exceptions=True)

                # 统计高风险用户
                high_risk_count = sum(
                    1 for p in profiles
                    if isinstance(p, BehaviorProfile) and p.risk_level in ['HIGH', 'CRITICAL']
                )

                logger.info(
                    f"[行为监控] 完成分析 | "
                    f"高风险用户: {high_risk_count}/{len(active_users)}"
                )

            except Exception as e:
                logger.error(f"[行为监控] 错误: {e}")

            # 等待下一次检查
            await asyncio.sleep(self.check_interval)

    async def stop(self):
        """停止监控"""
        self.is_running = False
        logger.info("行为监控器已停止")

    async def _get_active_users(self) -> List[int]:
        """获取最近活跃的用户列表"""
        result = await self.analyzer.db.execute("""
            SELECT DISTINCT from_user_id
            FROM messages
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            LIMIT 1000
        """)

        return [row['from_user_id'] for row in result.fetchall()]


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("用户行为分析模块")
    print("=" * 60)
    print("\n核心功能:")
    print("✅ 消息频率分析（检测刷屏）")
    print("✅ 内容相似度分析（检测重复）")
    print("✅ 链接行为分析（检测广告）")
    print("✅ 活跃时间分析（检测异常）")
    print("✅ 机器人行为检测（检测自动化）")
    print("✅ 历史违规分析（累计评分）")
    print("\n风险等级:")
    print("- LOW: 0-40 分")
    print("- MEDIUM: 40-60 分")
    print("- HIGH: 60-80 分")
    print("- CRITICAL: 80-100 分")
    print("=" * 60)
