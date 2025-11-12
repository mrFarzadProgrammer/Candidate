# 🚀 پیشنهادات پیشرفته برای سیستم مدیریت نامزدهای انتخاباتی

## 📊 تحلیل وضعیت فعلی سیستم

### ✅ امکانات موجود (100% کامل):
1. ✅ سیستم مدیریت نامزدها با پنل مجزا
2. ✅ ربات تلگرام با امکانات پیشرفته
3. ✅ سیستم پلن‌های اشتراک
4. ✅ مدیریت کانال‌ها و ارسال پست
5. ✅ سیستم نظرسنجی (پول)
6. ✅ سیستم تیکتینگ و پرداخت
7. ✅ سیستم مشارکت شهروندی با گیمیفیکیشن
8. ✅ آنالیتیکس و آمارگیری

---

## 🎯 استراتژی توسعه: از تک‌نامزد به پلتفرم سیاسی

---

## 💡 بخش اول: سیستم احزاب و ائتلاف‌ها

### 1️⃣ مدل احزاب سیاسی (Political Parties)

**مشکل فعلی:** 
- هر نامزد مستقل است
- همکاری بین نامزدها وجود ندارد
- نمی‌توان کمپین مشترک داشت

**راه‌حل:**

```python
# مدل حزب
class PoliticalParty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    name_english = db.Column(db.String(200))
    abbreviation = db.Column(db.String(20))  # مثلاً جبهه اصلاحات -> JI
    logo = db.Column(db.String(500))
    color_primary = db.Column(db.String(7), default='#6366f1')  # رنگ اختصاصی
    color_secondary = db.Column(db.String(7))
    
    # اطلاعات حزب
    description = db.Column(db.Text)
    ideology = db.Column(db.String(100))  # اصلاح‌طلب، اصولگرا، میانه‌رو
    founded_year = db.Column(db.Integer)
    website = db.Column(db.String(200))
    
    # مدیریت
    leader_candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    secretary_general_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    
    # پنل مشترک
    shared_bot_token = db.Column(db.String(500))  # ربات مشترک حزب
    shared_channel_id = db.Column(db.String(100))  # کانال رسمی حزب
    
    # آمار
    total_members = db.Column(db.Integer, default=0)
    total_candidates = db.Column(db.Integer, default=0)
    total_votes_estimate = db.Column(db.Integer, default=0)
    
    # اشتراک حزبی
    party_subscription_plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'))
    subscription_expires_at = db.Column(db.DateTime)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# عضویت نامزدها در حزب
class PartyMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('political_party.id'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    
    role = db.Column(db.String(50))  # leader, deputy, member, supporter
    position = db.Column(db.String(100))  # دبیر استان، مسئول کمیته
    
    # سطح دسترسی در پنل حزب
    can_manage_party = db.Column(db.Boolean, default=False)
    can_send_broadcast = db.Column(db.Boolean, default=False)
    can_view_analytics = db.Column(db.Boolean, default=True)
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


# ائتلاف‌های انتخاباتی
class ElectoralCoalition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_english = db.Column(db.String(200))
    
    # اطلاعات ائتلاف
    description = db.Column(db.Text)
    manifesto = db.Column(db.Text)  # بیانیه مشترک
    logo = db.Column(db.String(500))
    
    # برای انتخابات خاص
    election_type = db.Column(db.String(50))  # مجلس، شورا، ریاست‌جمهوری
    election_year = db.Column(db.Integer)
    target_constituency = db.Column(db.String(100))  # حوزه انتخابیه
    
    # رهبری
    coordinator_candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    
    # وضعیت
    status = db.Column(db.String(30), default='forming')  # forming, active, dissolved
    formed_at = db.Column(db.DateTime)
    dissolved_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# عضویت در ائتلاف
class CoalitionMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coalition_id = db.Column(db.Integer, db.ForeignKey('electoral_coalition.id'))
    
    # می‌تواند حزب یا نامزد مستقل باشد
    party_id = db.Column(db.Integer, db.ForeignKey('political_party.id'), nullable=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=True)
    
    # شرایط همکاری
    vote_share_percentage = db.Column(db.Float)  # سهم از آرا
    resource_contribution = db.Column(db.Float)  # سهم مالی/منابع
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
```

