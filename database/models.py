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
    
    def __repr__(self):
        return f'<Plan {self.name}>'


class Candidate(db.Model):
    """نماینده / کاندیدا"""
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    city = db.Column(db.String(50))
    district = db.Column(db.String(100))
    bio = db.Column(db.Text)
    photo = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # روابط
    bot_instance = db.relationship('BotInstance', backref='candidate', uselist=False, lazy=True)
    resumes = db.relationship('Resume', backref='candidate', lazy=True, cascade='all, delete-orphan')
    programs = db.relationship('Program', backref='candidate', lazy=True, cascade='all, delete-orphan')
    slogans = db.relationship('Slogan', backref='candidate', lazy=True, cascade='all, delete-orphan')
    headquarters = db.relationship('Headquarters', backref='candidate', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='candidate', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('Analytics', backref='candidate', lazy=True, cascade='all, delete-orphan')
    
    # رابطه چند به چند با پلن‌ها
    plans = db.relationship('Plan', secondary=candidate_plans, lazy='subquery',
                           backref=db.backref('candidates', lazy=True))
    
    def __repr__(self):
        return f'<Candidate {self.full_name}>'


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
