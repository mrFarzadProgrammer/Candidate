"""
پنل مدیریت سوپر ادمین
مدیریت نماینده‌ها، پلن‌ها و راه‌اندازی بات‌ها
"""
import sys
import os

# Add parent directory to path FIRST
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from utils.db_utils import safe_commit
from utils.validators import Validator, validate_form_data
from utils.security_headers import SecurityHeaders, ADMIN_HEADERS
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta

from database.models import (db, Admin, Candidate, Plan, BotInstance, 
                            PlanPurchase, ConsultationRequest, Ticket, Payment)
from config.settings import ADMIN_SECRET_KEY, DATABASE_URI
from bot_engine.bot_manager import BotManager

from flask_migrate import Migrate
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = ADMIN_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Setup Security Headers با تنظیمات admin
SecurityHeaders.init_app(app, custom_headers=ADMIN_HEADERS)

bot_manager = BotManager()


def login_required(f):
    """دکوراتور بررسی لاگین"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """صفحه اصلی - ریدایرکت به داشبورد یا لاگین"""
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحه ورود ادمین"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('ورود موفقیت‌آمیز بود', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
    
    return render_template('admin/login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """داشبورد اصلی ادمین"""
    candidates = Candidate.query.all()
    
    # جمع‌آوری آمار
    stats = {
        'total_candidates': len(candidates),
        'total_bots': BotInstance.query.count(),
        'total_plans': Plan.query.count(),
        'active_plans': Plan.query.filter(Plan.price > 0).count()
    }
    
    return render_template('admin/dashboard.html',
                         candidates=candidates,
                         stats=stats)


@app.route('/candidates')
@login_required
def candidates():
    """لیست نماینده‌ها"""
    candidates = Candidate.query.all()
    return render_template('admin/candidates.html', candidates=candidates)


@app.route('/candidate/create', methods=['GET', 'POST'])
@login_required
def create_candidate():
    """ایجاد نماینده جدید"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        education = request.form.get('education')
        province = request.form.get('province')
        city = request.form.get('city')
        district = request.form.get('district')
        telegram_id = request.form.get('telegram_id')
        
        # بررسی تکراری نبودن نام کاربری
        existing = Candidate.query.filter_by(username=username).first()
        if existing:
            flash('این نام کاربری قبلاً استفاده شده است', 'danger')
            return redirect(url_for('create_candidate'))
        
        # ایجاد نماینده جدید
        candidate = Candidate(
            username=username,
            password=generate_password_hash(password),
            full_name=full_name,
            last_name=last_name,
            phone=phone,
            email=email,
            education=education,
            province=province,
            city=city,
            district=district,
            telegram_id=telegram_id
        )
        
        db.session.add(candidate)
        safe_commit(db, "Database commit failed")
        
        # اختصاص پلن پایه "استارت"
        base_plan = Plan.query.filter_by(code='START').first()
        if base_plan:
            candidate.plans.append(base_plan)
            safe_commit(db, "Database commit failed")
            flash(f'✅ نماینده {full_name} {last_name} با موفقیت ایجاد شد و پلن پایه استارت به وی اختصاص یافت', 'success')
        else:
            flash(f'⚠️ نماینده {full_name} {last_name} ایجاد شد اما پلن پایه یافت نشد', 'warning')
        
        return redirect(url_for('candidates'))
    
    return render_template('admin/create_candidate.html')


