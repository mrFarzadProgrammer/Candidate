"""
مدل‌های دیتابیس
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# جدول رابطه چند به چند برای نماینده و پلن‌ها
candidate_plans = db.Table('candidate_plans',
    db.Column('candidate_id', db.Integer, db.ForeignKey('candidates.id'), primary_key=True),
    db.Column('plan_id', db.Integer, db.ForeignKey('plans.id'), primary_key=True),
    db.Column('activated_at', db.DateTime, default=datetime.utcnow)
)


class Admin(db.Model):
    """مدیر سیستم"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class Plan(db.Model):
    """پلن‌های قابل فروش"""
    __tablename__ = 'plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, default=0)
    duration_days = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # محدودیت‌ها و امکانات
    max_messages = db.Column(db.Integer, default=-1)  # -1 = نامحدود
    max_programs = db.Column(db.Integer, default=-1)
    max_headquarters = db.Column(db.Integer, default=-1)
    max_bot_users = db.Column(db.Integer, default=-1)
    
    # امکانات AI
    has_ai = db.Column(db.Boolean, default=False)
    ai_message_classification = db.Column(db.Boolean, default=False)
    ai_sentiment_analysis = db.Column(db.Boolean, default=False)
    ai_auto_reply = db.Column(db.Boolean, default=False)
    ai_content_generation = db.Column(db.Boolean, default=False)
    ai_smart_chatbot = db.Column(db.Boolean, default=False)
    
    # امکانات دیگر
    can_mass_message = db.Column(db.Boolean, default=False)
    max_mass_message_per_day = db.Column(db.Integer, default=0)
    has_analytics = db.Column(db.Boolean, default=False)
    has_advanced_analytics = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    
    # ترتیب نمایش و رنگ
    display_order = db.Column(db.Integer, default=0)
    badge_color = db.Column(db.String(20), default='primary')  # primary, success, warning, danger
    is_popular = db.Column(db.Boolean, default=False)
    
    # مدیریت مرحله‌ای انتشار پلن‌ها (Gradual Release)
    is_available_for_purchase = db.Column(db.Boolean, default=False)  # آیا برای خرید فعال است؟
    release_scheduled_at = db.Column(db.DateTime, nullable=True)  # زمان برنامه‌ریزی شده انتشار
    release_notes = db.Column(db.Text)  # یادداشت‌های انتشار
    enabled_at = db.Column(db.DateTime, nullable=True)  # زمان واقعی فعال‌سازی
    enabled_by_admin_id = db.Column(db.Integer, nullable=True)  # ادمینی که فعال کرده
    
    def __repr__(self):
        return f'<Plan {self.name}>'


