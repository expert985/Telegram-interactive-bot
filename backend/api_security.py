# -*- coding: utf-8 -*-
"""
SafeLine 安全模块 API 端点
提供安全事件、用户行为、防护规则、威胁情报等查询接口
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from database import execute_raw_sql

# 创建路由
router = APIRouter(prefix="/api/security", tags=["SafeLine Security"])


# ==================== Pydantic Models ====================

class SecurityEventFilter(BaseModel):
    """安全事件过滤器"""
    user_id: Optional[int] = None
    event_type: Optional[str] = None
    threat_level: Optional[str] = None
    handled: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)


class SecurityEventHandle(BaseModel):
    """处理安全事件"""
    handle_action: str
    handle_notes: Optional[str] = None


class ProtectionRuleCreate(BaseModel):
    """创建防护规则"""
    name: str
    description: Optional[str] = None
    category: str  # spam | phishing | malicious_link | rate_limit | behavior | custom
    conditions: dict
    actions: dict
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    enabled: bool = True
    priority: int = 50


class ThreatIntelligenceCreate(BaseModel):
    """创建威胁情报"""
    threat_type: str  # malicious_ip | malicious_domain | malicious_hash | spam_pattern | phishing_url
    threat_value: str
    threat_level: str  # LOW | MEDIUM | HIGH | CRITICAL
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "manual"
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


# ==================== API Endpoints ====================

@router.get("/events")
async def get_security_events(
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    threat_level: Optional[str] = None,
    handled: Optional[bool] = None,
    limit: int = 100
):
    """
    获取安全事件列表
    
    支持按用户、事件类型、威胁等级、处理状态过滤
    """
    # 构建查询条件
    conditions = []
    params = {"limit": limit}
    
    if user_id is not None:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id
    
    if event_type:
        conditions.append("event_type = :event_type")
        params["event_type"] = event_type
    
    if threat_level:
        conditions.append("threat_level = :threat_level")
        params["threat_level"] = threat_level
    
    if handled is not None:
        conditions.append("handled = :handled")
        params["handled"] = handled
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            id, user_id, username, event_type, threat_level,
            reason, evidence, handled, handled_by, handled_at,
            handle_action, source, action_taken, created_at
        FROM security_events
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
    """
    
    events = await execute_raw_sql(query, params)
    return {"success": True, "events": events, "count": len(events)}


@router.get("/events/unhandled")
async def get_unhandled_threats():
    """
    获取未处理的高危威胁（使用视图）
    """
    query = """
        SELECT *
        FROM v_unhandled_threats
        LIMIT 50
    """
    
    threats = await execute_raw_sql(query)
    return {
        "success": True,
        "threats": threats,
        "count": len(threats)
    }


@router.post("/events/{event_id}/handle")
async def handle_security_event(event_id: int, handle_data: SecurityEventHandle):
    """
    处理安全事件
    """
    query = """
        UPDATE security_events
        SET 
            handled = TRUE,
            handled_at = NOW(),
            handle_action = :handle_action,
            handle_notes = :handle_notes,
            updated_at = NOW()
        WHERE id = :event_id
    """
    
    params = {
        "event_id": event_id,
        "handle_action": handle_data.handle_action,
        "handle_notes": handle_data.handle_notes
    }
    
    await execute_raw_sql(query, params)
    
    return {
        "success": True,
        "message": "安全事件已处理"
    }


@router.get("/users/high-risk")
async def get_high_risk_users(limit: int = 50):
    """
    获取高风险用户列表（使用视图）
    """
    query = f"""
        SELECT *
        FROM v_high_risk_users
        LIMIT {limit}
    """
    
    users = await execute_raw_sql(query)
    return {
        "success": True,
        "users": users,
        "count": len(users)
    }


@router.get("/users/{user_id}/behavior")
async def get_user_behavior(user_id: int):
    """
    获取用户行为分析详情
    """
    query = """
        SELECT *
        FROM user_behaviors
        WHERE user_id = :user_id
    """
    
    result = await execute_raw_sql(query, {"user_id": user_id})
    
    if not result:
        return {
            "success": False,
            "error": "用户行为数据不存在"
        }
    
    return {
        "success": True,
        "behavior": result[0]
    }


