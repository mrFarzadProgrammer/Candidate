"""
پنل اختصاصی نماینده
مدیریت اطلاعات شخصی، رزومه، برنامه‌ها، ستادها
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sys
import os
from datetime import datetime
import requests
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging first
from utils.logging_config import setup_logging
from utils.db_utils import safe_commit
from utils.validators import Validator, validate_form_data
from utils.security_headers import SecurityHeaders

from database.models import (db, Candidate, Resume, Program, Slogan, 
                            Headquarters, Message, Analytics, Plan, 
                            PlanPurchase, ConsultationRequest, BotChannel,
                            ScheduledPost, BotInstance, ChannelStats, 
                            BroadcastMessage, BroadcastLog, Poll, PollOption, 
                            PollVote, AutoReply, Ticket, Payment,
                            CitizenContribution, ContributionVote, ContributionComment, CitizenProfile,
                            MarketplaceBenchmark, CandidateRanking, TrialPeriod, 
                            ReferralProgram, ReferralReward, MonthlyTopCitizen, VIPInteraction,
                            PoliticalParty, PartyMembership, ElectoralCoalition, CoalitionMembership)
from config.settings import CANDIDATE_SECRET_KEY, DATABASE_URI, UPLOAD_FOLDER
from security.security_utils import (
    hash_password, verify_password, sanitize_input, 
    csrf_protected, rate_limiter
)

# Get absolute paths for templates and static
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = CANDIDATE_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)

# Setup logging
logger = setup_logging(app, log_level='DEBUG' if app.debug else 'INFO')

# Setup Security Headers
SecurityHeaders.init_app(app)


# Global security: Auto-sanitize all form inputs
@app.before_request
def sanitize_request_data():
    """خودکار کردن sanitization برای همه form inputs"""
    if request.method == 'POST' and request.form:
        # Create a new form data dict with sanitized values
        from werkzeug.datastructures import ImmutableMultiDict
        sanitized = {}
        for key, value in request.form.items():
            # Skip password fields and files
            if 'password' not in key.lower() and 'csrf' not in key.lower():
                if isinstance(value, str):
                    sanitized[key] = sanitize_input(value)
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        # Replace request.form with sanitized version
        request.form = ImmutableMultiDict(sanitized)


def login_required(f):
    """دکوراتور بررسی لاگین"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug(f"Checking login - session: {dict(session)}")
        if 'candidate_id' not in session:
            logger.warning(f"Unauthorized access attempt to {f.__name__}")
            flash("لطفاً ابتدا وارد شوید", "warning")
            return redirect(url_for('login'))
        logger.debug(f"User authenticated: candidate_id={session['candidate_id']}")
        return f(*args, **kwargs)
    return decorated_function


def secure_route(rate_limit="100 per minute"):
    """
    دکوراتور امنیتی ترکیبی برای route های POST
    شامل: login_required + csrf_protected + rate_limiter
    """
    def decorator(f):
        # Apply all security layers
        secured_function = csrf_protected(f)
        secured_function = rate_limiter.limit(rate_limit)(secured_function)
        secured_function = login_required(secured_function)
        return secured_function
    return decorator


