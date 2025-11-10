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

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (db, Candidate, Resume, Program, Slogan, 
                            Headquarters, Message, Analytics)
from config.settings import CANDIDATE_SECRET_KEY, DATABASE_URI, UPLOAD_FOLDER

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.config['SECRET_KEY'] = CANDIDATE_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)


def login_required(f):
    """دکوراتور بررسی لاگین"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"🔒 بررسی لاگین - session: {dict(session)}")
        if 'candidate_id' not in session:
            print(f"❌ candidate_id در session نیست - ریدایرکت به login")
            return redirect(url_for('login'))
        print(f"✅ کاربر لاگین هست: candidate_id={session['candidate_id']}")
        return f(*args, **kwargs)
    return decorated_function


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


@app.route('/')
def index():
    """صفحه اصلی"""
    if 'candidate_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ورود نماینده"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"🔍 تلاش ورود - نام کاربری: {username}, رمز: {password}")
        
        candidate = Candidate.query.filter_by(username=username).first()
        
        if not candidate:
            print(f"❌ نماینده با نام کاربری '{username}' پیدا نشد")
            flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
        else:
            print(f"✅ نماینده پیدا شد: {candidate.full_name}")
            print(f"🔐 هش در DB: {candidate.password[:60]}...")
            password_match = check_password_hash(candidate.password, password)
            print(f"🔐 نتیجه بررسی: {'موفق ✅' if password_match else 'ناموفق ❌'}")
            
            if password_match:
                session.clear()
                session['candidate_id'] = candidate.id
                session['candidate_name'] = candidate.full_name
                session.permanent = True
                print(f"✅ Session ست شد: candidate_id={candidate.id}")
                print(f"✅ ورود موفق - ریدایرکت به داشبورد")
                flash('خوش آمدید!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
    
    return render_template('candidate/login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """داشبورد نماینده"""
    candidate = Candidate.query.get(session['candidate_id'])
    
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
                         analytics_data=analytics_data)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """ویرایش اطلاعات شخصی"""
    candidate = Candidate.query.get(session['candidate_id'])
    
    if request.method == 'POST':
        candidate.full_name = request.form.get('full_name')
        candidate.city = request.form.get('city')
        candidate.district = request.form.get('district')
        candidate.phone = request.form.get('phone')
        candidate.email = request.form.get('email')
        candidate.bio = request.form.get('bio')
        
        # آپلود تصویر
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                filename = secure_filename(f"candidate_{candidate.id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                candidate.photo = filename
        
        db.session.commit()
        flash('اطلاعات با موفقیت به‌روزرسانی شد', 'success')
        return redirect(url_for('profile'))
    
    return render_template('candidate/profile.html', candidate=candidate)


@app.route('/resume', methods=['GET', 'POST'])
@login_required
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
        db.session.commit()
        flash('آیتم رزومه اضافه شد', 'success')
        return redirect(url_for('resume'))
    
    return render_template('candidate/resume.html', candidate=candidate, resumes=resumes)


@app.route('/programs', methods=['GET', 'POST'])
@login_required
def programs():
    """مدیریت برنامه‌های انتخاباتی"""
    candidate = Candidate.query.get(session['candidate_id'])
    programs = Program.query.filter_by(candidate_id=candidate.id).all()
    
    if request.method == 'POST':
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
        db.session.commit()
        flash('برنامه جدید اضافه شد', 'success')
        return redirect(url_for('programs'))
    
    return render_template('candidate/programs.html', candidate=candidate, programs=programs)


@app.route('/headquarters', methods=['GET', 'POST'])
@login_required
def headquarters():
    """مدیریت ستادهای انتخاباتی"""
    candidate = Candidate.query.get(session['candidate_id'])
    hqs = Headquarters.query.filter_by(candidate_id=candidate.id).all()
    
    if request.method == 'POST':
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
        db.session.commit()
        flash('ستاد جدید اضافه شد', 'success')
        return redirect(url_for('headquarters'))
    
    return render_template('candidate/headquarters.html', candidate=candidate, headquarters=hqs)


@app.route('/messages')
@login_required
@has_plan('PUBLIC_MESSAGING')
def messages():
    """پیام‌های دریافتی از مردم"""
    candidate = Candidate.query.get(session['candidate_id'])
    messages = Message.query.filter_by(candidate_id=candidate.id).order_by(Message.created_at.desc()).all()
    
    return render_template('candidate/messages.html', candidate=candidate, messages=messages)


@app.route('/message/<int:message_id>/read', methods=['POST'])
@login_required
def mark_read(message_id):
    """علامت‌گذاری پیام به‌عنوان خوانده‌شده"""
    message = Message.query.get_or_404(message_id)
    
    if message.candidate_id == session['candidate_id']:
        message.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 403


@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
@has_plan('MASS_MESSAGING')
def broadcast():
    """ارسال پیام انبوه"""
    candidate = Candidate.query.get(session['candidate_id'])
    
    if request.method == 'POST':
        message_text = request.form.get('message')
        
        # TODO: پیاده‌سازی سیستم ارسال انبوه
        flash('پیام برای ارسال به صف اضافه شد', 'success')
        return redirect(url_for('broadcast'))
    
    return render_template('broadcast.html', candidate=candidate)


@app.route('/analytics')
@login_required
@has_plan('ANALYTICS')
def analytics():
    """آمار و تحلیل"""
    candidate = Candidate.query.get(session['candidate_id'])
    analytics_data = Analytics.query.filter_by(candidate_id=candidate.id).order_by(Analytics.date.desc()).limit(30).all()
    
    return render_template('analytics.html', candidate=candidate, analytics=analytics_data)


@app.route('/logout')
def logout():
    """خروج"""
    session.clear()
    flash('با موفقیت خارج شدید', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, port=5001, host='0.0.0.0')