@app.route('/candidate/<int:candidate_id>/bot-setup', methods=['GET', 'POST'])
@login_required
def setup_bot(candidate_id):
    """راه‌اندازی بات برای نماینده"""
    candidate = Candidate.query.get_or_404(candidate_id)
    
    if request.method == 'POST':
        bot_token = request.form.get('bot_token')
        bot_username = request.form.get('bot_username')
        
        # بروزرسانی توکن بات در نماینده
        candidate.bot_token = bot_token
        candidate.bot_username = bot_username
        
        # ایجاد یا بروزرسانی نمونه بات
        bot_instance = BotInstance.query.filter_by(candidate_id=candidate.id).first()
        if not bot_instance:
            bot_instance = BotInstance(
                candidate_id=candidate.id,
                bot_token=bot_token,
                bot_username=bot_username,
                is_active=True
            )
            db.session.add(bot_instance)
        else:
            bot_instance.bot_token = bot_token
            bot_instance.bot_username = bot_username
            bot_instance.is_active = True
        
        safe_commit(db, "Database commit failed")
        
        # راه‌اندازی بات (در محیط واقعی)
        # در محیط تست، فقط وضعیت را فعال می‌کنیم
        try:
            # اگر توکن معتبر است، بات را راه‌اندازی کن
            if bot_token and len(bot_token) > 20:
                bot_manager.start_bot(bot_instance.id)
                flash(f'✅ بات @{bot_username} با موفقیت راه‌اندازی شد و آماده دریافت پیام است', 'success')
            else:
                flash(f'⚠️ توکن بات ذخیره شد اما برای راه‌اندازی کامل باید از BotFather توکن معتبر دریافت کنید', 'warning')
        except Exception as e:
            # حتی اگر خطا داشت، اطلاعات ذخیره شده
            flash(f'✅ اطلاعات بات ذخیره شد. بات در صورت معتبر بودن توکن فعال خواهد شد', 'info')
        
        return redirect(url_for('candidates'))
    
    return render_template('admin/setup_bot.html', candidate=candidate)