class Candidate(db.Model):
    """نماینده / کاندیدا"""
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    education = db.Column(db.String(200))
    province = db.Column(db.String(50))
    city = db.Column(db.String(50))
    district = db.Column(db.String(100))
    bio = db.Column(db.Text)
    photo = db.Column(db.String(200))
    voice_file = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    has_used_trial = db.Column(db.Boolean, default=False)  # آیا قبلاً تست رایگان استفاده شده؟
    referred_by = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=True)  # ID معرف
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # روابط
    bot_instance = db.relationship('BotInstance', backref='candidate', uselist=False, lazy=True)
    resumes = db.relationship('Resume', backref='candidate', lazy=True, cascade='all, delete-orphan')
    programs = db.relationship('Program', backref='candidate', lazy=True, cascade='all, delete-orphan')
    slogans = db.relationship('Slogan', backref='candidate', lazy=True, cascade='all, delete-orphan')
    headquarters = db.relationship('Headquarters', backref='candidate', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='candidate', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('Analytics', backref='candidate', lazy=True, cascade='all, delete-orphan')
    images = db.relationship('CandidateImage', backref='candidate', lazy=True, cascade='all, delete-orphan')
    
    # رابطه چند به چند با پلن‌ها
    plans = db.relationship('Plan', secondary=candidate_plans, lazy='subquery',
                           backref=db.backref('candidates', lazy=True))
    
    def __repr__(self):
        return f'<Candidate {self.full_name}>'
    
    def get_active_plan(self):
        """دریافت پلن فعال فعلی کاندیدا"""
        from datetime import datetime
        active_purchase = PlanPurchase.query.filter_by(
            candidate_id=self.id,
            is_active=True
        ).filter(
            PlanPurchase.end_date > datetime.utcnow()
        ).order_by(PlanPurchase.end_date.desc()).first()
        
        return active_purchase.plan if active_purchase else None
    
    def has_feature(self, feature_name):
        """بررسی دسترسی به یک امکان خاص"""
        active_plan = self.get_active_plan()
        if not active_plan:
            return False
        return getattr(active_plan, feature_name, False)
    
    def can_add_message(self):
        """بررسی امکان دریافت پیام جدید"""
        active_plan = self.get_active_plan()
        if not active_plan or active_plan.max_messages == -1:
            return True
        
        from datetime import datetime, timedelta
        # شمارش پیام‌های این ماه
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        message_count = Message.query.filter_by(candidate_id=self.id).filter(
            Message.created_at >= month_start
        ).count()
        
        return message_count < active_plan.max_messages
    
    def can_add_program(self):
        """بررسی امکان اضافه کردن برنامه"""
        active_plan = self.get_active_plan()
        if not active_plan or active_plan.max_programs == -1:
            return True
        
        program_count = Program.query.filter_by(candidate_id=self.id).count()
        return program_count < active_plan.max_programs
    
    def can_add_headquarters(self):
        """بررسی امکان اضافه کردن دفتر"""
        active_plan = self.get_active_plan()
        if not active_plan or active_plan.max_headquarters == -1:
            return True
        
        hq_count = Headquarters.query.filter_by(candidate_id=self.id).count()
        return hq_count < active_plan.max_headquarters


class BotInstance(db.Model):
    """نمونه بات برای هر نماینده"""
    __tablename__ = 'bot_instances'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    bot_token = db.Column(db.String(200), nullable=False)
    bot_username = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=False)
    last_active = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # تنظیمات BotFather
    bot_name = db.Column(db.String(100))  # Edit Name
    bot_about = db.Column(db.String(120))  # Edit About (حداکثر 120 کاراکتر)
    bot_description = db.Column(db.Text)  # Edit Description
    bot_description_picture = db.Column(db.String(200))  # Edit Description Picture
    bot_pic = db.Column(db.String(200))  # Edit Botpic
    bot_commands = db.Column(db.Text)  # Edit Commands (JSON format)
    privacy_policy_url = db.Column(db.String(500))  # Edit Privacy Policy
    
    # روابط
    users = db.relationship('BotUser', backref='bot_instance', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BotInstance @{self.bot_username}>'


class BotUser(db.Model):
    """کاربران بات (مردم)"""
    __tablename__ = 'bot_users'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_instance_id = db.Column(db.Integer, db.ForeignKey('bot_instances.id'), nullable=False)
    telegram_id = db.Column(db.BigInteger, nullable=False)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Gamification Fields
    total_points = db.Column(db.Integer, default=0)  # مجموع امتیازات
    level = db.Column(db.Integer, default=1)  # سطح کاربر
    streak_days = db.Column(db.Integer, default=0)  # تعداد روزهای حضور پیاپی
    last_daily_login = db.Column(db.Date)  # آخرین حضور روزانه
    
    def __repr__(self):
        return f'<BotUser {self.first_name}>'


class Resume(db.Model):
    """رزومه نماینده"""
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    year = db.Column(db.String(20))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Resume {self.title}>'


class Program(db.Model):
    """برنامه‌های انتخاباتی"""
    __tablename__ = 'programs'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Program {self.title}>'


class Slogan(db.Model):
    """شعارهای انتخاباتی"""
    __tablename__ = 'slogans'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Slogan {self.text[:30]}...>'


class Headquarters(db.Model):
    """ستادهای انتخاباتی"""
    __tablename__ = 'headquarters'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Headquarters {self.name}>'


class Message(db.Model):
    """پیام‌های دریافتی از مردم"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    user_name = db.Column(db.String(200))
    message_text = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI Features - دسته‌بندی و تحلیل خودکار
    category = db.Column(db.String(50))  # complaint, suggestion, question, support, criticism, unknown
    category_fa = db.Column(db.String(50))  # شکایت، پیشنهاد، سوال، حمایت، انتقاد
    category_confidence = db.Column(db.Float)  # 0.0 - 1.0
    category_priority = db.Column(db.String(20))  # high, medium, low
    
    # Sentiment Analysis
    sentiment_score = db.Column(db.Float)  # -1.0 (negative) to 1.0 (positive)
    sentiment_label = db.Column(db.String(20))  # positive, neutral, negative
    
    def __repr__(self):
        return f'<Message from {self.user_name}>'


class Analytics(db.Model):
    """آمار و تحلیل"""
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    total_messages = db.Column(db.Integer, default=0)
    resume_views = db.Column(db.Integer, default=0)
    programs_views = db.Column(db.Integer, default=0)
    headquarters_views = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Analytics {self.date}>'


class CandidateImage(db.Model):
    """تصاویر نماینده"""
    __tablename__ = 'candidate_images'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(500))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CandidateImage {self.image_path}>'


class PlanPurchase(db.Model):
    """تاریخچه خرید و فعالسازی پلن‌ها"""
    __tablename__ = 'plan_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    # اطلاعات زمانی
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # اطلاعات پرداخت
    payment_amount = db.Column(db.Integer, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    payment_method = db.Column(db.String(50))  # online, transfer, cash, free
    transaction_id = db.Column(db.String(100))
    
    # Trial و کنترل ادمین
    is_trial = db.Column(db.Boolean, default=False)  # آیا دوره تست است؟
    trial_used = db.Column(db.Boolean, default=False)  # آیا قبلاً تست استفاده شده؟
    custom_duration_days = db.Column(db.Integer)  # مدت دلخواه ادمین (اولویت با duration_days پلن)
    admin_granted = db.Column(db.Boolean, default=False)  # آیا توسط ادمین رایگان داده شده؟
    admin_note = db.Column(db.Text)  # یادداشت ادمین برای اعطای رایگان
    
    # یادداشت‌ها
    notes = db.Column(db.Text)  # برای ادمین
    auto_renew = db.Column(db.Boolean, default=False)
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)
    
    # روابط
    candidate = db.relationship('Candidate', backref='plan_purchases')
    plan = db.relationship('Plan', backref='purchases')
    
    def __repr__(self):
        return f'<PlanPurchase {self.candidate_id} - {self.plan_id}>'
    
    def is_expired(self):
        """بررسی انقضای پلن"""
        return datetime.utcnow() > self.end_date
    
    def days_remaining(self):
        """تعداد روزهای باقی‌مانده"""
        if self.is_expired():
            return 0
        delta = self.end_date - datetime.utcnow()
        return delta.days


class ConsultationRequest(db.Model):
    """درخواست‌های مشاوره و تماس"""
    __tablename__ = 'consultation_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))  # پلن مورد نظر برای خرید
    
    # اطلاعات تماس
    phone = db.Column(db.String(20), nullable=False)
    preferred_time = db.Column(db.String(100))  # صبح، بعدازظهر، عصر
    message = db.Column(db.Text)
    
    # وضعیت
    status = db.Column(db.String(20), default='pending')  # pending, contacted, converted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contacted_at = db.Column(db.DateTime)
    contacted_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    
    # یادداشت ادمین
    admin_notes = db.Column(db.Text)
    
    # روابط
    candidate = db.relationship('Candidate', backref='consultation_requests')
    plan = db.relationship('Plan', backref='consultation_requests')
    
    def __repr__(self):
        return f'<ConsultationRequest {self.id} - {self.phone}>'


class BotChannel(db.Model):
    """کانال/گروه تلگرام متصل به بات"""
    __tablename__ = 'bot_channels'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_instance_id = db.Column(db.Integer, db.ForeignKey('bot_instances.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    
    # اطلاعات کانال
    channel_id = db.Column(db.BigInteger, nullable=False)  # Chat ID تلگرام
    channel_username = db.Column(db.String(100))  # @channel_name
    channel_title = db.Column(db.String(200), nullable=False)
    channel_type = db.Column(db.String(20), default='channel')  # channel, group, supergroup
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # آیا بات ادمین کانال است؟
    member_count = db.Column(db.Integer, default=0)
    
    # تاریخ
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_post_at = db.Column(db.DateTime)
    
    # تنظیمات
    auto_post_enabled = db.Column(db.Boolean, default=True)
    moderation_enabled = db.Column(db.Boolean, default=False)
    
    # روابط
    bot_instance = db.relationship('BotInstance', backref='channels')
    candidate = db.relationship('Candidate', backref='channels')
    scheduled_posts = db.relationship('ScheduledPost', backref='channel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BotChannel {self.channel_title}>'


class ScheduledPost(db.Model):
    """پست‌های زمان‌بندی شده برای کانال"""
    __tablename__ = 'scheduled_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('bot_channels.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    
    # محتوای پست
    content = db.Column(db.Text, nullable=False)
    media_type = db.Column(db.String(20))  # photo, video, document, none
    media_url = db.Column(db.String(500))
    
    # زمان‌بندی
    scheduled_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # وضعیت
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, cancelled
    sent_at = db.Column(db.DateTime)
    message_id = db.Column(db.BigInteger)  # ID پیام ارسال شده در تلگرام
    
    # خطا
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
    # تنظیمات اضافی
    disable_notification = db.Column(db.Boolean, default=False)
    pin_message = db.Column(db.Boolean, default=False)
    
    # روابط
    candidate = db.relationship('Candidate', backref='scheduled_posts')
    
    def __repr__(self):
        return f'<ScheduledPost {self.id} - {self.status}>'


class ChannelStats(db.Model):
    """آمار روزانه کانال"""
    __tablename__ = 'channel_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('bot_channels.id'), nullable=False)
    
    # تاریخ
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    # آمار
    member_count = db.Column(db.Integer, default=0)
    new_members = db.Column(db.Integer, default=0)
    left_members = db.Column(db.Integer, default=0)
    posts_count = db.Column(db.Integer, default=0)
    total_views = db.Column(db.Integer, default=0)
    
    # روابط
    channel = db.relationship('BotChannel', backref='stats')
    
    def __repr__(self):
        return f'<ChannelStats {self.date}>'


class BroadcastMessage(db.Model):
    """پیام‌های ارسال انبوه"""
    __tablename__ = 'broadcast_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    bot_instance_id = db.Column(db.Integer, db.ForeignKey('bot_instances.id'), nullable=False)
    
    # محتوای پیام
    message_text = db.Column(db.Text, nullable=False)
    media_type = db.Column(db.String(20))  # photo, video, document
    media_url = db.Column(db.String(500))
    
    # تنظیمات ارسال
    target_filter = db.Column(db.String(50), default='all')  # all, active, new
    scheduled_time = db.Column(db.DateTime)  # اگر خالی باشد فوری ارسال می‌شود
    
    # وضعیت
    status = db.Column(db.String(20), default='pending')  # pending, sending, completed, failed
    total_users = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    
    # زمان‌ها
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # روابط
    candidate = db.relationship('Candidate', backref='broadcasts')
    bot_instance = db.relationship('BotInstance', backref='broadcasts')
    
    def __repr__(self):
        return f'<BroadcastMessage {self.id} - {self.status}>'


class BroadcastLog(db.Model):
    """لاگ ارسال پیام به هر کاربر"""
    __tablename__ = 'broadcast_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    broadcast_id = db.Column(db.Integer, db.ForeignKey('broadcast_messages.id'), nullable=False)
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    
    # وضعیت ارسال
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    error_message = db.Column(db.Text)
    
    # زمان
    sent_at = db.Column(db.DateTime)
    
    # روابط
    broadcast = db.relationship('BroadcastMessage', backref='logs')
    
    def __repr__(self):
        return f'<BroadcastLog {self.broadcast_id} - {self.user_telegram_id}>'


class Poll(db.Model):
    """نظرسنجی‌ها"""
    __tablename__ = 'polls'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    bot_instance_id = db.Column(db.Integer, db.ForeignKey('bot_instances.id'), nullable=False)
    
    # محتوای نظرسنجی
    question = db.Column(db.Text, nullable=False)
    
    # تنظیمات
    is_anonymous = db.Column(db.Boolean, default=True)
    allows_multiple_answers = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # زمان‌ها
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    # آمار
    total_votes = db.Column(db.Integer, default=0)
    
    # روابط
    candidate = db.relationship('Candidate', backref='polls')
    bot_instance = db.relationship('BotInstance', backref='polls')
    
    def __repr__(self):
        return f'<Poll {self.id} - {self.question[:30]}>'


class PollOption(db.Model):
    """گزینه‌های نظرسنجی"""
    __tablename__ = 'poll_options'
    
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    
    # محتوا
    option_text = db.Column(db.String(200), nullable=False)
    option_order = db.Column(db.Integer, default=0)
    
    # آمار
    vote_count = db.Column(db.Integer, default=0)
    
    # روابط
    poll = db.relationship('Poll', backref='options')
    
    def __repr__(self):
        return f'<PollOption {self.option_text}>'


class PollVote(db.Model):
    """رای‌های نظرسنجی"""
    __tablename__ = 'poll_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_options.id'), nullable=False)
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    
    # زمان
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # روابط
    poll = db.relationship('Poll', backref='votes')
    option = db.relationship('PollOption', backref='votes')
    
    def __repr__(self):
        return f'<PollVote {self.poll_id} - {self.user_telegram_id}>'


class AutoReply(db.Model):
    """پاسخ‌های خودکار"""
    __tablename__ = 'auto_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    
    # کلمات کلیدی و پاسخ
    keyword = db.Column(db.String(100), nullable=False)
    reply_text = db.Column(db.Text, nullable=False)
    
    # تنظیمات
    is_active = db.Column(db.Boolean, default=True)
    case_sensitive = db.Column(db.Boolean, default=False)
    exact_match = db.Column(db.Boolean, default=False)  # تطابق دقیق یا شامل شدن
    
    # آمار
    usage_count = db.Column(db.Integer, default=0)
    
    # زمان
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # روابط
    candidate = db.relationship('Candidate', backref='auto_replies')
    
    def __repr__(self):
        return f'<AutoReply {self.keyword}>'


class Ticket(db.Model):
    """تیکت‌های پشتیبانی و درخواست خرید"""
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)  # شماره تیکت مثل TK-1001
    
    # اطلاعات کاربر
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    
    # نوع تیکت
    ticket_type = db.Column(db.String(50), nullable=False)  # 'purchase' یا 'support'
    
    # موضوع و پیام
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    
    # برای تیکت‌های خرید
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=True)
    payment_method = db.Column(db.String(50))  # 'card_to_card' یا 'sheba'
    payment_amount = db.Column(db.Integer)  # مبلغ پرداختی
    receipt_image = db.Column(db.String(300))  # مسیر فایل فیش
    
    # وضعیت
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, closed
    
    # پاسخ ادمین
    admin_response = db.Column(db.Text)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    
    # زمان‌ها
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # روابط
    candidate = db.relationship('Candidate', backref='tickets')
    plan = db.relationship('Plan', backref='tickets')
    admin = db.relationship('Admin', backref='tickets')
    
    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'


class Payment(db.Model):
    """سوابق پرداخت و فعال‌سازی پلن"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # ارجاع به تیکت
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    
    # اطلاعات پرداخت
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    amount = db.Column(db.Integer, nullable=False)  # مبلغ
    payment_method = db.Column(db.String(50))  # card_to_card, sheba
    receipt_image = db.Column(db.String(300))  # فیش پرداخت
    
    # وضعیت
    status = db.Column(db.String(50), default='pending')  # pending, verified, failed
    
    # تاریخ‌ها
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # فعال‌سازی پلن
    plan_activated = db.Column(db.Boolean, default=False)
    activation_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    
    # روابط
    ticket = db.relationship('Ticket', backref='payments')
    candidate = db.relationship('Candidate', backref='payments')
    plan = db.relationship('Plan', backref='payments')
    
    def __repr__(self):
        return f'<Payment {self.id} - Ticket {self.ticket_id}>'


# ============================================
# سیستم مشارکت مردمی
# Citizen Participation System
# ============================================

class CitizenContribution(db.Model):
    """
    مشارکت‌های مردمی (ایده‌ها و گزارش‌ها)
    """
    __tablename__ = 'citizen_contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_code = db.Column(db.String(20), unique=True, nullable=False)  # IDEA-1001, RPT-2001
    
    # کاندید و کاربر
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    user_username = db.Column(db.String(100))
    user_first_name = db.Column(db.String(100))
    user_last_name = db.Column(db.String(100))
    
    # نوع و محتوا
    contribution_type = db.Column(db.String(50), nullable=False)  # idea, report
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    
    # محل
    location_text = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # تصاویر
    images = db.Column(db.JSON, default=[])
    
    # وضعیت و اولویت
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.String(20), default='medium')
    
    # تعاملات
    votes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    
    # پاسخ
    admin_response = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    
    # تاریخ‌ها
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # روابط
    candidate = db.relationship('Candidate', backref='citizen_contributions')
    votes = db.relationship('ContributionVote', backref='contribution', cascade='all, delete-orphan')
    comments = db.relationship('ContributionComment', backref='contribution', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CitizenContribution {self.tracking_code}>'


class ContributionVote(db.Model):
    """رای‌های مردم به پیشنهادات"""
    __tablename__ = 'contribution_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    contribution_id = db.Column(db.Integer, db.ForeignKey('citizen_contributions.id'), nullable=False)
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    user_name = db.Column(db.String(100))
    vote_type = db.Column(db.String(20), default='upvote')
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('contribution_id', 'user_telegram_id', name='unique_contribution_vote'),
    )
    
    def __repr__(self):
        return f'<ContributionVote {self.user_telegram_id} -> {self.contribution_id}>'


