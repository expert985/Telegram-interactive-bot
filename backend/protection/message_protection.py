# -*- coding: utf-8 -*-
"""
消息防护引擎（参考 SafeLine WAF）
检测恶意消息、垃圾广告、钓鱼链接等
"""
import re
import logging
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """威胁等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProtectionAction(str, Enum):
    """防护动作"""
    ALLOW = "ALLOW"          # 允许
    BLOCK = "BLOCK"          # 阻止
    WARN = "WARN"            # 警告
    QUARANTINE = "QUARANTINE"  # 隔离


class ProtectionResult:
    """防护检测结果"""

    def __init__(self):
        self.is_blocked = False
        self.threat_level = ThreatLevel.LOW
        self.reason = ""
        self.action = ProtectionAction.ALLOW
        self.matched_rules = []
        self.evidence = {}

    def to_dict(self) -> dict:
        return {
            "is_blocked": self.is_blocked,
            "threat_level": self.threat_level,
            "reason": self.reason,
            "action": self.action,
            "matched_rules": self.matched_rules,
            "evidence": self.evidence
        }


# ==================== 垃圾消息检测器 ====================

class SpamDetector:
    """垃圾消息检测器"""

    def __init__(self):
        # 垃圾广告特征词库
        self.spam_keywords = [
            # 赌博相关
            "赌博", "博彩", "澳门赌场", "线上赌场", "网上赌博",
            "百家乐", "21点", "轮盘", "老虎机", "德州扑克",

            # 色情相关
            "约炮", "一夜情", "成人网站", "色情视频",

            # 诈骗相关
            "刷单", "兼职", "日赚", "躺赚", "被动收入",
            "投资理财", "高回报", "保本保息", "稳赚不赔",
            "加微信", "加QQ", "加群", "添加好友",

            # 虚假宣传
            "免费领取", "点击领取", "限时优惠", "最后一天",
            "不看后悔", "速来", "快来",

            # 垃圾广告
            "代开发票", "办证", "贷款", "信用卡提额",
        ]

        # 常见垃圾广告模式
        self.spam_patterns = [
            r'微信[:：]?\s*\w+',  # 微信: xxx
            r'QQ[:：]?\s*\d+',    # QQ: 123456
            r'电话[:：]?\s*\d{11}',  # 电话: 13800138000
            r'[\d一二三四五六七八九十百千万]+元/天',  # xx元/天
            r'日入\d+',  # 日入xxx
        ]

    def is_spam(self, text: str) -> bool:
        """判断是否为垃圾消息"""
        if not text:
            return False

        text_lower = text.lower()

        # 1. 关键词匹配
        spam_keyword_count = sum(1 for keyword in self.spam_keywords if keyword in text_lower)

        if spam_keyword_count >= 2:  # 包含2个以上垃圾关键词
            return True

        # 2. 正则模式匹配
        pattern_match_count = sum(1 for pattern in self.spam_patterns if re.search(pattern, text))

        if pattern_match_count >= 2:  # 匹配2个以上模式
            return True

        # 3. 特殊字符比例检测（垃圾广告常用特殊符号）
        special_char_ratio = self._calculate_special_char_ratio(text)
        if special_char_ratio > 0.3:  # 特殊字符超过30%
            return True

        # 4. 大写字母比例检测
        if len(text) > 10:
            upper_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if upper_ratio > 0.5:  # 大写字母超过50%
                return True

        return False

    def _calculate_special_char_ratio(self, text: str) -> float:
        """计算特殊字符比例"""
        if not text:
            return 0

        special_chars = '！!@#￥$%^&*()（）_+-=【】{}|、\\;；:：""\'\'《》<>,.。，？?~·`'
        special_count = sum(1 for char in text if char in special_chars)

        return special_count / len(text)


# ==================== 链接安全扫描器 ====================

class LinkScanner:
    """链接安全扫描器"""

    def __init__(self):
        # 已知恶意域名黑名单
        self.malicious_domains = [
            'malicious-site.com',
            'phishing-site.com',
            # 可以集成外部威胁情报 API
        ]

        # 可疑 TLD（顶级域名）
        self.suspicious_tlds = [
            '.tk', '.ml', '.ga', '.cf', '.gq',  # 免费域名，常被滥用
            '.xyz', '.top', '.click', '.loan',
        ]

        # 短链服务（需要展开检测）
        self.short_url_domains = [
            'bit.ly', 't.co', 'goo.gl', 'tinyurl.com',
            'ow.ly', 'short.link'
        ]

    def is_malicious(self, url: str) -> bool:
        """判断链接是否恶意"""

        # 1. 检查是否在黑名单中
        for domain in self.malicious_domains:
            if domain in url.lower():
                logger.warning(f"检测到黑名单域名: {url}")
                return True

        # 2. 检查可疑 TLD
        for tld in self.suspicious_tlds:
            if url.lower().endswith(tld):
                logger.warning(f"检测到可疑 TLD: {url}")
                return True

        # 3. 检查是否为短链（需要展开检测，此处简化）
        for short_domain in self.short_url_domains:
            if short_domain in url.lower():
                logger.info(f"检测到短链: {url}（建议展开检测）")
                # TODO: 展开短链并递归检测
                pass

        # 4. 检查 IP 地址形式的 URL（可疑）
        if re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
            logger.warning(f"检测到 IP 地址 URL: {url}")
            return True

        return False

    def extract_links(self, text: str) -> List[str]:
        """提取文本中的所有链接"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)