@app.route('/candidate/<int:candidate_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_candidate(candidate_id):
    """ویرایش اطلاعات نماینده"""
    candidate = Candidate.query.get_or_404(candidate_id)
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        education = request.form.get('education')
        province = request.form.get('province')
        city = request.form.get('city')
        district = request.form.get('district')
        password = request.form.get('password')
        telegram_id = request.form.get('telegram_id')
        
        candidate.full_name = full_name
        candidate.last_name = last_name
        candidate.phone = phone
        candidate.email = email
        candidate.education = education
        candidate.province = province
        candidate.city = city
        candidate.district = district
        candidate.telegram_id = telegram_id
        
        # اگر رمز عبور جدید وارد شده، آن را بروز کن
        if password:
            candidate.password = generate_password_hash(password)
        
        safe_commit(db, "Database commit failed")
        flash(f'اطلاعات {full_name} {last_name or ""} با موفقیت بروزرسانی شد', 'success')
        return redirect(url_for('candidates'))
    
    plans = Plan.query.all()
    return render_template('admin/edit_candidate.html', candidate=candidate, plans=plans)


@app.route('/candidate/<int:candidate_id>/delete', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    """حذف نماینده و تمام اطلاعات مرتبط"""
    try:
        candidate = Candidate.query.get_or_404(candidate_id)
        full_name = candidate.full_name
        
        # Import necessary models for cascade deletion
        from database.models import (
            BotInstance, PlanPurchase, ConsultationRequest, 
            Ticket, Payment, CitizenContribution, CandidateRanking,
            TrialPeriod, ReferralProgram, ReferralReward, MonthlyTopCitizen,
            VIPInteraction, LiveEvent, PartyMembership, CoalitionMembership,
            DataExportLog, BetaTester, BotChannel, ScheduledPost,
            BroadcastMessage, Poll, AutoReply
        )
        
        # حذف تمام رکوردهای وابسته به candidate
        # (رکوردهایی که در relationship cascade='all, delete-orphan' ندارند)
        BotInstance.query.filter_by(candidate_id=candidate_id).delete()
        PlanPurchase.query.filter_by(candidate_id=candidate_id).delete()
        ConsultationRequest.query.filter_by(candidate_id=candidate_id).delete()
        Ticket.query.filter_by(candidate_id=candidate_id).delete()
        Payment.query.filter_by(candidate_id=candidate_id).delete()
        CitizenContribution.query.filter_by(candidate_id=candidate_id).delete()
        CandidateRanking.query.filter_by(candidate_id=candidate_id).delete()
        TrialPeriod.query.filter_by(candidate_id=candidate_id).delete()
        ReferralProgram.query.filter_by(candidate_id=candidate_id).delete()
        ReferralReward.query.filter_by(referred_candidate_id=candidate_id).delete()
        MonthlyTopCitizen.query.filter_by(candidate_id=candidate_id).delete()
        VIPInteraction.query.filter_by(candidate_id=candidate_id).delete()
        LiveEvent.query.filter_by(candidate_id=candidate_id).delete()
        PartyMembership.query.filter_by(candidate_id=candidate_id).delete()
        CoalitionMembership.query.filter_by(candidate_id=candidate_id).delete()
        DataExportLog.query.filter_by(candidate_id=candidate_id).delete()
        BetaTester.query.filter_by(candidate_id=candidate_id).delete()
        BotChannel.query.filter_by(candidate_id=candidate_id).delete()
        ScheduledPost.query.filter_by(candidate_id=candidate_id).delete()
        BroadcastMessage.query.filter_by(candidate_id=candidate_id).delete()
        Poll.query.filter_by(candidate_id=candidate_id).delete()
        AutoReply.query.filter_by(candidate_id=candidate_id).delete()
        
        # حذف رکوردهای referred_by (نمایندگانی که این candidate آنها را معرفی کرده)
        Candidate.query.filter_by(referred_by=candidate_id).update({Candidate.referred_by: None})
        
        # حذف از جدول many-to-many (candidate_plans)
        candidate.plans = []
        
        # حذف نماینده (relationships با cascade خودشان حذف می‌شوند)
        db.session.delete(candidate)
        safe_commit(db, "خطا در حذف نماینده از دیتابیس")
        
        flash(f'نماینده {full_name} و تمام اطلاعات مرتبط با موفقیت حذف شدند', 'success')
        return redirect(url_for('candidates'))
        
    except Exception as e:
        logging.error(f"Error deleting candidate {candidate_id}: {str(e)}")
        flash(f'خطا در حذف نماینده: {str(e)}', 'danger')
        return redirect(url_for('candidates'))


@app.route('/plans')
@login_required
def plans():
    """مدیریت پلن‌ها"""
    plans = Plan.query.all()
    return render_template('admin/plans.html', plans=plans)


@app.route('/plans/create', methods=['POST'])
@login_required
def create_plan():
    """ایجاد پلن جدید"""
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')
    price = int(request.form.get('price', 0))
    duration_days = int(request.form.get('duration_days', 30))
    is_active = request.form.get('is_active') == '1'
    
    # بررسی تکراری نبودن کد
    existing = Plan.query.filter_by(code=code).first()
    if existing:
        flash(f'پلنی با کد {code} قبلاً ثبت شده است', 'danger')
        return redirect(url_for('plans'))
    
    # ایجاد پلن جدید
    plan = Plan(
        name=name,
        code=code.upper(),
        description=description,
        price=price,
        duration_days=duration_days,
        is_active=is_active,
        # محدودیت‌ها
        max_messages=int(request.form.get('max_messages', -1)),
        max_programs=int(request.form.get('max_programs', -1)),
        max_headquarters=int(request.form.get('max_headquarters', -1)),
        max_bot_users=int(request.form.get('max_bot_users', -1)),
        # امکانات AI
        has_ai=request.form.get('has_ai') == '1',
        ai_message_classification=request.form.get('ai_message_classification') == '1',
        ai_sentiment_analysis=request.form.get('ai_sentiment_analysis') == '1',
        ai_auto_reply=request.form.get('ai_auto_reply') == '1',
        ai_content_generation=request.form.get('ai_content_generation') == '1',
        ai_smart_chatbot=request.form.get('ai_smart_chatbot') == '1',
        # سایر امکانات
        can_mass_message=request.form.get('can_mass_message') == '1',
        max_mass_message_per_day=int(request.form.get('max_mass_message_per_day', 0)),
        has_analytics=request.form.get('has_analytics') == '1',
        has_advanced_analytics=request.form.get('has_advanced_analytics') == '1',
        priority_support=request.form.get('priority_support') == '1',
        # ظاهر
        display_order=int(request.form.get('display_order', 0)),
        badge_color=request.form.get('badge_color', 'primary'),
        is_popular=request.form.get('is_popular') == '1'
    )
    
    db.session.add(plan)
    safe_commit(db, "Database commit failed")
    
    flash(f'پلن {name} با موفقیت ایجاد شد', 'success')
    return redirect(url_for('plans'))


@app.route('/plans/<int:plan_id>/edit', methods=['POST'])
@login_required
def edit_plan(plan_id):
    """ویرایش پلن"""
    plan = Plan.query.get_or_404(plan_id)
    
    plan.name = request.form.get('name')
    code = request.form.get('code')
    plan.description = request.form.get('description')
    plan.price = int(request.form.get('price', 0))
    plan.duration_days = int(request.form.get('duration_days', 30))
    plan.is_active = request.form.get('is_active') == '1'
    
    # محدودیت‌ها
    plan.max_messages = int(request.form.get('max_messages', -1))
    plan.max_programs = int(request.form.get('max_programs', -1))
    plan.max_headquarters = int(request.form.get('max_headquarters', -1))
    plan.max_bot_users = int(request.form.get('max_bot_users', -1))
    
    # امکانات AI
    plan.has_ai = request.form.get('has_ai') == '1'
    plan.ai_message_classification = request.form.get('ai_message_classification') == '1'
    plan.ai_sentiment_analysis = request.form.get('ai_sentiment_analysis') == '1'
    plan.ai_auto_reply = request.form.get('ai_auto_reply') == '1'
    plan.ai_content_generation = request.form.get('ai_content_generation') == '1'
    plan.ai_smart_chatbot = request.form.get('ai_smart_chatbot') == '1'
    
    # سایر امکانات
    plan.can_mass_message = request.form.get('can_mass_message') == '1'
    plan.max_mass_message_per_day = int(request.form.get('max_mass_message_per_day', 0))
    plan.has_analytics = request.form.get('has_analytics') == '1'
    plan.has_advanced_analytics = request.form.get('has_advanced_analytics') == '1'
    plan.priority_support = request.form.get('priority_support') == '1'
    
    # ظاهر
    plan.display_order = int(request.form.get('display_order', 0))
    plan.badge_color = request.form.get('badge_color', 'primary')
    plan.is_popular = request.form.get('is_popular') == '1'
    
    # بررسی تکراری نبودن کد (برای پلن‌های دیگر)
    existing = Plan.query.filter(Plan.code == code.upper(), Plan.id != plan_id).first()
    if existing:
        flash(f'پلنی دیگر با کد {code} وجود دارد', 'danger')
        return redirect(url_for('plans'))
    
    plan.code = code.upper()
    
    safe_commit(db, "Database commit failed")
    flash(f'پلن {plan.name} با موفقیت به‌روزرسانی شد', 'success')
    return redirect(url_for('plans'))


@app.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """حذف پلن"""
    plan = Plan.query.get_or_404(plan_id)
    
    # بررسی استفاده از این پلن توسط نمایندگان
    if plan.candidates:
        flash(f'پلن {plan.name} توسط {len(plan.candidates)} نماینده استفاده می‌شود و قابل حذف نیست', 'danger')
        return redirect(url_for('plans'))
    
    plan_name = plan.name
    db.session.delete(plan)
    safe_commit(db, "Database commit failed")
    
    flash(f'پلن {plan_name} با موفقیت حذف شد', 'success')
    return redirect(url_for('plans'))


@app.route('/candidate/<int:candidate_id>/activate-plan', methods=['POST'])
@login_required
def activate_plan(candidate_id):
    """فعال‌سازی پلن برای نماینده"""
    from datetime import datetime, timedelta
    
    candidate = Candidate.query.get_or_404(candidate_id)
    plan_id = request.form.get('plan_id')
    plan = Plan.query.get_or_404(plan_id)
    
    # ایجاد رکورد خرید
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=plan.duration_days)
    
    purchase = PlanPurchase(
        candidate_id=candidate.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        payment_amount=plan.price,
        payment_status='completed',
        payment_method='admin',  # فعال‌سازی توسط ادمین
        is_active=True
    )
    
    db.session.add(purchase)
    
    # اضافه کردن پلن به نماینده (برای سازگاری با کد قدیمی)
    if plan not in candidate.plans:
        candidate.plans.append(plan)
    
    safe_commit(db, "Database commit failed")
    
    # پردازش پاداش معرفی (اگر این نامزد معرفی شده باشد)
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'candidate_panel'))
        from referral_utils import process_conversion_reward
        reward = process_conversion_reward(candidate.id)
        if reward:
            flash(f'پاداش معرفی ({reward.reward_amount:,.0f} تومان) برای معرف ثبت شد', 'info')
    except Exception as e:
        logger.debug(f"خطا در پردازش پاداش معرفی: {e}")
    
    flash(f'پلن {plan.name} برای {candidate.full_name} تا تاریخ {end_date.strftime("%Y/%m/%d")} فعال شد', 'success')
    
    return redirect(url_for('candidates'))


