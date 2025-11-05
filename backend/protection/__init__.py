# -*- coding: utf-8 -*-
"""
SafeLine 风格的防护模块
"""
from .message_protection import (
    MessageProtectionEngine,
    ProtectionResult,
    ThreatLevel,
    ProtectionAction,
    get_protection_engine
)

from .rate_limiter import (
    RateLimiter,
    RateLimitResult,
    RateLimit,
    UserTier,
    LimitAction,
    TokenBucket,
    RedisRateLimiter,
    AutoResponseManager,
    get_rate_limiter
)

__all__ = [
    # Message Protection
    'MessageProtectionEngine',
    'ProtectionResult',
    'ThreatLevel',
    'ProtectionAction',
    'get_protection_engine',

    # Rate Limiting
    'RateLimiter',
    'RateLimitResult',
    'RateLimit',
    'UserTier',
    'LimitAction',
    'TokenBucket',
    'RedisRateLimiter',
    'AutoResponseManager',
    'get_rate_limiter'
]
