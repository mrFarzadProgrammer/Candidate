# 📊 تحلیل کامل سیستم و پیشنهادات توسعه

## 🎯 وضعیت فعلی سیستم

### ✅ امکانات موجود:

#### 1. **پنل ادمین**
- ✅ مدیریت کاندیداها (ایجاد، ویرایش، حذف)
- ✅ مدیریت پلن‌ها
- ✅ راه‌اندازی بات برای هر کاندید
- ✅ اهدای پلن رایگان
- ✅ مدیریت تیکت‌ها (تایید/رد پرداخت‌ها)
- ✅ نمایش لیست تمام کاندیداها با بات‌هایشان

#### 2. **پنل کاندید**
- ✅ مدیریت پروفایل شخصی
- ✅ مدیریت رزومه
- ✅ مدیریت برنامه‌های انتخاباتی
- ✅ مدیریت شعارها
- ✅ مدیریت دفاتر و ستادها (با نقشه)
- ✅ مشاهده پیام‌های مردم
- ✅ ارسال پیام انبوه (broadcast)
- ✅ زمان‌بندی پست‌ها
- ✅ داشبورد آمار و تحلیل
- ✅ سیستم نظرسنجی (polls)
- ✅ پاسخ‌گوی خودکار
- ✅ مدیریت کانال‌ها
- ✅ خرید پلن با پرداخت دستی
- ✅ مشاهده تیکت‌ها

#### 3. **بات تلگرام**
- ✅ نمایش اطلاعات کاندید
- ✅ نمایش رزومه
- ✅ نمایش برنامه‌ها
- ✅ نمایش ستادها
- ✅ ارسال پیام به کاندید
- ✅ ثبت تعاملات کاربر
- ✅ دکمه‌های inline

---

## 🚨 نقاط ضعف و کمبودها

### 1️⃣ **امنیت و احراز هویت**

#### 🔴 مشکلات فعلی:
- ❌ عدم Two-Factor Authentication (2FA)
- ❌ عدم تایید ایمیل/موبایل
- ❌ عدم Session Management حرفه‌ای
- ❌ عدم Rate Limiting
- ❌ لاگ ورود/خروج کاربران وجود ندارد

#### 💡 راه‌حل‌های پیشنهادی:
```python
# ✨ پیشنهاد 1: Two-Factor Authentication
class TwoFactorAuth(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    secret_key = db.Column(db.String(32))  # TOTP secret
    backup_codes = db.Column(db.JSON)  # کدهای پشتیبان
    is_enabled = db.Column(db.Boolean, default=False)

# ✨ پیشنهاد 2: Login History
class LoginHistory(db.Model):
    user_id = db.Column(db.Integer)
    user_type = db.Column(db.String(20))  # candidate/admin
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    login_time = db.Column(db.DateTime)
    logout_time = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # success/failed
```

---

### 2️⃣ **سیستم ارتباط مردمی (CRM)**

#### 🔴 مشکلات فعلی:
- ❌ فقط پیام ساده (بدون دسته‌بندی)
- ❌ عدم سیستم تیکتینگ داخلی برای پیام‌ها
- ❌ عدم اولویت‌بندی پیام‌ها
- ❌ عدم تگ‌گذاری و برچسب‌زنی
- ❌ عدم پیگیری وضعیت پیام
- ❌ عدم Chatbot هوشمند

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 3: سیستم CRM پیشرفته

class MessageCategory(db.Model):
    """دسته‌بندی پیام‌ها"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # شکایت، پیشنهاد، سوال، درخواست
    color = db.Column(db.String(20))
    icon = db.Column(db.String(50))

class MessageTag(db.Model):
    """تگ‌های پیام"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))  # عاجل، مهم، پیگیری، حل‌شده

class MessageStatus(db.Model):
    """وضعیت پیام"""
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    WAITING = 'waiting'
    RESOLVED = 'resolved'
    CLOSED = 'closed'

