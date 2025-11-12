"""
مدل‌های سیستم مشارکت مردمی
Citizen Participation System Models

این مدل‌ها برای ذخیره ایده‌ها، گزارش‌ها، رای‌ها و نظرات مردم هستند.
"""

# این کد باید به database/models.py اضافه شود

class CitizenContribution(db.Model):
    """
    مشارکت‌های مردمی (ایده‌ها و گزارش‌ها)
    
    هر رکورد یک پیشنهاد یا گزارش مشکل از سوی شهروند است.
    """
    __tablename__ = 'citizen_contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # شناسه یکتا برای پیگیری
    tracking_code = db.Column(db.String(20), unique=True, nullable=False)
    # مثال: IDEA-1001, RPT-2001
    
    # کاندید مربوطه
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    
    # اطلاعات کاربر
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    user_username = db.Column(db.String(100))
    user_first_name = db.Column(db.String(100))
    user_last_name = db.Column(db.String(100))
    
    # نوع مشارکت
    contribution_type = db.Column(db.String(50), nullable=False)
    # 'idea' = ایده/پیشنهاد
    # 'report' = گزارش مشکل
    
    # محتوا
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # دسته‌بندی
    category = db.Column(db.String(100), nullable=False)
    # آموزش، بهداشت، ترافیک، امنیت، محیط زیست، ...
    
    # محل
    location_text = db.Column(db.String(500))  # آدرس متنی
    latitude = db.Column(db.Float)  # عرض جغرافیایی
    longitude = db.Column(db.Float)  # طول جغرافیایی
    
    # تصاویر (آرایه JSON از مسیرها)
    images = db.Column(db.JSON, default=[])
    # مثال: ["uploads/contributions/img1.jpg", "uploads/contributions/img2.jpg"]
    
    # وضعیت
    status = db.Column(db.String(50), default='pending')
    # pending, under_review, approved, in_progress, completed, rejected
    
    # اولویت
    priority = db.Column(db.String(20), default='medium')
    # low, medium, high, urgent
    
    # تعاملات
    votes_count = db.Column(db.Integer, default=0)  # تعداد رای
    comments_count = db.Column(db.Integer, default=0)  # تعداد نظر
    views_count = db.Column(db.Integer, default=0)  # تعداد بازدید
    
    # پاسخ کاندید
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
        return f'<CitizenContribution {self.tracking_code}: {self.title}>'
    
    @property
    def status_persian(self):
        """نمایش فارسی وضعیت"""
        status_map = {
            'pending': 'در انتظار بررسی',
            'under_review': 'در حال بررسی',
            'approved': 'تایید شده',
            'in_progress': 'در حال اجرا',
            'completed': 'اجرا شده',
            'rejected': 'رد شده'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def type_persian(self):
        """نمایش فارسی نوع"""
        return 'ایده/پیشنهاد' if self.contribution_type == 'idea' else 'گزارش مشکل'
    
    @property
    def type_emoji(self):
        """ایموجی نوع"""
        return '💡' if self.contribution_type == 'idea' else '📣'


class ContributionVote(db.Model):
    """
    رای‌های مردم به پیشنهادات
    
    هر کاربر فقط یکبار می‌تواند به هر پیشنهاد رای دهد.
    """
    __tablename__ = 'contribution_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # پیشنهاد مربوطه
    contribution_id = db.Column(db.Integer, db.ForeignKey('citizen_contributions.id'), nullable=False)
    
    # کاربر رای‌دهنده
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    user_name = db.Column(db.String(100))
    
    # نوع رای
    vote_type = db.Column(db.String(20), default='upvote')
    # upvote = رای مثبت
    # downvote = رای منفی (اختیاری - ممکنه نخوایم)
    
    # تاریخ
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraint: هر کاربر فقط یکبار رای بدهد
    __table_args__ = (
        db.UniqueConstraint('contribution_id', 'user_telegram_id', name='unique_contribution_vote'),
    )
    
    def __repr__(self):
        return f'<ContributionVote {self.user_telegram_id} -> {self.contribution_id}>'


class ContributionComment(db.Model):
    """
    نظرات مردم روی پیشنهادات
    
    کاربران می‌توانند زیر هر پیشنهاد نظر بگذارند.
    """
    __tablename__ = 'contribution_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # پیشنهاد مربوطه
    contribution_id = db.Column(db.Integer, db.ForeignKey('citizen_contributions.id'), nullable=False)
    
    # کاربر نظردهنده
    user_telegram_id = db.Column(db.BigInteger, nullable=False)
    user_name = db.Column(db.String(100))
    
    # متن نظر
    comment_text = db.Column(db.Text, nullable=False)
    
    # پاسخ به نظر دیگری (اختیاری)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('contribution_comments.id'))
    
    # تاریخ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # روابط
    replies = db.relationship('ContributionComment', backref=db.backref('parent', remote_side=[id]))
    
    def __repr__(self):
        return f'<ContributionComment {self.id} on {self.contribution_id}>'


class CitizenProfile(db.Model):
    """
    پروفایل شهروند (برای گیمیفیکیشن - فاز 2)
    
    این جدول اطلاعات هر شهروند و امتیازاتش را ذخیره می‌کند.
    فعلاً optional هست، بعداً فعالش می‌کنیم.
    """
    __tablename__ = 'citizen_profiles'
    
    telegram_id = db.Column(db.BigInteger, primary_key=True)
    
    # اطلاعات پایه
    full_name = db.Column(db.String(200))
    username = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    neighborhood = db.Column(db.String(200))  # محله
    
    # امتیازات و سطح
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    
    # آمار مشارکت
    contributions_count = db.Column(db.Integer, default=0)  # تعداد ایده/گزارش
    votes_given = db.Column(db.Integer, default=0)  # تعداد رای داده
    comments_count = db.Column(db.Integer, default=0)  # تعداد نظر
    
    # نشان‌ها (Badges)
    badges = db.Column(db.JSON, default=[])
    # مثال: ["first_contribution", "active_citizen", "top_10"]
    
    # تاریخ‌ها
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CitizenProfile {self.telegram_id}: {self.full_name}>'
    
    @property
    def rank_title(self):
        """عنوان رتبه بر اساس سطح"""
        if self.level >= 10:
            return 'شهروند ممتاز'
        elif self.level >= 5:
            return 'شهروند فعال'
        elif self.level >= 2:
            return 'شهروند'
        else:
            return 'تازه‌وارد'


# ============================================
# تنظیمات و ثابت‌ها
# ============================================

# دسته‌بندی‌ها
CONTRIBUTION_CATEGORIES = [
    'آموزش',
    'بهداشت و درمان',
    'ترافیک و حمل‌ونقل',
    'امنیت',
    'محیط زیست',
    'فرهنگی و ورزشی',
    'زیرساخت‌ها (آب، برق، گاز)',
    'اقتصاد و اشتغال',
    'رفاه اجتماعی',
    'سایر'
]

# وضعیت‌ها
CONTRIBUTION_STATUSES = {
    'pending': {'fa': 'در انتظار بررسی', 'color': '#fbbf24', 'icon': '⏳'},
    'under_review': {'fa': 'در حال بررسی', 'color': '#3b82f6', 'icon': '🔍'},
    'approved': {'fa': 'تایید شده', 'color': '#10b981', 'icon': '✅'},
    'in_progress': {'fa': 'در حال اجرا', 'color': '#8b5cf6', 'icon': '🔄'},
    'completed': {'fa': 'اجرا شده', 'color': '#059669', 'icon': '🎉'},
    'rejected': {'fa': 'رد شده', 'color': '#ef4444', 'icon': '❌'}
}

# اولویت‌ها
PRIORITY_LEVELS = {
    'low': {'fa': 'کم', 'color': '#6b7280'},
    'medium': {'fa': 'متوسط', 'color': '#f59e0b'},
    'high': {'fa': 'بالا', 'color': '#ef4444'},
    'urgent': {'fa': 'فوری', 'color': '#dc2626'}
}

# سیستم امتیازدهی (برای فاز 2)
POINTS_SYSTEM = {
    'submit_idea': 10,
    'submit_report': 10,
    'vote': 1,
    'comment': 2,
    'idea_approved': 50,
    'idea_in_progress': 75,
    'idea_completed': 100,
}