**مزایا:**
- ✅ کمپین‌های مشترک حزبی
- ✅ تقسیم هزینه‌ها بین اعضا
- ✅ برندینگ یکپارچه
- ✅ همکاری در جمع‌آوری آرا
- ✅ پنل مدیریت حزبی مشترک

---

### 2️⃣ پنل مدیریت حزب (Party Management Dashboard)

**ویژگی‌ها:**

```
📊 داشبورد حزبی:
├── نمای کلی حزب
│   ├── تعداد نامزدها: 45 نفر
│   ├── تعداد کل رای‌دهندگان: 1.2 میلیون
│   ├── بودجه مشترک: 500 میلیون تومان
│   └── فعالیت هفتگی: +25%
│
├── مدیریت نامزدها
│   ├── لیست نامزدهای عضو
│   ├── نقش‌ها و مسئولیت‌ها
│   ├── آمار فردی هر نامزد
│   └── تخصیص منابع
│
├── کمپین‌های مشترک
│   ├── ارسال پیام انبوه به کل پایگاه
│   ├── برنامه‌ریزی رویدادهای مشترک
│   ├── محتوای اشتراکی برندینگ
│   └── هماهنگی جلسات
│
├── آمار مقایسه‌ای
│   ├── مقایسه نامزدها با یکدیگر
│   ├── رتبه‌بندی فعالیت
│   ├── نمودار رشد پایگاه
│   └── نقاط قوت و ضعف
│
└── مالی و اشتراک
    ├── پرداخت گروهی
    ├── تخفیف حزبی (30%)
    ├── تسهیم هزینه
    └── صورت‌حساب مشترک
```

**Route جدید:**
```python
@app.route('/party/dashboard')
@party_admin_required
def party_dashboard():
    party = current_party()
    
    stats = {
        'total_candidates': PartyMembership.query.filter_by(
            party_id=party.id, is_active=True
        ).count(),
        'total_supporters': db.session.query(func.sum(Analytics.total_messages)).join(
            Candidate
        ).join(PartyMembership).filter(
            PartyMembership.party_id == party.id
        ).scalar() or 0,
        'active_campaigns': BroadcastMessage.query.join(Candidate).join(
            PartyMembership
        ).filter(
            PartyMembership.party_id == party.id,
            BroadcastMessage.status == 'completed'
        ).count()
    }
    
    # رتبه‌بندی نامزدهای حزب
    top_candidates = db.session.query(
        Candidate, Analytics
    ).join(Analytics).join(PartyMembership).filter(
        PartyMembership.party_id == party.id
    ).order_by(Analytics.total_messages.desc()).limit(10).all()
    
    return render_template('party/dashboard.html',
                         party=party,
                         stats=stats,
                         top_candidates=top_candidates)
```

---

## 💰 بخش دوم: استراتژی جذب نامزدهای جدید

### 3️⃣ سیستم Trial و نمایش رقابتی

**مشکل:**
- نامزدها نمی‌دانند رقبایشان چقدر موفق‌اند
- انگیزه‌ای برای ارتقا ندارند
- ترس از خرید (قبل از امتحان)

**راه‌حل: داشبورد آماری رقابتی (Competitive Analytics)**