@app.route('/subscriptions')
@login_required
def subscriptions():
    """مدیریت اشتراک‌ها و خریدها"""
    purchases = PlanPurchase.query.order_by(PlanPurchase.purchase_date.desc()).all()
    consultations = ConsultationRequest.query.filter_by(status='pending').order_by(ConsultationRequest.created_at.desc()).all()
    
    return render_template('admin/subscriptions.html', purchases=purchases, consultations=consultations)


@app.route('/consultation/<int:consultation_id>/update', methods=['POST'])
@login_required
def update_consultation(consultation_id):
    """به‌روزرسانی وضعیت درخواست مشاوره"""
    from datetime import datetime
    
    consultation = ConsultationRequest.query.get_or_404(consultation_id)
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes')
    
    consultation.status = status
    consultation.admin_notes = admin_notes
    consultation.contacted_at = datetime.utcnow()
    consultation.contacted_by = session.get('admin_id')
    
    safe_commit(db, "Database commit failed")
    flash('وضعیت درخواست به‌روزرسانی شد', 'success')
    
    return redirect(url_for('subscriptions'))


@app.route('/logout')
def logout():
    """خروج از سیستم"""
    session.clear()
    flash('با موفقیت خارج شدید', 'info')
    return redirect(url_for('login'))


@app.route('/api/bot/status/<int:bot_id>')
@login_required
def bot_status(bot_id):
    """وضعیت بات (API)"""
    bot = BotInstance.query.get_or_404(bot_id)
    return jsonify({
        'is_active': bot.is_active,
        'last_active': bot.last_active.isoformat() if bot.last_active else None
    })