class ContributionComment(db.Model):
    """نظرات مردم روی پیشنهادات"""
    __tablename__ = 'contribution_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    contribution_id = db.Column(db.Integer, db.ForeignKey('citizen_contributions.id'), nullable=False)
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    user_name = db.Column(db.String(100))
    comment_text = db.Column(db.Text, nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('contribution_comments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    replies = db.relationship('ContributionComment', backref=db.backref('parent', remote_side=[id]))
    
    def __repr__(self):
        return f'<ContributionComment {self.id}>'


class CitizenProfile(db.Model):
    """پروفایل شهروند برای گیمیفیکیشن"""
    __tablename__ = 'citizen_profiles'
    
    telegram_id = db.Column(db.BigInteger, primary_key=True)
    full_name = db.Column(db.String(200))
    username = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    neighborhood = db.Column(db.String(200))
    
    # امتیازات
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    
    # آمار
    contributions_count = db.Column(db.Integer, default=0)
    votes_given = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    
    # نشان‌ها
    badges = db.Column(db.JSON, default=[])
    
    # تاریخ‌ها
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CitizenProfile {self.telegram_id}>'


# ═══════════════════════════════════════════════════════════════
# بخش اول: سیستم Benchmark و مقایسه رقابتی
# ═══════════════════════════════════════════════════════════════

class MarketplaceBenchmark(db.Model):
    """آمار گمنام از همه نامزدها برای مقایسه"""
    __tablename__ = 'marketplace_benchmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date, index=True)
    
    # آمار برای هر پلن
    plan_code = db.Column(db.String(50), nullable=False, index=True)
    
    # میانگین‌ها
    avg_daily_messages = db.Column(db.Float, default=0)
    avg_bot_users = db.Column(db.Float, default=0)
    avg_engagement_rate = db.Column(db.Float, default=0)
    avg_citizen_contributions = db.Column(db.Float, default=0)
    avg_poll_participation = db.Column(db.Float, default=0)
    
    # محدوده‌ها (برای نمایش رنج)
    min_messages = db.Column(db.Integer, default=0)
    max_messages = db.Column(db.Integer, default=0)
    median_messages = db.Column(db.Integer, default=0)
    
    # صدک‌ها (percentiles)
    top_10_percent_messages = db.Column(db.Integer, default=0)  # 90th percentile
    top_25_percent_messages = db.Column(db.Integer, default=0)  # 75th percentile
    bottom_25_percent_messages = db.Column(db.Integer, default=0)  # 25th percentile
    
    # تعداد نمونه
    sample_size = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MarketplaceBenchmark {self.plan_code} {self.date}>'


class CandidateRanking(db.Model):
    """رتبه‌بندی نامزدها (برای نمایش رقابتی)"""
    __tablename__ = 'candidate_rankings'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    date = db.Column(db.Date, default=datetime.utcnow().date, index=True)
    
    # رتبه‌ها
    overall_rank = db.Column(db.Integer)  # رتبه کلی
    plan_rank = db.Column(db.Integer)  # رتبه در بین هم‌پلنی‌ها
    percentile = db.Column(db.Float)  # بهتر از چند درصد
    
    # امتیاز کلی (برای رتبه‌بندی)
    total_score = db.Column(db.Float, default=0)
    
    # جزئیات امتیاز
    messages_score = db.Column(db.Float, default=0)
    users_score = db.Column(db.Float, default=0)
    engagement_score = db.Column(db.Float, default=0)
    growth_score = db.Column(db.Float, default=0)
    
    # آمار واقعی (برای محاسبه)
    total_messages = db.Column(db.Integer, default=0)
    total_bot_users = db.Column(db.Integer, default=0)
    engagement_rate = db.Column(db.Float, default=0)
    weekly_growth = db.Column(db.Float, default=0)
    
    # مقایسه با میانگین
    messages_vs_avg = db.Column(db.Float, default=0)  # +45% یا -30%
    users_vs_avg = db.Column(db.Float, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # رابطه
    candidate = db.relationship('Candidate', backref='rankings')
    
    def __repr__(self):
        return f'<CandidateRanking {self.candidate_id} Rank:{self.overall_rank}>'


# ═══════════════════════════════════════════════════════════════
# بخش دوم: سیستم Trial و Referral
# ═══════════════════════════════════════════════════════════════

class TrialPeriod(db.Model):
    """دوره تریال برای نامزدهای جدید"""
    __tablename__ = 'trial_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), unique=True, nullable=False)
    
    # تنظیمات
    duration_days = db.Column(db.Integer, default=14)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # محدودیت‌های تریال
    max_bot_users = db.Column(db.Integer, default=100)
    max_messages = db.Column(db.Integer, default=50)
    max_broadcasts = db.Column(db.Integer, default=5)
    max_channels = db.Column(db.Integer, default=1)
    
    # استفاده فعلی
    used_bot_users = db.Column(db.Integer, default=0)
    used_messages = db.Column(db.Integer, default=0)
    used_broadcasts = db.Column(db.Integer, default=0)
    used_channels = db.Column(db.Integer, default=0)
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    is_expired = db.Column(db.Boolean, default=False)
    converted_to_paid = db.Column(db.Boolean, default=False)
    conversion_date = db.Column(db.DateTime)
    
    # یادآوری‌ها
    reminder_7_days_sent = db.Column(db.Boolean, default=False)
    reminder_3_days_sent = db.Column(db.Boolean, default=False)
    reminder_1_day_sent = db.Column(db.Boolean, default=False)
    expiry_notice_sent = db.Column(db.Boolean, default=False)
    
    # رابطه
    candidate = db.relationship('Candidate', backref=db.backref('trial', uselist=False))
    
    def __repr__(self):
        return f'<TrialPeriod {self.candidate_id}>'
    
    def days_remaining(self):
        """روزهای باقی‌مانده"""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def is_limit_reached(self, limit_type):
        """آیا به محدودیت رسیده؟"""
        limits = {
            'bot_users': (self.used_bot_users, self.max_bot_users),
            'messages': (self.used_messages, self.max_messages),
            'broadcasts': (self.used_broadcasts, self.max_broadcasts),
            'channels': (self.used_channels, self.max_channels)
        }
        if limit_type in limits:
            used, max_limit = limits[limit_type]
            return used >= max_limit
        return False


class ReferralProgram(db.Model):
    """برنامه معرفی دوستان - یک نامزد یک برنامه دارد"""
    __tablename__ = 'referral_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, unique=True, index=True)
    
    # کد معرفی یونیک
    referral_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # وضعیت
    status = db.Column(db.String(20), default='active')  # active, suspended
    
    # آمار
    total_referrals = db.Column(db.Integer, default=0)  # تعداد کل معرفی‌ها
    successful_conversions = db.Column(db.Integer, default=0)  # تعداد افرادی که پلن خریدند
    total_rewards_earned = db.Column(db.Float, default=0)  # مجموع پاداش‌ها
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    candidate = db.relationship('Candidate', backref='referral_program')
    
    def __repr__(self):
        return f'<ReferralProgram {self.referral_code}>'


class ReferralReward(db.Model):
    """پاداش‌های معرفی - هر تبدیل موفق یک پاداش"""
    __tablename__ = 'referral_rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    referral_program_id = db.Column(db.Integer, db.ForeignKey('referral_programs.id'), nullable=False, index=True)
    referred_candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    
    # نوع و مقدار پاداش
    reward_type = db.Column(db.String(30), default='plan_purchase')  # plan_purchase
    reward_amount = db.Column(db.Float, nullable=False)  # مبلغ پاداش (20% قیمت پلن)
    
    # وضعیت
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    # تاریخ‌ها
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)  # زمان ایجاد پاداش
    approved_at = db.Column(db.DateTime)  # زمان تایید توسط ادمین
    
    # روابط
    referral_program = db.relationship('ReferralProgram', backref='rewards')
    referred_candidate = db.relationship('Candidate', backref='referral_rewards_received')
    
    def __repr__(self):
        return f'<ReferralReward {self.reward_amount} - {self.status}>'


# ═══════════════════════════════════════════════════════════════
# بخش سوم: سیستم VIP و شهروند ماه
# ═══════════════════════════════════════════════════════════════

class MonthlyTopCitizen(db.Model):
    """شهروندان برتر هر ماه"""
    __tablename__ = 'monthly_top_citizens'
    
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    citizen_telegram_id = db.Column(db.BigInteger, db.ForeignKey('citizen_profiles.telegram_id'), nullable=False)
    
    # دوره
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False, index=True)  # 1-12
    
    # رتبه
    rank = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    total_score = db.Column(db.Integer, default=0)
    
    # آمار تفصیلی
    contributions_count = db.Column(db.Integer, default=0)
    upvotes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    
    # سطح VIP
    vip_status = db.Column(db.String(20), default='gold')  # gold, silver, bronze
    
    # تاریخ اعطا
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # روابط
    candidate = db.relationship('Candidate', backref='monthly_top_citizens')
    citizen = db.relationship('CitizenProfile', backref='monthly_achievements')
    
    def __repr__(self):
        return f'<MonthlyTopCitizen {self.year}/{self.month} Rank:{self.rank}>'


class VIPInteraction(db.Model):
    """تعامل VIP با نماینده"""
    __tablename__ = 'vip_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    citizen_telegram_id = db.Column(db.BigInteger, nullable=False)
    
    # نوع تعامل
    interaction_type = db.Column(db.String(30), nullable=False, index=True)
    # live_qa: سوال و جواب زنده
    # video_call: ویدیو کال
    # priority_response: پاسخ اولویت‌دار
    # exclusive_event: دعوت به رویداد ویژه
    # private_meeting: جلسه خصوصی
    
    # جزئیات
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # زمان‌بندی
    scheduled_at = db.Column(db.DateTime, index=True)
    duration_minutes = db.Column(db.Integer, default=30)
    
    # وضعیت
    status = db.Column(db.String(20), default='scheduled', index=True)
    # scheduled: برنامه‌ریزی شده
    # confirmed: تایید شده
    # in_progress: در حال انجام
    # completed: انجام شده
    # cancelled: لغو شده
    # no_show: حضور نیافت
    
    # لینک/اطلاعات
    meeting_link = db.Column(db.String(500))  # لینک Zoom/Google Meet
    meeting_password = db.Column(db.String(50))
    meeting_id = db.Column(db.String(50))
    
    # یادداشت‌ها
    notes = db.Column(db.Text)  # یادداشت‌های نماینده
    feedback = db.Column(db.Text)  # بازخورد شهروند
    rating = db.Column(db.Integer)  # 1-5 ستاره
    
    # یادآوری‌ها
    reminder_24h_sent = db.Column(db.Boolean, default=False)
    reminder_1h_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # رابطه
    candidate = db.relationship('Candidate', backref='vip_interactions')
    
    def __repr__(self):
        return f'<VIPInteraction {self.interaction_type} {self.status}>'


class LiveEvent(db.Model):
    """رویدادهای زنده نماینده"""
    __tablename__ = 'live_events'
    
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    
    # مشخصات
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    banner_image = db.Column(db.String(500))
    
    event_type = db.Column(db.String(30), nullable=False)
    # live_qa: سوال و جواب زنده
    # town_hall: جلسه عمومی
    # webinar: وبینار
    # ama: Ask Me Anything
    # workshop: کارگاه
    
    # زمان
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, default=60)
    timezone = db.Column(db.String(50), default='Asia/Tehran')
    
    # پلتفرم
    platform = db.Column(db.String(30), default='telegram_live')  # telegram_live, zoom, youtube_live, instagram_live
    stream_url = db.Column(db.String(500))
    chat_enabled = db.Column(db.Boolean, default=True)
    
    # محدودیت
    max_participants = db.Column(db.Integer)  # null = نامحدود
    vip_only = db.Column(db.Boolean, default=False)
    min_points_required = db.Column(db.Integer, default=0)
    requires_registration = db.Column(db.Boolean, default=True)
    
    # وضعیت
    status = db.Column(db.String(20), default='scheduled', index=True)
    # scheduled: برنامه‌ریزی شده
    # live: در حال پخش
    # completed: تمام شده
    # cancelled: لغو شده
    
    # آمار
    registered_count = db.Column(db.Integer, default=0)
    attended_count = db.Column(db.Integer, default=0)
    questions_count = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0)
    
    # یادآوری‌ها
    reminder_1day_sent = db.Column(db.Boolean, default=False)
    reminder_1hour_sent = db.Column(db.Boolean, default=False)
    starting_notice_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # رابطه
    candidate = db.relationship('Candidate', backref='live_events')
    
    def __repr__(self):
        return f'<LiveEvent {self.title}>'