# ==================== 敏感词过滤器 ====================

class SensitiveWordFilter:
    """敏感词过滤器（使用 DFA 算法）"""

    def __init__(self):
        self.sensitive_words = set([
            # 政治敏感词（示例）
            # 根据实际需求添加

            # 暴力相关
            "杀人", "自杀", "爆炸", "恐怖袭击",

            # 违法相关
            "毒品", "大麻", "冰毒", "海洛因",
            "枪支", "军火", "炸药",

            # 其他
            # ...
        ])

        # 构建 DFA 字典树
        self.dfa_tree = self._build_dfa_tree()

    def _build_dfa_tree(self) -> dict:
        """构建 DFA（确定有限状态自动机）字典树"""
        tree = {}

        for word in self.sensitive_words:
            current = tree
            for char in word:
                current = current.setdefault(char, {})
            current['end'] = True

        return tree

    def find(self, text: str) -> List[str]:
        """查找文本中的所有敏感词"""
        if not text:
            return []

        found_words = []
        text_length = len(text)

        for i in range(text_length):
            current = self.dfa_tree
            word = ""

            for j in range(i, text_length):
                char = text[j]

                if char in current:
                    word += char
                    current = current[char]

                    if 'end' in current:
                        found_words.append(word)
                        break
                else:
                    break

        return found_words

    def replace(self, text: str, replacement: str = "*") -> str:
        """替换敏感词"""
        for word in self.find(text):
            text = text.replace(word, replacement * len(word))

        return text


# ==================== 钓鱼检测器 ====================

class PhishingDetector:
    """钓鱼检测器"""

    def __init__(self):
        # 钓鱼特征模式
        self.phishing_patterns = [
            r'验证.*账号',
            r'点击.*链接.*领取',
            r'中奖.*点击',
            r'账户.*异常.*验证',
            r'密码.*过期.*重置',
            r'安全.*认证.*立即',
        ]

    def is_phishing(self, message: dict) -> bool:
        """判断是否为钓鱼消息"""
        text = message.get('text', '')

        if not text:
            return False

        # 1. 检查钓鱼特征模式
        for pattern in self.phishing_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"检测到钓鱼模式: {pattern}")
                return True

        # 2. 检查是否包含链接 + 紧急词汇
        if 'http' in text.lower():
            urgent_words = ['立即', '马上', '紧急', '尽快', '限时', '即将过期']
            if any(word in text for word in urgent_words):
                logger.warning("检测到链接 + 紧急词汇（疑似钓鱼）")
                return True

        return False


# ==================== 消息防护引擎主类 ====================