class MessageAssignment(db.Model):
    """ارجاع پیام به کارمند"""
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'))
    staff_id = db.Column(db.Integer)  # کارمند ستاد
    assigned_at = db.Column(db.DateTime)
    assigned_by = db.Column(db.Integer)  # کاندید یا مدیر ستاد

class MessageNote(db.Model):
    """یادداشت‌های داخلی روی پیام"""
    message_id = db.Column(db.Integer)
    note_text = db.Column(db.Text)
    created_by = db.Column(db.Integer)
    is_private = db.Column(db.Boolean)  # فقط برای تیم
```

---

### 3️⃣ **مدیریت تیم و کارمندان**

#### 🔴 مشکلات فعلی:
- ❌ فقط یک کاندید به پنل دسترسی دارد
- ❌ عدم نقش‌های مختلف (Role-Based Access)
- ❌ عدم سیستم تیم و کارمندان ستاد
- ❌ عدم لاگ فعالیت‌ها

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 4: سیستم تیم و نقش‌ها

class Role(db.Model):
    """نقش‌های کاربری"""
    OWNER = 'owner'  # کاندید
    MANAGER = 'manager'  # مدیر ستاد
    STAFF = 'staff'  # کارمند
    SOCIAL_MEDIA = 'social_media'  # مدیر شبکه‌های اجتماعی
    CONTENT = 'content'  # تولید محتوا
    SUPPORT = 'support'  # پشتیبانی

class TeamMember(db.Model):
    """اعضای تیم کاندید"""
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(50))
    password = db.Column(db.String(200))
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(50))  # owner, manager, staff, ...
    permissions = db.Column(db.JSON)  # {"can_edit_profile": True, "can_send_broadcast": False}
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime)

class ActivityLog(db.Model):
    """لاگ تمام فعالیت‌ها"""
    user_id = db.Column(db.Integer)
    user_type = db.Column(db.String(20))  # candidate, team_member, admin
    action = db.Column(db.String(100))  # 'created_program', 'sent_broadcast'
    target_type = db.Column(db.String(50))  # 'program', 'message', 'poll'
    target_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)
```

---

### 4️⃣ **سیستم مالی و حسابداری**

#### 🔴 مشکلات فعلی:
- ❌ فقط پرداخت دستی (کارت به کارت/شبا)
- ❌ عدم فاکتور خودکار
- ❌ عدم سیستم کد تخفیف
- ❌ عدم گزارش مالی جامع
- ❌ عدم Refund
- ❌ عدم ارتقای خودکار پلن

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 5: سیستم مالی پیشرفته

class Invoice(db.Model):
    """فاکتور خودکار"""
    invoice_number = db.Column(db.String(20))  # INV-2025-001
    candidate_id = db.Column(db.Integer)
    plan_id = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    tax = db.Column(db.Integer)  # مالیات
    discount = db.Column(db.Integer)  # تخفیف
    final_amount = db.Column(db.Integer)
    status = db.Column(db.String(20))  # pending, paid, cancelled
    issued_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    pdf_path = db.Column(db.String(300))  # مسیر PDF فاکتور

class DiscountCode(db.Model):
    """کد تخفیف"""
    code = db.Column(db.String(20), unique=True)  # SUMMER2025
    discount_type = db.Column(db.String(20))  # percentage, fixed
    discount_value = db.Column(db.Integer)  # 20 (%) or 50000 (تومان)
    max_uses = db.Column(db.Integer)  # تعداد استفاده مجاز
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    applicable_plans = db.Column(db.JSON)  # [1, 2, 3] - ID پلن‌ها
    is_active = db.Column(db.Boolean)

class Refund(db.Model):
    """استرداد وجه"""
    payment_id = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20))  # requested, approved, rejected, completed
    requested_at = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime)