```python
class MarketplaceBenchmark(db.Model):
    """آمار گمنام از همه نامزدها برای مقایسه"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    
    # آمار anonymized
    plan_name = db.Column(db.String(50))
    
    # میانگین‌ها (برای هر پلن)
    avg_daily_messages = db.Column(db.Float)
    avg_bot_users = db.Column(db.Float)
    avg_engagement_rate = db.Column(db.Float)
    avg_citizen_contributions = db.Column(db.Float)
    
    # محدوده‌ها (بالا-پایین)
    top_10_percent_messages = db.Column(db.Integer)  # ۱۰٪ برتر چقدر؟
    median_messages = db.Column(db.Integer)
    bottom_10_percent_messages = db.Column(db.Integer)


# نمایش به کاربر
@app.route('/benchmark')
@login_required
def view_benchmark():
    candidate_id = session['candidate_id']
    candidate = Candidate.query.get(candidate_id)
    
    # پلن فعلی کاربر
    current_plan = get_active_plan(candidate_id)
    
    # آمار خود کاربر
    my_analytics = Analytics.query.filter_by(candidate_id=candidate_id).first()
    
    # آمار بازار
    benchmark = MarketplaceBenchmark.query.filter_by(
        plan_name=current_plan.name if current_plan else 'trial'
    ).order_by(MarketplaceBenchmark.date.desc()).first()
    
    # محاسبه رتبه
    better_than_percentage = calculate_percentile(
        my_analytics.total_messages,
        current_plan.name if current_plan else 'trial'
    )
    
    return render_template('candidate/benchmark.html',
                         my_stats=my_analytics,
                         benchmark=benchmark,
                         better_than=better_than_percentage,
                         current_plan=current_plan)
```

**نمای داشبورد:**
```
╔═══════════════════════════════════════════════════════════╗
║  📊 عملکرد شما در مقایسه با سایر نامزدها                   ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  پلن فعلی شما: رایگان (Trial)                            ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                           ║
║  📬 پیام‌های دریافتی (ماه جاری)                          ║
║  ┌─────────────────────────────────────────────┐         ║
║  │  شما:         45 پیام                       │         ║
║  │  میانگین:    120 پیام                      │         ║
║  │  برترین‌ها:  850 پیام                      │         ║
║  └─────────────────────────────────────────────┘         ║
║                                                           ║
║  📊 رتبه شما: پایین‌تر از 78٪ نامزدها                   ║
║  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░ 22/100                            ║
║                                                           ║
║  💡 نکته: نامزدهایی که پلن "استاندارد" دارند            ║
║      به طور میانگین 5 برابر بیشتر پیام دریافت می‌کنند! ║
║                                                           ║
║  ┌───────────────────────────────────────────────┐       ║
║  │ 🚀 ارتقا به پلن استاندارد                    │       ║
║  │    ✅ ربات نامحدود                            │       ║
║  │    ✅ ارسال انبوه تا 10،000 نفر              │       ║
║  │    ✅ آمار پیشرفته                            │       ║
║  │                                                │       ║
║  │    فقط 500،000 تومان/ماه                     │       ║
║  └───────────────────────────────────────────────┘       ║
╚═══════════════════════════════════════════════════════════╝
```

**مزایا:**
- ✅ FOMO (Fear of Missing Out): "دیگران دارن موفق میشن!"
- ✅ Social Proof: "850 پیام؟ پس میشه!"
- ✅ شفافیت: آمار واقعی
- ✅ بدون فاش کردن هویت رقبا

---

### 4️⃣ سیستم Referral و تخفیف گروهی

```python
class ReferralProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    referred_candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    
    referral_code = db.Column(db.String(20), unique=True)  # AHMAD2024
    
    # پاداش
    reward_type = db.Column(db.String(20))  # discount, free_month, cash
    reward_amount = db.Column(db.Float)  # مثلا 20٪ تخفیف
    reward_claimed = db.Column(db.Boolean, default=False)
    
    # شرایط
    referred_must_purchase = db.Column(db.Boolean, default=True)
    minimum_plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    claimed_at = db.Column(db.DateTime)


# تخفیف گروهی (برای احزاب)
class GroupPurchaseDiscount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # تعداد خریدار
    min_members = db.Column(db.Integer)  # 5, 10, 20
    discount_percentage = db.Column(db.Float)  # 10%, 20%, 30%
    
    # محدودیت زمانی
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    
    description = db.Column(db.String(200))  # "خرید گروهی 10 نفره"
    is_active = db.Column(db.Boolean, default=True)
```

