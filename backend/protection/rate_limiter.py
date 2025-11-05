# -*- coding: utf-8 -*-
"""
频率限制器（参考 SafeLine WAF 的 CC 防护）
防止消息刷屏、API 滥用、自动化攻击
"""
import time
import redis
import logging
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class UserTier(str, Enum):
    """用户等级"""
    NORMAL = "NORMAL"      # 普通用户
    VIP = "VIP"            # VIP 用户
    ADMIN = "ADMIN"        # 管理员（不限流）
    BLACKLIST = "BLACKLIST"  # 黑名单（完全封禁）


class LimitAction(str, Enum):
    """限流动作"""
    ALLOW = "ALLOW"              # 允许
    THROTTLE = "THROTTLE"        # 限速（延迟处理）
    REJECT = "REJECT"            # 拒绝
    BAN_TEMPORARY = "BAN_TEMPORARY"  # 临时封禁
    BAN_PERMANENT = "BAN_PERMANENT"  # 永久封禁


@dataclass
class RateLimit:
    """限流规则"""
    # 时间窗口内的最大请求数
    max_requests: int
    # 时间窗口（秒）
    window_seconds: int
    # 达到限制后的动作
    action: LimitAction = LimitAction.REJECT
    # 临时封禁时长（秒）
    ban_duration: int = 3600


@dataclass
class RateLimitResult:
    """限流检测结果"""
    allowed: bool
    action: LimitAction
    reason: str = ""
    current_count: int = 0
    limit: int = 0
    reset_at: Optional[datetime] = None
    ban_until: Optional[datetime] = None


# ==================== 令牌桶算法实现 ====================