class Commission(db.Model):
    """کمیسیون فروش (اگر سیستم همکاری در فروش دارید)"""
    sale_id = db.Column(db.Integer)
    affiliate_id = db.Column(db.Integer)
    commission_rate = db.Column(db.Float)  # 10%
    commission_amount = db.Column(db.Integer)
    status = db.Column(db.String(20))  # pending, paid
```

---

### 5️⃣ **تحلیل داده و گزارش‌گیری**

#### 🔴 مشکلات فعلی:
- ❌ آمار ساده (فقط تعداد)
- ❌ عدم نمودار‌های پیشرفته
- ❌ عدم مقایسه دوره‌ای
- ❌ عدم پیش‌بینی (Prediction)
- ❌ عدم صادرات Excel/PDF
- ❌ عدم Real-time Analytics

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 6: سیستم آمار و تحلیل پیشرفته

class AdvancedAnalytics(db.Model):
    """آمار پیشرفته"""
    candidate_id = db.Column(db.Integer)
    date = db.Column(db.Date)
    
    # آمار بات
    total_bot_users = db.Column(db.Integer)
    new_bot_users = db.Column(db.Integer)
    active_users = db.Column(db.Integer)  # فعال در 24 ساعت
    churn_rate = db.Column(db.Float)  # نرخ ترک
    
    # آمار تعاملات
    button_clicks = db.Column(db.JSON)  # {"resume": 50, "programs": 30}
    messages_received = db.Column(db.Integer)
    messages_response_time = db.Column(db.Float)  # میانگین زمان پاسخ (دقیقه)
    
    # آمار محتوا
    most_viewed_program = db.Column(db.Integer)
    most_visited_headquarters = db.Column(db.Integer)
    
    # آمار پیام انبوه
    broadcasts_sent = db.Column(db.Integer)
    broadcast_open_rate = db.Column(db.Float)  # نرخ بازشدن
    
    # آمار نظرسنجی
    polls_created = db.Column(db.Integer)
    polls_participation = db.Column(db.Float)  # نرخ مشارکت
    
    # دموگرافیک
    user_demographics = db.Column(db.JSON)  # {"age_groups": {...}, "genders": {...}}
    user_locations = db.Column(db.JSON)  # شهرها

class Report(db.Model):
    """گزارش‌های خودکار"""
    report_type = db.Column(db.String(50))  # daily, weekly, monthly
    candidate_id = db.Column(db.Integer)
    generated_at = db.Column(db.DateTime)
    pdf_path = db.Column(db.String(300))
    excel_path = db.Column(db.String(300))
```

---

### 6️⃣ **محتوای چندرسانه‌ای**

#### 🔴 مشکلات فعلی:
- ❌ فقط تصویر و ویس
- ❌ عدم گالری تصاویر
- ❌ عدم ویدیو
- ❌ عدم فایل PDF
- ❌ عدم لایو استریم

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 7: سیستم مدیریت محتوا

class MediaGallery(db.Model):
    """گالری تصاویر"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    images = db.Column(db.JSON)  # لیست مسیر تصاویر
    album_type = db.Column(db.String(50))  # campaign, events, meetings
    created_at = db.Column(db.DateTime)

class VideoContent(db.Model):
    """ویدیوها"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500))  # لینک آپارات/یوتیوب
    video_file = db.Column(db.String(300))  # یا فایل محلی
    thumbnail = db.Column(db.String(300))
    duration = db.Column(db.Integer)  # ثانیه
    views_count = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))  # speech, interview, ad

class Document(db.Model):
    """اسناد و فایل‌های PDF"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    file_path = db.Column(db.String(300))
    file_type = db.Column(db.String(20))  # pdf, doc, ppt
    file_size = db.Column(db.Integer)
    downloads_count = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))  # manifesto, biography, achievements

class LiveStream(db.Model):
    """پخش زنده"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    stream_url = db.Column(db.String(500))
    scheduled_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # scheduled, live, ended
    viewers_count = db.Column(db.Integer, default=0)