**مثال عملی:**
```
🎁 برنامه معرفی دوستان

شما 3 نامزد دیگر را دعوت کرده‌اید:
├── احمد محمدی → ✅ خرید کرد → شما: 100،000 تومان اعتبار
├── زهرا احمدی → ⏳ ثبت‌نام کرد
└── علی رضایی → ⏳ هنوز ثبت‌نام نکرده

کد اختصاصی شما: AHMAD2024
لینک دعوت: https://election-bot.ir?ref=AHMAD2024

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 تخفیف گروهی ویژه!

اگر 5 نامزد با هم خرید کنید:
✅ 15٪ تخفیف برای همه
✅ 1 ماه اضافه رایگان

اگر 10 نامزد با هم خرید کنید:
✅ 30٪ تخفیف برای همه
✅ 2 ماه اضافه رایگان
✅ پنل مدیریت حزبی رایگان
```

---

## 🌟 بخش سوم: سیستم تعامل VIP با نماینده

### 5️⃣ برنامه "شهروند ماه" (Citizen of the Month)

**ایده شما عالی بود!** بهبودش می‌دم:

```python
class MonthlyTopCitizen(db.Model):
    """کاربران برتر هر ماه"""
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    citizen_profile_id = db.Column(db.Integer, db.ForeignKey('citizen_profile.id'))
    
    # دوره
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)  # 1-12
    
    # رتبه
    rank = db.Column(db.Integer)  # 1, 2, 3, ...
    total_points = db.Column(db.Integer)
    
    # امتیازات ویژه
    vip_status = db.Column(db.String(20))  # gold, silver, bronze
    rewards_json = db.Column(db.JSON)  # جوایز اختصاصی
    
    # آیا جایزه دریافت شد؟
    reward_claimed = db.Column(db.Boolean, default=False)
    claimed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VIPInteraction(db.Model):
    """تعامل VIP با نماینده"""
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    citizen_telegram_id = db.Column(db.String(50))
    
    # نوع تعامل
    interaction_type = db.Column(db.String(30))
    # live_qa: سوال و جواب زنده
    # video_call: ویدیو کال
    # priority_response: پاسخ اولویت‌دار
    # exclusive_event: دعوت به رویداد ویژه
    
    # جزئیات
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # زمان‌بندی
    scheduled_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer, default=30)
    
    # وضعیت
    status = db.Column(db.String(20), default='scheduled')
    # scheduled, completed, cancelled, no_show
    
    # لینک/اطلاعات
    meeting_link = db.Column(db.String(500))  # لینک Zoom/Google Meet
    notes = db.Column(db.Text)  # یادداشت‌های نماینده
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
```

**فلو عملیاتی:**

```
📅 روز 1 ماه:
├── سیستم خودکار رتبه‌بندی می‌کند
├── 3 نفر برتر انتخاب می‌شوند
└── پیام تبریک ارسال می‌شود

💬 پیام به شهروند برتر:
┌───────────────────────────────────────────┐
│ 🎉 تبریک! شما "شهروند ماه" شدید!         │
│                                           │
│ 🏆 رتبه: 1 از 2،450 شهروند               │
│ ⭐ امتیاز: 1،250 امتیاز                  │
│                                           │
│ 🎁 جوایز شما:                             │
│ ✅ جلسه ویدیویی 30 دقیقه‌ای با نماینده   │
│ ✅ نشان طلایی در پروفایل                  │
│ ✅ اولویت در پاسخ‌گویی (24 ساعت)         │
│ ✅ دعوت به رویداد ویژه "شام با نماینده" │
│                                           │
│ 📅 برای رزرو وقت ملاقات: /book_vip_meet │
└───────────────────────────────────────────┘

📨 پیام به نماینده در پنل:
┌───────────────────────────────────────────┐
│ 🌟 شهروندان برتر ماه جاری:                │
│                                           │
│ 🥇 علی محمدی (1،250 امتیاز)              │
│    📞 جلسه را رزرو کنید                   │
│    [زمان‌بندی جلسه]                      │
│                                           │
│ 🥈 فاطمه احمدی (980 امتیاز)               │
│ 🥉 حسین رضایی (850 امتیاز)                │
└───────────────────────────────────────────┘
```

