# Telegram Interactive Bot - 功能新增建议方案

**文档版本**: 1.0
**日期**: 2025-10-28
**目标**: 提升用户体验、增强管理功能、扩展应用场景

---

## 目录

1. [用户体验增强](#1-用户体验增强)
2. [管理功能增强](#2-管理功能增强)
3. [高级功能](#3-高级功能)
4. [集成和扩展](#4-集成和扩展)
5. [数据分析和报表](#5-数据分析和报表)
6. [自动化功能](#6-自动化功能)
7. [实施路线图](#7-实施路线图)

---

## 1. 用户体验增强

### 1.1 富文本欢迎消息

**功能描述**: 支持自定义欢迎消息，包括按钮、图片、视频等

**实施方案**:

```python
# services/welcome_service.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class WelcomeService:
    """欢迎消息服务"""

    async def send_welcome(
        self,
        user: User,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """发送自定义欢迎消息"""
        # 从配置或数据库加载欢迎内容
        welcome_config = self._load_welcome_config()

        # 构建按钮
        buttons = []
        if welcome_config.get('show_faq_button'):
            buttons.append([
                InlineKeyboardButton("📖 常见问题", callback_data="show_faq")
            ])
        if welcome_config.get('show_services_button'):
            buttons.append([
                InlineKeyboardButton("🛠️ 服务介绍", callback_data="show_services")
            ])
        if welcome_config.get('show_contact_button'):
            buttons.append([
                InlineKeyboardButton("💬 联系客服", callback_data="start_chat")
            ])

        # 发送欢迎消息
        if welcome_config.get('welcome_image'):
            await context.bot.send_photo(
                chat_id=user.id,
                photo=welcome_config['welcome_image'],
                caption=welcome_config['welcome_text'],
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text=welcome_config['welcome_text'],
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='HTML'
            )

# 配置示例
welcome_config = {
    'welcome_text': """
👋 欢迎来到客服中心！

我们的客服团队随时为您服务。
工作时间：周一至周五 9:00-18:00

请选择您需要的服务：
    """,
    'welcome_image': 'https://example.com/welcome.jpg',
    'show_faq_button': True,
    'show_services_button': True,
    'show_contact_button': True
}
```

**用户价值**:
- 🎨 更专业的第一印象
- 📱 清晰的服务导航
- ⏱️ 减少用户困惑时间

---

### 1.2 快捷回复按钮

**功能描述**: 用户可以通过预设按钮快速发送常见问题

**实施方案**:

```python
# handlers/quick_reply_handler.py
class QuickReplyHandler:
    """快捷回复处理器"""

    QUICK_REPLIES = {
        'order_status': '我想查询订单状态',
        'refund': '我要申请退款',
        'technical_support': '遇到技术问题需要帮助',
        'billing': '关于账单的问题',
        'other': '其他问题'
    }

    async def show_quick_replies(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """显示快捷回复按钮"""
        buttons = [
            [InlineKeyboardButton(text, callback_data=f"quick_{key}")]
            for key, text in self.QUICK_REPLIES.items()
        ]

        await update.message.reply_text(
            "请选择您的问题类型，以便我们更快地为您服务：",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def handle_quick_reply(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """处理快捷回复"""
        query = update.callback_query
        reply_key = query.data.replace("quick_", "")

        # 记录用户选择的问题类型
        context.user_data['issue_type'] = reply_key

        # 转发到管理群组（带标签）
        message_text = f"🏷️ 问题类型: {self.QUICK_REPLIES[reply_key]}"
        # ... 转发逻辑

        await query.answer("已收到，客服将尽快回复")
```

**用户价值**:
- ⚡ 快速表达问题
- 🎯 问题分类清晰
- 📊 便于统计常见问题

---

### 1.3 消息状态提示

**功能描述**: 显示消息已读、客服正在输入等状态

**实施方案**:

```python
# services/message_status_service.py
class MessageStatusService:
    """消息状态服务"""

    async def notify_message_read(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """通知用户消息已读"""
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ 客服已读您的消息",
            disable_notification=True
        )

    async def notify_typing(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """显示客服正在输入"""
        await context.bot.send_chat_action(
            chat_id=user_id,
            action="typing"
        )

# handlers/admin_handler.py
async def forwarding_message_a2u_enhanced(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """管理员消息转发（增强版）"""
    # 获取目标用户
    user_id = get_user_from_thread(update.message.message_thread_id)

    # 显示正在输入
    await context.bot.send_chat_action(chat_id=user_id, action="typing")

    # 转发消息
    await forward_message(update, context, user_id)

    # 标记消息已读（在管理群组）
    await update.message.react("👀")
```

**用户价值**:
- 👀 知道消息已被看到
- ⌨️ 知道客服正在回复
- 😊 更好的互动体验

---

### 1.4 多语言支持

**功能描述**: 自动检测用户语言，提供多语言界面

**实施方案**:

```python
# services/i18n_service.py
from typing import Dict
import gettext

class I18nService:
    """国际化服务"""

    def __init__(self):
        self.translations: Dict[str, dict] = {
            'en': {
                'welcome': 'Welcome! How can we help you?',
                'conversation_closed': 'Conversation is closed',
                'rate_limit': 'Please don\'t send messages too frequently',
            },
            'zh': {
                'welcome': '欢迎！有什么可以帮助您的吗？',
                'conversation_closed': '对话已关闭',
                'rate_limit': '请不要频繁发送消息',
            },
            'es': {
                'welcome': '¡Bienvenido! ¿Cómo podemos ayudarle?',
                'conversation_closed': 'La conversación está cerrada',
                'rate_limit': 'Por favor, no envíe mensajes con frecuencia',
            },
            'ru': {
                'welcome': 'Добро пожаловать! Чем мы можем вам помочь?',
                'conversation_closed': 'Разговор закрыт',
                'rate_limit': 'Пожалуйста, не отправляйте сообщения слишком часто',
            }
        }

    def detect_language(self, user: TelegramUser) -> str:
        """检测用户语言"""
        if hasattr(user, 'language_code') and user.language_code:
            lang = user.language_code.split('-')[0]
            if lang in self.translations:
                return lang
        return 'en'  # 默认英语

    def get_text(self, key: str, lang: str = 'en') -> str:
        """获取翻译文本"""
        return self.translations.get(lang, {}).get(key, key)

# 使用
i18n = I18nService()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = i18n.detect_language(user)
    context.user_data['language'] = lang

    welcome_text = i18n.get_text('welcome', lang)
    await update.message.reply_text(welcome_text)
```

**用户价值**:
- 🌍 支持全球用户
- 🗣️ 母语交流更舒适
- 📈 扩大用户群体

---

### 1.5 文件上传进度提示

**功能描述**: 大文件上传时显示进度

**实施方案**:

```python
# handlers/file_handler.py
import asyncio

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理文档上传"""
    document = update.message.document

    # 如果文件较大，显示处理中提示
    if document.file_size > 5 * 1024 * 1024:  # 5MB
        status_msg = await update.message.reply_text(
            "📤 正在处理大文件，请稍候...\n⏳ 0%"
        )

        # 模拟进度更新（实际应根据真实进度）
        for progress in [25, 50, 75, 100]:
            await asyncio.sleep(1)
            await status_msg.edit_text(
                f"📤 正在处理大文件，请稍候...\n⏳ {progress}%"
            )

        await status_msg.edit_text("✅ 文件已发送给客服")

    # 转发文件
    await forward_document(update, context)
```

**用户价值**:
- ⏱️ 了解处理进度
- 🔄 避免重复发送
- 😌 减少焦虑感

---

## 2. 管理功能增强

### 2.1 客服工作台

**功能描述**: 为客服提供专门的工作台，显示待处理对话、统计数据等

**实施方案**:

```python
# handlers/admin_dashboard_handler.py
class AdminDashboardHandler:
    """管理员工作台"""

    async def show_dashboard(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """显示工作台"""
        # 获取统计数据
        stats = await self._get_statistics()

        dashboard_text = f"""
📊 **客服工作台**

🔔 待处理对话: {stats['pending_conversations']}
💬 今日消息数: {stats['today_messages']}
👥 今日新用户: {stats['today_new_users']}
⏱️ 平均响应时间: {stats['avg_response_time']}

🟢 在线客服: {stats['online_admins']}
📈 本周趋势: {stats['week_trend']}
        """

        buttons = [
            [InlineKeyboardButton("📋 待处理列表", callback_data="pending_list")],
            [InlineKeyboardButton("📊 详细统计", callback_data="detailed_stats")],
            [InlineKeyboardButton("⚙️ 设置", callback_data="admin_settings")],
        ]

        await update.message.reply_text(
            dashboard_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )

    async def show_pending_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """显示待处理对话列表"""
        pending_conversations = db.query(User).filter(
            User.last_message_time > datetime.now() - timedelta(hours=24),
            User.last_reply_time.is_(None)
        ).all()

        text = "📋 **待处理对话**\n\n"
        buttons = []

        for user in pending_conversations:
            waiting_time = datetime.now() - user.last_message_time
            text += f"👤 {user.first_name} - 等待 {format_timedelta(waiting_time)}\n"
            buttons.append([
                InlineKeyboardButton(
                    f"➡️ {user.first_name}",
                    url=f"https://t.me/c/{abs(admin_group_id)}/{user.message_thread_id}"
                )
            ])

        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )

    async def _get_statistics(self) -> dict:
        """获取统计数据"""
        today = datetime.now().date()

        return {
            'pending_conversations': db.query(User).filter(
                User.last_message_time > datetime.now() - timedelta(hours=24),
                User.last_reply_time.is_(None)
            ).count(),
            'today_messages': db.query(MessageMap).filter(
                MessageMap.created_at >= today
            ).count(),
            'today_new_users': db.query(User).filter(
                User.created_at >= today
            ).count(),
            'avg_response_time': self._calculate_avg_response_time(),
            'online_admins': len(context.application.user_data),
            'week_trend': self._calculate_week_trend()
        }
```

**客服价值**:
- 📊 一目了然的工作概况
- ⚡ 快速访问待处理对话
- 📈 了解工作表现

---

### 2.2 对话标签系统

**功能描述**: 为对话添加标签，便于分类和检索

**实施方案**:

```python
# db/models.py
class ConversationTag(Base):
    __tablename__ = "conversation_tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True)
    color = Column(String(16))  # 颜色代码
    icon = Column(String(8))    # emoji
    created_at = Column(DateTime, default=func.now())

class UserTag(Base):
    __tablename__ = "user_tags"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    tag_id = Column(Integer, ForeignKey('conversation_tags.id'))
    added_by = Column(Integer)  # 添加标签的管理员ID
    added_at = Column(DateTime, default=func.now())

# handlers/tag_handler.py
class TagHandler:
    """标签处理器"""

    async def add_tag(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """为对话添加标签"""
        # 解析命令: /tag add 技术支持
        args = context.args
        if not args or args[0] != 'add':
            await self.show_tag_usage(update)
            return

        tag_name = ' '.join(args[1:])
        thread_id = update.message.message_thread_id

        # 获取用户
        user = db.query(User).filter(
            User.message_thread_id == thread_id
        ).first()

        if not user:
            await update.message.reply_text("❌ 未找到对应的用户")
            return

        # 获取或创建标签
        tag = db.query(ConversationTag).filter(
            ConversationTag.name == tag_name
        ).first()

        if not tag:
            tag = ConversationTag(
                name=tag_name,
                color='#3498db',
                icon='🏷️'
            )
            db.add(tag)
            db.commit()

        # 添加标签关联
        user_tag = UserTag(
            user_id=user.id,
            tag_id=tag.id,
            added_by=update.effective_user.id
        )
        db.add(user_tag)
        db.commit()

        # 更新论坛主题名称
        current_name = f"{user.first_name}|{user.user_id}"
        new_name = f"{tag.icon} {current_name}"

        await context.bot.edit_forum_topic(
            chat_id=admin_group_id,
            message_thread_id=thread_id,
            name=new_name
        )

        await update.message.reply_text(f"✅ 已添加标签: {tag.icon} {tag_name}")

    async def search_by_tag(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """按标签搜索对话"""
        # /tag search 技术支持
        if not context.args or context.args[0] != 'search':
            return

        tag_name = ' '.join(context.args[1:])

        # 查询带该标签的用户
        results = db.query(User).join(UserTag).join(ConversationTag).filter(
            ConversationTag.name.like(f"%{tag_name}%")
        ).all()

        if not results:
            await update.message.reply_text(f"❌ 未找到标签包含 '{tag_name}' 的对话")
            return

        text = f"🔍 找到 {len(results)} 个对话:\n\n"
        buttons = []

        for user in results:
            tags = [ut.tag.name for ut in user.tags]
            text += f"👤 {user.first_name} - 标签: {', '.join(tags)}\n"
            buttons.append([
                InlineKeyboardButton(
                    f"➡️ {user.first_name}",
                    url=f"https://t.me/c/{abs(admin_group_id)}/{user.message_thread_id}"
                )
            ])

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
```

**客服价值**:
- 🏷️ 快速分类对话
- 🔍 便于检索历史对话
- 📊 统计不同类型问题

---

### 2.3 客服绩效统计

**功能描述**: 统计每个客服的工作量和响应时间

**实施方案**:

```python
# db/models.py
class AdminAction(Base):
    __tablename__ = "admin_actions"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer)
    action_type = Column(String(32))  # reply, close, tag, etc.
    user_id = Column(Integer)
    message_id = Column(Integer)
    response_time = Column(Integer)  # 响应时间（秒）
    created_at = Column(DateTime, default=func.now())

# services/performance_service.py
class PerformanceService:
    """绩效统计服务"""

    async def get_admin_performance(
        self,
        admin_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """获取客服绩效数据"""
        actions = db.query(AdminAction).filter(
            AdminAction.admin_id == admin_id,
            AdminAction.created_at.between(start_date, end_date)
        ).all()

        total_replies = len([a for a in actions if a.action_type == 'reply'])
        total_closed = len([a for a in actions if a.action_type == 'close'])

        response_times = [
            a.response_time for a in actions
            if a.response_time is not None
        ]

        return {
            'admin_id': admin_id,
            'period': f"{start_date.date()} - {end_date.date()}",
            'total_replies': total_replies,
            'total_closed': total_closed,
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
        }

    async def generate_performance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """生成绩效报告"""
        report = "📊 **客服绩效报告**\n\n"
        report += f"📅 统计周期: {start_date.date()} - {end_date.date()}\n\n"

        for admin_id in admin_user_ids:
            perf = await self.get_admin_performance(admin_id, start_date, end_date)

            admin = await context.bot.get_chat(admin_id)
            report += f"👤 **{admin.first_name}**\n"
            report += f"  💬 回复消息: {perf['total_replies']}\n"
            report += f"  ✅ 关闭对话: {perf['total_closed']}\n"
            report += f"  ⏱️ 平均响应: {format_seconds(perf['avg_response_time'])}\n\n"

        return report

# 命令处理
async def performance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示绩效统计"""
    if update.effective_user.id not in admin_user_ids:
        return

    # 默认显示本周数据
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())

    service = PerformanceService()
    report = await service.generate_performance_report(start_of_week, today)

    await update.message.reply_text(report, parse_mode='Markdown')
```

**客服价值**:
- 📈 了解个人工作表现
- 🏆 激励优秀客服
- 📊 管理层决策依据

---

### 2.4 智能分配系统

**功能描述**: 根据客服在线状态和工作负载智能分配新对话

**实施方案**:

```python
# services/assignment_service.py
from collections import defaultdict

class AssignmentService:
    """对话分配服务"""

    def __init__(self):
        self.admin_workload: Dict[int, int] = defaultdict(int)
        self.admin_status: Dict[int, str] = {}  # online, busy, away

    def get_available_admin(self) -> Optional[int]:
        """获取可用的客服"""
        # 筛选在线客服
        online_admins = [
            admin_id for admin_id, status in self.admin_status.items()
            if status == 'online'
        ]

        if not online_admins:
            return None

        # 选择工作负载最低的客服
        return min(online_admins, key=lambda x: self.admin_workload[x])

    async def assign_conversation(
        self,
        user: User,
        context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """分配对话给客服"""
        admin_id = self.get_available_admin()

        if not admin_id:
            # 没有在线客服，使用轮询
            admin_id = admin_user_ids[user.id % len(admin_user_ids)]

        # 更新工作负载
        self.admin_workload[admin_id] += 1

        # 通知被分配的客服
        await context.bot.send_message(
            admin_id,
            f"🔔 新对话已分配给您\n"
            f"👤 用户: {user.first_name}\n"
            f"🔗 点击查看对话",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "查看对话",
                    url=f"https://t.me/c/{abs(admin_group_id)}/{user.message_thread_id}"
                )
            ]])
        )

        # 记录分配
        assignment = ConversationAssignment(
            user_id=user.id,
            admin_id=admin_id,
            assigned_at=datetime.now()
        )
        db.add(assignment)
        db.commit()

        return admin_id

    def update_admin_status(self, admin_id: int, status: str):
        """更新客服状态"""
        self.admin_status[admin_id] = status

    def conversation_closed(self, admin_id: int):
        """对话关闭，减少工作负载"""
        if self.admin_workload[admin_id] > 0:
            self.admin_workload[admin_id] -= 1

# 状态切换命令
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """切换客服状态"""
    if update.effective_user.id not in admin_user_ids:
        return

    buttons = [
        [InlineKeyboardButton("🟢 在线", callback_data="status_online")],
        [InlineKeyboardButton("🟡 忙碌", callback_data="status_busy")],
        [InlineKeyboardButton("🔴 离开", callback_data="status_away")],
    ]

    await update.message.reply_text(
        "请选择您的状态：",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
```

**客服价值**:
- ⚖️ 均衡工作负载
- 🎯 提高响应效率
- 🔔 及时接收新对话通知

---

### 2.5 预设回复模板

**功能描述**: 客服可以使用预设模板快速回复常见问题

**实施方案**:

```python
# db/models.py
class ReplyTemplate(Base):
    __tablename__ = "reply_templates"
    id = Column(Integer, primary_key=True)
    shortcut = Column(String(32), unique=True)  # 快捷键
    title = Column(String(128))
    content = Column(Text)
    category = Column(String(64))
    usage_count = Column(Integer, default=0)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=func.now())

# handlers/template_handler.py
class TemplateHandler:
    """模板处理器"""

    async def list_templates(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """列出所有模板"""
        templates = db.query(ReplyTemplate).order_by(
            ReplyTemplate.category,
            ReplyTemplate.usage_count.desc()
        ).all()

        text = "📝 **快捷回复模板**\n\n"

        by_category = defaultdict(list)
        for template in templates:
            by_category[template.category].append(template)

        for category, tmps in by_category.items():
            text += f"**{category}**\n"
            for tmp in tmps:
                text += f"  /{tmp.shortcut} - {tmp.title}\n"
            text += "\n"

        text += "💡 使用方法: /{shortcut} 发送模板内容"

        await update.message.reply_text(text, parse_mode='Markdown')

    async def use_template(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        shortcut: str
    ):
        """使用模板"""
        template = db.query(ReplyTemplate).filter(
            ReplyTemplate.shortcut == shortcut
        ).first()

        if not template:
            await update.message.reply_text(f"❌ 未找到模板: {shortcut}")
            return

        # 获取对话中的用户
        thread_id = update.message.message_thread_id
        user = db.query(User).filter(
            User.message_thread_id == thread_id
        ).first()

        if not user:
            await update.message.reply_text("❌ 请在对话线程中使用")
            return

        # 发送模板内容给用户
        await context.bot.send_message(
            chat_id=user.user_id,
            text=template.content,
            parse_mode='HTML'
        )

        # 更新使用次数
        template.usage_count += 1
        db.commit()

        # 在管理群组确认
        await update.message.reply_text(
            f"✅ 已发送模板: {template.title}",
            message_thread_id=thread_id
        )

# 预设模板示例
DEFAULT_TEMPLATES = [
    {
        'shortcut': 'welcome',
        'title': '欢迎语',
        'content': '您好！我是客服团队的成员，很高兴为您服务。请问有什么可以帮助您的？',
        'category': '问候'
    },
    {
        'shortcut': 'wait',
        'title': '请稍等',
        'content': '好的，我正在为您查询，请稍等片刻...',
        'category': '处理中'
    },
    {
        'shortcut': 'solved',
        'title': '问题解决',
        'content': '很高兴能帮助到您！如果还有其他问题，随时联系我们。',
        'category': '结束'
    },
    {
        'shortcut': 'hours',
        'title': '工作时间',
        'content': '我们的工作时间是周一至周五 9:00-18:00。当前非工作时间，我们会在下个工作日尽快回复您。',
        'category': '信息'
    },
]
```

**客服价值**:
- ⚡ 快速回复提高效率
- ✅ 标准化回复内容
- 📊 了解常用模板

---

## 3. 高级功能

### 3.1 AI 智能回复建议

**功能描述**: 使用 AI 分析用户消息，为客服提供回复建议

**实施方案**:

```python
# services/ai_service.py
import openai

class AIAssistantService:
    """AI 助手服务"""

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    async def get_reply_suggestion(
        self,
        user_message: str,
        conversation_history: List[dict]
    ) -> str:
        """获取回复建议"""
        messages = [
            {
                "role": "system",
                "content": "你是一个客服助手，帮助客服人员回复用户问题。请提供专业、友好的回复建议。"
            }
        ]

        # 添加对话历史
        for msg in conversation_history[-5:]:  # 最近5条
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200
        )

        return response.choices[0].message.content

    async def analyze_sentiment(self, text: str) -> dict:
        """分析情感倾向"""
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "分析以下文本的情感倾向，返回：positive（积极）、neutral（中性）或 negative（消极）"
                },
                {"role": "user", "content": text}
            ]
        )

        sentiment = response.choices[0].message.content.strip().lower()

        return {
            'sentiment': sentiment,
            'emoji': {
                'positive': '😊',
                'neutral': '😐',
                'negative': '😢'
            }.get(sentiment, '😐')
        }

# handlers/user_handler.py (增强版)
async def forwarding_message_u2a_with_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """转发用户消息并提供 AI 建议"""
    # 原有的转发逻辑
    await forward_message(update, context)

    # AI 分析和建议
    if ai_service:
        # 情感分析
        sentiment = await ai_service.analyze_sentiment(update.message.text)

        # 获取回复建议
        conversation_history = get_conversation_history(update.effective_user.id)
        suggestion = await ai_service.get_reply_suggestion(
            update.message.text,
            conversation_history
        )

        # 发送建议到管理群组
        thread_id = get_user_thread_id(update.effective_user.id)
        await context.bot.send_message(
            chat_id=admin_group_id,
            message_thread_id=thread_id,
            text=f"🤖 **AI 建议**\n\n"
                 f"😊 情感: {sentiment['emoji']} {sentiment['sentiment']}\n\n"
                 f"💡 建议回复:\n{suggestion}\n\n"
                 f"_点击使用或自行修改_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ 使用此回复", callback_data=f"use_ai_{message_id}")
            ]])
        )
```

**客服价值**:
- 🤖 AI 辅助提高效率
- 💡 新手客服培训辅助
- 😊 情感分析辅助判断用户状态

---

### 3.2 自动回复规则

**功能描述**: 设置自动回复规则，常见问题自动回复

**实施方案**:

```python
# db/models.py
class AutoReplyRule(Base):
    __tablename__ = "auto_reply_rules"
    id = Column(Integer, primary_key=True)
    trigger_type = Column(String(32))  # keyword, regex, time, user_status
    trigger_value = Column(Text)
    reply_content = Column(Text)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # 优先级
    created_at = Column(DateTime, default=func.now())

# services/auto_reply_service.py
import re

class AutoReplyService:
    """自动回复服务"""

    async def check_auto_reply(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """检查是否触发自动回复"""
        message_text = update.message.text

        # 按优先级查询规则
        rules = db.query(AutoReplyRule).filter(
            AutoReplyRule.is_active == True
        ).order_by(AutoReplyRule.priority.desc()).all()

        for rule in rules:
            if self._check_rule(rule, message_text, update):
                await self._send_auto_reply(rule, update, context)
                return True

        return False

    def _check_rule(
        self,
        rule: AutoReplyRule,
        message_text: str,
        update: Update
    ) -> bool:
        """检查规则是否匹配"""
        if rule.trigger_type == 'keyword':
            # 关键词匹配
            keywords = rule.trigger_value.split('|')
            return any(kw.lower() in message_text.lower() for kw in keywords)

        elif rule.trigger_type == 'regex':
            # 正则匹配
            return bool(re.search(rule.trigger_value, message_text))

        elif rule.trigger_type == 'time':
            # 时间段匹配（非工作时间）
            hour = datetime.now().hour
            start, end = map(int, rule.trigger_value.split('-'))
            return not (start <= hour < end)

        return False

    async def _send_auto_reply(
        self,
        rule: AutoReplyRule,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """发送自动回复"""
        await update.message.reply_text(
            f"🤖 自动回复\n\n{rule.reply_content}",
            parse_mode='HTML'
        )

        # 记录自动回复
        log = AutoReplyLog(
            rule_id=rule.id,
            user_id=update.effective_user.id,
            message_text=update.message.text,
            created_at=datetime.now()
        )
        db.add(log)
        db.commit()

# 预设规则示例
DEFAULT_AUTO_REPLY_RULES = [
    {
        'trigger_type': 'keyword',
        'trigger_value': '工作时间|营业时间|上班时间',
        'reply_content': '我们的工作时间是：\n周一至周五：9:00-18:00\n周六日：休息',
        'priority': 10
    },
    {
        'trigger_type': 'keyword',
        'trigger_value': '价格|多少钱|费用',
        'reply_content': '关于价格信息，请访问我们的官网查看详细价目表，或等待客服为您提供准确报价。',
        'priority': 5
    },
    {
        'trigger_type': 'time',
        'trigger_value': '9-18',  # 非9-18点
        'reply_content': '感谢您的留言！当前为非工作时间，我们会在下个工作日尽快回复您。',
        'priority': 15
    }
]
```

**用户价值**:
- ⚡ 常见问题即时回复
- 🌙 非工作时间自动告知
- 📊 减少客服重复工作

---

### 3.3 对话评价系统

**功能描述**: 对话结束后，用户可以评价客服服务

**实施方案**:

```python
# db/models.py
class ConversationRating(Base):
    __tablename__ = "conversation_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    admin_id = Column(Integer)
    rating = Column(Integer)  # 1-5星
    comment = Column(Text)
    created_at = Column(DateTime, default=func.now())

# services/rating_service.py
class RatingService:
    """评价服务"""

    async def request_rating(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """请求用户评价"""
        buttons = [
            [
                InlineKeyboardButton("⭐", callback_data="rate_1"),
                InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
                InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
            ],
            [
                InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5"),
            ],
            [
                InlineKeyboardButton("⏭️ 跳过", callback_data="rate_skip")
            ]
        ]

        await context.bot.send_message(
            chat_id=user_id,
            text="感谢您使用我们的服务！\n请为本次客服体验打分：",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def save_rating(
        self,
        user_id: int,
        rating: int,
        admin_id: int
    ):
        """保存评价"""
        rating_record = ConversationRating(
            user_id=user_id,
            admin_id=admin_id,
            rating=rating,
            created_at=datetime.now()
        )
        db.add(rating_record)
        db.commit()

        # 通知客服
        if rating >= 4:
            emoji = "🎉"
            message = f"{emoji} 您收到了一个好评！⭐ {rating}/5"
        else:
            emoji = "📝"
            message = f"{emoji} 您收到了一个评价：⭐ {rating}/5"

        await context.bot.send_message(admin_id, message)

    async def get_admin_rating_stats(self, admin_id: int) -> dict:
        """获取客服评价统计"""
        ratings = db.query(ConversationRating).filter(
            ConversationRating.admin_id == admin_id
        ).all()

        if not ratings:
            return {'avg_rating': 0, 'total_ratings': 0}

        total = len(ratings)
        avg = sum(r.rating for r in ratings) / total

        distribution = defaultdict(int)
        for r in ratings:
            distribution[r.rating] += 1

        return {
            'avg_rating': round(avg, 2),
            'total_ratings': total,
            'distribution': dict(distribution)
        }

# 对话关闭时触发
async def close_conversation_with_rating(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """关闭对话并请求评价"""
    # 原有的关闭逻辑
    thread_id = update.message.message_thread_id
    user = db.query(User).filter(
        User.message_thread_id == thread_id
    ).first()

    await context.bot.close_forum_topic(admin_group_id, thread_id)

    # 发送通知给用户
    await context.bot.send_message(
        user.user_id,
        "对话已结束，感谢您的咨询！"
    )

    # 请求评价
    rating_service = RatingService()
    await rating_service.request_rating(user.user_id, context)
```

**客服价值**:
- 📊 了解服务质量
- 🏆 激励优秀表现
- 📈 持续改进依据

---

### 3.4 知识库系统

**功能描述**: 内置知识库，客服可快速搜索和分享解决方案

**实施方案**:

```python
# db/models.py
class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    content = Column(Text)
    category = Column(String(64))
    tags = Column(String(256))  # 逗号分隔的标签
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# services/knowledge_service.py
class KnowledgeService:
    """知识库服务"""

    async def search_articles(
        self,
        query: str,
        limit: int = 5
    ) -> List[KnowledgeArticle]:
        """搜索文章"""
        # 简单的全文搜索
        articles = db.query(KnowledgeArticle).filter(
            or_(
                KnowledgeArticle.title.like(f"%{query}%"),
                KnowledgeArticle.content.like(f"%{query}%"),
                KnowledgeArticle.tags.like(f"%{query}%")
            )
        ).order_by(
            KnowledgeArticle.view_count.desc()
        ).limit(limit).all()

        return articles

    async def get_article(self, article_id: int) -> Optional[KnowledgeArticle]:
        """获取文章详情"""
        article = db.query(KnowledgeArticle).filter(
            KnowledgeArticle.id == article_id
        ).first()

        if article:
            # 增加浏览次数
            article.view_count += 1
            db.commit()

        return article

    async def mark_helpful(self, article_id: int):
        """标记文章有帮助"""
        article = db.query(KnowledgeArticle).filter(
            KnowledgeArticle.id == article_id
        ).first()

        if article:
            article.helpful_count += 1
            db.commit()

# handlers/knowledge_handler.py
class KnowledgeHandler:
    """知识库处理器"""

    async def search_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """搜索知识库"""
        # /kb search 退款流程
        if not context.args or context.args[0] != 'search':
            return

        query = ' '.join(context.args[1:])
        service = KnowledgeService()
        articles = await service.search_articles(query)

        if not articles:
            await update.message.reply_text(f"❌ 未找到相关文章")
            return

        text = f"🔍 找到 {len(articles)} 篇相关文章:\n\n"
        buttons = []

        for article in articles:
            text += f"📄 {article.title}\n"
            text += f"   👁️ {article.view_count} | 👍 {article.helpful_count}\n\n"
            buttons.append([
                InlineKeyboardButton(
                    article.title[:30],
                    callback_data=f"kb_{article.id}"
                )
            ])

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def show_article(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """显示文章详情"""
        query = update.callback_query
        article_id = int(query.data.replace("kb_", ""))

        service = KnowledgeService()
        article = await service.get_article(article_id)

        if not article:
            await query.answer("❌ 文章不存在")
            return

        text = f"📄 **{article.title}**\n\n"
        text += f"{article.content}\n\n"
        text += f"🏷️ 标签: {article.tags}\n"
        text += f"👁️ 浏览: {article.view_count} | 👍 有用: {article.helpful_count}"

        buttons = [
            [InlineKeyboardButton("👍 有用", callback_data=f"kb_helpful_{article_id}")],
            [InlineKeyboardButton("📤 分享给用户", callback_data=f"kb_share_{article_id}")],
        ]

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )

    async def share_article(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """分享文章给用户"""
        query = update.callback_query
        article_id = int(query.data.replace("kb_share_", ""))

        # 获取当前对话的用户
        thread_id = query.message.message_thread_id
        user = db.query(User).filter(
            User.message_thread_id == thread_id
        ).first()

        if not user:
            await query.answer("❌ 请在对话线程中操作")
            return

        # 获取文章
        service = KnowledgeService()
        article = await service.get_article(article_id)

        # 发送给用户
        await context.bot.send_message(
            chat_id=user.user_id,
            text=f"📄 **{article.title}**\n\n{article.content}",
            parse_mode='Markdown'
        )

        await query.answer("✅ 已发送给用户")
```

**客服价值**:
- 📚 快速找到解决方案
- 🔄 知识沉淀和复用
- 🎓 新人培训材料

---

## 4. 集成和扩展

### 4.1 工单系统集成

**功能描述**: 将复杂问题转为工单，跟踪处理进度

**实施方案**:

```python
# db/models.py
class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    ticket_number = Column(String(32), unique=True)  # TKT-20250101-0001
    user_id = Column(Integer)
    subject = Column(String(256))
    description = Column(Text)
    status = Column(String(32))  # open, in_progress, resolved, closed
    priority = Column(String(32))  # low, medium, high, urgent
    assigned_to = Column(Integer)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    resolved_at = Column(DateTime)

class TicketComment(Base):
    __tablename__ = "ticket_comments"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'))
    user_id = Column(Integer)
    comment = Column(Text)
    is_internal = Column(Boolean, default=False)  # 内部备注
    created_at = Column(DateTime, default=func.now())

# services/ticket_service.py
class TicketService:
    """工单服务"""

    def generate_ticket_number(self) -> str:
        """生成工单编号"""
        today = datetime.now().strftime("%Y%m%d")
        count = db.query(Ticket).filter(
            Ticket.ticket_number.like(f"TKT-{today}%")
        ).count()
        return f"TKT-{today}-{count + 1:04d}"

    async def create_ticket(
        self,
        user_id: int,
        subject: str,
        description: str,
        priority: str = "medium",
        created_by: int = None
    ) -> Ticket:
        """创建工单"""
        ticket = Ticket(
            ticket_number=self.generate_ticket_number(),
            user_id=user_id,
            subject=subject,
            description=description,
            status="open",
            priority=priority,
            created_by=created_by or user_id,
            created_at=datetime.now()
        )
        db.add(ticket)
        db.commit()

        return ticket

    async def add_comment(
        self,
        ticket_id: int,
        user_id: int,
        comment: str,
        is_internal: bool = False
    ):
        """添加评论"""
        comment = TicketComment(
            ticket_id=ticket_id,
            user_id=user_id,
            comment=comment,
            is_internal=is_internal,
            created_at=datetime.now()
        )
        db.add(comment)

        # 更新工单更新时间
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        ticket.updated_at = datetime.now()
        db.commit()

# handlers/ticket_handler.py
async def create_ticket_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """创建工单"""
    # /ticket create 标题 | 描述 | 优先级
    if not context.args:
        await update.message.reply_text(
            "使用方法: /ticket create 标题 | 描述 | 优先级(可选)"
        )
        return

    args_text = ' '.join(context.args[1:])
    parts = [p.strip() for p in args_text.split('|')]

    if len(parts) < 2:
        await update.message.reply_text("❌ 请提供标题和描述")
        return

    subject = parts[0]
    description = parts[1]
    priority = parts[2] if len(parts) > 2 else "medium"

    # 获取当前对话的用户
    thread_id = update.message.message_thread_id
    user = db.query(User).filter(
        User.message_thread_id == thread_id
    ).first()

    service = TicketService()
    ticket = await service.create_ticket(
        user_id=user.user_id,
        subject=subject,
        description=description,
        priority=priority,
        created_by=update.effective_user.id
    )

    # 通知用户
    await context.bot.send_message(
        user.user_id,
        f"🎫 工单已创建\n\n"
        f"工单号: `{ticket.ticket_number}`\n"
        f"标题: {ticket.subject}\n"
        f"优先级: {ticket.priority}\n\n"
        f"我们会尽快处理，您可以使用工单号查询进度。",
        parse_mode='Markdown'
    )

    # 在管理群组确认
    await update.message.reply_text(
        f"✅ 工单已创建: {ticket.ticket_number}",
        message_thread_id=thread_id
    )
```

**客服价值**:
- 📝 结构化问题跟踪
- 👥 团队协作处理
- 📊 SLA 监控

---

### 4.2 CRM 系统集成

**功能描述**: 同步用户信息到 CRM 系统，提供完整客户画像

**实施方案**:

```python
# services/crm_integration.py
import httpx

class CRMIntegration:
    """CRM 集成服务"""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def sync_user(self, user: User):
        """同步用户信息到 CRM"""
        data = {
            'telegram_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'is_premium': user.is_premium,
            'created_at': user.created_at.isoformat()
        }

        try:
            response = await self.client.post(
                f"{self.api_url}/contacts",
                json=data,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CRM sync failed: {e}")
            return None

    async def get_user_info(self, telegram_id: int) -> dict:
        """从 CRM 获取用户信息"""
        try:
            response = await self.client.get(
                f"{self.api_url}/contacts/telegram/{telegram_id}",
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch CRM info: {e}")
            return {}

    async def add_interaction(
        self,
        telegram_id: int,
        interaction_type: str,
        notes: str
    ):
        """记录互动"""
        data = {
            'telegram_id': telegram_id,
            'type': interaction_type,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }

        try:
            await self.client.post(
                f"{self.api_url}/interactions",
                json=data,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")

# 使用示例
crm = CRMIntegration(
    api_url=os.getenv("CRM_API_URL"),
    api_key=os.getenv("CRM_API_KEY")
)

async def start_with_crm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动命令（集成 CRM）"""
    user = update.effective_user

    # 同步到 CRM
    await crm.sync_user(user)

    # 获取 CRM 信息
    crm_info = await crm.get_user_info(user.id)

    if crm_info:
        # 显示历史互动信息
        await update.message.reply_text(
            f"欢迎回来，{user.first_name}!\n"
            f"上次互动: {crm_info.get('last_interaction', '无记录')}"
        )
    else:
        await update.message.reply_text(f"欢迎，{user.first_name}!")

    # 记录互动
    await crm.add_interaction(user.id, 'start_command', 'User initiated conversation')
```

**客服价值**:
- 👤 完整客户画像
- 📜 历史互动记录
- 🎯 个性化服务

---

### 4.3 支付系统集成

**功能描述**: 支持用户直接在机器人内完成支付

**实施方案**:

```python
# handlers/payment_handler.py
from telegram import LabeledPrice

class PaymentHandler:
    """支付处理器"""

    def __init__(self, payment_token: str):
        self.payment_token = payment_token

    async def send_invoice(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        title: str,
        description: str,
        amount: int,  # 单位：分
        currency: str = "USD"
    ):
        """发送发票"""
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=f"payment_{update.effective_user.id}_{int(time.time())}",
            provider_token=self.payment_token,
            currency=currency,
            prices=[LabeledPrice(title, amount)],
            start_parameter="payment"
        )

    async def handle_precheckout(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """处理预结账查询"""
        query = update.pre_checkout_query

        # 验证订单
        if self._validate_order(query.invoice_payload):
            await query.answer(ok=True)
        else:
            await query.answer(
                ok=False,
                error_message="订单验证失败，请重试"
            )

    async def handle_successful_payment(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """处理成功支付"""
        payment = update.message.successful_payment

        # 记录支付
        payment_record = Payment(
            user_id=update.effective_user.id,
            amount=payment.total_amount,
            currency=payment.currency,
            provider_payment_charge_id=payment.provider_payment_charge_id,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
            created_at=datetime.now()
        )
        db.add(payment_record)
        db.commit()

        # 通知用户
        await update.message.reply_text(
            f"✅ 支付成功!\n\n"
            f"金额: {payment.total_amount / 100} {payment.currency}\n"
            f"订单号: {payment.telegram_payment_charge_id}"
        )

        # 通知管理员
        await context.bot.send_message(
            admin_user_ids[0],
            f"💰 新的支付\n"
            f"用户: {update.effective_user.first_name}\n"
            f"金额: {payment.total_amount / 100} {payment.currency}"
        )
```

**用户价值**:
- 💳 便捷支付流程
- 🔒 安全可靠
- 📱 无需跳转外部

---

## 5. 数据分析和报表

### 5.1 实时数据看板

**功能描述**: 实时显示关键指标和趋势

**实施方案**:

```python
# services/analytics_service.py
import matplotlib.pyplot as plt
import io

class AnalyticsService:
    """数据分析服务"""

    async def generate_dashboard(self) -> bytes:
        """生成数据看板图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        # 1. 每日消息量趋势
        daily_stats = self._get_daily_message_stats(days=7)
        ax1.plot(daily_stats['dates'], daily_stats['counts'])
        ax1.set_title('每日消息量')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('消息数')

        # 2. 响应时间分布
        response_times = self._get_response_times()
        ax2.hist(response_times, bins=20)
        ax2.set_title('响应时间分布')
        ax2.set_xlabel('响应时间(分钟)')
        ax2.set_ylabel('频次')

        # 3. 问题类型分布
        issue_types = self._get_issue_type_distribution()
        ax3.pie(
            issue_types.values(),
            labels=issue_types.keys(),
            autopct='%1.1f%%'
        )
        ax3.set_title('问题类型分布')

        # 4. 客服工作量对比
        admin_workload = self._get_admin_workload()
        ax4.bar(admin_workload.keys(), admin_workload.values())
        ax4.set_title('客服工作量对比')
        ax4.set_xlabel('客服')
        ax4.set_ylabel('处理数量')

        plt.tight_layout()

        # 保存到字节流
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        plt.close()

        return buf.getvalue()

# 命令处理
async def dashboard_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """显示数据看板"""
    if update.effective_user.id not in admin_user_ids:
        return

    await update.message.reply_text("📊 正在生成数据看板...")

    service = AnalyticsService()
    image_data = await service.generate_dashboard()

    await update.message.reply_photo(
        photo=image_data,
        caption="📊 数据看板 - 实时更新"
    )
```

**管理价值**:
- 📊 数据可视化
- 🎯 快速决策支持
- 📈 趋势分析

---

### 5.2 自动报表生成

**功能描述**: 定期生成并发送运营报表

**实施方案**:

```python
# services/report_service.py
class ReportService:
    """报表服务"""

    async def generate_weekly_report(self) -> str:
        """生成周报"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        stats = {
            'total_conversations': self._count_conversations(start_date, end_date),
            'total_messages': self._count_messages(start_date, end_date),
            'new_users': self._count_new_users(start_date, end_date),
            'avg_response_time': self._calculate_avg_response_time(start_date, end_date),
            'avg_rating': self._calculate_avg_rating(start_date, end_date),
            'top_issues': self._get_top_issues(start_date, end_date),
            'admin_performance': self._get_admin_performance(start_date, end_date)
        }

        report = f"""
📊 **周度运营报告**
📅 {start_date.date()} - {end_date.date()}

---

## 📈 整体数据

💬 总对话数: {stats['total_conversations']}
📨 总消息数: {stats['total_messages']}
👥 新增用户: {stats['new_users']}
⏱️ 平均响应时间: {format_seconds(stats['avg_response_time'])}
⭐ 平均评分: {stats['avg_rating']}/5.0

---

## 🔥 热门问题

"""
        for i, (issue, count) in enumerate(stats['top_issues'][:5], 1):
            report += f"{i}. {issue}: {count}次\n"

        report += "\n---\n\n## 👥 客服表现\n\n"

        for admin_id, perf in stats['admin_performance'].items():
            report += f"**{perf['name']}**\n"
            report += f"  💬 回复: {perf['replies']}\n"
            report += f"  ⏱️ 响应时间: {format_seconds(perf['avg_response'])}\n"
            report += f"  ⭐ 评分: {perf['avg_rating']}/5.0\n\n"

        return report

# 定时任务
async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    """发送周报"""
    service = ReportService()
    report = await service.generate_weekly_report()

    # 发送给管理员
    for admin_id in admin_user_ids:
        await context.bot.send_message(
            admin_id,
            report,
            parse_mode='Markdown'
        )

# 在应用启动时注册
application.job_queue.run_weekly(
    send_weekly_report,
    day=0,  # 周一
    time=datetime.time(hour=9, minute=0)
)
```

**管理价值**:
- 📧 自动化报表
- 📊 全面数据概览
- 🎯 发现改进点

---

## 6. 自动化功能

### 6.1 智能提醒系统

**功能描述**: 自动提醒客服处理超时对话

**实施方案**:

```python
# services/reminder_service.py
class ReminderService:
    """提醒服务"""

    async def check_overdue_conversations(
        self,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """检查超时对话"""
        # 查询超过30分钟未回复的对话
        threshold = datetime.now() - timedelta(minutes=30)

        overdue = db.query(User).filter(
            User.last_message_time > threshold,
            User.last_reply_time < User.last_message_time
        ).all()

        for user in overdue:
            # 获取负责的客服
            assignment = db.query(ConversationAssignment).filter(
                ConversationAssignment.user_id == user.user_id
            ).first()

            if assignment:
                admin_id = assignment.admin_id
            else:
                admin_id = admin_user_ids[0]  # 默认通知第一个管理员

            # 发送提醒
            waiting_time = datetime.now() - user.last_message_time
            await context.bot.send_message(
                admin_id,
                f"⏰ 提醒\n\n"
                f"👤 用户 {user.first_name} 等待回复已超过 {format_timedelta(waiting_time)}\n"
                f"请尽快处理",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "立即处理",
                        url=f"https://t.me/c/{abs(admin_group_id)}/{user.message_thread_id}"
                    )
                ]])
            )

# 定时检查（每10分钟）
async def check_overdue(context: ContextTypes.DEFAULT_TYPE):
    service = ReminderService()
    await service.check_overdue_conversations(context)

application.job_queue.run_repeating(
    check_overdue,
    interval=600,  # 10分钟
    first=60
)
```

**客服价值**:
- ⏰ 避免遗漏对话
- 🎯 提高响应及时性
- 📊 改善服务质量

---

### 6.2 工作时间自动切换

**功能描述**: 根据工作时间自动调整机器人行为

**实施方案**:

```python
# services/schedule_service.py
class ScheduleService:
    """排班服务"""

    def __init__(self):
        self.work_hours = {
            'start': 9,
            'end': 18
        }
        self.work_days = [0, 1, 2, 3, 4]  # 周一到周五

    def is_work_time(self) -> bool:
        """判断是否工作时间"""
        now = datetime.now()

        # 检查星期
        if now.weekday() not in self.work_days:
            return False

        # 检查小时
        if not (self.work_hours['start'] <= now.hour < self.work_hours['end']):
            return False

        return True

    async def set_auto_reply_status(
        self,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """自动切换自动回复状态"""
        is_work_time = self.is_work_time()

        # 更新自动回复规则状态
        non_work_hour_rule = db.query(AutoReplyRule).filter(
            AutoReplyRule.trigger_type == 'time'
        ).first()

        if non_work_hour_rule:
            non_work_hour_rule.is_active = not is_work_time
            db.commit()

# 每小时检查一次
async def update_schedule(context: ContextTypes.DEFAULT_TYPE):
    service = ScheduleService()
    await service.set_auto_reply_status(context)

application.job_queue.run_repeating(
    update_schedule,
    interval=3600,  # 1小时
    first=0
)
```

**用户价值**:
- 🌙 非工作时间自动告知
- ⏰ 明确响应时间预期
- 😊 更好的体验

---

## 7. 实施路线图

### 阶段一：基础增强（1-2个月）

**优先级：高**

1. ✅ 富文本欢迎消息
2. ✅ 快捷回复按钮
3. ✅ 多语言支持
4. ✅ 客服工作台
5. ✅ 对话标签系统
6. ✅ 预设回复模板

**预期收益**:
- 用户体验提升30%
- 客服效率提升40%
- 消息响应速度提升50%

---

### 阶段二：智能化（2-3个月）

**优先级：中**

1. 🤖 AI 智能回复建议
2. 🤖 自动回复规则
3. 📊 客服绩效统计
4. 🏷️ 智能分配系统
5. ⭐ 对话评价系统

**预期收益**:
- AI 辅助减少响应时间25%
- 自动回复处理常见问题60%
- 客服满意度数据化

---

### 阶段三：集成扩展（3-4个月）

**优先级：中低**

1. 🎫 工单系统
2. 📚 知识库系统
3. 💳 支付集成
4. 👤 CRM 集成
5. 📊 数据看板

**预期收益**:
- 复杂问题处理效率提升35%
- 知识复用率提升50%
- 业务闭环完善

---

### 阶段四：自动化优化（持续）

**优先级：低**

1. ⏰ 智能提醒
2. 📈 自动报表
3. 🤖 工作时间切换
4. 📊 高级分析

**预期收益**:
- 管理效率提升40%
- 数据驱动决策
- 运营成本降低20%

---

## 总结

本功能新增方案共包含 **25+ 个新功能**，分为 4 个实施阶段，预计完整实施周期为 **4-6 个月**。

### 关键价值

**用户侧**:
- 💬 更流畅的交互体验
- ⚡ 更快的响应速度
- 🌍 多语言支持
- 💳 完整的服务闭环

**客服侧**:
- 🚀 效率提升 40-60%
- 🤖 AI 辅助决策
- 📊 数据化管理
- 🎯 智能工作分配

**管理侧**:
- 📈 实时数据洞察
- 📊 自动化报表
- 🎯 绩效考核依据
- 💰 降低运营成本

### 投资回报

按照阶段实施，预计：
- 第一阶段后：客服效率提升 40%，用户满意度提升 30%
- 第二阶段后：运营成本降低 25%，响应速度提升 50%
- 第三阶段后：业务转化率提升 35%
- 第四阶段后：管理效率提升 40%，实现数据驱动运营

建议优先实施阶段一和阶段二的功能，这些功能投入产出比最高，能够最快看到效果。