@router.get("/users/{user_id}/events")
async def get_user_security_events(user_id: int, limit: int = 50):
    """
    获取用户的所有安全事件
    """
    query = """
        SELECT *
        FROM security_events
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT :limit
    """
    
    events = await execute_raw_sql(query, {"user_id": user_id, "limit": limit})
    
    return {
        "success": True,
        "events": events,
        "count": len(events)
    }


@router.get("/rules")
async def get_protection_rules(
    category: Optional[str] = None,
    enabled: Optional[bool] = None
):
    """
    获取防护规则列表
    """
    conditions = []
    params = {}
    
    if category:
        conditions.append("category = :category")
        params["category"] = category
    
    if enabled is not None:
        conditions.append("enabled = :enabled")
        params["enabled"] = enabled
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            id, name, description, category, conditions, actions,
            severity, enabled, priority, trigger_count, last_triggered_at,
            created_at
        FROM protection_rules
        WHERE {where_clause}
        ORDER BY priority DESC, created_at DESC
    """
    
    rules = await execute_raw_sql(query, params)
    return {
        "success": True,
        "rules": rules,
        "count": len(rules)
    }


@router.post("/rules")
async def create_protection_rule(rule: ProtectionRuleCreate):
    """
    创建防护规则
    """
    query = """
        INSERT INTO protection_rules 
        (name, description, category, conditions, actions, severity, enabled, priority, created_at)
        VALUES 
        (:name, :description, :category, :conditions, :actions, :severity, :enabled, :priority, NOW())
    """
    
    params = {
        "name": rule.name,
        "description": rule.description,
        "category": rule.category,
        "conditions": str(rule.conditions),  # JSON会被自动转换
        "actions": str(rule.actions),
        "severity": rule.severity,
        "enabled": rule.enabled,
        "priority": rule.priority
    }
    
    await execute_raw_sql(query, params)
    
    return {
        "success": True,
        "message": "防护规则已创建"
    }


@router.put("/rules/{rule_id}/toggle")
async def toggle_protection_rule(rule_id: int):
    """
    启用/禁用防护规则
    """
    query = """
        UPDATE protection_rules
        SET enabled = NOT enabled, updated_at = NOW()
        WHERE id = :rule_id
    """
    
    await execute_raw_sql(query, {"rule_id": rule_id})
    
    return {
        "success": True,
        "message": "规则状态已更新"
    }


@router.get("/threat-intelligence")
async def get_threat_intelligence(
    threat_type: Optional[str] = None,
    is_active: bool = True,
    limit: int = 100
):
    """
    获取威胁情报列表
    """
    conditions = ["is_active = :is_active"]
    params = {"is_active": is_active, "limit": limit}
    
    if threat_type:
        conditions.append("threat_type = :threat_type")
        params["threat_type"] = threat_type
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            id, threat_type, threat_value, threat_level, confidence,
            source, description, tags, is_active, expires_at,
            hit_count, last_hit_at, created_at
        FROM threat_intelligence
        WHERE {where_clause}
        ORDER BY threat_level DESC, hit_count DESC, created_at DESC
        LIMIT :limit
    """
    
    intelligence = await execute_raw_sql(query, params)
    return {
        "success": True,
        "intelligence": intelligence,
        "count": len(intelligence)
    }


@router.post("/threat-intelligence")
async def create_threat_intelligence(intel: ThreatIntelligenceCreate):
    """
    添加威胁情报
    """
    query = """
        INSERT INTO threat_intelligence 
        (threat_type, threat_value, threat_level, confidence, source, 
         description, tags, is_active, expires_at, created_at)
        VALUES 
        (:threat_type, :threat_value, :threat_level, :confidence, :source,
         :description, :tags, TRUE, :expires_at, NOW())
    """
    
    params = {
        "threat_type": intel.threat_type,
        "threat_value": intel.threat_value,
        "threat_level": intel.threat_level,
        "confidence": intel.confidence,
        "source": intel.source,
        "description": intel.description,
        "tags": str(intel.tags) if intel.tags else None,
        "expires_at": intel.expires_at
    }
    
    await execute_raw_sql(query, params)
    
    return {
        "success": True,
        "message": "威胁情报已添加"
    }