@app.route('/candidate/<int:id>/activate-trial', methods=['POST'])
@login_required
def activate_trial(id):
    """فعال‌سازی Trial 3 روزه رایگان"""
    from datetime import timedelta
    
    candidate = Candidate.query.get_or_404(id)
    
    # چک کردن استفاده قبلی از Trial
    if candidate.has_used_trial:
        flash('این کاندیدا قبلاً از دوره تست رایگان استفاده کرده است', 'danger')
        return redirect(url_for('candidates'))
    
    # پیدا کردن پلن PROFESSIONAL
    professional_plan = Plan.query.filter_by(code='PROFESSIONAL').first()
    if not professional_plan:
        # اگر پلن PROFESSIONAL نبود، اولین پلن فعال را بگیر
        professional_plan = Plan.query.filter_by(is_active=True).first()
    
    if not professional_plan:
        flash('هیچ پلن فعالی برای اعطای Trial وجود ندارد', 'danger')
        return redirect(url_for('candidates'))
    
    # ایجاد Trial Purchase
    from datetime import datetime
    trial_purchase = PlanPurchase(
        candidate_id=candidate.id,
        plan_id=professional_plan.id,
        purchase_date=datetime.utcnow(),
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=3),
        payment_amount=0,
        payment_status='completed',
        payment_method='free',
        is_trial=True,
        trial_used=True,
        is_active=True,
        notes='دوره تست 3 روزه رایگان - فعال‌سازی توسط ادمین'
    )
    
    # علامت‌گذاری کاندیدا
    candidate.has_used_trial = True
    
    db.session.add(trial_purchase)
    safe_commit(db, "Database commit failed")
    
    flash(f'✅ دوره تست 3 روزه برای {candidate.full_name} فعال شد!', 'success')
    return redirect(url_for('candidates'))


@app.route('/candidate/<int:id>/grant-free', methods=['GET', 'POST'])
@login_required
def grant_free_plan(id):
    """اعطای پلن رایگان با هر مدت دلخواه"""
    from datetime import timedelta, datetime
    
    candidate = Candidate.query.get_or_404(id)
    
    if request.method == 'POST':
        plan_id = request.form.get('plan_id')
        duration_days = int(request.form.get('duration_days', 30))
        admin_note = request.form.get('admin_note', '')
        
        plan = Plan.query.get_or_404(plan_id)
        
        # ایجاد Free Grant Purchase
        free_purchase = PlanPurchase(
            candidate_id=candidate.id,
            plan_id=plan.id,
            purchase_date=datetime.utcnow(),
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_days),
            payment_amount=0,
            payment_status='completed',
            payment_method='free',
            custom_duration_days=duration_days,
            admin_granted=True,
            admin_note=admin_note,
            is_active=True,
            notes=f'اعطای رایگان {duration_days} روزه توسط ادمین'
        )
        
        db.session.add(free_purchase)
        safe_commit(db, "Database commit failed")
        
        flash(f'✅ پلن {plan.name} برای {duration_days} روز به {candidate.full_name} اعطا شد!', 'success')
        return redirect(url_for('candidates'))
    
    # GET - نمایش فرم
    plans = Plan.query.filter_by(is_active=True).all()
    return render_template('admin/grant_free.html', candidate=candidate, plans=plans)


