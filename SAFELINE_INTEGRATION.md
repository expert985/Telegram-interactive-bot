# SafeLine 防护集成方案

## 📋 项目定位

**Telegram 智能客服系统 + SafeLine 级防护能力**

将雷池（SafeLine）的 Web 应用防护理念应用到 Telegram 客服场景，打造一个**安全、智能、美观**的企业级客服系统。

---

## 🎯 核心理念

### SafeLine 是什么？

[SafeLine](https://github.com/chaitin/SafeLine) 是长亭科技开源的 Web 应用防火墙（WAF），提供：

- ✅ SQL 注入、XSS 等 OWASP Top 10 防护
- ✅ CC 攻击防护
- ✅ 访问控制（IP 黑白名单、地区封禁）
- ✅ 实时流量分析
- ✅ 威胁情报联动
- ✅ 现代化管理界面

### 如何应用到 Telegram 客服？

虽然 SafeLine 是 WAF，但其防护理念可以应用到 Telegram 场景：

| SafeLine 功能 | Telegram 客服应用 |
|--------------|------------------|
| **Web 攻击检测** | → **恶意消息检测**（垃圾广告、钓鱼链接、恶意代码） |
| **CC 攻击防护** | → **消息刷屏防护**（频率限制、自动封禁） |
| **IP 黑白名单** | → **用户黑白名单**（恶意用户、VIP 用户） |
| **流量分析** | → **用户行为分析**（异常行为检测） |
| **威胁情报** | → **恶意用户数据库**（全局共享黑名单） |
| **实时监控** | → **客服工作台实时数据** |

---

## 🏗️ 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端层（参考 SafeLine UI）                     │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐       │
│  │ 防护控制台│ 客服工作台│ 威胁情报  │ 统计分析  │ 系统设置  │       │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                      后端层（FastAPI）                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API 路由层                                                │   │
│  │  - 防护配置 API                                            │   │
│  │  - 客服功能 API                                            │   │
│  │  - 数据分析 API                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    防护引擎层（核心）                             │
│  ┌────────────────────┬────────────────────┬──────────────┐     │
│  │  消息防护引擎       │  用户行为分析       │  威胁情报    │     │
│  │  - 恶意内容检测     │  - 异常行为识别     │  - 黑名单库  │     │
│  │  - 链接安全检测     │  - 频率限制         │  - 威胁评分  │     │
│  │  - 敏感词过滤       │  - 风险评估         │  - 自动封禁  │     │
│  └────────────────────┴────────────────────┴──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                 Telegram 账号层（多账号池）                       │
│  Bot Token 池（1-100） + Userbot 池（1-100）                     │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    数据持久化层                                   │
│  MySQL 8.0（核心数据） + Redis（缓存/限流） + ClickHouse（日志）  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ 防护模块设计

### 1. 消息防护引擎（Message Protection Engine）

#### 1.1 恶意内容检测

```python
class MessageProtectionEngine:
    """消息防护引擎"""

    def __init__(self):
        self.spam_detector = SpamDetector()          # 垃圾消息检测
        self.link_scanner = LinkScanner()             # 链接安全扫描
        self.sensitive_word_filter = SensitiveWordFilter()  # 敏感词过滤
        self.phishing_detector = PhishingDetector()  # 钓鱼检测

    async def check_message(self, message: Message) -> ProtectionResult:
        """检查消息是否安全"""

        result = ProtectionResult()

        # 1. 垃圾消息检测
        if self.spam_detector.is_spam(message.text):
            result.is_blocked = True
            result.reason = "检测到垃圾广告"
            result.threat_level = ThreatLevel.HIGH
            return result

        # 2. 链接安全检测
        if links := self._extract_links(message.text):
            for link in links:
                if self.link_scanner.is_malicious(link):
                    result.is_blocked = True
                    result.reason = f"检测到恶意链接: {link}"
                    result.threat_level = ThreatLevel.CRITICAL
                    return result

        # 3. 敏感词过滤
        if sensitive_words := self.sensitive_word_filter.find(message.text):
            result.is_blocked = True
            result.reason = f"包含敏感词: {', '.join(sensitive_words)}"
            result.threat_level = ThreatLevel.MEDIUM
            return result

        # 4. 钓鱼检测
        if self.phishing_detector.is_phishing(message):
            result.is_blocked = True
            result.reason = "检测到钓鱼攻击"
            result.threat_level = ThreatLevel.HIGH
            return result

        result.is_blocked = False
        return result
```

#### 1.2 防护规则引擎

```python
class ProtectionRule:
    """防护规则"""

    def __init__(self):
        self.rules = []

    def add_rule(self, rule: dict):
        """
        添加防护规则

        示例规则:
        {
            "name": "禁止发送链接",
            "type": "content",
            "pattern": r"https?://",
            "action": "block",
            "message": "不允许发送链接"
        }
        """
        self.rules.append(rule)

    async def check(self, message: Message) -> RuleCheckResult:
        """检查消息是否违反规则"""
        for rule in self.rules:
            if self._match_rule(message, rule):
                return RuleCheckResult(
                    matched=True,
                    rule_name=rule['name'],
                    action=rule['action'],
                    message=rule.get('message')
                )

        return RuleCheckResult(matched=False)
```

### 2. 用户行为分析（Behavior Analysis）

#### 2.1 异常行为检测

```python
class BehaviorAnalyzer:
    """用户行为分析器"""

    async def analyze_user(self, user_id: int) -> BehaviorProfile:
        """分析用户行为"""

        profile = BehaviorProfile(user_id=user_id)

        # 1. 消息频率分析
        message_rate = await self._get_message_rate(user_id)
        if message_rate > 10:  # 每分钟超过 10 条
            profile.risk_factors.append("消息频率异常")
            profile.risk_score += 30

        # 2. 内容相似度分析
        similarity = await self._check_message_similarity(user_id)
        if similarity > 0.8:  # 80% 相似
            profile.risk_factors.append("重复内容刷屏")
            profile.risk_score += 40

        # 3. 活跃时间分析
        is_bot_like = await self._check_bot_behavior(user_id)
        if is_bot_like:
            profile.risk_factors.append("疑似机器人行为")
            profile.risk_score += 50

        # 4. 历史违规记录
        violation_count = await self._get_violation_count(user_id)
        profile.risk_score += violation_count * 10

        # 风险等级判定
        profile.risk_level = self._calculate_risk_level(profile.risk_score)

        return profile
```

#### 2.2 频率限制（Rate Limiting）

```python
class RateLimiter:
    """频率限制器（基于令牌桶算法）"""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        user_id: int,
        limit: int = 5,      # 每分钟 5 条
        window: int = 60      # 60 秒窗口
    ) -> RateLimitResult:
        """检查是否超过频率限制"""

        key = f"rate_limit:{user_id}"

        # 使用 Redis 滑动窗口计数
        now = time.time()
        pipeline = self.redis.pipeline()

        # 移除过期的记录
        pipeline.zremrangebyscore(key, 0, now - window)

        # 获取当前窗口内的计数
        pipeline.zcard(key)

        # 添加当前请求
        pipeline.zadd(key, {str(now): now})

        # 设置过期时间
        pipeline.expire(key, window)

        results = await pipeline.execute()
        current_count = results[1]

        if current_count >= limit:
            return RateLimitResult(
                is_limited=True,
                current_count=current_count,
                limit=limit,
                retry_after=window
            )

        return RateLimitResult(is_limited=False)
```

### 3. 威胁情报系统（Threat Intelligence）

#### 3.1 恶意用户数据库

```python
class ThreatIntelligence:
    """威胁情报系统"""

    def __init__(self, db):
        self.db = db
        self.blacklist_cache = {}  # 本地缓存
        self.threat_feeds = []      # 外部威胁源

    async def check_user(self, user_id: int) -> ThreatInfo:
        """检查用户是否在黑名单中"""

        # 1. 检查本地黑名单
        if threat := await self._check_local_blacklist(user_id):
            return threat

        # 2. 检查全局威胁情报（可选）
        if threat := await self._check_global_threat_feeds(user_id):
            # 自动加入本地黑名单
            await self._add_to_local_blacklist(user_id, threat)
            return threat

        return ThreatInfo(is_threat=False)

    async def add_threat(
        self,
        user_id: int,
        reason: str,
        threat_type: str,
        severity: int,
        evidence: dict = None
    ):
        """添加威胁情报"""

        threat = {
            'user_id': user_id,
            'reason': reason,
            'threat_type': threat_type,  # spam, phishing, abuse, etc.
            'severity': severity,         # 1-10
            'evidence': evidence,
            'reported_at': datetime.now(),
            'auto_block': severity >= 7   # 严重程度 >= 7 自动封禁
        }

        await self.db['threat_intelligence'].insert_one(threat)

        # 自动封禁
        if threat['auto_block']:
            await self._auto_block_user(user_id, reason)

    async def get_user_reputation(self, user_id: int) -> int:
        """获取用户信誉分（0-100）"""

        score = 100  # 初始满分

        # 违规记录
        violations = await self.db['violations'].count_documents({'user_id': user_id})
        score -= violations * 10

        # 被举报次数
        reports = await self.db['user_reports'].count_documents({'reported_user_id': user_id})
        score -= reports * 5

        # 黑名单记录
        blacklist_count = await self.db['blacklist'].count_documents({'user_id': user_id})
        score -= blacklist_count * 20

        return max(0, min(100, score))
```

#### 3.2 自动化响应

```python
class AutomatedResponse:
    """自动化响应系统"""

    async def handle_threat(self, user_id: int, threat_info: ThreatInfo):
        """根据威胁级别自动处理"""

        if threat_info.severity >= 9:
            # 严重威胁：立即封禁
            await self._ban_user(user_id, duration='permanent', reason=threat_info.reason)
            await self._notify_admins(f"用户 {user_id} 因严重威胁已被封禁")

        elif threat_info.severity >= 7:
            # 高风险：临时封禁
            await self._ban_user(user_id, duration='24h', reason=threat_info.reason)

        elif threat_info.severity >= 5:
            # 中风险：限制功能
            await self._restrict_user(user_id, restrictions=['send_media', 'send_links'])

        else:
            # 低风险：警告
            await self._warn_user(user_id, threat_info.reason)

        # 记录日志
        await self._log_security_event(user_id, threat_info)
```

---

## 🎨 前端设计（参考 SafeLine）

### UI/UX 设计理念

SafeLine 的界面特点：
- ✅ **深色主题** - 专业、科技感
- ✅ **数据可视化** - 实时图表、仪表盘
- ✅ **极简设计** - 功能清晰、操作便捷
- ✅ **响应式** - 支持桌面/移动端

### 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│  顶部导航栏                                                   │
│  [Logo] [防护控制台] [客服工作台] [威胁情报] [统计] [设置]    │
└─────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────────────────────────────────────┐
│              │                                              │
│  侧边栏       │              主内容区                         │
│              │                                              │
│  - 实时监控   │  根据不同模块显示内容                          │
│  - 防护规则   │                                              │
│  - 黑白名单   │                                              │
│  - 日志分析   │                                              │
│  - 报警配置   │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### 核心页面设计

#### 1. 防护控制台（SafeLine 风格）

```vue
<!-- ProtectionDashboard.vue -->
<template>
  <div class="protection-dashboard">
    <!-- 顶部统计卡片 -->
    <div class="stats-cards">
      <StatCard
        title="今日拦截"
        :value="stats.blocked_today"
        icon="shield"
        trend="+12%"
        color="red"
      />
      <StatCard
        title="威胁等级"
        :value="stats.threat_level"
        icon="alert"
        color="orange"
      />
      <StatCard
        title="安全评分"
        :value="stats.security_score"
        icon="check"
        color="green"
      />
      <StatCard
        title="在线用户"
        :value="stats.online_users"
        icon="users"
        color="blue"
      />
    </div>

    <!-- 实时流量图表 -->
    <div class="charts-row">
      <ChartCard title="消息流量趋势">
        <LineChart :data="trafficData" />
      </ChartCard>

      <ChartCard title="威胁分布">
        <PieChart :data="threatDistribution" />
      </ChartCard>
    </div>

    <!-- 实时事件日志 -->
    <div class="event-log">
      <h3>实时安全事件</h3>
      <EventTable
        :events="securityEvents"
        :columns="['时间', '用户', '事件类型', '威胁等级', '操作']"
      />
    </div>

    <!-- 防护规则配置 -->
    <div class="protection-rules">
      <h3>防护规则</h3>
      <RuleEditor v-model="rules" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'

const stats = ref({
  blocked_today: 0,
  threat_level: 'LOW',
  security_score: 98,
  online_users: 0
})

const { data: securityEvents } = useWebSocket('/ws/security-events')

onMounted(async () => {
  // 加载统计数据
  stats.value = await fetchStats()
})
</script>

<style scoped>
.protection-dashboard {
  background: #1a1a1a;
  color: #ffffff;
  padding: 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}
</style>
```

#### 2. 客服工作台（结合防护信息）

```vue
<!-- CustomerServiceWorkbench.vue -->
<template>
  <div class="workbench">
    <div class="layout">
      <!-- 左侧：会话列表 -->
      <div class="conversation-list">
        <ConversationItem
          v-for="conv in conversations"
          :key="conv.id"
          :conversation="conv"
          :risk-info="conv.risk_info"  <!-- 显示风险信息 -->
          @click="selectConversation(conv)"
        >
          <!-- 风险标识 -->
          <template #risk-badge>
            <RiskBadge
              v-if="conv.risk_info.level !== 'LOW'"
              :level="conv.risk_info.level"
              :score="conv.risk_info.score"
            />
          </template>
        </ConversationItem>
      </div>

      <!-- 中间：聊天界面 -->
      <div class="chat-area">
        <ChatHeader :user="currentUser" :risk-info="currentUser.risk_info" />

        <MessageList :messages="messages" />

        <!-- 消息输入框（带安全检测） -->
        <MessageInput
          v-model="newMessage"
          :safety-check="true"  <!-- 发送前检测 -->
          @send="sendMessage"
        />
      </div>

      <!-- 右侧：用户信息 + 安全分析 -->
      <div class="user-panel">
        <UserInfo :user="currentUser" />

        <!-- 安全分析面板 -->
        <SecurityAnalysis :user-id="currentUser.id">
          <div class="security-score">
            <h4>用户信誉分</h4>
            <ScoreGauge :score="currentUser.reputation_score" />
          </div>

          <div class="behavior-analysis">
            <h4>行为分析</h4>
            <BehaviorChart :data="behaviorData" />
          </div>

          <div class="threat-history">
            <h4>威胁历史</h4>
            <ThreatTimeline :events="threatEvents" />
          </div>

          <!-- 快速操作 -->
          <div class="quick-actions">
            <button @click="addToBlacklist">加入黑名单</button>
            <button @click="restrictUser">限制功能</button>
            <button @click="reportThreat">上报威胁</button>
          </div>
        </SecurityAnalysis>
      </div>
    </div>
  </div>
</template>
```

#### 3. 威胁情报中心

```vue
<!-- ThreatIntelligence.vue -->
<template>
  <div class="threat-intelligence">
    <!-- 威胁地图 -->
    <div class="threat-map">
      <h3>实时威胁分布</h3>
      <ThreatMap :threats="realTimeThreats" />
    </div>

    <!-- 黑名单管理 -->
    <div class="blacklist-management">
      <h3>黑名单管理</h3>
      <BlacklistTable
        :data="blacklist"
        :columns="['用户ID', '原因', '威胁类型', '严重程度', '时间', '操作']"
        @add="showAddDialog"
        @remove="removeFromBlacklist"
      />
    </div>

    <!-- 威胁趋势分析 -->
    <div class="threat-trends">
      <h3>威胁趋势</h3>
      <TrendChart :data="trendData" />
    </div>

    <!-- 情报源配置 -->
    <div class="intel-sources">
      <h3>情报源</h3>
      <IntelSourceManager :sources="intelSources" />
    </div>
  </div>
</template>
```

---

## 📊 数据库扩展（防护相关表）

### 新增表结构

```sql
-- 安全事件表
CREATE TABLE security_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    event_type VARCHAR(50) NOT NULL COMMENT '事件类型',
    threat_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL COMMENT '威胁等级',
    description TEXT COMMENT '事件描述',
    evidence JSON COMMENT '证据（消息内容、行为数据等）',
    action_taken VARCHAR(100) COMMENT '采取的措施',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_threat_level (threat_level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='安全事件表';

-- 防护规则表
CREATE TABLE protection_rules (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_type VARCHAR(50) NOT NULL COMMENT '规则类型',
    pattern TEXT COMMENT '匹配模式',
    action VARCHAR(50) NOT NULL COMMENT '动作',
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    priority INT DEFAULT 0 COMMENT '优先级',
    config JSON COMMENT '配置参数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='防护规则表';

-- 威胁情报表
CREATE TABLE threat_intelligence (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户 ID',
    threat_type VARCHAR(50) NOT NULL COMMENT '威胁类型',
    severity INT NOT NULL COMMENT '严重程度 1-10',
    reason TEXT COMMENT '原因',
    evidence JSON COMMENT '证据',
    source VARCHAR(50) COMMENT '情报来源',
    auto_block BOOLEAN DEFAULT FALSE COMMENT '是否自动封禁',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_id (user_id),
    INDEX idx_threat_type (threat_type),
    INDEX idx_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='威胁情报表';

-- 用户行为日志表（大数据量，建议用 ClickHouse）
CREATE TABLE user_behavior_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action VARCHAR(50) NOT NULL COMMENT '行为类型',
    metadata JSON COMMENT '行为元数据',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户行为日志';

-- 频率限制记录表（用 Redis 更佳）
CREATE TABLE rate_limit_violations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    limit_type VARCHAR(50) NOT NULL COMMENT '限制类型',
    violation_count INT DEFAULT 1 COMMENT '违规次数',
    last_violation_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='频率限制违规记录';
```

---

## 🚀 部署架构

### Docker Compose 扩展

```yaml
version: '3.8'

services:
  # FastAPI 后端
  backend:
    # ... 原有配置

  # MySQL 数据库
  mysql:
    # ... 原有配置

  # Redis（缓存 + 限流）
  redis:
    # ... 原有配置

  # ClickHouse（日志存储，可选）
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: telegram_customer_clickhouse
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    environment:
      - CLICKHOUSE_DB=telegram_logs
      - CLICKHOUSE_USER=admin
      - CLICKHOUSE_PASSWORD=clickhouse123
    networks:
      - telegram_network

  # Grafana（数据可视化，可选）
  grafana:
    image: grafana/grafana:latest
    container_name: telegram_customer_grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    depends_on:
      - clickhouse
    networks:
      - telegram_network

volumes:
  clickhouse_data:
  grafana_data:
```

---

## 📈 监控和告警

### 实时监控指标

```python
class SecurityMonitor:
    """安全监控"""

    async def collect_metrics(self) -> SecurityMetrics:
        """收集安全指标"""

        return SecurityMetrics(
            # 实时指标
            messages_per_minute=await self._get_message_rate(),
            blocked_messages=await self._get_blocked_count(),
            active_threats=await self._get_active_threats(),

            # 用户指标
            total_users=await self._get_total_users(),
            blacklisted_users=await self._get_blacklist_count(),
            high_risk_users=await self._get_high_risk_users(),

            # 系统指标
            system_health=await self._check_system_health(),
            protection_rules_count=await self._get_rules_count(),
            threat_level=await self._calculate_threat_level()
        )

    async def send_alert(self, alert: Alert):
        """发送告警"""

        if alert.severity >= AlertSeverity.HIGH:
            # 发送到管理员 Telegram
            await self._send_telegram_alert(alert)

            # 发送邮件
            await self._send_email_alert(alert)

            # 写入日志
            await self._log_alert(alert)
```

---

## 🎯 实施路线图

### Phase 1: 基础防护（2 周）
- ✅ 消息防护引擎
- ✅ 频率限制
- ✅ 黑白名单
- ✅ 基础前端界面

### Phase 2: 智能分析（2 周）
- ✅ 用户行为分析
- ✅ 威胁情报系统
- ✅ 自动化响应
- ✅ 数据可视化

### Phase 3: 高级功能（2 周）
- ✅ AI 辅助检测
- ✅ 全局威胁共享
- ✅ 性能优化
- ✅ 完整文档

---

## 📞 技术栈总结

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | Vue 3 + TypeScript | 参考 SafeLine UI |
| 后端 | FastAPI + Python | 高性能异步框架 |
| 数据库 | MySQL 8.0 | 核心数据存储 |
| 缓存 | Redis | 限流 + 缓存 |
| 日志 | ClickHouse（可选） | 海量日志存储 |
| 监控 | Grafana（可选） | 数据可视化 |
| 容器 | Docker + Compose | 一键部署 |

---

**这就是完整的 SafeLine 集成方案！接下来我会逐步实现核心模块。**