class EventRegistration(db.Model):
    """ثبت‌نام در رویداد"""
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    event_id = db.Column(db.Integer, db.ForeignKey('live_events.id'), nullable=False, index=True)
    citizen_telegram_id = db.Column(db.BigInteger, nullable=False)
    
    # اطلاعات
    full_name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    
    # وضعیت
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)
    attended_at = db.Column(db.DateTime)
    
    # سوالات شهروند
    submitted_question = db.Column(db.Text)
    question_answered = db.Column(db.Boolean, default=False)
    question_answer = db.Column(db.Text)
    
    # بازخورد
    rating = db.Column(db.Integer)  # 1-5
    feedback = db.Column(db.Text)
    
    # یادآوری‌ها
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # رابطه
    event = db.relationship('LiveEvent', backref='registrations')
    
    def __repr__(self):
        return f'<EventRegistration {self.event_id} {self.citizen_telegram_id}>'


class EventQuestion(db.Model):
    """سوالات شهروندان در رویدادها"""
    __tablename__ = 'event_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    event_id = db.Column(db.Integer, db.ForeignKey('live_events.id'), nullable=False, index=True)
    citizen_telegram_id = db.Column(db.BigInteger, nullable=False)
    citizen_name = db.Column(db.String(200))
    
    # سوال
    question_text = db.Column(db.Text, nullable=False)
    question_category = db.Column(db.String(50))  # اقتصاد، فرهنگ، اجتماعی، etc.
    
    # وضعیت
    status = db.Column(db.String(20), default='pending', index=True)
    # pending: در انتظار بررسی
    # approved: تایید شده
    # answered: پاسخ داده شده
    # rejected: رد شده
    
    # پاسخ
    answer_text = db.Column(db.Text)
    answered_by = db.Column(db.String(100))  # نام نماینده یا مدیر
    answered_at = db.Column(db.DateTime)
    
    # اولویت و رای‌گیری
    priority = db.Column(db.Integer, default=0)  # 0=عادی، 1=مهم، 2=فوری
    upvotes = db.Column(db.Integer, default=0)  # رای مثبت از شهروندان
    
    # زمان
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # رابطه
    event = db.relationship('LiveEvent', backref='questions')
    
    def __repr__(self):
        return f'<EventQuestion {self.id} Event:{self.event_id}>'