def has_plan(plan_code):
    """بررسی فعال بودن پلن"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            candidate_id = session.get('candidate_id')
            candidate = Candidate.query.get(candidate_id)
            
            if not any(plan.code == plan_code for plan in candidate.plans):
                flash(f'برای استفاده از این امکان باید پلن مربوطه را خریداری کنید', 'warning')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator



logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """صفحه اصلی"""
    if 'candidate_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@rate_limiter.limit("10 per minute")
def login():
    """ورود نماینده"""
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        logger.debug(f"🔍 تلاش ورود - نام کاربری: {username}")
        
        candidate = Candidate.query.filter_by(username=username).first()
        
        if not candidate:
            logger.debug(f"❌ نماینده با نام کاربری '{username}' پیدا نشد")
            flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
        else:
            logger.debug(f"✅ نماینده پیدا شد: {candidate.full_name}")
            # Try bcrypt first, fallback to werkzeug for backward compatibility
            password_match = verify_password(password, candidate.password)
            if not password_match and check_password_hash(candidate.password, password):
                # Rehash with bcrypt for security
                candidate.password = hash_password(password)
                safe_commit(db, "Database commit failed")
                password_match = True
            
            logger.debug(f"🔐 نتیجه بررسی: {'موفق ✅' if password_match else 'ناموفق ❌'}")
            
            if password_match:
                session.clear()
                session['candidate_id'] = candidate.id
                session['candidate_name'] = candidate.full_name
                session.permanent = True
                logger.debug(f"✅ Session ست شد: candidate_id={candidate.id}")
                logger.debug(f"✅ ورود موفق - ریدایرکت به داشبورد")
                flash('خوش آمدید!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
    
    return render_template('candidate/login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """داشبورد نماینده"""
    from datetime import datetime
    candidate = Candidate.query.get(session['candidate_id'])
    
    # اطلاعات پلن فعلی
    active_plan = candidate.get_active_plan()
    latest_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate.id, is_active=True
    ).order_by(PlanPurchase.end_date.desc()).first()
    
    # محاسبه استفاده از محدودیت‌ها
    plan_usage = {}
    if active_plan:
        # استفاده از پیام در ماه جاری
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        messages_this_month = Message.query.filter_by(candidate_id=candidate.id).filter(
            Message.created_at >= month_start
        ).count()
        
        # تعداد برنامه‌ها
        total_programs = Program.query.filter_by(candidate_id=candidate.id).count()
        
        # تعداد دفاتر
        total_headquarters = Headquarters.query.filter_by(candidate_id=candidate.id).count()
        
        plan_usage = {
            'messages': {
                'used': messages_this_month,
                'limit': active_plan.max_messages if active_plan.max_messages != -1 else 'نامحدود',
                'percentage': (messages_this_month / active_plan.max_messages * 100) if active_plan.max_messages > 0 else 0
            },
            'programs': {
                'used': total_programs,
                'limit': active_plan.max_programs if active_plan.max_programs != -1 else 'نامحدود',
                'percentage': (total_programs / active_plan.max_programs * 100) if active_plan.max_programs > 0 else 0
            },
            'headquarters': {
                'used': total_headquarters,
                'limit': active_plan.max_headquarters if active_plan.max_headquarters != -1 else 'نامحدود',
                'percentage': (total_headquarters / active_plan.max_headquarters * 100) if active_plan.max_headquarters > 0 else 0
            }
        }
    
    # آمار کلی
    total_messages = Message.query.filter_by(candidate_id=candidate.id).count()
    unread_messages = Message.query.filter_by(candidate_id=candidate.id, is_read=False).count()
    
    # آمار بازدید (اگر پلن آمار فعال باشد)
    analytics_data = None
    if any(plan.code == 'ANALYTICS' for plan in candidate.plans):
        analytics_data = Analytics.query.filter_by(candidate_id=candidate.id).order_by(Analytics.date.desc()).limit(7).all()
    
    return render_template('candidate/dashboard.html',
                         candidate=candidate,
                         total_messages=total_messages,
                         unread_messages=unread_messages,
                         analytics_data=analytics_data,
                         active_plan=active_plan,
                         latest_purchase=latest_purchase,
                         plan_usage=plan_usage)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
@csrf_protected
@rate_limiter.limit("30 per minute")
def profile():
    """ویرایش اطلاعات شخصی"""
    candidate = Candidate.query.get(session['candidate_id'])
    
    if request.method == 'POST':
        # تغییر رمز عبور
        if request.form.get('change_password'):
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not verify_password(current_password, candidate.password):
                flash('رمز عبور فعلی اشتباه است', 'error')
            elif new_password != confirm_password:
                flash('رمز عبور جدید و تکرار آن یکسان نیستند', 'error')
            elif len(new_password) < 8:
                flash('رمز عبور باید حداقل 8 کاراکتر باشد', 'error')
            else:
                candidate.password = hash_password(new_password)
                safe_commit(db, "Database commit failed")
                flash('رمز عبور با موفقیت تغییر کرد', 'success')
                return redirect(url_for('profile'))
        else:
            # به‌روزرسانی اطلاعات شخصی
            candidate.full_name = sanitize_input(request.form.get('full_name', ''))
            candidate.last_name = sanitize_input(request.form.get('last_name', ''))
            candidate.email = sanitize_input(request.form.get('email', ''))
            candidate.phone = sanitize_input(request.form.get('phone', ''))
            candidate.province = sanitize_input(request.form.get('province', ''))
            candidate.city = sanitize_input(request.form.get('city', ''))
            candidate.district = sanitize_input(request.form.get('district', ''))
            candidate.education = sanitize_input(request.form.get('education', ''))
            
            # آپلود تصویر
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename:
                    filename = secure_filename(f"candidate_{candidate.id}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    candidate.photo = filename
            
            safe_commit(db, "Database commit failed")
            flash('اطلاعات با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('profile'))
    
    return render_template('candidate/profile.html', candidate=candidate)


@app.route('/resume', methods=['GET', 'POST'])
@secure_route()
def resume():
    """مدیریت رزومه"""
    candidate = Candidate.query.get(session['candidate_id'])
    resumes = Resume.query.filter_by(candidate_id=candidate.id).order_by(Resume.order).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        year = request.form.get('year')
        
        resume_item = Resume(
            candidate_id=candidate.id,
            title=title,
            description=description,
            year=year,
            order=len(resumes) + 1
        )
        
        db.session.add(resume_item)
        safe_commit(db, "Database commit failed")
        flash('آیتم رزومه اضافه شد', 'success')
        return redirect(url_for('resume'))
    
    return render_template('candidate/resume.html', candidate=candidate, resumes=resumes)


@app.route('/programs', methods=['GET', 'POST'])
@secure_route()
def programs():
    """مدیریت برنامه‌های انتخاباتی"""
    candidate = Candidate.query.get(session['candidate_id'])
    programs = Program.query.filter_by(candidate_id=candidate.id).all()
    
    if request.method == 'POST':
        # بررسی محدودیت پلن
        if not candidate.can_add_program():
            active_plan = candidate.get_active_plan()
            if active_plan:
                flash(f'شما به حداکثر تعداد برنامه‌ها ({active_plan.max_programs}) رسیده‌اید. برای افزودن برنامه بیشتر، پلن خود را ارتقا دهید.', 'warning')
            else:
                flash('شما پلن فعالی ندارید. برای افزودن برنامه، لطفاً یک پلن خریداری کنید.', 'danger')
            return redirect(url_for('view_plans'))
        
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        
        program = Program(
            candidate_id=candidate.id,
            title=title,
            description=description,
            category=category
        )
        
        db.session.add(program)
        safe_commit(db, "Database commit failed")
        flash('برنامه جدید اضافه شد', 'success')
        return redirect(url_for('programs'))
    
    return render_template('candidate/programs.html', candidate=candidate, programs=programs)


@app.route('/headquarters', methods=['GET', 'POST'])
@secure_route()
def headquarters():
    """مدیریت ستادهای انتخاباتی"""
    candidate = Candidate.query.get(session['candidate_id'])
    hqs = Headquarters.query.filter_by(candidate_id=candidate.id).all()
    
    if request.method == 'POST':
        # بررسی محدودیت پلن
        if not candidate.can_add_headquarters():
            active_plan = candidate.get_active_plan()
            if active_plan:
                flash(f'شما به حداکثر تعداد دفاتر ({active_plan.max_headquarters}) رسیده‌اید. برای افزودن دفتر بیشتر، پلن خود را ارتقا دهید.', 'warning')
            else:
                flash('شما پلن فعالی ندارید. برای افزودن دفتر، لطفاً یک پلن خریداری کنید.', 'danger')
            return redirect(url_for('view_plans'))
        
        name = request.form.get('name')
        address = request.form.get('address')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        phone = request.form.get('phone')
        
        hq = Headquarters(
            candidate_id=candidate.id,
            name=name,
            address=address,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            phone=phone
        )
        
        db.session.add(hq)
        safe_commit(db, "Database commit failed")
        flash('ستاد جدید اضافه شد', 'success')
        return redirect(url_for('headquarters'))
    
    return render_template('candidate/headquarters.html', candidate=candidate, headquarters=hqs)


@app.route('/bot', methods=['GET', 'POST'])
@secure_route()
def bot_management():
    """مدیریت اطلاعات بات"""
    candidate = Candidate.query.get(session['candidate_id'])
    
    if request.method == 'POST':
        # دریافت اطلاعات از فرم
        candidate.full_name = request.form.get('full_name', candidate.full_name)
        candidate.last_name = request.form.get('last_name', candidate.last_name)
        candidate.bio = request.form.get('bio', candidate.bio)
        candidate.phone = request.form.get('phone', candidate.phone)
        candidate.email = request.form.get('email', candidate.email)
        candidate.province = request.form.get('province', candidate.province)
        candidate.city = request.form.get('city', candidate.city)
        candidate.district = request.form.get('district', candidate.district)
        candidate.education = request.form.get('education', candidate.education)
        
        safe_commit(db, "Database commit failed")
        flash('اطلاعات بات با موفقیت به‌روزرسانی شد', 'success')
        return redirect(url_for('bot_management'))
    
    # دریافت اطلاعات بات
    bot_info = None
    if candidate.bot_instance:
        bot_info = {
            'username': candidate.bot_instance.bot_username,
            'is_active': candidate.bot_instance.is_active,
            'bot_link': f"https://t.me/{candidate.bot_instance.bot_username}" if candidate.bot_instance.bot_username else None,
            'bot_name': candidate.bot_instance.bot_name,
            'bot_about': candidate.bot_instance.bot_about,
            'bot_description': candidate.bot_instance.bot_description,
            'bot_description_picture': candidate.bot_instance.bot_description_picture,
            'bot_pic': candidate.bot_instance.bot_pic,
            'bot_commands': candidate.bot_instance.bot_commands,
            'privacy_policy_url': candidate.bot_instance.privacy_policy_url
        }
    
    # دریافت رزومه، برنامه‌ها، و ستادها
    resume = Resume.query.filter_by(candidate_id=candidate.id).first()
    programs = Program.query.filter_by(candidate_id=candidate.id).all()
    headquarters = Headquarters.query.filter_by(candidate_id=candidate.id).all()
    
    return render_template('candidate/bot.html', 
                         candidate=candidate, 
                         bot_info=bot_info,
                         resume=resume,
                         programs=programs,
                         headquarters=headquarters)


@app.route('/bot/settings', methods=['POST'])
@login_required
@csrf_protected
@rate_limiter.limit("50 per minute")
def update_bot_settings():
    """به‌روزرسانی تنظیمات BotFather"""
    candidate = Candidate.query.get(session['candidate_id'])
    
    if not candidate.bot_instance:
        flash('بات شما هنوز فعال نشده است', 'error')
        return redirect(url_for('bot_management'))
    
    bot = candidate.bot_instance
    
    # دریافت اطلاعات از فرم
    bot.bot_name = sanitize_input(request.form.get('bot_name', ''))
    bot.bot_about = sanitize_input(request.form.get('bot_about', ''))
    bot.bot_description = sanitize_input(request.form.get('bot_description', ''))
    bot.bot_commands = sanitize_input(request.form.get('bot_commands', ''))
    bot.privacy_policy_url = sanitize_input(request.form.get('privacy_policy_url', ''))
    
    # آپلود تصویر توضیحات
    if 'bot_description_picture' in request.files:
        file = request.files['bot_description_picture']
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"bot_desc_{candidate.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            bot.bot_description_picture = filename
    
    # آپلود تصویر پروفایل
    if 'bot_pic' in request.files:
        file = request.files['bot_pic']
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"bot_pic_{candidate.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            bot.bot_pic = filename
    
    safe_commit(db, "Database commit failed")
    flash('تنظیمات BotFather با موفقیت ذخیره شد', 'success')
    return redirect(url_for('bot_management'))


@app.route('/messages')
@login_required
def messages():
    """پیام‌های دریافتی از مردم با فیلترهای هوشمند"""
    candidate = Candidate.query.get(session['candidate_id'])
    
    # دریافت فیلترها از query string
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', 'all')
    read_filter = request.args.get('read', 'all')
    
    # Query اصلی
    query = Message.query.filter_by(candidate_id=candidate.id)
    
    # اعمال فیلتر دسته‌بندی
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    # اعمال فیلتر اولویت
    if priority_filter != 'all':
        query = query.filter_by(category_priority=priority_filter)
    
    # اعمال فیلتر خوانده شده/نشده
    if read_filter == 'read':
        query = query.filter_by(is_read=True)
    elif read_filter == 'unread':
        query = query.filter_by(is_read=False)
    
    messages_list = query.order_by(Message.created_at.desc()).all()
    
    # آمار دسته‌بندی و احساسات
    stats = {
        'total': Message.query.filter_by(candidate_id=candidate.id).count(),
        'unread': Message.query.filter_by(candidate_id=candidate.id, is_read=False).count(),
        'complaint': Message.query.filter_by(candidate_id=candidate.id, category='complaint').count(),
        'question': Message.query.filter_by(candidate_id=candidate.id, category='question').count(),
        'suggestion': Message.query.filter_by(candidate_id=candidate.id, category='suggestion').count(),
        'support': Message.query.filter_by(candidate_id=candidate.id, category='support').count(),
        'criticism': Message.query.filter_by(candidate_id=candidate.id, category='criticism').count(),
        'high_priority': Message.query.filter_by(candidate_id=candidate.id, category_priority='high').count(),
        # Sentiment stats
        'positive': Message.query.filter_by(candidate_id=candidate.id, sentiment_label='positive').count(),
        'neutral': Message.query.filter_by(candidate_id=candidate.id, sentiment_label='neutral').count(),
        'negative': Message.query.filter_by(candidate_id=candidate.id, sentiment_label='negative').count(),
    }
    
    # محاسبه میانگین رضایت
    all_sentiments = Message.query.filter_by(candidate_id=candidate.id)\
        .filter(Message.sentiment_score != None).all()
    if all_sentiments:
        avg_sentiment = sum(msg.sentiment_score for msg in all_sentiments) / len(all_sentiments)
        stats['avg_sentiment'] = round(avg_sentiment, 2)
        stats['satisfaction_rate'] = round((avg_sentiment + 1) / 2 * 100, 1)  # تبدیل -1,1 به 0-100
    else:
        stats['avg_sentiment'] = 0
        stats['satisfaction_rate'] = 50
    
    # استفاده از template جدید با AI features
    return render_template('candidate/messages_ai.html', 
                         candidate=candidate, 
                         messages=messages_list,
                         stats=stats,
                         category_filter=category_filter,
                         priority_filter=priority_filter,
                         read_filter=read_filter)


@app.route('/message/<int:message_id>/read', methods=['POST'])
@login_required
@csrf_protected
@rate_limiter.limit("100 per minute")
def mark_read(message_id):
    """علامت‌گذاری پیام به‌عنوان خوانده‌شده"""
    message = Message.query.get_or_404(message_id)
    
    if message.candidate_id == session['candidate_id']:
        message.is_read = True
        safe_commit(db, "Database commit failed")
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 403


@app.route('/plans')
@login_required
def view_plans():
    """مشاهده و مقایسه پلن‌ها"""
    candidate = Candidate.query.get(session['candidate_id'])
    all_plans = Plan.query.filter_by(is_active=True).order_by(Plan.display_order).all()
    
    # پلن فعال فعلی کاندیدا
    active_plan = candidate.get_active_plan()
    
    # آخرین خرید
    latest_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate.id,
        is_active=True
    ).order_by(PlanPurchase.end_date.desc()).first()
    
    return render_template('candidate/plans.html', 
                         candidate=candidate,
                         plans=all_plans,
                         active_plan=active_plan,
                         latest_purchase=latest_purchase)


@app.route('/plans/request-consultation', methods=['POST'])
@login_required
@csrf_protected
@rate_limiter.limit("20 per hour")
def request_consultation():
    """درخواست مشاوره برای خرید پلن"""
    candidate = Candidate.query.get(session['candidate_id'])
    
    plan_id = request.form.get('plan_id')
    phone = request.form.get('phone', '')
    preferred_time = request.form.get('preferred_time', '')
    message = request.form.get('message', '')
    
    # بررسی درخواست تکراری
    existing = ConsultationRequest.query.filter_by(
        candidate_id=candidate.id,
        status='pending'
    ).first()
    
    if existing:
        flash('شما یک درخواست در انتظار پاسخ دارید', 'warning')
        return redirect(url_for('view_plans'))
    
    # ایجاد درخواست جدید
    consultation = ConsultationRequest(
        candidate_id=candidate.id,
        plan_id=plan_id if plan_id else None,
        phone=phone,
        preferred_time=preferred_time,
        message=message,
        status='pending'
    )
    
    db.session.add(consultation)
    safe_commit(db, "Database commit failed")
    
    flash('درخواست شما با موفقیت ثبت شد. به زودی با شما تماس خواهیم گرفت', 'success')
    return redirect(url_for('view_plans'))


@app.route('/plans/activate-trial', methods=['POST'])
@secure_route(rate_limit="5 per hour")
def activate_trial():
    """فعال‌سازی Trial 3 روزه توسط کاندیدا"""
    from datetime import timedelta
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # بررسی استفاده قبلی از Trial
    if candidate.has_used_trial:
        flash('شما قبلاً از دوره تست رایگان استفاده کرده‌اید', 'warning')
        return redirect(url_for('view_plans'))
    
    # پیدا کردن پلن PROFESSIONAL
    professional_plan = Plan.query.filter_by(code='PROFESSIONAL').first()
    if not professional_plan:
        # fallback به اولین پلن فعال
        professional_plan = Plan.query.filter_by(is_active=True).first()
    
    if not professional_plan:
        flash('متأسفانه در حال حاضر امکان فعال‌سازی Trial وجود ندارد', 'danger')
        return redirect(url_for('view_plans'))
    
    # ایجاد Trial Purchase
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
        notes='دوره تست 3 روزه رایگان'
    )
    
    # علامت‌گذاری کاندیدا
    candidate.has_used_trial = True
    
    db.session.add(trial_purchase)
    safe_commit(db, "Database commit failed")
    
    flash('🎉 تبریک! دوره تست 3 روزه رایگان شما فعال شد. از تمام امکانات پلن حرفه‌ای لذت ببرید!', 'success')
    return redirect(url_for('dashboard'))


# ==================== کانال‌ها و گروه‌ها ====================

@app.route('/channels')
@login_required
def manage_channels():
    """مدیریت کانال‌ها و گروه‌ها"""
    from database.models import BotChannel
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # دریافت پلن فعال و محدودیت تعداد کانال
    active_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate.id,
        is_active=True
    ).order_by(PlanPurchase.end_date.desc()).first()
    
    max_channels = 0
    plan_limit_reached = False
    active_plan = None
    
    if active_purchase:
        active_plan = active_purchase.plan
        # محدودیت تعداد کانال بر اساس پلن
        if active_plan.name == 'BASIC':
            max_channels = 1
        elif active_plan.name == 'PROFESSIONAL':
            max_channels = 3
        elif active_plan.name == 'GOLD':
            max_channels = 10
        else:
            max_channels = 1
    
    # دریافت کانال‌های موجود
    channels = BotChannel.query.filter_by(
        candidate_id=candidate.id
    ).order_by(BotChannel.connected_at.desc()).all()
    
    if len(channels) >= max_channels:
        plan_limit_reached = True
    
    return render_template('candidate/channels.html',
                         candidate=candidate,
                         channels=channels,
                         max_channels=max_channels,
                         plan_limit_reached=plan_limit_reached,
                         active_plan=active_plan)


@app.route('/channels/add', methods=['POST'])
@secure_route()
def add_channel():
    """افزودن کانال جدید"""
    from database.models import BotChannel, BotInstance
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # چک محدودیت پلن
    active_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate.id,
        is_active=True
    ).first()
    
    if not active_purchase:
        flash('برای افزودن کانال، ابتدا یک پلن فعال کنید', 'warning')
        return redirect(url_for('view_plans'))
    
    # محاسبه حد مجاز
    plan_name = active_purchase.plan.name
    if plan_name == 'BASIC':
        max_channels = 1
    elif plan_name == 'PROFESSIONAL':
        max_channels = 3
    elif plan_name == 'GOLD':
        max_channels = 10
    else:
        max_channels = 1
    
    current_count = BotChannel.query.filter_by(candidate_id=candidate.id).count()
    
    if current_count >= max_channels:
        flash(f'محدودیت پلن: حداکثر {max_channels} کانال مجاز است', 'warning')
        return redirect(url_for('manage_channels'))
    
    # دریافت اطلاعات فرم
    channel_id = request.form.get('channel_id')
    channel_title = request.form.get('channel_title')
    channel_username = request.form.get('channel_username')
    channel_type = request.form.get('channel_type', 'channel')
    
    # پیدا کردن بات کاندیدا
    bot_instance = BotInstance.query.filter_by(candidate_id=candidate.id).first()
    
    if not bot_instance:
        flash('ابتدا باید بات تلگرام خود را راه‌اندازی کنید', 'warning')
        return redirect(url_for('view_bot'))
    
    # ایجاد کانال جدید
    new_channel = BotChannel(
        bot_instance_id=bot_instance.id,
        candidate_id=candidate.id,
        channel_id=int(channel_id),
        channel_username=channel_username if channel_username else None,
        channel_title=channel_title,
        channel_type=channel_type,
        is_active=True
    )
    
    db.session.add(new_channel)
    safe_commit(db, "Database commit failed")
    
    flash(f'✅ کانال "{channel_title}" با موفقیت اضافه شد!', 'success')
    return redirect(url_for('manage_channels'))


@app.route('/channels/<int:channel_id>/delete', methods=['POST'])
@secure_route()
def delete_channel(channel_id):
    """حذف کانال"""
    from database.models import BotChannel
    
    candidate = Candidate.query.get(session['candidate_id'])
    channel = BotChannel.query.filter_by(
        id=channel_id,
        candidate_id=candidate.id
    ).first_or_404()
    
    title = channel.channel_title
    db.session.delete(channel)
    safe_commit(db, "Database commit failed")
    
    flash(f'کانال "{title}" حذف شد', 'success')
    return redirect(url_for('manage_channels'))


@app.route('/channels/<int:channel_id>/schedule', methods=['GET', 'POST'])
@secure_route()
def schedule_post(channel_id):
    """صفحه زمان‌بندی پست جدید"""
    from database.models import BotChannel, ScheduledPost
    
    candidate = Candidate.query.get(session['candidate_id'])
    channel = BotChannel.query.filter_by(
        id=channel_id,
        candidate_id=candidate.id
    ).first_or_404()
    
    if request.method == 'POST':
        content = request.form.get('content')
        scheduled_time_str = request.form.get('scheduled_time')
        media_type = request.form.get('media_type', 'none')
        
        # تبدیل زمان
        from datetime import datetime
        scheduled_time = datetime.fromisoformat(scheduled_time_str)
        
        new_post = ScheduledPost(
            channel_id=channel.id,
            candidate_id=candidate.id,
            content=content,
            media_type=media_type if media_type != 'none' else None,
            scheduled_time=scheduled_time,
            status='pending'
        )
        
        db.session.add(new_post)
        safe_commit(db, "Database commit failed")
        
        flash('✅ پست با موفقیت زمان‌بندی شد!', 'success')
        return redirect(url_for('manage_channels'))
    
    return render_template('candidate/schedule_post.html',
                         candidate=candidate,
                         channel=channel)


@app.route('/posts/scheduled')
@login_required
def view_scheduled_posts():
    """مشاهده تمام پست‌های زمان‌بندی شده"""
    from database.models import ScheduledPost
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # دریافت پست‌های زمان‌بندی شده
    posts = ScheduledPost.query.filter_by(
        candidate_id=candidate.id
    ).order_by(ScheduledPost.scheduled_time.desc()).all()
    
    return render_template('candidate/scheduled_posts.html',
                         candidate=candidate,
                         posts=posts)


@app.route('/posts/<int:post_id>/cancel', methods=['POST'])
@secure_route()
def cancel_post(post_id):
    """لغو پست زمان‌بندی شده"""
    from database.models import ScheduledPost
    
    candidate = Candidate.query.get(session['candidate_id'])
    post = ScheduledPost.query.filter_by(
        id=post_id,
        candidate_id=candidate.id
    ).first_or_404()
    
    if post.status == 'pending':
        post.status = 'cancelled'
        safe_commit(db, "Database commit failed")
        flash('پست لغو شد', 'success')
    else:
        flash('فقط پست‌های در انتظار قابل لغو هستند', 'warning')
    
    return redirect(url_for('view_scheduled_posts'))


@app.route('/posts/<int:post_id>/delete', methods=['POST'])
@secure_route()
def delete_post(post_id):
    """حذف پست"""
    from database.models import ScheduledPost
    
    candidate = Candidate.query.get(session['candidate_id'])
    post = ScheduledPost.query.filter_by(
        id=post_id,
        candidate_id=candidate.id
    ).first_or_404()
    
    db.session.delete(post)
    safe_commit(db, "Database commit failed")
    
    flash('پست حذف شد', 'success')
    return redirect(url_for('view_scheduled_posts'))


@app.route('/channels/<int:channel_id>/stats')
@login_required
def channel_stats(channel_id):
    """آمار و تحلیل کانال"""
    from database.models import BotChannel, ScheduledPost, ChannelStats
    from datetime import datetime, timedelta
    
    candidate = Candidate.query.get(session['candidate_id'])
    channel = BotChannel.query.filter_by(
        id=channel_id,
        candidate_id=candidate.id
    ).first_or_404()
    
    # آمار کلی
    total_posts = ScheduledPost.query.filter_by(
        channel_id=channel.id,
        status='sent'
    ).count()
    
    pending_posts = ScheduledPost.query.filter_by(
        channel_id=channel.id,
        status='pending'
    ).count()
    
    failed_posts = ScheduledPost.query.filter_by(
        channel_id=channel.id,
        status='failed'
    ).count()
    
    # آمار 7 روز گذشته
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_stats = ChannelStats.query.filter(
        ChannelStats.channel_id == channel.id,
        ChannelStats.date >= seven_days_ago.date()
    ).order_by(ChannelStats.date).all()
    
    # آخرین پست‌ها
    recent_posts = ScheduledPost.query.filter_by(
        channel_id=channel.id
    ).order_by(ScheduledPost.scheduled_time.desc()).limit(10).all()
    
    return render_template('candidate/channel_stats.html',
                         candidate=candidate,
                         channel=channel,
                         total_posts=total_posts,
                         pending_posts=pending_posts,
                         failed_posts=failed_posts,
                         recent_stats=recent_stats,
                         recent_posts=recent_posts)


@app.route('/broadcast')
@login_required
def broadcast():
    """صفحه ارسال پیام انبوه"""
    from database.models import BroadcastMessage, BotUser
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # بررسی داشتن پلن ارسال انبوه
    has_broadcast = any(plan.code == 'MASS_BROADCAST' for plan in candidate.plans)
    
    if not has_broadcast:
        flash('برای استفاده از این امکان باید پلن "ارسال پیام انبوه" را فعال کنید', 'warning')
        return redirect(url_for('view_plans'))
    
    # دریافت اطلاعات بات
    bot_instance = BotInstance.query.filter_by(candidate_id=candidate.id).first()
    
    if not bot_instance:
        flash('ابتدا باید بات خود را راه‌اندازی کنید', 'warning')
        return redirect(url_for('bot_management'))
    
    # تعداد کاربران
    total_users = BotUser.query.filter_by(bot_instance_id=bot_instance.id).count()
    
    # پیام‌های قبلی
    broadcasts = BroadcastMessage.query.filter_by(candidate_id=candidate.id).order_by(BroadcastMessage.created_at.desc()).limit(10).all()
    
    return render_template('candidate/broadcast.html',
                         candidate=candidate,
                         total_users=total_users,
                         broadcasts=broadcasts)


@app.route('/broadcast/send', methods=['POST'])
@secure_route(rate_limit="10 per hour")
def send_broadcast():
    """ارسال پیام انبوه"""
    from database.models import BroadcastMessage
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # بررسی پلن
    has_broadcast = any(plan.code == 'MASS_BROADCAST' for plan in candidate.plans)
    
    if not has_broadcast:
        return jsonify({'success': False, 'message': 'پلن ارسال انبوه فعال نیست'}), 403
    
    # دریافت اطلاعات بات
    bot_instance = BotInstance.query.filter_by(candidate_id=candidate.id).first()
    
    if not bot_instance:
        return jsonify({'success': False, 'message': 'بات راه‌اندازی نشده است'}), 400
    
    # دریافت داده‌های فرم
    message_text = request.form.get('message_text')
    target_filter = request.form.get('target_filter', 'all')
    scheduled_time_str = request.form.get('scheduled_time')
    
    if not message_text:
        return jsonify({'success': False, 'message': 'متن پیام الزامی است'}), 400
    
    # تبدیل زمان
    scheduled_time = None
    if scheduled_time_str:
        try:
            scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
        except Exception as e:
            pass
    
    # ایجاد پیام انبوه
    broadcast = BroadcastMessage(
        candidate_id=candidate.id,
        bot_instance_id=bot_instance.id,
        message_text=message_text,
        target_filter=target_filter,
        scheduled_time=scheduled_time,
        status='pending'
    )
    
    db.session.add(broadcast)
    safe_commit(db, "Database commit failed")
    
    flash('پیام انبوه با موفقیت ثبت شد و به زودی ارسال خواهد شد', 'success')
    return jsonify({'success': True, 'broadcast_id': broadcast.id})


@app.route('/broadcast/<int:broadcast_id>')
@login_required
def broadcast_detail(broadcast_id):
    """جزئیات و آمار یک پیام انبوه"""
    from database.models import BroadcastMessage, BroadcastLog
    
    candidate = Candidate.query.get(session['candidate_id'])
    broadcast = BroadcastMessage.query.filter_by(id=broadcast_id, candidate_id=candidate.id).first()
    
    if not broadcast:
        flash('پیام انبوه یافت نشد', 'error')
        return redirect(url_for('broadcast'))
    
    # لاگ‌ها
    logs = BroadcastLog.query.filter_by(broadcast_id=broadcast_id).limit(100).all()
    
    return render_template('candidate/broadcast_detail.html',
                         candidate=candidate,
                         broadcast=broadcast,
                         logs=logs)


@app.route('/broadcast/<int:broadcast_id>/cancel', methods=['POST'])
@secure_route()
def cancel_broadcast(broadcast_id):
    """لغو یک پیام انبوه"""
    from database.models import BroadcastMessage
    
    candidate = Candidate.query.get(session['candidate_id'])
    broadcast = BroadcastMessage.query.filter_by(id=broadcast_id, candidate_id=candidate.id).first()
    
    if not broadcast:
        return jsonify({'success': False, 'message': 'پیام یافت نشد'}), 404
    
    if broadcast.status != 'pending':
        return jsonify({'success': False, 'message': 'فقط پیام‌های در انتظار قابل لغو هستند'}), 400
    
    broadcast.status = 'cancelled'
    safe_commit(db, "Database commit failed")
    
    return jsonify({'success': True, 'message': 'پیام لغو شد'})


@app.route('/analytics')
@login_required
def analytics():
    """صفحه آمار و تحلیل"""
    from database.models import Analytics, BotUser
    from sqlalchemy import func
    from datetime import timedelta
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # بررسی داشتن پلن آمار
    has_analytics = any(plan.code == 'ANALYTICS' for plan in candidate.plans)
    
    if not has_analytics:
        flash('برای استفاده از این امکان باید پلن "آمار و تحلیل" را فعال کنید', 'warning')
        return redirect(url_for('view_plans'))
    
    # آمار 30 روز اخیر
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    analytics_data = Analytics.query.filter(
        Analytics.candidate_id == candidate.id,
        Analytics.date >= thirty_days_ago.date()
    ).order_by(Analytics.date.asc()).all()
    
    # محاسبه کل آمار
    total_bot_users = Analytics.query.filter_by(candidate_id=candidate.id).with_entities(
        func.sum(Analytics.new_users)
    ).scalar() or 0
    
    total_interactions = Analytics.query.filter_by(candidate_id=candidate.id).with_entities(
        func.sum(Analytics.total_interactions)
    ).scalar() or 0
    
    total_messages = Analytics.query.filter_by(candidate_id=candidate.id).with_entities(
        func.sum(Analytics.total_messages)
    ).scalar() or 0
    
    # محبوب‌ترین بخش‌ها
    total_views = Analytics.query.filter_by(candidate_id=candidate.id).with_entities(
        func.sum(Analytics.resume_views).label('resume'),
        func.sum(Analytics.programs_views).label('programs'),
        func.sum(Analytics.headquarters_views).label('headquarters')
    ).first()
    
    popular_sections = {
        'resume': total_views.resume or 0 if total_views else 0,
        'programs': total_views.programs or 0 if total_views else 0,
        'headquarters': total_views.headquarters or 0 if total_views else 0
    }
    
    # آمار پیام‌ها
    total_messages_count = Message.query.filter_by(candidate_id=candidate.id).count()
    unread_messages_count = Message.query.filter_by(candidate_id=candidate.id, is_read=False).count()
    
    # آمار کاربران بات
    bot_instance = BotInstance.query.filter_by(candidate_id=candidate.id).first()
    active_bot_users = 0
    if bot_instance:
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_bot_users = BotUser.query.filter(
            BotUser.bot_instance_id == bot_instance.id,
            BotUser.last_interaction >= week_ago
        ).count()
    
    return render_template('candidate/analytics.html',
                         candidate=candidate,
                         analytics_data=analytics_data,
                         total_bot_users=total_bot_users,
                         total_interactions=total_interactions,
                         total_messages=total_messages,
                         popular_sections=popular_sections,
                         messages_count=total_messages_count,
                         unread_messages=unread_messages_count,
                         active_bot_users=active_bot_users)


@app.route('/polls')
@login_required
def polls():
    """صفحه نظرسنجی‌ها"""
    from database.models import Poll
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # بررسی پلن
    has_polls = any(plan.code == 'SURVEYS' for plan in candidate.plans)
    
    if not has_polls:
        flash('برای استفاده از این امکان باید پلن "نظرسنجی" را فعال کنید', 'warning')
        return redirect(url_for('view_plans'))
    
    # لیست نظرسنجی‌ها
    polls_list = Poll.query.filter_by(candidate_id=candidate.id).order_by(Poll.created_at.desc()).all()
    
    return render_template('candidate/polls.html',
                         candidate=candidate,
                         polls=polls_list)


@app.route('/polls/create', methods=['GET', 'POST'])
@secure_route()  
def create_poll():
    """ایجاد نظرسنجی جدید"""
    from database.models import Poll, PollOption
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    if request.method == 'POST':
        question = request.form.get('question')
        options = request.form.getlist('options[]')
        is_anonymous = request.form.get('is_anonymous') == 'on'
        end_date_str = request.form.get('end_date')
        
        # ایجاد نظرسنجی
        bot_instance = BotInstance.query.filter_by(candidate_id=candidate.id).first()
        
        poll = Poll(
            candidate_id=candidate.id,
            bot_instance_id=bot_instance.id if bot_instance else None,
            question=question,
            is_anonymous=is_anonymous,
            start_date=datetime.utcnow()
        )
        
        if end_date_str:
            try:
                poll.end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
            except Exception as e:
                pass
        
        db.session.add(poll)
        db.session.flush()
        
        # افزودن گزینه‌ها
        for i, option_text in enumerate(options):
            if option_text.strip():
                option = PollOption(
                    poll_id=poll.id,
                    option_text=option_text.strip(),
                    option_order=i
                )
                db.session.add(option)
        
        safe_commit(db, "Database commit failed")
        
        flash('نظرسنجی با موفقیت ایجاد شد', 'success')
        return redirect(url_for('polls'))
    
    return render_template('candidate/create_poll.html', candidate=candidate)


@app.route('/polls/<int:poll_id>')
@login_required
def poll_results(poll_id):
    """نمایش نتایج نظرسنجی"""
    from database.models import Poll
    
    candidate = Candidate.query.get(session['candidate_id'])
    poll = Poll.query.filter_by(id=poll_id, candidate_id=candidate.id).first()
    
    if not poll:
        flash('نظرسنجی یافت نشد', 'error')
        return redirect(url_for('polls'))
    
    return render_template('candidate/poll_results.html',
                         candidate=candidate,
                         poll=poll)


@app.route('/auto-replies', methods=['GET', 'POST'])
@secure_route()
def auto_replies():
    """مدیریت پاسخ‌های خودکار"""
    from database.models import AutoReply
    
    candidate = Candidate.query.get(session['candidate_id'])
    
    # بررسی پلن
    has_auto_reply = any(plan.code == 'AI_RESPONDER' for plan in candidate.plans)
    
    if not has_auto_reply:
        flash('برای استفاده از این امکان باید پلن "پاسخ‌گوی هوشمند" را فعال کنید', 'warning')
        return redirect(url_for('view_plans'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            keyword = request.form.get('keyword')
            reply_text = request.form.get('reply_text')
            case_sensitive = request.form.get('case_sensitive') == 'on'
            exact_match = request.form.get('exact_match') == 'on'
            
            auto_reply = AutoReply(
                candidate_id=candidate.id,
                keyword=keyword,
                reply_text=reply_text,
                case_sensitive=case_sensitive,
                exact_match=exact_match
            )
            
            db.session.add(auto_reply)
            safe_commit(db, "Database commit failed")
            
            flash('پاسخ خودکار با موفقیت افزوده شد', 'success')
        
        elif action == 'delete':
            reply_id = request.form.get('reply_id')
            auto_reply = AutoReply.query.filter_by(id=reply_id, candidate_id=candidate.id).first()
            if auto_reply:
                db.session.delete(auto_reply)
                safe_commit(db, "Database commit failed")
                flash('پاسخ خودکار حذف شد', 'success')
        
        return redirect(url_for('auto_replies'))
    
    # لیست پاسخ‌های خودکار
    replies = AutoReply.query.filter_by(candidate_id=candidate.id).order_by(AutoReply.created_at.desc()).all()
    
    return render_template('candidate/auto_replies.html',
                         candidate=candidate,
                         replies=replies)


@app.route('/plans/purchase/<int:plan_id>', methods=['GET', 'POST'])
@secure_route()
def purchase_plan(plan_id):
    """خرید پلن"""
    candidate = Candidate.query.get(session['candidate_id'])
    plan = Plan.query.get_or_404(plan_id)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        receipt_image = request.files.get('receipt_image')
        
        if not receipt_image:
            flash('لطفا تصویر فیش واریزی را آپلود کنید', 'danger')
            return redirect(request.url)
        
        # ذخیره فایل
        filename = secure_filename(f"receipt_{candidate.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{receipt_image.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'receipts', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        receipt_image.save(filepath)
        
        # ساخت شماره تیکت
        last_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
        ticket_number = f"TK-{(last_ticket.id + 1001) if last_ticket else 1001}"
        
        # ساخت تیکت
        ticket = Ticket(
            ticket_number=ticket_number,
            candidate_id=candidate.id,
            ticket_type='purchase',
            subject=f'درخواست خرید پلن {plan.name}',
            message=f'درخواست فعال‌سازی پلن {plan.name} با روش پرداخت {payment_method}',
            plan_id=plan.id,
            payment_method=payment_method,
            payment_amount=plan.price,
            receipt_image=filepath,
            status='pending'
        )
        
        db.session.add(ticket)
        db.session.flush()  # برای گرفتن ID
        
        # ساخت رکورد پرداخت
        payment = Payment(
            ticket_id=ticket.id,
            candidate_id=candidate.id,
            plan_id=plan.id,
            amount=plan.price,
            payment_method=payment_method,
            receipt_image=filepath,
            status='pending'
        )
        
        db.session.add(payment)
        safe_commit(db, "Database commit failed")
        
        flash(f'درخواست شما با شماره {ticket_number} ثبت شد. پس از بررسی توسط پشتیبانی، پلن شما فعال خواهد شد.', 'success')
        return redirect(url_for('my_tickets'))
    
    return render_template('candidate/purchase_plan.html',
                         candidate=candidate,
                         plan=plan)


@app.route('/my-tickets')
@login_required
def my_tickets():
    """تیکت‌های من"""
    candidate = Candidate.query.get(session['candidate_id'])
    tickets = Ticket.query.filter_by(candidate_id=candidate.id).order_by(Ticket.created_at.desc()).all()
    
    return render_template('candidate/my_tickets.html',
                         candidate=candidate,
                         tickets=tickets)


@app.route('/logout')
def logout():
    """خروج"""
    session.clear()
    flash('با موفقیت خارج شدید', 'info')
    return redirect(url_for('login'))


# ============================================================
# مشارکت شهروندی (Citizen Participation)
# ============================================================

def generate_tracking_code(contribution_type):
    """تولید کد پیگیری یکتا"""
    prefix = "IDEA" if contribution_type == "idea" else "RPT"
    
    # پیدا کردن آخرین کد
    last = CitizenContribution.query.filter(
        CitizenContribution.tracking_code.like(f'{prefix}-%')
    ).order_by(CitizenContribution.id.desc()).first()
    
    if last:
        last_num = int(last.tracking_code.split('-')[1])
        new_num = last_num + 1
    else:
        new_num = 1001 if prefix == "IDEA" else 2001
    
    return f"{prefix}-{new_num:04d}"


def award_points(telegram_id, action, contribution_id=None):
    """اعطای امتیاز به کاربر"""
    POINTS = {
        'submit': 10,
        'vote': 1,
        'comment': 2,
        'approved': 50,
        'in_progress': 75,
        'completed': 100
    }
    
    points = POINTS.get(action, 0)
    if points == 0:
        return
    
    # پیدا یا ساخت پروفایل
    profile = CitizenProfile.query.filter_by(telegram_id=telegram_id).first()
    if not profile:
        profile = CitizenProfile(telegram_id=telegram_id)
        db.session.add(profile)
    
    # افزودن امتیاز
    profile.total_points += points
    
    # محاسبه سطح
    old_level = profile.level
    profile.level = calculate_level(profile.total_points)
    
    # به‌روزرسانی آمار
    if action == 'submit':
        profile.contributions_count += 1
    elif action == 'vote':
        profile.votes_given += 1
    elif action == 'comment':
        profile.comments_count += 1
    
    profile.last_active = datetime.utcnow()
    
    try:
        safe_commit(db, "Database commit failed")
        
        # بررسی نشان‌ها در صورت ارتقا سطح
        if profile.level > old_level:
            check_and_award_badges(profile)
        
        return True
    except Exception as e:
        db.session.rollback()
        return False


def calculate_level(points):
    """محاسبه سطح بر اساس امتیاز"""
    if points < 50: return 1
    elif points < 150: return 2
    elif points < 300: return 3
    elif points < 500: return 4
    elif points < 1000: return 5
    elif points < 2000: return 6
    elif points < 5000: return 7
    elif points < 10000: return 8
    else: return 9


def check_and_award_badges(profile):
    """بررسی و اعطای نشان‌ها"""
    if not profile.badges:
        profile.badges = []
    
    badges = profile.badges if isinstance(profile.badges, list) else []
    
    # نشان شروع
    if 'beginner' not in badges:
        badges.append('beginner')
    
    # نشان مشارکت
    if profile.contributions_count >= 5 and 'contributor' not in badges:
        badges.append('contributor')
    
    # نشان فعال
    if profile.votes_given >= 20 and 'active_voter' not in badges:
        badges.append('active_voter')
    
    # نشان گفتگوگر
    if profile.comments_count >= 10 and 'discusser' not in badges:
        badges.append('discusser')
    
    # نشان ستاره
    if profile.total_points >= 500 and 'star' not in badges:
        badges.append('star')
    
    # نشان قهرمان
    if profile.total_points >= 1000 and 'champion' not in badges:
        badges.append('champion')
    
    profile.badges = badges
    safe_commit(db, "Database commit failed")


def send_telegram_notification(bot_token, user_telegram_id, message_text):
    """ارسال اعلان تلگرام به کاربر"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': user_telegram_id,
            'text': message_text,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"خطا در ارسال نوتیفیکیشن: {e}")
        return False