@app.route('/candidate/<int:id>/extend-plan', methods=['POST'])
@login_required
def extend_plan(id):
    """تمدید پلن فعلی کاندیدا"""
    from datetime import timedelta
    
    candidate = Candidate.query.get_or_404(id)
    extend_days = int(request.form.get('extend_days', 30))
    
    # پیدا کردن آخرین خرید فعال
    latest_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate.id,
        is_active=True
    ).order_by(PlanPurchase.end_date.desc()).first()
    
    if not latest_purchase:
        flash('این کاندیدا پلن فعالی ندارد', 'warning')
        return redirect(url_for('candidates'))
    
    # تمدید تاریخ پایان
    latest_purchase.end_date = latest_purchase.end_date + timedelta(days=extend_days)
    latest_purchase.notes = (latest_purchase.notes or '') + f'\n[تمدید {extend_days} روزه توسط ادمین]'
    
    safe_commit(db, "Database commit failed")
    
    flash(f'✅ پلن {candidate.full_name} به مدت {extend_days} روز تمدید شد!', 'success')
    return redirect(url_for('candidates'))


@app.route('/tickets')
@login_required
def tickets():
    """مدیریت تیکت‌ها"""
    status_filter = request.args.get('status', 'all')
    
    query = Ticket.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    # آمار تیکت‌ها
    stats = {
        'total': Ticket.query.count(),
        'pending': Ticket.query.filter_by(status='pending').count(),
        'approved': Ticket.query.filter_by(status='approved').count(),
        'rejected': Ticket.query.filter_by(status='rejected').count(),
    }
    
    return render_template('admin/tickets.html', 
                         tickets=tickets, 
                         stats=stats,
                         status_filter=status_filter)


@app.route('/tickets/<int:ticket_id>/approve', methods=['POST'])
@login_required
def approve_ticket(ticket_id):
    """تایید تیکت و فعال‌سازی پلن"""
    ticket = Ticket.query.get_or_404(ticket_id)
    admin_response = request.form.get('admin_response', '')
    
    if ticket.ticket_type == 'purchase' and ticket.plan_id:
        # فعال‌سازی پلن
        from datetime import timedelta
        
        # بروزرسانی یا ساخت Payment
        payment = Payment.query.filter_by(ticket_id=ticket.id).first()
        if not payment:
            payment = Payment(
                ticket_id=ticket.id,
                candidate_id=ticket.candidate_id,
                plan_id=ticket.plan_id,
                amount=ticket.payment_amount,
                payment_method=ticket.payment_method,
                receipt_image=ticket.receipt_image
            )
            db.session.add(payment)
        
        payment.status = 'verified'
        payment.verified_at = datetime.utcnow()
        payment.plan_activated = True
        payment.activation_date = datetime.utcnow()
        payment.expiry_date = datetime.utcnow() + timedelta(days=ticket.plan.duration_days)
        
        # اضافه کردن پلن به کاندید
        candidate = ticket.candidate
        if ticket.plan not in candidate.plans:
            candidate.plans.append(ticket.plan)
        
        # ثبت در PlanPurchase
        plan_purchase = PlanPurchase(
            candidate_id=candidate.id,
            plan_id=ticket.plan_id,
            price=ticket.payment_amount,
            payment_method=ticket.payment_method,
            start_date=payment.activation_date,
            end_date=payment.expiry_date,
            is_active=True,
            notes=f'فعال‌سازی از طریق تیکت {ticket.ticket_number}'
        )
        db.session.add(plan_purchase)
    
    # بروزرسانی تیکت
    ticket.status = 'approved'
    ticket.admin_response = admin_response or 'پرداخت شما تایید و پلن فعال شد.'
    ticket.admin_id = session.get('admin_id')
    ticket.updated_at = datetime.utcnow()
    
    safe_commit(db, "Database commit failed")
    
    flash(f'✅ تیکت {ticket.ticket_number} تایید شد و پلن فعال گردید', 'success')
    return redirect(url_for('tickets'))