# ═══════════════════════════════════════════════════════════════
# بخش چهارم: سیستم احزاب و ائتلاف‌ها
# ═══════════════════════════════════════════════════════════════

class PoliticalParty(db.Model):
    """احزاب سیاسی"""
    __tablename__ = 'political_parties'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # اطلاعات پایه
    name = db.Column(db.String(200), nullable=False, unique=True)
    name_english = db.Column(db.String(200))
    abbreviation = db.Column(db.String(20))  # مثلاً جبهه اصلاحات -> JI
    
    # برندینگ
    logo = db.Column(db.String(500))
    banner = db.Column(db.String(500))
    color_primary = db.Column(db.String(7), default='#6366f1')  # HEX color
    color_secondary = db.Column(db.String(7), default='#ec4899')
    
    # اطلاعات حزب
    description = db.Column(db.Text)
    manifesto = db.Column(db.Text)  # برنامه و منشور حزب
    ideology = db.Column(db.String(100))  # اصلاح‌طلب، اصولگرا، میانه‌رو، مستقل
    founded_year = db.Column(db.Integer)
    website = db.Column(db.String(200))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # مدیریت
    leader_candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    secretary_general_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    
    # پنل مشترک
    shared_bot_token = db.Column(db.String(500))  # ربات مشترک حزب
    shared_channel_id = db.Column(db.String(100))  # کانال رسمی حزب
    shared_channel_username = db.Column(db.String(100))
    
    # آمار
    total_members = db.Column(db.Integer, default=0)
    total_candidates = db.Column(db.Integer, default=0)
    total_votes_estimate = db.Column(db.Integer, default=0)
    
    # اشتراک حزبی
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))
    subscription_started_at = db.Column(db.DateTime)
    subscription_expires_at = db.Column(db.DateTime)
    subscription_is_active = db.Column(db.Boolean, default=False)
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)  # تایید شده توسط admin
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    leader = db.relationship('Candidate', foreign_keys=[leader_candidate_id], backref='led_parties')
    secretary = db.relationship('Candidate', foreign_keys=[secretary_general_id], backref='managed_parties')
    subscription_plan = db.relationship('Plan', backref='party_subscriptions')
    
    def __repr__(self):
        return f'<PoliticalParty {self.name}>'