@app.route('/contributions')
@login_required
def contributions():
    """لیست مشارکت‌های شهروندی"""
    candidate_id = session['candidate_id']
    
    # فیلترها
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'newest')
    
    # کوئری اولیه
    query = CitizenContribution.query.filter_by(candidate_id=candidate_id)
    
    # اعمال فیلتر وضعیت
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # اعمال فیلتر دسته‌بندی
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    # مرتب‌سازی
    if sort_by == 'newest':
        query = query.order_by(CitizenContribution.created_at.desc())
    elif sort_by == 'popular':
        query = query.order_by(CitizenContribution.votes_count.desc())
    elif sort_by == 'most_commented':
        query = query.order_by(CitizenContribution.comments_count.desc())
    
    contributions = query.all()
    
    # آمار
    stats = {
        'total': CitizenContribution.query.filter_by(candidate_id=candidate_id).count(),
        'pending': CitizenContribution.query.filter_by(candidate_id=candidate_id, status='pending').count(),
        'under_review': CitizenContribution.query.filter_by(candidate_id=candidate_id, status='under_review').count(),
        'approved': CitizenContribution.query.filter_by(candidate_id=candidate_id, status='approved').count(),
        'in_progress': CitizenContribution.query.filter_by(candidate_id=candidate_id, status='in_progress').count(),
        'completed': CitizenContribution.query.filter_by(candidate_id=candidate_id, status='completed').count(),
        'rejected': CitizenContribution.query.filter_by(candidate_id=candidate_id, status='rejected').count()
    }
    
    # دسته‌بندی‌ها
    categories = [
        ('education', '📚 آموزش'),
        ('health', '🏥 بهداشت'),
        ('traffic', '🚗 ترافیک'),
        ('security', '🛡️ امنیت'),
        ('environment', '🌳 محیط زیست'),
        ('cultural', '🎭 فرهنگی'),
        ('infrastructure', '🏗️ زیرساخت'),
        ('economic', '💰 اقتصاد'),
        ('welfare', '🤝 رفاه'),
        ('other', '📋 سایر')
    ]
    
    return render_template('candidate/contributions.html',
                         contributions=contributions,
                         stats=stats,
                         categories=categories,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         sort_by=sort_by)


