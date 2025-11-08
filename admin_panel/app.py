"""
پنل مدیریت سوپر ادمین
مدیریت نماینده‌ها، پلن‌ها و راه‌اندازی بات‌ها
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, Admin, Candidate, Plan, BotInstance
from config.settings import ADMIN_SECRET_KEY, DATABASE_URI
from bot_engine.bot_manager import BotManager

app = Flask(__name__, 
            template_folder='../templates/admin',
            static_folder='../static')
app.config['SECRET_KEY'] = ADMIN_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

bot_manager = BotManager()


def login_required(f):
    """دکوراتور بررسی لاگین"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


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
    
    return render_template('login.html')


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
    
    return render_template('dashboard.html',
                         candidates=candidates,
                         stats=stats)


@app.route('/candidates')
@login_required
def candidates():
    """لیست نماینده‌ها"""
    candidates = Candidate.query.all()
    return render_template('candidates.html', candidates=candidates)


@app.route('/candidate/create', methods=['GET', 'POST'])
@login_required
def create_candidate():
    """ایجاد نماینده جدید"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
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
            phone=phone
        )
        
        db.session.add(candidate)
        db.session.commit()
        
        flash(f'نماینده {full_name} با موفقیت ایجاد شد', 'success')
        return redirect(url_for('candidates'))
    
    return render_template('create_candidate.html')


@app.route('/candidate/<int:candidate_id>/bot-setup', methods=['GET', 'POST'])
@login_required
def setup_bot(candidate_id):
    """راه‌اندازی بات برای نماینده"""
    candidate = Candidate.query.get_or_404(candidate_id)
    
    if request.method == 'POST':
        bot_token = request.form.get('bot_token')
        bot_username = request.form.get('bot_username')
        
        # ایجاد نمونه بات
        bot_instance = BotInstance(
            candidate_id=candidate.id,
            bot_token=bot_token,
            bot_username=bot_username,
            is_active=True
        )
        
        db.session.add(bot_instance)
        db.session.commit()
        
        # راه‌اندازی بات
        try:
            bot_manager.start_bot(bot_instance.id)
            flash(f'بات {bot_username} با موفقیت راه‌اندازی شد', 'success')
        except Exception as e:
            flash(f'خطا در راه‌اندازی بات: {str(e)}', 'danger')
        
        return redirect(url_for('candidates'))
    
    return render_template('setup_bot.html', candidate=candidate)


@app.route('/plans')
@login_required
def plans():
    """مدیریت پلن‌ها"""
    plans = Plan.query.all()
    return render_template('plans.html', plans=plans)


@app.route('/candidate/<int:candidate_id>/activate-plan', methods=['POST'])
@login_required
def activate_plan(candidate_id):
    """فعال‌سازی پلن برای نماینده"""
    candidate = Candidate.query.get_or_404(candidate_id)
    plan_id = request.form.get('plan_id')
    
    plan = Plan.query.get_or_404(plan_id)
    
    if plan not in candidate.plans:
        candidate.plans.append(plan)
        db.session.commit()
        flash(f'پلن {plan.name} برای {candidate.full_name} فعال شد', 'success')
    else:
        flash('این پلن قبلاً فعال شده است', 'warning')
    
    return redirect(url_for('candidates'))


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
            db.session.commit()
            print('✅ ادمین پیش‌فرض ایجاد شد: admin / admin123')
    
    app.run(debug=True, port=5000, host='0.0.0.0')