```

---

### 7️⃣ **ارتباطات و نوتیفیکیشن**

#### 🔴 مشکلات فعلی:
- ❌ فقط تلگرام
- ❌ عدم ایمیل نوتیفیکیشن
- ❌ عدم SMS
- ❌ عدم Push Notification
- ❌ عدم خبرنامه

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 8: سیستم ارتباطات چندکاناله

class EmailCampaign(db.Model):
    """کمپین ایمیلی"""
    candidate_id = db.Column(db.Integer)
    subject = db.Column(db.String(200))
    body_html = db.Column(db.Text)
    recipients_list = db.Column(db.JSON)  # لیست ایمیل‌ها
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    open_rate = db.Column(db.Float)
    click_rate = db.Column(db.Float)

class SMSCampaign(db.Model):
    """کمپین پیامکی"""
    candidate_id = db.Column(db.Integer)
    message_text = db.Column(db.String(500))
    recipients_list = db.Column(db.JSON)
    sent_count = db.Column(db.Integer)
    delivered_count = db.Column(db.Integer)
    cost = db.Column(db.Integer)

class Newsletter(db.Model):
    """خبرنامه"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    subscribers_count = db.Column(db.Integer)
    published_at = db.Column(db.DateTime)
```

---

### 8️⃣ **مدیریت رویدادها و جلسات**

#### 🔴 مشکلات فعلی:
- ❌ عدم سیستم رویداد
- ❌ عدم تقویم
- ❌ عدم ثبت‌نام در رویدادها
- ❌ عدم یادآوری خودکار

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 9: سیستم مدیریت رویداد