@app.route('/contributions/<int:contribution_id>')
@login_required
def contribution_detail(contribution_id):
    """جزئیات مشارکت"""
    candidate_id = session['candidate_id']
    
    contribution = CitizenContribution.query.filter_by(
        id=contribution_id,
        candidate_id=candidate_id
    ).first_or_404()
    
    # افزایش تعداد بازدید
    contribution.views_count += 1
    safe_commit(db, "Database commit failed")
    
    # دریافت نظرات (فقط والد - بدون ریپلای‌ها)
    comments = ContributionComment.query.filter_by(
        contribution_id=contribution_id,
        parent_comment_id=None
    ).order_by(ContributionComment.created_at.desc()).all()
    
    return render_template('candidate/contribution_detail.html',
                         contribution=contribution,
                         comments=comments)


@app.route('/contributions/<int:contribution_id>/approve', methods=['POST'])
@secure_route()
def approve_contribution(contribution_id):
    """تایید مشارکت"""
    candidate_id = session['candidate_id']
    
    contribution = CitizenContribution.query.filter_by(
        id=contribution_id,
        candidate_id=candidate_id
    ).first_or_404()
    
    contribution.status = 'approved'
    contribution.reviewed_at = datetime.utcnow()
    
    try:
        safe_commit(db, "Database commit failed")
        
        # اعطای امتیاز به کاربر
        award_points(contribution.user_telegram_id, 'approved', contribution_id)
        
        # ارسال نوتیفیکیشن
        bot_instance = BotInstance.query.filter_by(candidate_id=candidate_id).first()
        if bot_instance and bot_instance.token:
            message = f"""
✅ *مشارکت شما تایید شد!*

📌 کد: `{contribution.tracking_code}`
📝 عنوان: *{contribution.title}*

🎉 امتیاز کسب شده: *50 امتیاز*

برای مشاهده جزئیات: /track_{contribution.tracking_code}
"""
            send_telegram_notification(bot_instance.token, contribution.user_telegram_id, message)
        
        flash('مشارکت با موفقیت تایید شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash('خطا در تایید مشارکت', 'danger')
    
    return redirect(url_for('contribution_detail', contribution_id=contribution_id))


@app.route('/contributions/<int:contribution_id>/reject', methods=['POST'])
@secure_route()
def reject_contribution(contribution_id):
    """رد مشارکت"""
    candidate_id = session['candidate_id']
    
    contribution = CitizenContribution.query.filter_by(
        id=contribution_id,
        candidate_id=candidate_id
    ).first_or_404()
    
    reject_reason = request.form.get('reason', '')
    
    contribution.status = 'rejected'
    contribution.reviewed_at = datetime.utcnow()
    contribution.admin_response = reject_reason
    contribution.response_date = datetime.utcnow()
    
    try:
        safe_commit(db, "Database commit failed")
        
        # ارسال نوتیفیکیشن
        bot_instance = BotInstance.query.filter_by(candidate_id=candidate_id).first()
        if bot_instance and bot_instance.token:
            reason_text = f"\n\n📋 *دلیل:*\n{reject_reason}" if reject_reason else ""
            message = f"""
❌ *مشارکت شما رد شد*

📌 کد: `{contribution.tracking_code}`
📝 عنوان: *{contribution.title}*
{reason_text}

برای اطلاعات بیشتر: /track_{contribution.tracking_code}
"""
            send_telegram_notification(bot_instance.token, contribution.user_telegram_id, message)
        
        flash('مشارکت رد شد', 'info')
    except Exception as e:
        db.session.rollback()
        flash('خطا در رد مشارکت', 'danger')
    
    return redirect(url_for('contribution_detail', contribution_id=contribution_id))


@app.route('/contributions/<int:contribution_id>/update-status', methods=['POST'])
@secure_route()
def update_contribution_status(contribution_id):
    """تغییر وضعیت مشارکت"""
    candidate_id = session['candidate_id']
    
    contribution = CitizenContribution.query.filter_by(
        id=contribution_id,
        candidate_id=candidate_id
    ).first_or_404()
    
    new_status = request.form.get('status')
    old_status = contribution.status
    
    if new_status in ['pending', 'under_review', 'approved', 'in_progress', 'completed', 'rejected']:
        contribution.status = new_status
        
        # به‌روزرسانی تاریخ‌ها
        if new_status in ['approved', 'rejected']:
            contribution.reviewed_at = datetime.utcnow()
        
        if new_status == 'completed':
            contribution.completed_at = datetime.utcnow()
        
        try:
            safe_commit(db, "Database commit failed")
            
            # اعطای امتیاز در صورت پیشرفت
            if new_status == 'in_progress' and old_status != 'in_progress':
                award_points(contribution.user_telegram_id, 'in_progress', contribution_id)
            elif new_status == 'completed' and old_status != 'completed':
                award_points(contribution.user_telegram_id, 'completed', contribution_id)
            
            # ارسال نوتیفیکیشن
            bot_instance = BotInstance.query.filter_by(candidate_id=candidate_id).first()
            if bot_instance and bot_instance.token:
                status_messages = {
                    'under_review': ('🔍 مشارکت شما در حال بررسی است', ''),
                    'approved': ('✅ مشارکت شما تایید شد!', '\n\n🎉 امتیاز: *50 امتیاز*'),
                    'in_progress': ('🔄 اجرای مشارکت شما آغاز شد!', '\n\n🎉 امتیاز: *75 امتیاز*'),
                    'completed': ('✔️ مشارکت شما تکمیل شد!', '\n\n🎉 امتیاز: *100 امتیاز*'),
                    'rejected': ('❌ متاسفانه مشارکت شما رد شد', '')
                }
                
                if new_status in status_messages and new_status != old_status:
                    status_text, bonus_text = status_messages[new_status]
                    message = f"""
{status_text}

📌 کد: `{contribution.tracking_code}`
📝 عنوان: *{contribution.title}*
{bonus_text}

برای جزئیات بیشتر: /track_{contribution.tracking_code}
"""
                    send_telegram_notification(bot_instance.token, contribution.user_telegram_id, message)
            
            flash('وضعیت مشارکت به‌روزرسانی شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash('خطا در به‌روزرسانی وضعیت', 'danger')
    else:
        flash('وضعیت نامعتبر است', 'danger')
    
    return redirect(url_for('contribution_detail', contribution_id=contribution_id))


@app.route('/contributions/<int:contribution_id>/respond', methods=['POST'])
@secure_route()
def respond_to_contribution(contribution_id):
    """پاسخ به مشارکت"""
    candidate_id = session['candidate_id']
    
    contribution = CitizenContribution.query.filter_by(
        id=contribution_id,
        candidate_id=candidate_id
    ).first_or_404()
    
    response_text = request.form.get('response', '').strip()
    
    if response_text:
        contribution.admin_response = response_text
        contribution.response_date = datetime.utcnow()
        
        try:
            safe_commit(db, "Database commit failed")
            
            # ارسال نوتیفیکیشن
            bot_instance = BotInstance.query.filter_by(candidate_id=candidate_id).first()
            if bot_instance and bot_instance.token:
                message = f"""
💬 *پاسخ جدید به مشارکت شما*

📌 کد: `{contribution.tracking_code}`
📝 عنوان: *{contribution.title}*

💬 *پاسخ نامزد:*
{response_text}

برای جزئیات: /track_{contribution.tracking_code}
"""
                send_telegram_notification(bot_instance.token, contribution.user_telegram_id, message)
            
            flash('پاسخ شما ثبت شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash('خطا در ثبت پاسخ', 'danger')
    else:
        flash('لطفا متن پاسخ را وارد کنید', 'warning')
    
    return redirect(url_for('contribution_detail', contribution_id=contribution_id))


@app.route('/contributions/<int:contribution_id>/priority', methods=['POST'])
@secure_route()
def set_contribution_priority(contribution_id):
    """تعیین اولویت مشارکت"""
    candidate_id = session['candidate_id']
    
    contribution = CitizenContribution.query.filter_by(
        id=contribution_id,
        candidate_id=candidate_id
    ).first_or_404()
    
    priority = request.form.get('priority')
    
    if priority in ['low', 'medium', 'high', 'urgent']:
        contribution.priority = priority
        
        try:
            safe_commit(db, "Database commit failed")
            flash('اولویت مشارکت به‌روزرسانی شد', 'success')
        except Exception as e:
            db.session.rollback()
            flash('خطا در تعیین اولویت', 'danger')
    else:
        flash('اولویت نامعتبر است', 'danger')
    
    return redirect(url_for('contribution_detail', contribution_id=contribution_id))


@app.route('/leaderboard')
@login_required
def leaderboard():
    """جدول امتیازات شهروندان"""
    candidate_id = session['candidate_id']
    
    # لیدربورد بر اساس امتیاز
    top_citizens = CitizenProfile.query.order_by(
        CitizenProfile.total_points.desc()
    ).limit(50).all()
    
    return render_template('candidate/leaderboard.html',
                         top_citizens=top_citizens)


# ═══════════════════════════════════════════════════════════════
# بخش Benchmark و مقایسه رقابتی
# ═══════════════════════════════════════════════════════════════

@app.route('/benchmark')
@login_required
def benchmark():
    """داشبورد مقایسه رقابتی"""
    from candidate_panel.benchmark_utils import (
        get_candidate_benchmark_comparison,
        calculate_candidate_ranking
    )
    
    candidate_id = session['candidate_id']
    candidate = Candidate.query.get(candidate_id)
    
    # محاسبه رتبه جدید
    ranking = calculate_candidate_ranking(candidate_id)
    
    # دریافت مقایسه
    comparison = get_candidate_benchmark_comparison(candidate_id)
    
    # پلن فعلی
    active_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate_id,
        is_active=True
    ).first()
    
    current_plan = active_purchase.plan if active_purchase else None
    
    # سایر پلن‌ها (برای پیشنهاد ارتقا)
    all_plans = Plan.query.filter_by(is_active=True).order_by(Plan.price).all()
    
    # محاسبه پتانسیل رشد
    if comparison and comparison['benchmark']['avg_messages'] > 0:
        potential_growth = comparison['benchmark']['top_10_messages'] - comparison['my_stats']['messages']
    else:
        potential_growth = 0
    
    return render_template('candidate/benchmark.html',
                         candidate=candidate,
                         comparison=comparison,
                         current_plan=current_plan,
                         all_plans=all_plans,
                         ranking=ranking,
                         potential_growth=potential_growth)


@app.route('/benchmark/refresh')
@login_required
def benchmark_refresh():
    """به‌روزرسانی دستی benchmark"""
    from candidate_panel.benchmark_utils import (
        calculate_marketplace_benchmarks,
        calculate_all_rankings
    )
    
    try:
        # محاسبه benchmark بازار
        calculate_marketplace_benchmarks()
        
        # محاسبه رتبه‌بندی
        calculate_all_rankings()
        
        flash('آمار به‌روزرسانی شد', 'success')
    except Exception as e:
        flash(f'خطا در به‌روزرسانی: {str(e)}', 'danger')
    
    return redirect(url_for('benchmark'))


# ========== Referral Program Routes ==========

@app.route('/referral')
@login_required
def referral_dashboard():
    """داشبورد برنامه معرفی دوستان"""
    from candidate_panel.referral_utils import (
        get_referral_stats,
        create_referral_program
    )
    
    candidate_id = session.get('candidate_id')
    
    # اگر برنامه معرفی نداره، بسازیم
    stats = get_referral_stats(candidate_id)
    if not stats['has_program']:
        create_referral_program(candidate_id)
        stats = get_referral_stats(candidate_id)
    
    return render_template(
        'candidate/referral.html',
        stats=stats
    )


@app.route('/referral/leaderboard')
@login_required
def referral_leaderboard():
    """لیدربورد برترین معرفین"""
    from candidate_panel.referral_utils import get_leaderboard
    
    leaderboard = get_leaderboard(limit=20)
    candidate_id = session.get('candidate_id')
    
    # رتبه خودم
    my_rank = None
    for idx, item in enumerate(leaderboard):
        ref_program = ReferralProgram.query.filter_by(
            referral_code=item['referral_code']
        ).first()
        if ref_program and ref_program.candidate_id == candidate_id:
            my_rank = idx + 1
            break
    
    return render_template(
        'candidate/referral_leaderboard.html',
        leaderboard=leaderboard,
        my_rank=my_rank
    )


# ========== VIP Citizen System Routes ==========

@app.route('/vip')
@login_required
def vip_dashboard():
    """داشبورد سیستم VIP - شهروند ماه"""
    from candidate_panel.vip_utils import (
        get_vip_citizens,
        get_upcoming_vip_interactions,
        get_vip_statistics
    )
    
    candidate_id = session.get('candidate_id')
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # شهروندان VIP این ماه
    vip_citizens = get_vip_citizens(candidate_id, current_month, current_year)
    
    # جلسات آینده
    upcoming_meetings = get_upcoming_vip_interactions(candidate_id, days_ahead=30)
    
    # آمار کلی
    stats = get_vip_statistics(candidate_id)
    
    return render_template(
        'candidate/vip.html',
        vip_citizens=vip_citizens,
        upcoming_meetings=upcoming_meetings,
        stats=stats,
        current_month=current_month,
        current_year=current_year
    )


@app.route('/vip/award', methods=['POST'])
@secure_route()
def vip_award():
    """اعطای وضعیت VIP به برترین‌ها"""
    from candidate_panel.vip_utils import award_vip_status
    
    candidate_id = session.get('candidate_id')
    month = request.form.get('month', type=int) or datetime.now().month
    year = request.form.get('year', type=int) or datetime.now().year
    
    result = award_vip_status(candidate_id, month, year)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'warning')
    
    return redirect(url_for('vip_dashboard'))


@app.route('/vip/schedule', methods=['POST'])
@secure_route()
def vip_schedule_meeting():
    """زمان‌بندی جلسه VIP"""
    from candidate_panel.vip_utils import schedule_vip_interaction
    
    candidate_id = session.get('candidate_id')
    citizen_telegram_id = request.form.get('citizen_telegram_id', type=int)
    interaction_type = request.form.get('interaction_type')
    title = request.form.get('title')
    description = request.form.get('description')
    scheduled_date_str = request.form.get('scheduled_date')
    meeting_link = request.form.get('meeting_link')
    
    # تبدیل تاریخ
    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
    
    interaction = schedule_vip_interaction(
        candidate_id=candidate_id,
        citizen_telegram_id=citizen_telegram_id,
        interaction_type=interaction_type,
        title=title,
        description=description,
        scheduled_date=scheduled_date,
        meeting_link=meeting_link
    )
    
    flash(f'جلسه "{title}" زمان‌بندی شد', 'success')
    return redirect(url_for('vip_dashboard'))


@app.route('/vip/complete/<int:interaction_id>', methods=['POST'])
@secure_route()
def vip_complete_meeting(interaction_id):
    """تکمیل جلسه VIP"""
    from candidate_panel.vip_utils import complete_vip_interaction
    
    notes = request.form.get('notes')
    
    if complete_vip_interaction(interaction_id, notes):
        flash('جلسه با موفقیت تکمیل شد', 'success')
    else:
        flash('خطا در تکمیل جلسه', 'danger')
    
    return redirect(url_for('vip_dashboard'))


@app.route('/vip/cancel/<int:interaction_id>', methods=['POST'])
@secure_route()
def vip_cancel_meeting(interaction_id):
    """لغو جلسه VIP"""
    from candidate_panel.vip_utils import cancel_vip_interaction
    
    reason = request.form.get('cancellation_reason')
    
    if cancel_vip_interaction(interaction_id, reason):
        flash('جلسه لغو شد', 'warning')
    else:
        flash('خطا در لغو جلسه', 'danger')
    
    return redirect(url_for('vip_dashboard'))


# ============================================================
# Party Management Routes
# ============================================================

@app.route('/party')
@login_required
def party_dashboard():
    """داشبورد مدیریت حزب و ائتلاف"""
    from candidate_panel.party_utils import (
        get_candidate_parties, get_candidate_coalitions,
        get_party_statistics
    )
    
    candidate_id = session.get('candidate_id')
    
    # احزاب نامزد
    parties = get_candidate_parties(candidate_id)
    
    # ائتلاف‌های نامزد
    coalitions = get_candidate_coalitions(candidate_id)
    
    # آمار اولین حزب
    party_stats = None
    if parties:
        party_stats = get_party_statistics(parties[0][0].id)
    
    return render_template('candidate/party.html',
                         parties=parties,
                         coalitions=coalitions,
                         party_stats=party_stats)


@app.route('/party/create', methods=['POST'])
@secure_route()
def party_create():
    """ایجاد حزب جدید"""
    from candidate_panel.party_utils import create_party
    
    candidate_id = session.get('candidate_id')
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    ideology = request.form.get('ideology', 'مستقل')
    manifesto = request.form.get('manifesto', '')
    
    if not name:
        flash('نام حزب الزامی است', 'danger')
        return redirect(url_for('party_dashboard'))
    
    try:
        party = create_party(
            name=name,
            leader_candidate_id=candidate_id,
            description=description,
            ideology=ideology,
            manifesto=manifesto
        )
        flash(f'حزب {party.name} با موفقیت ایجاد شد', 'success')
    except Exception as e:
        flash(f'خطا در ایجاد حزب: {str(e)}', 'danger')
    
    return redirect(url_for('party_dashboard'))


@app.route('/party/<int:party_id>')
@login_required
def party_detail(party_id):
    """جزئیات حزب و لیست اعضا"""
    from candidate_panel.party_utils import (
        get_party_by_id, get_party_members, get_pending_members,
        get_party_statistics, check_member_permission
    )
    
    candidate_id = session.get('candidate_id')
    
    party = get_party_by_id(party_id)
    if not party:
        flash('حزب یافت نشد', 'danger')
        return redirect(url_for('party_dashboard'))
    
    # چک دسترسی
    can_manage = check_member_permission(party_id, candidate_id, 'can_manage_members')
    
    # اعضا
    members = get_party_members(party_id)
    pending = get_pending_members(party_id) if can_manage else []
    
    # آمار
    stats = get_party_statistics(party_id)
    
    return render_template('candidate/party_detail.html',
                         party=party,
                         members=members,
                         pending_members=pending,
                         stats=stats,
                         can_manage=can_manage)


@app.route('/party/<int:party_id>/add-member', methods=['POST'])
@secure_route()
def party_add_member(party_id):
    """افزودن عضو به حزب"""
    from candidate_panel.party_utils import add_member_to_party, check_member_permission
    
    candidate_id = session.get('candidate_id')
    
    # چک دسترسی
    if not check_member_permission(party_id, candidate_id, 'can_manage_members'):
        flash('شما دسترسی مدیریت اعضا را ندارید', 'danger')
        return redirect(url_for('party_detail', party_id=party_id))
    
    new_candidate_id = request.form.get('candidate_id', type=int)
    role = request.form.get('role', 'member')
    position = request.form.get('position', '')
    
    if not new_candidate_id:
        flash('لطفا نامزد را انتخاب کنید', 'danger')
        return redirect(url_for('party_detail', party_id=party_id))
    
    membership = add_member_to_party(
        party_id=party_id,
        candidate_id=new_candidate_id,
        role=role,
        position=position,
        is_approved=True  # مستقیم تایید می‌شود
    )
    
    if membership:
        flash('عضو با موفقیت اضافه شد', 'success')
    else:
        flash('این نامزد قبلاً عضو حزب است', 'warning')
    
    return redirect(url_for('party_detail', party_id=party_id))


@app.route('/party/<int:party_id>/remove-member/<int:member_candidate_id>', methods=['POST'])
@secure_route()
def party_remove_member(party_id, member_candidate_id):
    """حذف عضو از حزب"""
    from candidate_panel.party_utils import remove_member_from_party, check_member_permission
    
    candidate_id = session.get('candidate_id')
    
    # چک دسترسی
    if not check_member_permission(party_id, candidate_id, 'can_manage_members'):
        flash('شما دسترسی مدیریت اعضا را ندارید', 'danger')
        return redirect(url_for('party_detail', party_id=party_id))
    
    if remove_member_from_party(party_id, member_candidate_id):
        flash('عضو حذف شد', 'success')
    else:
        flash('خطا در حذف عضو', 'danger')
    
    return redirect(url_for('party_detail', party_id=party_id))


@app.route('/party/<int:party_id>/approve-member/<int:member_candidate_id>', methods=['POST'])
@secure_route()
def party_approve_member(party_id, member_candidate_id):
    """تایید عضویت"""
    from candidate_panel.party_utils import approve_member, check_member_permission
    
    candidate_id = session.get('candidate_id')
    
    # چک دسترسی
    if not check_member_permission(party_id, candidate_id, 'can_manage_members'):
        flash('شما دسترسی مدیریت اعضا را ندارید', 'danger')
        return redirect(url_for('party_detail', party_id=party_id))
    
    if approve_member(party_id, member_candidate_id):
        flash('عضویت تایید شد', 'success')
    else:
        flash('خطا در تایید عضو', 'danger')
    
    return redirect(url_for('party_detail', party_id=party_id))


@app.route('/party/<int:party_id>/update-role', methods=['POST'])
@secure_route()
def party_update_role(party_id):
    """تغییر نقش و دسترسی عضو"""
    from candidate_panel.party_utils import update_member_role, check_member_permission
    
    candidate_id = session.get('candidate_id')
    
    # چک دسترسی
    if not check_member_permission(party_id, candidate_id, 'can_manage_members'):
        flash('شما دسترسی مدیریت اعضا را ندارید', 'danger')
        return redirect(url_for('party_detail', party_id=party_id))
    
    member_candidate_id = request.form.get('candidate_id', type=int)
    role = request.form.get('role', 'member')
    position = request.form.get('position', '')
    
    permissions = {
        'can_manage_party': request.form.get('can_manage_party') == 'on',
        'can_manage_members': request.form.get('can_manage_members') == 'on',
        'can_send_broadcast': request.form.get('can_send_broadcast') == 'on',
        'can_view_analytics': request.form.get('can_view_analytics') == 'on',
        'can_create_events': request.form.get('can_create_events') == 'on',
    }
    
    if update_member_role(party_id, member_candidate_id, role, position, **permissions):
        flash('نقش و دسترسی‌ها بروز شد', 'success')
    else:
        flash('خطا در بروزرسانی', 'danger')
    
    return redirect(url_for('party_detail', party_id=party_id))


# ============================================================
# Coalition Management Routes
# ============================================================

@app.route('/coalition/create', methods=['POST'])
@secure_route()
def coalition_create():
    """ایجاد ائتلاف جدید"""
    from candidate_panel.party_utils import create_coalition
    
    candidate_id = session.get('candidate_id')
    
    name = request.form.get('name')
    election_type = request.form.get('election_type', 'مجلس')
    election_year = request.form.get('election_year', type=int)
    description = request.form.get('description', '')
    
    if not name or not election_year:
        flash('نام و سال انتخابات الزامی است', 'danger')
        return redirect(url_for('party_dashboard'))
    
    try:
        coalition = create_coalition(
            name=name,
            coordinator_candidate_id=candidate_id,
            election_type=election_type,
            election_year=election_year,
            description=description
        )
        flash(f'ائتلاف {coalition.name} ایجاد شد', 'success')
    except Exception as e:
        flash(f'خطا: {str(e)}', 'danger')
    
    return redirect(url_for('party_dashboard'))


@app.route('/coalition/<int:coalition_id>')
@login_required
def coalition_detail(coalition_id):
    """جزئیات ائتلاف"""
    from candidate_panel.party_utils import (
        get_coalition_members, get_coalition_statistics
    )
    from database.models import ElectoralCoalition
    
    coalition = ElectoralCoalition.query.get(coalition_id)
    if not coalition:
        flash('ائتلاف یافت نشد', 'danger')
        return redirect(url_for('party_dashboard'))
    
    members = get_coalition_members(coalition_id)
    stats = get_coalition_statistics(coalition_id)
    
    return render_template('candidate/coalition_detail.html',
                         coalition=coalition,
                         members=members,
                         stats=stats)


@app.route('/coalition/<int:coalition_id>/add-member', methods=['POST'])
@secure_route()
def coalition_add_member(coalition_id):
    """افزودن عضو به ائتلاف"""
    from candidate_panel.party_utils import add_party_to_coalition
    
    party_id = request.form.get('party_id', type=int)
    candidate_id = request.form.get('candidate_id', type=int)
    
    if not party_id and not candidate_id:
        flash('لطفا حزب یا نامزد را انتخاب کنید', 'danger')
        return redirect(url_for('coalition_detail', coalition_id=coalition_id))
    
    membership = add_party_to_coalition(
        coalition_id=coalition_id,
        party_id=party_id,
        candidate_id=candidate_id
    )
    
    if membership:
        flash('عضو به ائتلاف اضافه شد', 'success')
    else:
        flash('این عضو قبلاً در ائتلاف است', 'warning')
    
    return redirect(url_for('coalition_detail', coalition_id=coalition_id))


@app.route('/coalition/<int:coalition_id>/remove-member', methods=['POST'])
@secure_route()
def coalition_remove_member(coalition_id):
    """حذف عضو از ائتلاف"""
    from candidate_panel.party_utils import remove_from_coalition
    
    party_id = request.form.get('party_id', type=int)
    candidate_id = request.form.get('candidate_id', type=int)
    
    if remove_from_coalition(coalition_id, party_id, candidate_id):
        flash('عضو از ائتلاف خارج شد', 'success')
    else:
        flash('خطا در حذف', 'danger')
    
    return redirect(url_for('coalition_detail', coalition_id=coalition_id))


# ========== Live Events Management ==========

@app.route('/events')
@login_required
def events_dashboard():
    """داشبورد رویدادهای زنده"""
    from candidate_panel.events_utils import get_candidate_events, get_candidate_events_summary
    
    candidate_id = session.get('candidate_id')
    
    # آمار کلی
    summary = get_candidate_events_summary(candidate_id)
    
    # رویدادهای آینده
    upcoming_events = get_candidate_events(candidate_id, upcoming_only=True)
    
    # رویدادهای اخیر
    recent_events = get_candidate_events(candidate_id)[:10]
    
    return render_template('candidate/events.html',
                         summary=summary,
                         upcoming_events=upcoming_events,
                         recent_events=recent_events)


@app.route('/events/create', methods=['GET', 'POST'])
@secure_route()
def create_event():
    """ایجاد رویداد جدید"""
    from candidate_panel.events_utils import create_event as create_event_util
    from datetime import datetime
    
    if request.method == 'GET':
        return render_template('candidate/create_event.html')
    
    candidate_id = session.get('candidate_id')
    
    # دریافت اطلاعات از فرم
    title = request.form.get('title')
    description = request.form.get('description')
    event_type = request.form.get('event_type')
    starts_at_str = request.form.get('starts_at')
    duration_minutes = request.form.get('duration_minutes', 60, type=int)
    platform = request.form.get('platform', 'telegram_live')
    stream_url = request.form.get('stream_url')
    max_participants = request.form.get('max_participants', type=int)
    vip_only = request.form.get('vip_only') == 'on'
    min_points_required = request.form.get('min_points_required', 0, type=int)
    requires_registration = request.form.get('requires_registration', 'on') == 'on'
    
    # تبدیل تاریخ
    starts_at = datetime.fromisoformat(starts_at_str.replace('Z', '+00:00'))
    
    try:
        event = create_event_util(
            candidate_id=candidate_id,
            title=title,
            description=description,
            event_type=event_type,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            platform=platform,
            stream_url=stream_url,
            max_participants=max_participants,
            vip_only=vip_only,
            min_points_required=min_points_required,
            requires_registration=requires_registration
        )
        
        flash(f'✅ رویداد "{title}" با موفقیت ایجاد شد', 'success')
        return redirect(url_for('event_detail', event_id=event.id))
    
    except Exception as e:
        flash(f'❌ خطا در ایجاد رویداد: {str(e)}', 'danger')
        return redirect(url_for('create_event'))


@app.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    """جزئیات رویداد"""
    from candidate_panel.events_utils import (
        get_event_details,
        get_event_registrations,
        get_event_questions,
        get_event_statistics
    )
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    # جزئیات
    details = get_event_details(event_id)
    
    # ثبت‌نام‌کنندگان
    registrations = get_event_registrations(event_id)
    
    # سوالات
    questions = get_event_questions(event_id, sort_by='upvotes')
    
    # آمار
    statistics = get_event_statistics(event_id)
    
    return render_template('candidate/event_detail.html',
                         event=event,
                         details=details,
                         registrations=registrations,
                         questions=questions,
                         statistics=statistics)


@app.route('/events/<int:event_id>/edit', methods=['POST'])
@secure_route()
def edit_event(event_id):
    """ویرایش رویداد"""
    from candidate_panel.events_utils import update_event
    from database.models import LiveEvent
    from datetime import datetime
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    # دریافت فیلدهای قابل ویرایش
    updates = {}
    
    if request.form.get('title'):
        updates['title'] = request.form.get('title')
    
    if request.form.get('description'):
        updates['description'] = request.form.get('description')
    
    if request.form.get('starts_at'):
        updates['starts_at'] = datetime.fromisoformat(
            request.form.get('starts_at').replace('Z', '+00:00')
        )
    
    if request.form.get('duration_minutes'):
        updates['duration_minutes'] = request.form.get('duration_minutes', type=int)
    
    if request.form.get('stream_url'):
        updates['stream_url'] = request.form.get('stream_url')
    
    if request.form.get('max_participants'):
        updates['max_participants'] = request.form.get('max_participants', type=int)
    
    # به‌روزرسانی
    if update_event(event_id, **updates):
        flash('✅ رویداد به‌روز شد', 'success')
    else:
        flash('❌ خطا در به‌روزرسانی', 'danger')
    
    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/events/<int:event_id>/start', methods=['POST'])
@secure_route()
def start_event(event_id):
    """شروع رویداد (تغییر به حالت live)"""
    from candidate_panel.events_utils import start_event as start_event_util
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    if start_event_util(event_id):
        flash('🔴 رویداد شروع شد', 'success')
    else:
        flash('❌ خطا در شروع رویداد', 'danger')
    
    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/events/<int:event_id>/complete', methods=['POST'])
@secure_route()
def complete_event(event_id):
    """پایان رویداد"""
    from candidate_panel.events_utils import complete_event as complete_event_util
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    if complete_event_util(event_id):
        flash('✅ رویداد به پایان رسید', 'success')
    else:
        flash('❌ خطا در پایان رویداد', 'danger')
    
    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/events/<int:event_id>/cancel', methods=['POST'])
@secure_route()
def cancel_event(event_id):
    """لغو رویداد"""
    from candidate_panel.events_utils import cancel_event as cancel_event_util
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    reason = request.form.get('reason', 'دلیل مشخص نشده')
    
    if cancel_event_util(event_id, reason):
        flash(f'⛔ رویداد لغو شد: {reason}', 'warning')
    else:
        flash('❌ خطا در لغو رویداد', 'danger')
    
    return redirect(url_for('events_dashboard'))


@app.route('/events/<int:event_id>/registrations')
@login_required
def event_registrations(event_id):
    """لیست ثبت‌نام‌کنندگان"""
    from candidate_panel.events_utils import get_event_registrations
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    # فیلتر حضور
    attended_only = request.args.get('attended_only') == 'true'
    
    registrations = get_event_registrations(event_id, attended_only=attended_only)
    
    return render_template('candidate/event_registrations.html',
                         event=event,
                         registrations=registrations,
                         attended_only=attended_only)


@app.route('/events/<int:event_id>/questions')
@login_required
def event_questions(event_id):
    """مدیریت سوالات"""
    from candidate_panel.events_utils import get_event_questions
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    # فیلتر وضعیت
    status_filter = request.args.get('status')
    sort_by = request.args.get('sort_by', 'upvotes')
    
    questions = get_event_questions(event_id, status=status_filter, sort_by=sort_by)
    
    return render_template('candidate/event_questions.html',
                         event=event,
                         questions=questions,
                         status_filter=status_filter,
                         sort_by=sort_by)


@app.route('/events/<int:event_id>/questions/<int:question_id>/approve', methods=['POST'])
@secure_route()
def approve_question(event_id, question_id):
    """تایید سوال"""
    from candidate_panel.events_utils import approve_question as approve_question_util
    from database.models import LiveEvent, EventQuestion
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    if approve_question_util(question_id):
        flash('✅ سوال تایید شد', 'success')
    else:
        flash('❌ خطا در تایید', 'danger')
    
    return redirect(url_for('event_questions', event_id=event_id))


@app.route('/events/<int:event_id>/questions/<int:question_id>/answer', methods=['POST'])
@secure_route()
def answer_question(event_id, question_id):
    """پاسخ به سوال"""
    from candidate_panel.events_utils import answer_question as answer_question_util
    from database.models import LiveEvent, Candidate
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    answer_text = request.form.get('answer_text')
    candidate = Candidate.query.get(candidate_id)
    answered_by = candidate.full_name if candidate else 'نماینده'
    
    if answer_question_util(question_id, answer_text, answered_by):
        flash('✅ پاسخ ثبت شد', 'success')
    else:
        flash('❌ خطا در ثبت پاسخ', 'danger')
    
    return redirect(url_for('event_questions', event_id=event_id))


@app.route('/events/<int:event_id>/questions/<int:question_id>/reject', methods=['POST'])
@secure_route()
def reject_question(event_id, question_id):
    """رد سوال"""
    from candidate_panel.events_utils import reject_question as reject_question_util
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    if reject_question_util(question_id):
        flash('⛔ سوال رد شد', 'warning')
    else:
        flash('❌ خطا در رد', 'danger')
    
    return redirect(url_for('event_questions', event_id=event_id))


@app.route('/events/<int:event_id>/statistics')
@login_required
def event_statistics(event_id):
    """آمار کامل رویداد"""
    from candidate_panel.events_utils import get_event_statistics
    from database.models import LiveEvent
    
    candidate_id = session.get('candidate_id')
    
    # بررسی مالکیت
    event = LiveEvent.query.get_or_404(event_id)
    if event.candidate_id != candidate_id:
        flash('شما به این رویداد دسترسی ندارید', 'danger')
        return redirect(url_for('events_dashboard'))
    
    statistics = get_event_statistics(event_id)
    
    return render_template('candidate/event_statistics.html',
                         event=event,
                         statistics=statistics)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, port=5001, host='0.0.0.0')