@app.route('/tickets/<int:ticket_id>/reject', methods=['POST'])
@login_required
def reject_ticket(ticket_id):
    """رد تیکت"""
    ticket = Ticket.query.get_or_404(ticket_id)
    admin_response = request.form.get('admin_response', '')
    
    ticket.status = 'rejected'
    ticket.admin_response = admin_response or 'متاسفانه پرداخت شما تایید نشد.'
    ticket.admin_id = session.get('admin_id')
    ticket.updated_at = datetime.utcnow()
    
    # اگر Payment وجود داشت آن را هم reject کن
    payment = Payment.query.filter_by(ticket_id=ticket.id).first()
    if payment:
        payment.status = 'failed'
    
    safe_commit(db, "Database commit failed")
    
    flash(f'❌ تیکت {ticket.ticket_number} رد شد', 'warning')
    return redirect(url_for('tickets'))


# ========== Referral Rewards Management ==========

@app.route('/referrals')
@login_required
def referral_rewards():
    """مدیریت پاداش‌های معرفی"""
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'candidate_panel'))
    from database.models import ReferralReward, ReferralProgram, Candidate
    
    # لیست پاداش‌های در انتظار تایید
    pending_rewards = db.session.query(
        ReferralReward, ReferralProgram, Candidate
    ).join(
        ReferralProgram, ReferralReward.referral_program_id == ReferralProgram.id
    ).join(
        Candidate, ReferralProgram.candidate_id == Candidate.id
    ).filter(
        ReferralReward.status == 'pending'
    ).order_by(ReferralReward.awarded_at.desc()).all()
    
    # لیست پاداش‌های تایید شده
    approved_rewards = db.session.query(
        ReferralReward, ReferralProgram, Candidate
    ).join(
        ReferralProgram, ReferralReward.referral_program_id == ReferralProgram.id
    ).join(
        Candidate, ReferralProgram.candidate_id == Candidate.id
    ).filter(
        ReferralReward.status == 'approved'
    ).order_by(ReferralReward.approved_at.desc()).limit(50).all()
    
    return render_template(
        'admin/referrals.html',
        pending_rewards=pending_rewards,
        approved_rewards=approved_rewards
    )


@app.route('/referrals/approve/<int:reward_id>', methods=['POST'])
@login_required
def approve_referral_reward(reward_id):
    """تایید پاداش معرفی"""
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'candidate_panel'))
    from referral_utils import approve_reward
    from database.models import ReferralReward
    
    reward = ReferralReward.query.get_or_404(reward_id)
    
    if approve_reward(reward_id):
        flash(f'✅ پاداش {reward.reward_amount:,.0f} تومان تایید شد', 'success')
    else:
        flash('❌ خطا در تایید پاداش', 'danger')
    
    return redirect(url_for('referral_rewards'))


@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast_message():
    from database.models import Candidate
    from bot_engine.broadcast_sender import send_broadcast_message
    candidates = Candidate.query.filter(Candidate.telegram_id.isnot(None)).all()
    # جمع‌آوری آمار مشابه داشبورد
    from database.models import BotInstance, Plan
    stats = {
        'total_candidates': Candidate.query.count(),
        'total_bots': BotInstance.query.count(),
        'total_plans': Plan.query.count(),
        'active_plans': Plan.query.filter(Plan.price > 0).count()
    }
    if request.method == 'POST':
        message_type = request.form.get('message_type')
        message_text = request.form.get('message_text')
        recipients = request.form.getlist('recipients')
        file = request.files.get('file')
        # انتخاب همه نماینده‌ها
        if 'all' in recipients:
            recipient_ids = [c.id for c in candidates]
        else:
            recipient_ids = [int(r) for r in recipients]
        selected_candidates = [c for c in candidates if c.id in recipient_ids]
        telegram_ids = [c.telegram_id for c in selected_candidates if c.telegram_id]
        # ارسال پیام
        send_broadcast_message(telegram_ids, message_type, message_text, file)
        flash(f'پیام به {len(telegram_ids)} نماینده ارسال شد.', 'success')
        return redirect(url_for('broadcast_message'))
    return render_template('admin/broadcast_message.html', candidates=candidates, stats=stats)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # ایجاد ادمین پیش‌فرض در صورت عدم وجود
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                full_name='مدیر سیستم'
            )
            db.session.add(admin)
            safe_commit(db, "Database commit failed")
            logger.debug('✅ ادمین پیش‌فرض ایجاد شد: admin / admin123')
    
    app.run(debug=True, port=5000, host='0.0.0.0')