---

### 6️⃣ رویدادهای زنده (Live Events)

```python
class LiveEvent(db.Model):
    """رویدادهای زنده نماینده"""
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    
    # مشخصات
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(30))
    # live_qa: سوال و جواب زنده
    # town_hall: جلسه عمومی
    # webinar: وبینار
    # ama: Ask Me Anything
    
    # زمان
    starts_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    timezone = db.Column(db.String(50), default='Asia/Tehran')
    
    # پلتفرم
    platform = db.Column(db.String(30))  # telegram_live, zoom, youtube_live
    stream_url = db.Column(db.String(500))
    chat_enabled = db.Column(db.Boolean, default=True)
    
    # محدودیت
    max_participants = db.Column(db.Integer)  # null = نامحدود
    vip_only = db.Column(db.Boolean, default=False)
    min_points_required = db.Column(db.Integer, default=0)
    
    # وضعیت
    status = db.Column(db.String(20), default='scheduled')
    # scheduled, live, completed, cancelled
    
    # آمار
    registered_count = db.Column(db.Integer, default=0)
    attended_count = db.Column(db.Integer, default=0)
    questions_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EventRegistration(db.Model):
    """ثبت‌نام در رویداد"""
    id = db.Column(db.Integer, primary_key=True)
    
    event_id = db.Column(db.Integer, db.ForeignKey('live_event.id'))
    citizen_telegram_id = db.Column(db.String(50))
    
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)
    
    # سوالات شهروند
    submitted_question = db.Column(db.Text)
    question_answered = db.Column(db.Boolean, default=False)


# در ربات:
async def handle_live_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش رویدادهای زنده"""
    upcoming_events = LiveEvent.query.filter(
        LiveEvent.starts_at > datetime.utcnow(),
        LiveEvent.status == 'scheduled'
    ).order_by(LiveEvent.starts_at).limit(5).all()
    
    if not upcoming_events:
        await update.message.reply_text("🔴 در حال حاضر رویداد زنده‌ای برنامه‌ریزی نشده")
        return
    
    text = "📅 *رویدادهای زنده آینده*\n\n"
    
    for event in upcoming_events:
        jalali_date = gregorian_to_jalali(event.starts_at)
        text += f"🎯 *{event.title}*\n"
        text += f"📆 {jalali_date}\n"
        text += f"⏱ مدت: {event.duration_minutes} دقیقه\n"
        
        if event.vip_only:
            text += "👑 *ویژه اعضای VIP*\n"
        
        if event.registered_count < event.max_participants:
            text += f"✅ ظرفیت: {event.registered_count}/{event.max_participants}\n"
            text += f"/register_{event.id}\n"
        else:
            text += "❌ *ظرفیت تکمیل*\n"
        
        text += "\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')
```

---

## 📈 بخش چهارم: گیمیفیکیشن پیشرفته

### 7️⃣ سیستم Achievements (دستاوردها)