class TokenBucket:
    """
    令牌桶算法（Token Bucket）
    用于平滑的流量控制
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: 桶容量（最大令牌数）
            refill_rate: 令牌补充速率（令牌/秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill_time = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌

        Args:
            tokens: 需要消费的令牌数

        Returns:
            是否成功消费
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill_time

        # 计算应该补充的令牌数
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = now

    def get_available_tokens(self) -> int:
        """获取当前可用令牌数"""
        self._refill()
        return int(self.tokens)


# ==================== Redis 滑动窗口实现 ====================

class RedisRateLimiter:
    """
    基于 Redis 的滑动窗口限流器
    适用于分布式环境
    """

    def __init__(self, redis_client: redis.Redis, key_prefix: str = "rate_limit"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    async def check_limit(
        self,
        user_id: int,
        limit: RateLimit,
        scope: str = "global"
    ) -> RateLimitResult:
        """
        检查是否超过限流

        Args:
            user_id: 用户 ID
            limit: 限流规则
            scope: 限流范围（如 "global", "chat:123"）

        Returns:
            RateLimitResult
        """
        key = f"{self.key_prefix}:{scope}:{user_id}"
        now = time.time()
        window_start = now - limit.window_seconds

        try:
            # 使用 Redis 事务（MULTI/EXEC）
            pipe = self.redis.pipeline()

            # 1. 移除窗口外的旧记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 2. 统计窗口内的请求数
            pipe.zcard(key)

            # 3. 添加当前请求时间戳
            pipe.zadd(key, {str(now): now})

            # 4. 设置过期时间（窗口大小 + 1 秒）
            pipe.expire(key, limit.window_seconds + 1)

            results = pipe.execute()
            current_count = results[1]

            # 检查是否超限
            if current_count >= limit.max_requests:
                reset_at = datetime.fromtimestamp(now + limit.window_seconds)

                return RateLimitResult(
                    allowed=False,
                    action=limit.action,
                    reason=f"超过限流阈值: {current_count}/{limit.max_requests} 请求/{limit.window_seconds}秒",
                    current_count=current_count,
                    limit=limit.max_requests,
                    reset_at=reset_at
                )

            return RateLimitResult(
                allowed=True,
                action=LimitAction.ALLOW,
                current_count=current_count,
                limit=limit.max_requests
            )

        except redis.RedisError as e:
            logger.error(f"Redis 限流检查失败: {e}")
            # Redis 故障时，默认允许通过（fail-open）
            return RateLimitResult(
                allowed=True,
                action=LimitAction.ALLOW,
                reason="Redis 不可用，限流检查跳过"
            )

    async def reset_limit(self, user_id: int, scope: str = "global"):
        """重置用户的限流计数"""
        key = f"{self.key_prefix}:{scope}:{user_id}"
        try:
            self.redis.delete(key)
            logger.info(f"已重置限流: user_id={user_id}, scope={scope}")
        except redis.RedisError as e:
            logger.error(f"重置限流失败: {e}")


# ==================== 主限流器 ====================

class RateLimiter:
    """
    统一限流管理器（SafeLine 风格）
    支持多维度限流和分级管理
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # Redis 客户端
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info(f"✅ Redis 连接成功: {redis_url}")
        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            self.redis = None

        # 限流规则配置
        self.limits = self._init_limits()

        # 用户等级缓存（user_id -> UserTier）
        self.user_tiers: Dict[int, UserTier] = {}

        # 封禁记录（user_id -> ban_until_timestamp）
        self.ban_list: Dict[int, float] = {}

        # Redis 滑动窗口限流器
        self.redis_limiter = RedisRateLimiter(self.redis) if self.redis else None

        # 统计信息
        self.stats = {
            'total_checked': 0,
            'total_rejected': 0,
            'total_throttled': 0,
            'total_banned': 0,
        }

    def _init_limits(self) -> Dict[UserTier, Dict[str, RateLimit]]:
        """初始化分级限流规则"""
        return {
            # 普通用户
            UserTier.NORMAL: {
                'message': RateLimit(
                    max_requests=10,         # 10条消息
                    window_seconds=60,       # 每分钟
                    action=LimitAction.REJECT
                ),
                'message_hour': RateLimit(
                    max_requests=200,        # 200条消息
                    window_seconds=3600,     # 每小时
                    action=LimitAction.REJECT
                ),
                'api': RateLimit(
                    max_requests=60,         # 60次API调用
                    window_seconds=60,       # 每分钟
                    action=LimitAction.THROTTLE
                ),
            },

            # VIP 用户（更宽松的限制）
            UserTier.VIP: {
                'message': RateLimit(
                    max_requests=30,         # 30条消息
                    window_seconds=60,       # 每分钟
                    action=LimitAction.REJECT
                ),
                'message_hour': RateLimit(
                    max_requests=1000,       # 1000条消息
                    window_seconds=3600,     # 每小时
                    action=LimitAction.REJECT
                ),
                'api': RateLimit(
                    max_requests=300,        # 300次API调用
                    window_seconds=60,       # 每分钟
                    action=LimitAction.THROTTLE
                ),
            },

            # 管理员（基本不限流）
            UserTier.ADMIN: {
                'message': RateLimit(
                    max_requests=1000,
                    window_seconds=60,
                    action=LimitAction.ALLOW
                ),
            },
        }

    async def check_rate_limit(
        self,
        user_id: int,
        limit_type: str = "message",
        scope: str = "global"
    ) -> RateLimitResult:
        """
        检查用户是否超过限流

        Args:
            user_id: 用户 ID
            limit_type: 限流类型（message, api 等）
            scope: 限流范围（global, chat:123 等）

        Returns:
            RateLimitResult
        """
        self.stats['total_checked'] += 1

        # 1. 检查是否在封禁列表
        if user_id in self.ban_list:
            ban_until = self.ban_list[user_id]
            if time.time() < ban_until:
                return RateLimitResult(
                    allowed=False,
                    action=LimitAction.BAN_TEMPORARY,
                    reason="用户已被临时封禁",
                    ban_until=datetime.fromtimestamp(ban_until)
                )
            else:
                # 封禁已过期，移除
                del self.ban_list[user_id]

        # 2. 获取用户等级
        user_tier = await self._get_user_tier(user_id)

        # 黑名单用户直接拒绝
        if user_tier == UserTier.BLACKLIST:
            self.stats['total_rejected'] += 1
            return RateLimitResult(
                allowed=False,
                action=LimitAction.BAN_PERMANENT,
                reason="用户在黑名单中"
            )

        # 管理员基本不限流
        if user_tier == UserTier.ADMIN:
            return RateLimitResult(
                allowed=True,
                action=LimitAction.ALLOW,
                reason="管理员免限流"
            )

        # 3. 获取限流规则
        tier_limits = self.limits.get(user_tier, {})
        limit = tier_limits.get(limit_type)

        if not limit:
            # 没有配置限流规则，默认允许
            return RateLimitResult(
                allowed=True,
                action=LimitAction.ALLOW,
                reason=f"未配置 {limit_type} 限流规则"
            )

        # 4. 使用 Redis 滑动窗口检查
        if self.redis_limiter:
            result = await self.redis_limiter.check_limit(user_id, limit, scope)

            if not result.allowed:
                self.stats['total_rejected'] += 1

                # 如果超限且动作是 BAN，则添加到封禁列表
                if limit.action == LimitAction.BAN_TEMPORARY:
                    await self._ban_user(user_id, limit.ban_duration)
                    result.ban_until = datetime.fromtimestamp(
                        time.time() + limit.ban_duration
                    )

                logger.warning(
                    f"[限流] 用户 {user_id} 超限: {result.reason}"
                )

            return result

        # Redis 不可用，使用本地限流（备用）
        return RateLimitResult(
            allowed=True,
            action=LimitAction.ALLOW,
            reason="Redis 不可用，跳过限流"
        )

    async def _get_user_tier(self, user_id: int) -> UserTier:
        """
        获取用户等级

        TODO: 集成数据库查询
        """
        # 从缓存获取
        if user_id in self.user_tiers:
            return self.user_tiers[user_id]

        # TODO: 从数据库查询用户等级
        # user = await db.query(User).filter(User.id == user_id).first()
        # tier = user.tier if user else UserTier.NORMAL

        # 默认为普通用户
        tier = UserTier.NORMAL
        self.user_tiers[user_id] = tier

        return tier

    async def _ban_user(self, user_id: int, duration: int):
        """
        临时封禁用户

        Args:
            user_id: 用户 ID
            duration: 封禁时长（秒）
        """
        ban_until = time.time() + duration
        self.ban_list[user_id] = ban_until

        self.stats['total_banned'] += 1

        logger.warning(
            f"🚫 [封禁] 用户 {user_id} 已被封禁 {duration}秒 "
            f"(至 {datetime.fromtimestamp(ban_until).strftime('%H:%M:%S')})"
        )

        # 同步到 Redis
        if self.redis:
            try:
                key = f"ban:{user_id}"
                self.redis.setex(key, duration, ban_until)
            except redis.RedisError as e:
                logger.error(f"同步封禁记录到 Redis 失败: {e}")

    async def unban_user(self, user_id: int):
        """解除用户封禁"""
        if user_id in self.ban_list:
            del self.ban_list[user_id]

        if self.redis:
            try:
                key = f"ban:{user_id}"
                self.redis.delete(key)
            except redis.RedisError as e:
                logger.error(f"删除 Redis 封禁记录失败: {e}")

        logger.info(f"✅ 已解除用户 {user_id} 的封禁")

    async def set_user_tier(self, user_id: int, tier: UserTier):
        """设置用户等级"""
        self.user_tiers[user_id] = tier
        logger.info(f"用户 {user_id} 等级设置为: {tier}")

    def get_stats(self) -> dict:
        """获取限流统计"""
        return {
            **self.stats,
            'reject_rate': (
                self.stats['total_rejected'] / self.stats['total_checked']
                if self.stats['total_checked'] > 0 else 0
            ),
            'current_bans': len(self.ban_list)
        }

    def reset_stats(self):
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0