class PartyMembership(db.Model):
    """عضویت نامزدها در حزب"""
    __tablename__ = 'party_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    
    party_id = db.Column(db.Integer, db.ForeignKey('political_parties.id'), nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    
    # نقش
    role = db.Column(db.String(50), default='member')  # leader, deputy, secretary, member, supporter
    position = db.Column(db.String(100))  # دبیر استان، مسئول کمیته، ...
    
    # سطح دسترسی در پنل حزب
    can_manage_party = db.Column(db.Boolean, default=False)
    can_manage_members = db.Column(db.Boolean, default=False)
    can_send_broadcast = db.Column(db.Boolean, default=False)
    can_view_analytics = db.Column(db.Boolean, default=True)
    can_create_events = db.Column(db.Boolean, default=False)
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)  # تایید عضویت
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    left_at = db.Column(db.DateTime)
    
    # روابط
    party = db.relationship('PoliticalParty', backref='memberships')
    candidate = db.relationship('Candidate', backref='party_memberships')
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('party_id', 'candidate_id', name='unique_party_candidate'),
    )
    
    def __repr__(self):
        return f'<PartyMembership Party:{self.party_id} Candidate:{self.candidate_id}>'


class ElectoralCoalition(db.Model):
    """ائتلاف‌های انتخاباتی"""
    __tablename__ = 'electoral_coalitions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # اطلاعات
    name = db.Column(db.String(200), nullable=False)
    name_english = db.Column(db.String(200))
    short_name = db.Column(db.String(50))
    
    # محتوا
    description = db.Column(db.Text)
    manifesto = db.Column(db.Text)  # بیانیه مشترک
    logo = db.Column(db.String(500))
    
    # برای انتخابات خاص
    election_type = db.Column(db.String(50))  # مجلس، شورا، ریاست‌جمهوری
    election_year = db.Column(db.Integer, index=True)
    election_round = db.Column(db.Integer, default=1)  # دور اول، دوم
    target_constituency = db.Column(db.String(100))  # حوزه انتخابیه
    target_province = db.Column(db.String(50))
    target_city = db.Column(db.String(50))
    
    # رهبری
    coordinator_candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    
    # آمار
    total_parties = db.Column(db.Integer, default=0)
    total_candidates = db.Column(db.Integer, default=0)
    expected_votes = db.Column(db.Integer, default=0)
    
    # وضعیت
    status = db.Column(db.String(30), default='forming')  # forming, active, campaigning, dissolved
    
    formed_at = db.Column(db.DateTime)
    campaign_starts_at = db.Column(db.DateTime)
    election_date = db.Column(db.Date)
    dissolved_at = db.Column(db.DateTime)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # رابطه
    coordinator = db.relationship('Candidate', backref='coordinated_coalitions')
    
    def __repr__(self):
        return f'<ElectoralCoalition {self.name}>'


