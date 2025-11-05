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

__all__ = [
    'MessageProtectionEngine',
    'ProtectionResult',
    'ThreatLevel',
    'ProtectionAction',
    'get_protection_engine'
]