# ==================== 自动化响应管理器 ====================

class AutoResponseManager:
    """
    自动化响应管理器
    根据限流结果自动采取行动
    """

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.violation_count: Dict[int, int] = {}  # user_id -> 违规次数

    async def handle_limit_result(
        self,
        user_id: int,
        result: RateLimitResult
    ) -> dict:
        """
        处理限流结果并采取行动

        Returns:
            {
                "action": "notify" | "warn" | "ban" | "none",
                "message": str
            }
        """
        if result.allowed:
            return {"action": "none", "message": ""}

        # 记录违规次数
        self.violation_count[user_id] = self.violation_count.get(user_id, 0) + 1
        violations = self.violation_count[user_id]

        # 根据违规次数采取不同行动
        if violations == 1:
            # 第一次违规：友好提醒
            return {
                "action": "notify",
                "message": f"⚠️ 您的操作过于频繁，请稍后再试。\n"
                          f"限制: {result.limit} 次/{result.reset_at.strftime('%M分%S秒') if result.reset_at else '未知'}"
            }

        elif violations <= 3:
            # 2-3次违规：警告
            return {
                "action": "warn",
                "message": f"⚠️ 警告：您已多次触发频率限制！\n"
                          f"当前: {result.current_count}/{result.limit}\n"
                          f"继续违规可能导致封禁。"
            }

        else:
            # 多次违规：自动封禁
            await self.rate_limiter._ban_user(user_id, 3600)  # 封禁1小时

            return {
                "action": "ban",
                "message": f"🚫 由于多次违规，您已被临时封禁。\n"
                          f"封禁时长: 1小时\n"
                          f"解禁时间: {result.ban_until.strftime('%H:%M:%S') if result.ban_until else '未知'}"
            }

    def reset_violations(self, user_id: int):
        """重置用户违规记录"""
        if user_id in self.violation_count:
            del self.violation_count[user_id]