@router.get("/statistics/today")
async def get_today_protection_stats():
    """
    获取今日防护统计（使用视图）
    """
    query = """
        SELECT *
        FROM v_today_protection_stats
    """
    
    result = await execute_raw_sql(query)
    
    if not result:
        return {
            "success": True,
            "stats": {
                "total_messages": 0,
                "blocked_messages": 0,
                "block_rate": 0.0
            }
        }
    
    return {
        "success": True,
        "stats": result[0]
    }


@router.get("/statistics/trend")
async def get_protection_trend(days: int = 7):
    """
    获取防护趋势（最近N天）
    """
    query = """
        SELECT 
            date,
            total_messages,
            blocked_messages,
            ROUND((blocked_messages / NULLIF(total_messages, 0)) * 100, 2) as block_rate,
            spam_detected,
            phishing_detected,
            rate_limit_triggered,
            temporary_bans + permanent_bans as total_bans,
            (threat_low + threat_medium + threat_high + threat_critical) as total_threats
        FROM protection_statistics
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
        ORDER BY date ASC
    """
    
    trend = await execute_raw_sql(query, {"days": days})
    
    return {
        "success": True,
        "trend": trend,
        "days": days
    }


@router.get("/bans")
async def get_rate_limit_bans(
    is_active: bool = True,
    limit: int = 100
):
    """
    获取频率限制封禁列表
    """
    query = """
        SELECT 
            id, user_id, username, ban_type, ban_reason,
            trigger_type, trigger_threshold, actual_count,
            banned_at, expires_at, is_active,
            unbanned_at, unbanned_by, unban_reason
        FROM rate_limit_bans
        WHERE is_active = :is_active
        ORDER BY banned_at DESC
        LIMIT :limit
    """
    
    bans = await execute_raw_sql(query, {"is_active": is_active, "limit": limit})
    
    return {
        "success": True,
        "bans": bans,
        "count": len(bans)
    }


@router.post("/bans/{ban_id}/unban")
async def unban_user(ban_id: int, reason: Optional[str] = None):
    """
    解除用户封禁
    """
    query = """
        UPDATE rate_limit_bans
        SET 
            is_active = FALSE,
            unbanned_at = NOW(),
            unban_reason = :reason,
            updated_at = NOW()
        WHERE id = :ban_id
    """
    
    await execute_raw_sql(query, {"ban_id": ban_id, "reason": reason})
    
    return {
        "success": True,
        "message": "用户已解封"
    }


@router.get("/dashboard")
async def get_security_dashboard():
    """
    获取安全仪表盘数据（汇总统计）
    """
    # 今日统计
    today_stats_query = "SELECT * FROM v_today_protection_stats"
    today_stats = await execute_raw_sql(today_stats_query)
    
    # 未处理的高危事件数
    unhandled_query = """
        SELECT COUNT(*) as count
        FROM security_events
        WHERE handled = FALSE AND threat_level IN ('HIGH', 'CRITICAL')
    """
    unhandled = await execute_raw_sql(unhandled_query)
    
    # 高风险用户数
    high_risk_query = """
        SELECT COUNT(*) as count
        FROM user_behaviors
        WHERE risk_level IN ('high', 'critical')
    """
    high_risk = await execute_raw_sql(high_risk_query)
    
    # 活跃的封禁数
    active_bans_query = """
        SELECT COUNT(*) as count
        FROM rate_limit_bans
        WHERE is_active = TRUE
    """
    active_bans = await execute_raw_sql(active_bans_query)
    
    return {
        "success": True,
        "dashboard": {
            "today_stats": today_stats[0] if today_stats else {},
            "unhandled_threats": unhandled[0]["count"] if unhandled else 0,
            "high_risk_users": high_risk[0]["count"] if high_risk else 0,
            "active_bans": active_bans[0]["count"] if active_bans else 0
        }
    }