class Event(db.Model):
    """رویدادها و جلسات"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))  # meeting, rally, debate, townhall
    location = db.Column(db.String(300))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    max_capacity = db.Column(db.Integer)
    registered_count = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20))  # scheduled, ongoing, completed, cancelled

class EventRegistration(db.Model):
    """ثبت‌نام در رویداد"""
    event_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    registered_at = db.Column(db.DateTime)
    attended = db.Column(db.Boolean, default=False)
    qr_code = db.Column(db.String(100))  # برای check-in

class Calendar(db.Model):
    """تقویم فعالیت‌ها"""
    candidate_id = db.Column(db.Integer)
    date = db.Column(db.Date)
    events = db.Column(db.JSON)  # لیست رویدادهای روز
```

---

### 9️⃣ **اتوماسیون و هوش مصنوعی**

#### 🔴 مشکلات فعلی:
- ❌ پاسخ خودکار ساده (فقط keyword)
- ❌ عدم Chatbot هوشمند
- ❌ عدم تحلیل احساسات
- ❌ عدم تولید محتوای خودکار
- ❌ عدم توصیه‌گر هوشمند

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 10: هوش مصنوعی پیشرفته

class AIConversation(db.Model):
    """مکالمات AI"""
    user_telegram_id = db.Column(db.BigInteger)
    candidate_id = db.Column(db.Integer)
    messages = db.Column(db.JSON)  # تاریخچه مکالمه
    context = db.Column(db.JSON)  # زمینه مکالمه
    sentiment = db.Column(db.String(20))  # positive, neutral, negative
    topics = db.Column(db.JSON)  # موضوعات مطرح شده

class ContentSuggestion(db.Model):
    """پیشنهاد محتوا توسط AI"""
    candidate_id = db.Column(db.Integer)
    content_type = db.Column(db.String(50))  # post, program, slogan
    suggested_text = db.Column(db.Text)
    keywords = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)
    used = db.Column(db.Boolean, default=False)

class SmartRecommendation(db.Model):
    """توصیه‌های هوشمند"""
    candidate_id = db.Column(db.Integer)
    recommendation_type = db.Column(db.String(50))  # best_time_to_post, target_audience
    recommendation_text = db.Column(db.Text)
    confidence_score = db.Column(db.Float)  # میزان اطمینان
    applied = db.Column(db.Boolean)
```

---

### 🔟 **شبکه‌های اجتماعی**

#### 🔴 مشکلات فعلی:
- ❌ فقط تلگرام
- ❌ عدم اتصال به اینستاگرام
- ❌ عدم اتصال به توییتر
- ❌ عدم پست همزمان
- ❌ عدم آمار شبکه‌های اجتماعی

#### 💡 راه‌حل‌های پیشنهادی:

```python
# ✨ پیشنهاد 11: مدیریت چندکاناله

class SocialAccount(db.Model):
    """حساب‌های شبکه اجتماعی"""
    candidate_id = db.Column(db.Integer)
    platform = db.Column(db.String(50))  # telegram, instagram, twitter, facebook
    account_id = db.Column(db.String(100))
    account_name = db.Column(db.String(100))
    access_token = db.Column(db.String(500))
    is_active = db.Column(db.Boolean)
    connected_at = db.Column(db.DateTime)

class CrossPost(db.Model):
    """پست همزمان در چند پلتفرم"""
    candidate_id = db.Column(db.Integer)
    content = db.Column(db.Text)
    media_files = db.Column(db.JSON)
    platforms = db.Column(db.JSON)  # ["telegram", "instagram", "twitter"]
    scheduled_at = db.Column(db.DateTime)
    status = db.Column(db.String(20))

class SocialAnalytics(db.Model):
    """آمار شبکه‌های اجتماعی"""
    candidate_id = db.Column(db.Integer)
    platform = db.Column(db.String(50))
    date = db.Column(db.Date)
    followers_count = db.Column(db.Integer)
    engagement_rate = db.Column(db.Float)
    reach = db.Column(db.Integer)
    impressions = db.Column(db.Integer)
```

---

## 🎯 پیشنهادات ویژه برای مشارکت مردمی

### 💡 فیچر 1: **سیستم حمایت مردمی (Crowdsourcing)**

```python
class CitizenContribution(db.Model):
    """مشارکت مردمی"""
    candidate_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    contribution_type = db.Column(db.String(50))
    # انواع مشارکت:
    # - 'idea': پیشنهاد ایده
    # - 'report': گزارش مشکل محله
    # - 'volunteer': داوطلبی
    # - 'suggestion': پیشنهاد برنامه
    # - 'question': سوال از کاندید
    # - 'poll_vote': شرکت در نظرسنجی
    
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # آموزش، بهداشت، ترافیک، ...
    priority = db.Column(db.String(20))  # low, medium, high, urgent
    location = db.Column(db.String(300))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    images = db.Column(db.JSON)  # تصاویر ضمیمه
    status = db.Column(db.String(50))  # submitted, under_review, accepted, implemented, rejected
    votes = db.Column(db.Integer, default=0)  # رای مردمی
    comments_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    implemented_at = db.Column(db.DateTime)
    
class ContributionVote(db.Model):
    """رای به پیشنهادات مردم"""
    contribution_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    vote_type = db.Column(db.String(10))  # upvote, downvote
    voted_at = db.Column(db.DateTime)

class ContributionComment(db.Model):
    """نظرات روی پیشنهادات"""
    contribution_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    comment_text = db.Column(db.Text)
    parent_comment_id = db.Column(db.Integer)  # برای reply
    created_at = db.Column(db.DateTime)
```

#### فلوی کاربری:
```
مردم در بات:
1. دکمه "💡 مشارکت من" → انتخاب نوع
2. "گزارش مشکل محله" → ارسال توضیح + عکس + لوکیشن
3. سیستم ذخیره → نمایش در پنل کاندید
4. کاندید بررسی → تایید/رد → پاسخ
5. اگر پذیرفته شد → مردم vote می‌کنند
6. پیشنهادهای پراهمیت → در برنامه‌های کاندید
```

---

### 💡 فیچر 2: **داشبورد مردمی (Citizen Dashboard)**

```python
class CitizenProfile(db.Model):
    """پروفایل شهروند"""
    telegram_id = db.Column(db.BigInteger, unique=True)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    neighborhood = db.Column(db.String(100))
    
    # امتیازات و گیمیفیکیشن
    contribution_points = db.Column(db.Integer, default=0)
    badges = db.Column(db.JSON)  # ["active_citizen", "top_contributor"]
    level = db.Column(db.Integer, default=1)
    
    # آمار مشارکت
    ideas_submitted = db.Column(db.Integer, default=0)
    problems_reported = db.Column(db.Integer, default=0)
    polls_voted = db.Column(db.Integer, default=0)
    events_attended = db.Column(db.Integer, default=0)

class Leaderboard(db.Model):
    """تابلوی رتبه‌بندی"""
    candidate_id = db.Column(db.Integer)
    period = db.Column(db.String(20))  # weekly, monthly, alltime
    top_contributors = db.Column(db.JSON)  # [{user_id, points, rank}, ...]
    updated_at = db.Column(db.DateTime)
```

#### فیچرها:
- 🏆 رتبه‌بندی فعال‌ترین شهروندان
- 🎖️ نشان‌های افتخار (شهروند فعال، گزارشگر نمونه، ...)
- 📊 آمار شخصی (چند پیشنهاد دادم، چند رای گرفتم)
- 🎁 جوایز برای برترین‌ها

---

### 💡 فیچر 3: **بودجه مشارکتی (Participatory Budgeting)**

```python
class BudgetProject(db.Model):
    """پروژه‌های بودجه مشارکتی"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    estimated_cost = db.Column(db.Integer)
    location = db.Column(db.String(300))
    category = db.Column(db.String(50))  # پارک، مدرسه، کتابخانه، ...
    images = db.Column(db.JSON)
    
    # مراحل
    phase = db.Column(db.String(50))  # proposal, voting, approved, implementation
    voting_start = db.Column(db.DateTime)
    voting_end = db.Column(db.DateTime)
    votes_count = db.Column(db.Integer, default=0)
    voters_count = db.Column(db.Integer, default=0)
    
    # پیشرفت
    is_approved = db.Column(db.Boolean, default=False)
    implementation_progress = db.Column(db.Integer, default=0)  # درصد پیشرفت
    completion_date = db.Column(db.DateTime)