```python
class Achievement(db.Model):
    """دستاوردهای قابل کسب"""
    id = db.Column(db.Integer, primary_key=True)
    
    # مشخصات
    name = db.Column(db.String(100), unique=True)
    title_fa = db.Column(db.String(100))
    description = db.Column(db.Text)
    icon = db.Column(db.String(10))  # emoji
    
    # سطح دشواری
    rarity = db.Column(db.String(20))  # common, rare, epic, legendary
    difficulty = db.Column(db.Integer)  # 1-10
    
    # شرایط کسب
    conditions_json = db.Column(db.JSON)
    # مثال: {"contributions": 10, "votes": 50, "comments": 20}
    
    # پاداش
    points_reward = db.Column(db.Integer, default=0)
    badge_reward = db.Column(db.String(50))  # نشان ویژه
    
    # آمار
    total_earned = db.Column(db.Integer, default=0)
    earn_percentage = db.Column(db.Float)  # چند درصد کاربران کسب کردن
    
    is_secret = db.Column(db.Boolean, default=False)  # مخفی تا کسب
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# دستاوردهای پیشنهادی:
achievements_list = [
    {
        "name": "first_steps",
        "title": "🌱 اولین قدم‌ها",
        "description": "اولین ایده خود را ثبت کنید",
        "rarity": "common",
        "conditions": {"contributions": 1},
        "points": 10
    },
    {
        "name": "voice_of_people",
        "title": "📢 صدای مردم",
        "description": "10 ایده ثبت کنید",
        "rarity": "rare",
        "conditions": {"contributions": 10},
        "points": 100
    },
    {
        "name": "democratic_activist",
        "title": "🗳️ فعال دموکراسی",
        "description": "در 50 نظرسنجی شرکت کنید",
        "rarity": "epic",
        "conditions": {"poll_votes": 50},
        "points": 200
    },
    {
        "name": "community_leader",
        "title": "👑 رهبر اجتماع",
        "description": "به رتبه 1 صدرنشین شوید",
        "rarity": "legendary",
        "conditions": {"rank": 1},
        "points": 500
    },
    {
        "name": "night_owl",
        "title": "🦉 جغد شب",
        "description": "ساعت 2 بامداد ایده ثبت کنید",
        "rarity": "rare",
        "conditions": {"contribution_at_hour": 2},
        "points": 50,
        "is_secret": True
    }
]
```

---

## 🎯 بخش پنجم: ویژگی‌های منحصر به فرد

### 8️⃣ سیستم "نبض جامعه" (Society Pulse)

**ایده جدید:** نمایش زنده احساسات مردم

```python
class SocietyPulse(db.Model):
    """نبض لحظه‌ای افکار عمومی"""
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    date = db.Column(db.Date, default=datetime.utcnow().date)
    
    # آنالیز احساسات
    positive_percentage = db.Column(db.Float, default=0)
    neutral_percentage = db.Column(db.Float, default=0)
    negative_percentage = db.Column(db.Float, default=0)
    
    # ترندهای روز
    top_keywords_json = db.Column(db.JSON)  # ["ترافیک", "بهداشت", "اقتصاد"]
    hot_topics_json = db.Column(db.JSON)
    
    # مقایسه با گذشته
    trend_direction = db.Column(db.String(10))  # up, down, stable
    change_percentage = db.Column(db.Float)
    
    # تعداد نمونه
    sample_size = db.Column(db.Integer)  # چند نظر تحلیل شده


# تابع تحلیل (استفاده از هوش مصنوعی)
def analyze_society_pulse(candidate_id):
    """
    آنالیز احساسات از:
    - کامنت‌ها
    - رای‌ها
    - پیام‌های ارسالی
    - مشارکت‌های شهروندی
    """
    contributions = CitizenContribution.query.filter_by(
        candidate_id=candidate_id
    ).filter(
        CitizenContribution.created_at >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    comments = ContributionComment.query.join(CitizenContribution).filter(
        CitizenContribution.candidate_id == candidate_id,
        ContributionComment.created_at >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    # آنالیز ساده (بدون AI):
    positive = 0
    negative = 0
    neutral = 0
    
    keywords = {}
    
    for contrib in contributions:
        # مثلاً اگر رای‌های مثبت بیشتر باشه = مثبت
        if contrib.votes_count > 5:
            positive += 1
        elif contrib.votes_count < 0:
            negative += 1
        else:
            neutral += 1
        
        # استخراج کلمات کلیدی
        words = contrib.title.split() + contrib.description.split()
        for word in words:
            if len(word) > 3:  # کلمات بلندتر از 3 حرف
                keywords[word] = keywords.get(word, 0) + 1
    
    total = positive + negative + neutral
    
    pulse = SocietyPulse(
        candidate_id=candidate_id,
        positive_percentage=round(positive/total*100, 1) if total > 0 else 0,
        negative_percentage=round(negative/total*100, 1) if total > 0 else 0,
        neutral_percentage=round(neutral/total*100, 1) if total > 0 else 0,
        top_keywords_json=sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10],
        sample_size=total
    )
    
    db.session.add(pulse)
    db.session.commit()
    
    return pulse
```