class CoalitionMembership(db.Model):
    """عضویت در ائتلاف (احزاب یا نامزدهای مستقل)"""
    __tablename__ = 'coalition_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    
    coalition_id = db.Column(db.Integer, db.ForeignKey('electoral_coalitions.id'), nullable=False, index=True)
    
    # می‌تواند حزب یا نامزد مستقل باشد
    party_id = db.Column(db.Integer, db.ForeignKey('political_parties.id'), nullable=True, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=True, index=True)
    
    # شرایط همکاری
    vote_share_percentage = db.Column(db.Float)  # سهم از آرا
    resource_contribution_percentage = db.Column(db.Float)  # سهم مالی/منابع
    seat_allocation = db.Column(db.Integer)  # تعداد کرسی تخصیصی
    
    # توافقنامه
    agreement_text = db.Column(db.Text)
    agreement_signed = db.Column(db.Boolean, default=False)
    agreement_date = db.Column(db.Date)
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)
    
    # روابط
    coalition = db.relationship('ElectoralCoalition', backref='memberships')
    party = db.relationship('PoliticalParty', backref='coalition_memberships')
    candidate = db.relationship('Candidate', backref='coalition_memberships')
    
    def __repr__(self):
        return f'<CoalitionMembership Coalition:{self.coalition_id}>'