class BudgetVote(db.Model):
    """رای به پروژه‌ها"""
    project_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    voted_at = db.Column(db.DateTime)
```

#### فلو:
```
1. کاندید چند پروژه پیشنهادی می‌دهد (مثلا 10 پروژه)
2. مردم رای می‌دهند (هر نفر 3 رای)
3. پروژه‌های برتر اجرا می‌شوند
4. مردم پیشرفت را ببینند (با عکس و درصد)
```

---

### 💡 فیچر 4: **سیستم پرسش و پاسخ عمومی (Q&A)**

```python
class PublicQuestion(db.Model):
    """سوالات عمومی"""
    candidate_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    question_text = db.Column(db.Text)
    category = db.Column(db.String(50))
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # تعاملات
    upvotes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    
    # پاسخ
    answer_text = db.Column(db.Text)
    answered_at = db.Column(db.DateTime)
    answer_video = db.Column(db.String(300))  # پاسخ ویدیویی
    
    status = db.Column(db.String(20))  # pending, answered, featured
    is_featured = db.Column(db.Boolean, default=False)  # سوالات برجسته
    
class QuestionUpvote(db.Model):
    """رای به سوالات"""
    question_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    voted_at = db.Column(db.DateTime)
```

#### فیچرها:
- سوال ناشناس یا با نام
- رای‌گیری به سوالات (محبوب‌ترین سوالات بالا بیاید)
- پاسخ متنی یا ویدیویی
- بخش "سوالات متداول" در بات

---

### 💡 فیچر 5: **گزارش زنده از ستادها (Live Updates)**

```python
class CampaignUpdate(db.Model):
    """بروزرسانی‌های مبارزات انتخاباتی"""
    candidate_id = db.Column(db.Integer)
    update_type = db.Column(db.String(50))  # rally, meeting, achievement, announcement
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    media_files = db.Column(db.JSON)  # عکس/ویدیو
    location = db.Column(db.String(300))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime)
    views_count = db.Column(db.Integer, default=0)
    reactions = db.Column(db.JSON)  # {" like": 150, "heart": 80, ...}