**نمایش در داشبورد:**
```
╔═══════════════════════════════════════════════╗
║  🌡️ نبض جامعه - هفته جاری                    ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  😊 احساسات مثبت:  67% ▲ +5%                 ║
║  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░                       ║
║                                               ║
║  😐 خنثی:           25%                      ║
║  ▓▓▓▓▓░░░░░░░░░░░░░░░                       ║
║                                               ║
║  😟 منفی:            8% ▼ -2%                ║
║  ▓▓░░░░░░░░░░░░░░░░░░░                       ║
║                                               ║
║  📊 براساس 234 نظر شهروندان                  ║
║                                               ║
║  🔥 داغ‌ترین موضوعات:                         ║
║  1️⃣ ترافیک (42 اشاره)                       ║
║  2️⃣ بهداشت (38 اشاره)                       ║
║  3️⃣ فضای سبز (29 اشاره)                      ║
║  4️⃣ اقتصاد (21 اشاره)                        ║
║  5️⃣ آموزش (18 اشاره)                        ║
╚═══════════════════════════════════════════════╝
```

---

### 9️⃣ سیستم "چالش‌های هفتگی" (Weekly Challenges)

```python
class WeeklyChallenge(db.Model):
    """چالش‌های هفتگی برای شهروندان"""
    id = db.Column(db.Integer, primary_key=True)
    
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    
    # مشخصات
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(10))
    
    # زمان
    week_number = db.Column(db.Integer)  # هفته چندم سال
    year = db.Column(db.Integer)
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    
    # اهداف
    goal_type = db.Column(db.String(30))
    # submit_ideas: ثبت X ایده
    # collect_votes: جمع‌آوری X رای
    # engage_discussion: X کامنت بگذار
    # invite_friends: X نفر دعوت کن
    
    goal_target = db.Column(db.Integer)  # هدف عددی
    
    # پاداش
    reward_points = db.Column(db.Integer, default=100)
    reward_badge = db.Column(db.String(50))
    bonus_reward_json = db.Column(db.JSON)  # پاداش‌های اضافی
    
    # آمار
    participants_count = db.Column(db.Integer, default=0)
    completed_count = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# مثال‌های چالش:
weekly_challenges = [
    {
        "week": 1,
        "title": "🌟 هفته ایده‌پردازی",
        "description": "این هفته 3 ایده برای بهبود شهرتان ثبت کنید",
        "goal_type": "submit_ideas",
        "goal_target": 3,
        "reward_points": 150,
        "reward_badge": "idea_generator"
    },
    {
        "week": 2,
        "title": "🗳️ هفته مشارکت",
        "description": "در 10 نظرسنجی شرکت کنید",
        "goal_type": "poll_participation",
        "goal_target": 10,
        "reward_points": 100
    },
    {
        "week": 3,
        "title": "💬 هفته گفتگو",
        "description": "زیر ایده‌های دیگران 15 کامنت بگذارید",
        "goal_type": "engage_discussion",
        "goal_target": 15,
        "reward_points": 120
    },
    {
        "week": 4,
        "title": "👥 هفته دعوت",
        "description": "5 دوست جدید را به پلتفرم دعوت کنید",
        "goal_type": "invite_friends",
        "goal_target": 5,
        "reward_points": 200,
        "bonus_reward": {"free_vip_week": True}
    }
]
```