# ==================== 全局实例 ====================

# 全局限流器实例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(redis_url: str = "redis://localhost:6379") -> RateLimiter:
    """获取全局限流器实例"""
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimiter(redis_url)

    return _rate_limiter


# ==================== 测试代码 ====================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("频率限制器测试")
        print("=" * 60)

        # 创建限流器
        limiter = RateLimiter(redis_url="redis://localhost:6379")

        # 测试用户
        test_user_id = 123456

        print(f"\n[测试] 普通用户消息限流（10条/分钟）")
        print("-" * 60)

        # 模拟发送消息
        for i in range(15):
            result = await limiter.check_rate_limit(
                user_id=test_user_id,
                limit_type="message"
            )

            status = "✅ 允许" if result.allowed else "❌ 拒绝"
            print(f"消息 {i+1}: {status} | 当前: {result.current_count}/{result.limit}")

            if not result.allowed:
                print(f"  原因: {result.reason}")
                if result.reset_at:
                    print(f"  重置时间: {result.reset_at.strftime('%H:%M:%S')}")

            await asyncio.sleep(0.1)  # 模拟延迟

        # 测试 VIP 用户
        print(f"\n[测试] VIP 用户限流（30条/分钟）")
        print("-" * 60)

        vip_user_id = 789012
        await limiter.set_user_tier(vip_user_id, UserTier.VIP)

        for i in range(35):
            result = await limiter.check_rate_limit(
                user_id=vip_user_id,
                limit_type="message"
            )

            status = "✅ 允许" if result.allowed else "❌ 拒绝"

            if i < 5 or i >= 29:  # 只显示前5条和超限后的
                print(f"消息 {i+1}: {status} | 当前: {result.current_count}/{result.limit}")

            await asyncio.sleep(0.05)

        # 统计信息
        print(f"\n[统计]")
        print("-" * 60)
        stats = limiter.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

    # 运行测试
    asyncio.run(test())