class GroupPurchaseDiscount(db.Model):
    """تخفیف خرید گروهی"""
    __tablename__ = 'group_purchase_discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # تنظیمات
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    
    # شرایط
    min_members = db.Column(db.Integer, nullable=False)  # حداقل تعداد
    max_members = db.Column(db.Integer)  # حداکثر (اختیاری)
    
    discount_type = db.Column(db.String(20), default='percentage')  # percentage, fixed_amount
    discount_value = db.Column(db.Float, nullable=False)  # 20 (برای 20%) یا مبلغ ثابت
    
    # محدودیت‌ها
    applicable_plans = db.Column(db.JSON)  # لیست کد پلن‌های مجاز
    only_for_parties = db.Column(db.Boolean, default=False)  # فقط برای احزاب
    
    # محدودیت زمانی
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    
    # آمار
    total_groups_used = db.Column(db.Integer, default=0)
    total_discount_given = db.Column(db.Float, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GroupPurchaseDiscount {self.name}>'


# ============================================================
# Security & Audit Models
# ============================================================

class AuditLog(db.Model):
    """لاگ رویدادهای امنیتی"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    event_type = db.Column(db.String(50), nullable=False, index=True)  # login, logout, data_export, etc
    user_id = db.Column(db.Integer, nullable=True)
    user_type = db.Column(db.String(20))  # admin, candidate
    
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    details = db.Column(db.JSON)  # جزئیات event
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.event_type} - {self.created_at}>'


class DataExportLog(db.Model):
    """لاگ exportهای داده"""
    __tablename__ = 'data_export_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, index=True)
    
    file_type = db.Column(db.String(20))  # excel, csv, json
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # bytes
    
    exported_by_ip = db.Column(db.String(45))
    exported_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    is_encrypted = db.Column(db.Boolean, default=False)
    
    candidate = db.relationship('Candidate', backref='data_exports')
    
    def __repr__(self):
        return f'<DataExportLog Candidate:{self.candidate_id} - {self.file_type}>'


class BetaTester(db.Model):
    """کاربران آزمایشی"""
    __tablename__ = 'beta_testers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False, unique=True)
    plan_code = db.Column(db.String(20), nullable=True)  # پلن خاص یا همه
    
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by_admin_id = db.Column(db.Integer, nullable=True)
    
    feedback_submitted = db.Column(db.Boolean, default=False)
    feedback_text = db.Column(db.Text)
    
    candidate = db.relationship('Candidate', backref='beta_tester_profile')
    
    def __repr__(self):
        return f'<BetaTester Candidate:{self.candidate_id}>'


class SystemConfig(db.Model):
    """تنظیمات سیستم"""
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'


class DiscountCampaign(db.Model):
    """کمپین‌های تخفیف"""
    __tablename__ = 'discount_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    
    plan_code = db.Column(db.String(20), nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DiscountCampaign {self.plan_code} - {self.discount_percent}%>'


# ═══════════════════════════════════════════════════════════════
# Gamification System
# ═══════════════════════════════════════════════════════════════

class Badge(db.Model):
    """نشان‌های قابل دریافت"""
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # welcome, networker, active, etc.
    name = db.Column(db.String(100), nullable=False)  # نام فارسی
    description = db.Column(db.Text)  # توضیحات
    emoji = db.Column(db.String(10))  # 👋, 🌐, ⚡, etc.
    icon_url = db.Column(db.String(200))  # آدرس آیکون
    
    # شرایط دریافت
    condition_type = db.Column(db.String(50))  # points, action_count, streak, level
    condition_value = db.Column(db.Integer)  # مقدار مورد نیاز
    condition_action = db.Column(db.String(50))  # join, referral, message, etc.
    
    # رنگ و نمایش
    color = db.Column(db.String(20), default='blue')  # برای UI
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Badge {self.name}>'


class UserBadge(db.Model):
    """نشان‌های دریافتی کاربران"""
    __tablename__ = 'user_badges'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_user_id = db.Column(db.Integer, db.ForeignKey('bot_users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # برای نمایش
    is_pinned = db.Column(db.Boolean, default=False)  # نمایش در پروفایل
    
    def __repr__(self):
        return f'<UserBadge user={self.bot_user_id} badge={self.badge_id}>'


class GamificationAction(db.Model):
    """تعریف اکشن‌ها و امتیازات"""
    __tablename__ = 'gamification_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # join, message, referral, etc.
    name = db.Column(db.String(100), nullable=False)  # نام فارسی
    description = db.Column(db.Text)
    
    # امتیاز
    points = db.Column(db.Integer, nullable=False)  # تعداد امتیاز
    
    # تنظیمات
    is_repeatable = db.Column(db.Boolean, default=True)  # قابل تکرار؟
    cooldown_minutes = db.Column(db.Integer, default=0)  # فاصله بین تکرار (دقیقه)
    max_per_day = db.Column(db.Integer, default=-1)  # حداکثر در روز (-1 = نامحدود)
    
    # برای streak
    counts_for_streak = db.Column(db.Boolean, default=False)  # روزانه حساب شه؟
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GamificationAction {self.name}>'


class UserPoints(db.Model):
    """تاریخچه امتیازات کاربران"""
    __tablename__ = 'user_points'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_user_id = db.Column(db.Integer, db.ForeignKey('bot_users.id'), nullable=False)
    action_code = db.Column(db.String(50), nullable=False)  # join, message, referral, etc.
    
    points = db.Column(db.Integer, nullable=False)  # +50, +10, etc.
    description = db.Column(db.String(200))  # توضیح فارسی
    
    # context
    reference_id = db.Column(db.Integer)  # ID مرتبط (message_id, user_id, etc.)
    reference_type = db.Column(db.String(50))  # message, referral, poll, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserPoints user={self.bot_user_id} points={self.points}>'


class Leaderboard(db.Model):
    """جدول امتیازات (snapshot روزانه)"""
    __tablename__ = 'leaderboards'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_instance_id = db.Column(db.Integer, db.ForeignKey('bot_instances.id'), nullable=False)
    bot_user_id = db.Column(db.Integer, db.ForeignKey('bot_users.id'), nullable=False)
    
    date = db.Column(db.Date, default=datetime.utcnow().date)
    rank = db.Column(db.Integer)
    
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Leaderboard rank={self.rank} user={self.bot_user_id}>'