class MessageProtectionEngine:
    """消息防护引擎（SafeLine 风格）"""

    def __init__(self):
        self.spam_detector = SpamDetector()
        self.link_scanner = LinkScanner()
        self.sensitive_word_filter = SensitiveWordFilter()
        self.phishing_detector = PhishingDetector()

        # 统计信息
        self.stats = {
            'total_checked': 0,
            'total_blocked': 0,
            'spam_blocked': 0,
            'malicious_link_blocked': 0,
            'sensitive_word_blocked': 0,
            'phishing_blocked': 0
        }

    async def check_message(self, message: dict) -> ProtectionResult:
        """
        检查消息是否安全

        Args:
            message: {
                'text': str,
                'user_id': int,
                'username': str,
                'chat_id': int,
                ...
            }

        Returns:
            ProtectionResult
        """
        self.stats['total_checked'] += 1

        result = ProtectionResult()
        text = message.get('text', '')

        if not text:
            return result

        # ==================== 1. 垃圾消息检测 ====================
        if self.spam_detector.is_spam(text):
            result.is_blocked = True
            result.threat_level = ThreatLevel.HIGH
            result.reason = "检测到垃圾广告消息"
            result.action = ProtectionAction.BLOCK
            result.matched_rules.append("spam_detection")

            self.stats['total_blocked'] += 1
            self.stats['spam_blocked'] += 1

            logger.warning(f"[防护] 拦截垃圾消息: User {message.get('user_id')} | {text[:50]}")
            return result

        # ==================== 2. 链接安全检测 ====================
        links = self.link_scanner.extract_links(text)
        if links:
            result.evidence['links'] = links

            for link in links:
                if self.link_scanner.is_malicious(link):
                    result.is_blocked = True
                    result.threat_level = ThreatLevel.CRITICAL
                    result.reason = f"检测到恶意链接: {link}"
                    result.action = ProtectionAction.BLOCK
                    result.matched_rules.append("malicious_link")

                    self.stats['total_blocked'] += 1
                    self.stats['malicious_link_blocked'] += 1

                    logger.error(f"[防护] 拦截恶意链接: User {message.get('user_id')} | {link}")
                    return result

        # ==================== 3. 敏感词过滤 ====================
        sensitive_words = self.sensitive_word_filter.find(text)
        if sensitive_words:
            result.is_blocked = True
            result.threat_level = ThreatLevel.MEDIUM
            result.reason = f"包含敏感词: {', '.join(sensitive_words)}"
            result.action = ProtectionAction.BLOCK
            result.matched_rules.append("sensitive_word")
            result.evidence['sensitive_words'] = sensitive_words

            self.stats['total_blocked'] += 1
            self.stats['sensitive_word_blocked'] += 1

            logger.warning(f"[防护] 拦截敏感词: User {message.get('user_id')} | {sensitive_words}")
            return result

        # ==================== 4. 钓鱼检测 ====================
        if self.phishing_detector.is_phishing(message):
            result.is_blocked = True
            result.threat_level = ThreatLevel.HIGH
            result.reason = "检测到钓鱼攻击"
            result.action = ProtectionAction.BLOCK
            result.matched_rules.append("phishing_detection")

            self.stats['total_blocked'] += 1
            self.stats['phishing_blocked'] += 1

            logger.error(f"[防护] 拦截钓鱼消息: User {message.get('user_id')} | {text[:50]}")
            return result

        # ==================== 5. 所有检测通过 ====================
        result.is_blocked = False
        result.threat_level = ThreatLevel.LOW
        result.action = ProtectionAction.ALLOW

        return result

    def get_stats(self) -> dict:
        """获取防护统计信息"""
        return {
            **self.stats,
            'block_rate': (
                self.stats['total_blocked'] / self.stats['total_checked']
                if self.stats['total_checked'] > 0 else 0
            )
        }

    def reset_stats(self):
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0


# ==================== 全局实例 ====================

# 创建全局防护引擎实例
protection_engine = MessageProtectionEngine()


def get_protection_engine() -> MessageProtectionEngine:
    """获取防护引擎实例"""
    return protection_engine


# ==================== 测试代码 ====================

if __name__ == "__main__":
    import asyncio

    async def test():
        engine = MessageProtectionEngine()

        # 测试消息列表
        test_messages = [
            {"text": "你好，请问有什么可以帮助你的吗？", "user_id": 123},
            {"text": "加微信: abc123，日赚500元，不看后悔！", "user_id": 456},
            {"text": "点击链接领取奖品: http://malicious-site.com/gift", "user_id": 789},
            {"text": "这个产品不错，推荐给你", "user_id": 111},
        ]

        print("=" * 60)
        print("消息防护引擎测试")
        print("=" * 60)

        for msg in test_messages:
            result = await engine.check_message(msg)

            print(f"\n消息: {msg['text']}")
            print(f"结果: {'❌ 拦截' if result.is_blocked else '✅ 通过'}")
            print(f"威胁等级: {result.threat_level}")
            print(f"原因: {result.reason}")
            print(f"匹配规则: {result.matched_rules}")

        print("\n" + "=" * 60)
        print("防护统计:")
        print(engine.get_stats())
        print("=" * 60)

    asyncio.run(test())