class UserReaction(db.Model):
    """واکنش کاربران"""
    update_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    reaction_type = db.Column(db.String(20))  # like, heart, wow, sad
    created_at = db.Column(db.DateTime)
```

---

### 💡 فیچر 6: **چالش‌های مشارکتی (Challenges)**

```python
class Challenge(db.Model):
    """چالش‌های مشارکتی"""
    candidate_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    challenge_type = db.Column(db.String(50))
    # انواع چالش:
    # - 'photo': عکس از محله خود
    # - 'idea': بهترین ایده برای بهبود شهر
    # - 'story': داستان من و محله‌ام
    # - 'quiz': مسابقه دانش عمومی
    
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    reward = db.Column(db.String(200))  # جایزه
    participants_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20))  # active, ended, judging

class ChallengeSubmission(db.Model):
    """شرکت در چالش"""
    challenge_id = db.Column(db.Integer)
    user_telegram_id = db.Column(db.BigInteger)
    submission_content = db.Column(db.Text)
    media_files = db.Column(db.JSON)
    submitted_at = db.Column(db.DateTime)
    public_votes = db.Column(db.Integer, default=0)
    is_winner = db.Column(db.Boolean, default=False)
```

---

## 📋 خلاصه پیشنهادات به ترتیب اولویت

### 🔴 اولویت بالا (ضروری):
1. ✨ **Two-Factor Authentication (2FA)** - امنیت
2. ✨ **سیستم تیم و نقش‌ها** - مدیریت چندکاربره
3. ✨ **CRM پیشرفته** - دسته‌بندی و مدیریت پیام‌ها
4. ✨ **لاگ فعالیت‌ها** - حسابرسی
5. ✨ **سیستم حمایت مردمی** - مشارکت شهروندی

### 🟡 اولویت متوسط (مهم):
6. ✨ **کد تخفیف و فاکتور** - سیستم مالی
7. ✨ **آمار پیشرفته** - تحلیل داده
8. ✨ **گالری و ویدیو** - محتوای غنی
9. ✨ **مدیریت رویدادها** - تقویم و جلسات
10. ✨ **Q&A عمومی** - ارتباط مستقیم

### 🟢 اولویت پایین (خوب است داشته باشید):
11. ✨ **ایمیل و SMS** - کانال‌های دیگر
12. ✨ **شبکه‌های اجتماعی** - پست همزمان
13. ✨ **بودجه مشارکتی** - پروژه‌های مردمی
14. ✨ **چالش‌های مشارکتی** - گیمیفیکیشن
15. ✨ **AI پیشرفته** - هوش مصنوعی

---

## 🚀 پیشنهاد Roadmap

### فاز 1 (1-2 هفته):
- [ ] 2FA
- [ ] لاگ فعالیت‌ها
- [ ] نقش‌ها و دسترسی‌ها

### فاز 2 (2-3 هفته):
- [ ] CRM پیشرفته
- [ ] کد تخفیف و فاکتور
- [ ] سیستم حمایت مردمی (پایه)

### فاز 3 (3-4 هفته):
- [ ] گالری و ویدیو
- [ ] مدیریت رویدادها
- [ ] Q&A عمومی

### فاز 4 (4-6 هفته):
- [ ] آمار پیشرفته
- [ ] بودجه مشارکتی
- [ ] چالش‌ها

---

**نتیجه**: سیستم فعلی شما پایه خوبی دارد اما برای رقابت جدی نیاز به این فیچرها دارید! 🚀