---

## 📊 جمع‌بندی: نقشه راه پیشنهادی

### اولویت‌بندی توسعه:

```
🏆 فاز 1 (ماه اول): جذب نامزدهای جدید
├── ✅ سیستم benchmark رقابتی
├── ✅ Trial 14 روزه
├── ✅ داشبورد مقایسه‌ای
└── ✅ سیستم referral

💰 فاز 2 (ماه دوم): افزایش درآمد
├── ✅ پنل احزاب سیاسی
├── ✅ تخفیف گروهی
├── ✅ پلن‌های حزبی (با تخفیف 30%)
└── ✅ ائتلاف‌های انتخاباتی

🌟 فاز 3 (ماه سوم): افزایش engagement
├── ✅ سیستم VIP (شهروند ماه)
├── ✅ رویدادهای زنده
├── ✅ سیستم achievements
└── ✅ چالش‌های هفتگی

📈 فاز 4 (ماه چهارم): ویژگی‌های منحصربه‌فرد
├── ✅ نبض جامعه (آنالیز احساسات)
├── ✅ پیش‌بینی آرا (AI-powered)
├── ✅ نقشه حرارتی مسائل شهر
└── ✅ شبکه اجتماعی نامزدها
```

---

## 💎 ویژگی‌های پیشنهادی اضافی

### 10. سیستم "همکاری نامزدها" (Candidate Network)
- نامزدها می‌توانند با هم همکاری کنند
- اشتراک‌گذاری محتوا
- co-endorsement (حمایت متقابل)

### 11. "بازار ایده" (Idea Marketplace)
- نامزدها می‌توانند ایده‌های خوب را از یکدیگر بخرند!
- مثلاً نامزد A ایده خوبی دارد برای کاهش ترافیک
- نامزد B (شهر دیگر) می‌خرد و اجرا می‌کند

### 12. API عمومی
- دیگر پلتفرم‌ها می‌توانند وصل شوند
- افزایش دسترسی‌پذیری
- درآمد از API subscription

---

## 💵 مدل درآمدی پیشنهادی

```
📦 پلن‌های فعلی (تک‌نامزد):
├── Trial (14 روز رایگان)
├── Basic (300K/ماه)
├── Standard (500K/ماه)
└── Premium (1M/ماه)

🏛️ پلن‌های جدید (حزبی):
├── حزب کوچک (5-10 نامزد): 2M/ماه (تخفیف 30%)
├── حزب متوسط (11-30 نامزد): 5M/ماه (تخفیف 35%)
└── حزب بزرگ (31+ نامزد): 10M/ماه (تخفیف 40%)

🤝 ائتلاف (موقت):
├── ائتلاف 2-5 نامزد: 1.5M (برای کل دوره انتخابات)
└── ائتلاف 6+ نامزد: 3M

💎 امکانات VIP (addon):
├── رویدادهای زنده: +200K/ماه
├── آنالیز AI: +300K/ماه
└── پشتیبانی اختصاصی: +150K/ماه
```

---

## ✅ چک‌لیست اولویت‌ها

**فوری (این هفته):**
- [ ] اضافه کردن benchmark dashboard
- [ ] فیکس responsive بودن تمام صفحات
- [ ] Trial 14 روزه با محدودیت

**کوتاه‌مدت (این ماه):**
- [ ] پنل حزب (database models)
- [ ] سیستم referral code
- [ ] VIP citizen of month

**میان‌مدت (3 ماه):**
- [ ] رویدادهای زنده
- [ ] Achievements system
- [ ] نبض جامعه

**بلند‌مدت (6 ماه):**
- [ ] AI predictions
- [ ] Idea marketplace
- [ ] Public API

---

**آماده برای شروع هستم! از کدوم قسمت شروع کنیم؟** 🚀
