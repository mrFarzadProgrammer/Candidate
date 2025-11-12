"""
بات تلگرام اختصاصی نماینده
"""
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (
    db, BotInstance, Candidate, Resume, Program, Headquarters, Message, BotUser, Analytics,
    CitizenContribution, ContributionVote, ContributionComment, CitizenProfile
)
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from config.settings import DATABASE_URI
from datetime import datetime


# تنظیم دیتابیس برای استفاده در بات
engine = create_engine(DATABASE_URI)
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)


def get_candidate_by_bot_id(bot_instance_id: int):
    """دریافت اطلاعات نماینده از روی ID بات"""
    session = Session()
    try:
        bot_instance = session.query(BotInstance).filter_by(id=bot_instance_id).first()
        if bot_instance:
            return session.query(Candidate).filter_by(id=bot_instance.candidate_id).first()
    finally:
        session.close()
    return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع بات"""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_instance_id')
    
    # ثبت کاربر در دیتابیس
    session = Session()
    is_new_user = False
    try:
        bot_user = session.query(BotUser).filter_by(
            telegram_id=user.id,
            bot_instance_id=bot_id
        ).first()
        
        if not bot_user:
            bot_user = BotUser(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                bot_instance_id=bot_id,
                total_points=0,
                level=1
            )
            session.add(bot_user)
            session.commit()
            is_new_user = True
            
            # 🎮 Gamification: امتیاز عضویت
            try:
                from services.gamification_service import GamificationService
                result = GamificationService.award_points(bot_user, 'join')
                if result['success']:
                    await update.message.reply_text(
                        f"🎉 تبریک! {result['points_awarded']} امتیاز دریافت کردید!\n"
                        f"🏆 سطح: {result['level']['emoji']} {result['level']['name']}"
                    )
            except Exception as e:
                import logging
                logging.error(f"Gamification error: {e}")
    finally:
        session.close()
    
    # دریافت اطلاعات نماینده
    candidate = get_candidate_by_bot_id(bot_id)
    
    if not candidate:
        await update.message.reply_text("❌ خطا در دریافت اطلاعات")
        return
    
    welcome_text = f"""
🌟 سلام {user.first_name} عزیز!

به بات انتخاباتی *{candidate.full_name}* خوش آمدید.

📍 شهر: {candidate.city or 'نامشخص'}
🎯 حوزه انتخابیه: {candidate.district or 'نامشخص'}

از منوی زیر می‌توانید اطلاعات مورد نظر خود را مشاهده کنید.
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 رزومه", callback_data="resume"),
         InlineKeyboardButton("📢 برنامه‌ها", callback_data="programs")],
        [InlineKeyboardButton("📍 آدرس ستادها", callback_data="headquarters"),
         InlineKeyboardButton("📞 تماس با ما", callback_data="contact")],
        [InlineKeyboardButton("💡 مشارکت من", callback_data="contribute"),
         InlineKeyboardButton("💡 ایده‌های محبوب", callback_data="popular_ideas")],
        [InlineKeyboardButton("� ارسال پیام", callback_data="send_message")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های inline"""
    query = update.callback_query
    await query.answer()
    
    bot_id = context.bot_data.get('bot_instance_id')
    candidate = get_candidate_by_bot_id(bot_id)
    
    if not candidate:
        await query.edit_message_text("❌ خطا در دریافت اطلاعات")
        return
    
    session = Session()
    
    try:
        if query.data == "resume":
            resumes = session.query(Resume).filter_by(candidate_id=candidate.id).order_by(Resume.order).all()
            
            if not resumes:
                text = "📋 رزومه‌ای ثبت نشده است."
            else:
                text = f"📋 *رزومه {candidate.full_name}*\n\n"
                for resume in resumes:
                    text += f"▫️ *{resume.title}* ({resume.year})\n"
                    text += f"   {resume.description}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        elif query.data == "programs":
            programs = session.query(Program).filter_by(candidate_id=candidate.id).all()
            
            if not programs:
                text = "📢 برنامه‌ای ثبت نشده است."
            else:
                text = f"📢 *برنامه‌های {candidate.full_name}*\n\n"
                for program in programs:
                    text += f"🔹 *{program.title}*\n"
                    text += f"📂 دسته: {program.category}\n"
                    text += f"{program.description}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        elif query.data == "leaderboard":
            # نمایش جدول برترین‌ها
            await leaderboard_command(update, context)
            return
        
        elif query.data == "popular_ideas":
            # نمایش ایده‌های محبوب
            context.user_data['ideas_page'] = 0
            await show_popular_ideas(update, context)
            return
        
        elif query.data in ["ideas_next", "ideas_prev"]:
            # صفحه‌بندی ایده‌ها
            await ideas_navigation(update, context)
            return
        
        elif query.data == "track_by_code":
            # درخواست کد پیگیری
            await track_by_code_prompt(update, context)
            return
        
        elif query.data == "headquarters":
            hqs = session.query(Headquarters).filter_by(candidate_id=candidate.id).all()
            
            if not hqs:
                text = "📍 آدرس ستادی ثبت نشده است."
            else:
                text = f"📍 *ستادهای {candidate.full_name}*\n\n"
                for hq in hqs:
                    text += f"🏢 *{hq.name}*\n"
                    text += f"📍 {hq.address}\n"
                    if hq.phone:
                        text += f"📞 {hq.phone}\n"
                    text += "\n"
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        elif query.data == "contact":
            text = f"📞 *تماس با {candidate.full_name}*\n\n"
            
            if candidate.phone:
                text += f"📱 تلفن: {candidate.phone}\n"
            if candidate.email:
                text += f"📧 ایمیل: {candidate.email}\n"
            
            if not candidate.phone and not candidate.email:
                text += "اطلاعات تماس ثبت نشده است."
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        elif query.data == "send_message":
            # بررسی فعال بودن پلن ارتباط مردمی
            has_messaging = any(plan.code == 'PUBLIC_MESSAGING' for plan in candidate.plans)
            
            if not has_messaging:
                text = "❌ امکان ارسال پیام در حال حاضر فعال نیست."
                keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup)
            else:
                text = "💬 لطفاً پیام خود را برای نماینده ارسال کنید:"
                context.user_data['waiting_for_message'] = True
                await query.edit_message_text(text)
        
        elif query.data == "back":
            # بازگشت به منوی اصلی
            keyboard = [
                [InlineKeyboardButton("📋 رزومه", callback_data="resume"),
                 InlineKeyboardButton("📢 برنامه‌ها", callback_data="programs")],
                [InlineKeyboardButton("📍 آدرس ستادها", callback_data="headquarters"),
                 InlineKeyboardButton("📞 تماس با ما", callback_data="contact")],
                [InlineKeyboardButton("💬 ارسال پیام", callback_data="send_message")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"""
🌟 منوی اصلی

نماینده: *{candidate.full_name}*
📍 {candidate.city} - {candidate.district}

از منوی زیر انتخاب کنید:
"""
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    finally:
        session.close()


# ============================================================
# مشارکت شهروندی (Citizen Participation)
# ============================================================

# States for ConversationHandler
(CONTRIBUTION_TYPE, CATEGORY_SELECT, TITLE_INPUT, DESCRIPTION_INPUT, 
 LOCATION_INPUT, IMAGE_UPLOAD, CONFIRM) = range(7)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کاربر"""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_instance_id')
    
    session = Session()
    try:
        bot_user = session.query(BotUser).filter_by(
            telegram_id=user.id,
            bot_instance_id=bot_id
        ).first()
        
        if not bot_user:
            await update.message.reply_text("❌ کاربر یافت نشد. لطفا /start را بزنید.")
            return
        
        # دریافت آمار
        from services.gamification_service import GamificationService
        stats = GamificationService.get_user_stats(bot_user)
        
        # ساخت پیام
        text = f"""
🏆 *آمار شما*

👤 نام: {bot_user.first_name} {bot_user.last_name or ''}

💎 امتیازات: *{stats['total_points']:,}*
📊 سطح: {stats['level']['emoji']} *{stats['level']['name']}* (سطح {stats['level']['level']})
🔥 Streak: *{stats['streak_days']} روز*

{'📈 تا سطح بعدی: ' + str(stats['level']['points_to_next']) + ' امتیاز' if stats['level']['points_to_next'] > 0 else '✨ شما در بالاترین سطح هستید!'}

🏅 *نشان‌ها ({stats['badges_count']}):*
"""
        
        if stats['badges']:
            for badge in stats['badges']:
                text += f"  {badge['emoji']} {badge['name']}\n"
        else:
            text += "  هنوز نشانی دریافت نکرده‌اید\n"
        
        # دکمه‌ها
        keyboard = [
            [InlineKeyboardButton("🏆 جدول برترین‌ها", callback_data="leaderboard")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    finally:
        session.close()


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جدول برترین‌ها"""
    bot_id = context.bot_data.get('bot_instance_id')
    
    from services.gamification_service import GamificationService
    leaderboard = GamificationService.get_leaderboard(bot_id, limit=10)
    
    text = "🏆 *جدول برترین‌ها*\n\n"
    
    for user in leaderboard:
        medal = "🥇" if user['rank'] == 1 else "🥈" if user['rank'] == 2 else "🥉" if user['rank'] == 3 else f"{user['rank']}."
        text += f"{medal} *{user['name']}*\n"
        text += f"   💎 {user['points']:,} امتیاز | {user['level_emoji']} {user['level_name']}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    if query:
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def contribute_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند مشارکت"""
    keyboard = [
        [InlineKeyboardButton("💡 ارسال ایده", callback_data="contrib_idea")],
        [InlineKeyboardButton("📣 گزارش مشکل", callback_data="contrib_report")],
        [InlineKeyboardButton("❌ انصراف", callback_data="contrib_cancel")]
    ]
    
    text = """
🌟 *مشارکت شهروندی*

از طریق این بخش می‌توانید:
💡 ایده‌های خود برای بهبود شهر را ارسال کنید
📣 مشکلات و نیازهای محله را گزارش دهید

لطفاً یکی از گزینه‌ها را انتخاب کنید:
"""
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return CONTRIBUTION_TYPE


async def contribution_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب نوع مشارکت (ایده یا گزارش)"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "contrib_cancel":
        await query.edit_message_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    # ذخیره نوع
    if query.data == "contrib_idea":
        context.user_data['contrib_type'] = 'idea'
        type_text = "ایده"
    else:
        context.user_data['contrib_type'] = 'report'
        type_text = "گزارش مشکل"
    
    # نمایش دسته‌بندی‌ها
    keyboard = [
        [InlineKeyboardButton("📚 آموزش", callback_data="cat_education"),
         InlineKeyboardButton("🏥 بهداشت", callback_data="cat_health")],
        [InlineKeyboardButton("🚗 ترافیک", callback_data="cat_traffic"),
         InlineKeyboardButton("🛡️ امنیت", callback_data="cat_security")],
        [InlineKeyboardButton("🌳 محیط زیست", callback_data="cat_environment"),
         InlineKeyboardButton("🎭 فرهنگی", callback_data="cat_cultural")],
        [InlineKeyboardButton("🏗️ زیرساخت", callback_data="cat_infrastructure"),
         InlineKeyboardButton("💰 اقتصاد", callback_data="cat_economic")],
        [InlineKeyboardButton("🤝 رفاه", callback_data="cat_welfare"),
         InlineKeyboardButton("📋 سایر", callback_data="cat_other")],
        [InlineKeyboardButton("❌ انصراف", callback_data="contrib_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
📚 *دسته‌بندی {type_text}*

لطفاً دسته‌بندی مرتبط را انتخاب کنید:
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return CATEGORY_SELECT


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب دسته‌بندی"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "contrib_cancel":
        await query.edit_message_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    # ذخیره دسته‌بندی
    category_map = {
        "cat_education": ("education", "📚 آموزش"),
        "cat_health": ("health", "🏥 بهداشت"),
        "cat_traffic": ("traffic", "🚗 ترافیک"),
        "cat_security": ("security", "🛡️ امنیت"),
        "cat_environment": ("environment", "🌳 محیط زیست"),
        "cat_cultural": ("cultural", "🎭 فرهنگی"),
        "cat_infrastructure": ("infrastructure", "🏗️ زیرساخت"),
        "cat_economic": ("economic", "💰 اقتصاد"),
        "cat_welfare": ("welfare", "🤝 رفاه"),
        "cat_other": ("other", "📋 سایر")
    }
    
    category_code, category_name = category_map.get(query.data, ("other", "📋 سایر"))
    context.user_data['category'] = category_code
    context.user_data['category_name'] = category_name
    
    type_text = "ایده" if context.user_data['contrib_type'] == 'idea' else "گزارش مشکل"
    
    text = f"""
✍️ *عنوان {type_text}*

دسته‌بندی: {category_name}

لطفاً عنوان کوتاه و گویا بنویسید:
(حداکثر 200 کاراکتر)

برای انصراف /cancel را بزنید.
"""
    
    await query.edit_message_text(text, parse_mode='Markdown')
    return TITLE_INPUT


async def title_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت عنوان"""
    title = update.message.text.strip()
    
    if len(title) > 200:
        await update.message.reply_text("❌ عنوان نباید بیشتر از 200 کاراکتر باشد. دوباره بنویسید:")
        return TITLE_INPUT
    
    context.user_data['title'] = title
    
    type_text = "ایده" if context.user_data['contrib_type'] == 'idea' else "گزارش مشکل"
    
    text = f"""
📝 *توضیحات {type_text}*

عنوان: {title}

لطفاً توضیحات کامل را بنویسید:
(حداقل 20 کاراکتر)

برای انصراف /cancel را بزنید.
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')
    return DESCRIPTION_INPUT


async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت توضیحات"""
    description = update.message.text.strip()
    
    if len(description) < 20:
        await update.message.reply_text("❌ توضیحات باید حداقل 20 کاراکتر باشد. دوباره بنویسید:")
        return DESCRIPTION_INPUT
    
    context.user_data['description'] = description
    
    type_text = "ایده" if context.user_data['contrib_type'] == 'idea' else "مشکل"
    is_report = context.user_data['contrib_type'] == 'report'
    
    keyboard = [
        [KeyboardButton("📍 ارسال موقعیت GPS", request_location=True)],
        [KeyboardButton("✍️ نوشتن آدرس")],
    ]
    
    if not is_report:  # برای ایده موقعیت اختیاری است
        keyboard.append([KeyboardButton("⏭️ رد کردن")])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    required_text = "**الزامی**" if is_report else "(اختیاری)"
    
    text = f"""
📍 *موقعیت مکانی* {required_text}

لطفاً موقعیت مکانی {type_text} را مشخص کنید:

برای انصراف /cancel را بزنید.
"""
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return LOCATION_INPUT


async def location_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت موقعیت مکانی"""
    if update.message.location:
        # دریافت GPS
        location = update.message.location
        context.user_data['latitude'] = location.latitude
        context.user_data['longitude'] = location.longitude
        context.user_data['location_text'] = f"موقعیت GPS: {location.latitude}, {location.longitude}"
    elif update.message.text and update.message.text != "⏭️ رد کردن":
        # دریافت آدرس متنی
        context.user_data['location_text'] = update.message.text.strip()
        context.user_data['latitude'] = None
        context.user_data['longitude'] = None
    else:
        # رد کردن موقعیت (فقط برای ایده)
        context.user_data['location_text'] = None
        context.user_data['latitude'] = None
        context.user_data['longitude'] = None
    
    # سوال بعدی: تصویر
    keyboard = [
        [KeyboardButton("📷 ارسال تصویر")],
        [KeyboardButton("⏭️ بدون تصویر ادامه بده")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    text = """
📷 *تصویر* (اختیاری)

می‌توانید تا 3 تصویر ارسال کنید:

برای انصراف /cancel را بزنید.
"""
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    context.user_data['images'] = []
    return IMAGE_UPLOAD


async def image_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تصویر"""
    if update.message.photo:
        # دریافت تصویر
        if 'images' not in context.user_data:
            context.user_data['images'] = []
        
        if len(context.user_data['images']) >= 3:
            await update.message.reply_text("⚠️ حداکثر 3 تصویر می‌توانید ارسال کنید.")
            return IMAGE_UPLOAD
        
        # ذخیره file_id تصویر
        photo = update.message.photo[-1]  # بزرگترین سایز
        context.user_data['images'].append(photo.file_id)
        
        await update.message.reply_text(f"✅ تصویر {len(context.user_data['images'])} دریافت شد.\n\nتصویر بعدی را ارسال کنید یا «ادامه» را بزنید.")
        
        if len(context.user_data['images']) >= 3:
            # رفتن به تایید نهایی
            return await show_confirmation(update, context)
        
        return IMAGE_UPLOAD
    
    elif update.message.text and update.message.text == "⏭️ بدون تصویر ادامه بده":
        # ادامه بدون تصویر
        context.user_data['images'] = []
        return await show_confirmation(update, context)
    
    return IMAGE_UPLOAD


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش خلاصه برای تایید نهایی"""
    type_text = "ایده" if context.user_data['contrib_type'] == 'idea' else "گزارش مشکل"
    
    text = f"""
✅ *خلاصه {type_text}*

📌 نوع: {type_text}
🏷️ دسته: {context.user_data.get('category_name', 'نامشخص')}
📝 عنوان: {context.user_data.get('title', '')}
💬 توضیحات: {context.user_data.get('description', '')[:100]}...
📍 موقعیت: {context.user_data.get('location_text', 'ندارد')}
📷 تصاویر: {len(context.user_data.get('images', []))} عکس

آیا اطلاعات صحیح است؟
"""
    
    keyboard = [
        [KeyboardButton("✅ تایید و ارسال")],
        [KeyboardButton("❌ انصراف")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRM


async def final_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید نهایی و ذخیره در دیتابیس"""
    if update.message.text == "❌ انصراف":
        await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🏠 منوی اصلی")]], resize_keyboard=True))
        context.user_data.clear()
        return ConversationHandler.END
    
    # ذخیره در دیتابیس
    session = Session()
    try:
        user = update.effective_user
        bot_id = context.bot_data.get('bot_instance_id')
        
        bot_instance = session.query(BotInstance).filter_by(id=bot_id).first()
        if not bot_instance:
            await update.message.reply_text("❌ خطا در دریافت اطلاعات بات")
            return ConversationHandler.END
        
        # تولید کد پیگیری
        prefix = "IDEA" if context.user_data['contrib_type'] == 'idea' else "RPT"
        last = session.query(CitizenContribution).filter(
            CitizenContribution.tracking_code.like(f'{prefix}-%')
        ).order_by(CitizenContribution.id.desc()).first()
        
        if last:
            last_num = int(last.tracking_code.split('-')[1])
            new_num = last_num + 1
        else:
            new_num = 1001 if prefix == "IDEA" else 2001
        
        tracking_code = f"{prefix}-{new_num:04d}"
        
        # ایجاد مشارکت
        contribution = CitizenContribution(
            tracking_code=tracking_code,
            candidate_id=bot_instance.candidate_id,
            user_telegram_id=user.id,
            user_username=user.username,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            contribution_type=context.user_data['contrib_type'],
            title=context.user_data['title'],
            description=context.user_data['description'],
            category=context.user_data['category'],
            location_text=context.user_data.get('location_text'),
            latitude=context.user_data.get('latitude'),
            longitude=context.user_data.get('longitude'),
            images=context.user_data.get('images', []),
            status='pending',
            priority='medium',
            created_at=datetime.utcnow()
        )
        
        session.add(contribution)
        session.commit()
        
        # اعطای امتیاز به کاربر
        profile = session.query(CitizenProfile).filter_by(telegram_id=user.id).first()
        if not profile:
            profile = CitizenProfile(
                telegram_id=user.id,
                full_name=f"{user.first_name} {user.last_name or ''}".strip(),
                username=user.username,
                total_points=10,
                level=1,
                contributions_count=1,
                badges=['beginner'],
                joined_at=datetime.utcnow()
            )
            session.add(profile)
        else:
            profile.total_points += 10
            profile.contributions_count += 1
            profile.last_active = datetime.utcnow()
        
        session.commit()
        
        type_text = "ایده" if context.user_data['contrib_type'] == 'idea' else "گزارش"
        
        text = f"""
🎉 *{type_text} شما با موفقیت ثبت شد!*

📌 کد پیگیری: `{tracking_code}`

+10 امتیاز دریافت کردید!
امتیاز کل شما: {profile.total_points}

این مشارکت توسط تیم بررسی و در صورت تایید، به شما 50 امتیاز اضافی تعلق می‌گیرد.

برای پیگیری: /track_{tracking_code}
"""
        
        await update.message.reply_text(
            text, 
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🏠 منوی اصلی")]], resize_keyboard=True)
        )
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ثبت: {str(e)}")
        return ConversationHandler.END
    finally:
        session.close()


async def cancel_contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو فرآیند مشارکت"""
    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🏠 منوی اصلی")]], resize_keyboard=True)
    )
    context.user_data.clear()
    return ConversationHandler.END


# ============================================================
# لیست ایده‌ها و پیگیری (Ideas List & Tracking)
# ============================================================

async def show_popular_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش ایده‌های محبوب"""
    query = update.callback_query
    if query:
        await query.answer()
    
    bot_id = context.bot_data.get('bot_instance_id')
    session = Session()
    
    try:
        bot_instance = session.query(BotInstance).filter_by(id=bot_id).first()
        if not bot_instance:
            await (query.message if query else update.message).reply_text("❌ خطا در دریافت اطلاعات")
            return
        
        # دریافت محبوب‌ترین ایده‌ها (بر اساس رای)
        page = context.user_data.get('ideas_page', 0)
        per_page = 5
        
        contributions = session.query(CitizenContribution).filter(
            CitizenContribution.candidate_id == bot_instance.candidate_id,
            CitizenContribution.contribution_type == 'idea',
            CitizenContribution.status.in_(['approved', 'in_progress', 'completed'])
        ).order_by(
            CitizenContribution.votes_count.desc()
        ).limit(per_page).offset(page * per_page).all()
        
        total = session.query(CitizenContribution).filter(
            CitizenContribution.candidate_id == bot_instance.candidate_id,
            CitizenContribution.contribution_type == 'idea',
            CitizenContribution.status.in_(['approved', 'in_progress', 'completed'])
        ).count()
        
        if not contributions:
            text = "📋 هنوز ایده تاییدشده‌ای وجود ندارد."
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
        else:
            text = "💡 *ایده‌های محبوب*\n\n"
            
            for idx, contrib in enumerate(contributions, start=page * per_page + 1):
                status_emoji = {
                    'approved': '✅',
                    'in_progress': '🔄',
                    'completed': '✔️'
                }.get(contrib.status, '⏳')
                
                category_emoji = {
                    'education': '📚',
                    'health': '🏥',
                    'traffic': '🚗',
                    'security': '🛡️',
                    'environment': '🌳',
                    'cultural': '🎭',
                    'infrastructure': '🏗️',
                    'economic': '💰',
                    'welfare': '🤝',
                    'other': '📋'
                }.get(contrib.category, '📋')
                
                text += f"{idx}️⃣ {status_emoji} *{contrib.title}*\n"
                text += f"   {category_emoji} | 👍 {contrib.votes_count} | 💬 {contrib.comments_count}\n"
                text += f"   📍 `{contrib.tracking_code}`\n\n"
            
            text += f"📄 صفحه {page + 1} از {(total + per_page - 1) // per_page}"
            
            # دکمه‌های صفحه‌بندی
            keyboard = []
            nav_row = []
            
            if page > 0:
                nav_row.append(InlineKeyboardButton("◀️ قبلی", callback_data="ideas_prev"))
            
            if (page + 1) * per_page < total:
                nav_row.append(InlineKeyboardButton("بعدی ▶️", callback_data="ideas_next"))
            
            if nav_row:
                keyboard.append(nav_row)
            
            keyboard.append([
                InlineKeyboardButton("🔍 پیگیری با کد", callback_data="track_by_code"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="back")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    finally:
        session.close()


async def ideas_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت صفحه‌بندی ایده‌ها"""
    query = update.callback_query
    await query.answer()
    
    current_page = context.user_data.get('ideas_page', 0)
    
    if query.data == "ideas_next":
        context.user_data['ideas_page'] = current_page + 1
    elif query.data == "ideas_prev":
        context.user_data['ideas_page'] = max(0, current_page - 1)
    
    await show_popular_ideas(update, context)


async def track_by_code_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست کد پیگیری"""
    query = update.callback_query
    await query.answer()
    
    text = """
🔍 *پیگیری مشارکت*

لطفاً کد پیگیری خود را ارسال کنید:
(مثال: `IDEA-1001` یا `RPT-2001`)

برای انصراف: /cancel
"""
    
    await query.edit_message_text(text, parse_mode='Markdown')
    context.user_data['waiting_for_tracking_code'] = True


async def track_contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جزئیات مشارکت با کد پیگیری"""
    tracking_code = update.message.text.strip().upper()
    
    # بررسی فرمت
    if not (tracking_code.startswith('IDEA-') or tracking_code.startswith('RPT-')):
        await update.message.reply_text(
            "❌ فرمت کد پیگیری صحیح نیست.\n"
            "مثال: `IDEA-1001` یا `RPT-2001`",
            parse_mode='Markdown'
        )
        return
    
    bot_id = context.bot_data.get('bot_instance_id')
    session = Session()
    
    try:
        bot_instance = session.query(BotInstance).filter_by(id=bot_id).first()
        if not bot_instance:
            await update.message.reply_text("❌ خطا در دریافت اطلاعات")
            return
        
        contrib = session.query(CitizenContribution).filter_by(
            tracking_code=tracking_code,
            candidate_id=bot_instance.candidate_id
        ).first()
        
        if not contrib:
            await update.message.reply_text(
                f"❌ مشارکتی با کد `{tracking_code}` یافت نشد.",
                parse_mode='Markdown'
            )
            return
        
        # نمایش جزئیات
        type_text = "ایده" if contrib.contribution_type == 'idea' else "گزارش"
        
        status_text = {
            'pending': '⏳ در انتظار بررسی',
            'under_review': '👀 در حال بررسی',
            'approved': '✅ تایید شده',
            'in_progress': '🔄 در حال انجام',
            'completed': '✔️ انجام شده',
            'rejected': '❌ رد شده'
        }.get(contrib.status, 'نامشخص')
        
        category_name = {
            'education': '📚 آموزش',
            'health': '🏥 بهداشت',
            'traffic': '🚗 ترافیک',
            'security': '🛡️ امنیت',
            'environment': '🌳 محیط زیست',
            'cultural': '🎭 فرهنگی',
            'infrastructure': '🏗️ زیرساخت',
            'economic': '💰 اقتصاد',
            'welfare': '🤝 رفاه',
            'other': '📋 سایر'
        }.get(contrib.category, 'نامشخص')
        
        text = f"""
📌 *نتیجه پیگیری*

🆔 کد: `{contrib.tracking_code}`
📝 عنوان: *{contrib.title}*
🏷️ دسته: {category_name}
📊 وضعیت: {status_text}

💬 توضیحات:
{contrib.description}

📍 تاریخ ثبت: {contrib.created_at.strftime('%Y/%m/%d')}
👍 رای‌ها: {contrib.votes_count}
💬 نظرات: {contrib.comments_count}
👁️ بازدیدها: {contrib.views_count}
"""
        
        # تاریخچه
        timeline = []
        if contrib.created_at:
            timeline.append(f"✅ ثبت شد ({contrib.created_at.strftime('%Y/%m/%d')})")
        if contrib.reviewed_at:
            timeline.append(f"👀 بررسی شد ({contrib.reviewed_at.strftime('%Y/%m/%d')})")
        if contrib.status == 'in_progress':
            timeline.append("🔄 عملیات آغاز شد")
        if contrib.completed_at:
            timeline.append(f"✔️ اتمام یافت ({contrib.completed_at.strftime('%Y/%m/%d')})")
        
        if timeline:
            text += "\n📅 *تاریخچه:*\n" + "\n".join(timeline)
        
        # پاسخ نامزد
        if contrib.admin_response:
            text += f"\n\n💬 *پاسخ نامزد:*\n{contrib.admin_response}"
        
        # امتیاز کسب شده
        earned_points = 10  # ارسال
        if contrib.status == 'approved':
            earned_points += 50
        if contrib.status == 'in_progress':
            earned_points += 75
        if contrib.status == 'completed':
            earned_points += 100
        
        text += f"\n\n⭐ امتیاز کسب شده: *{earned_points}* امتیاز"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="popular_ideas")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        context.user_data['waiting_for_tracking_code'] = False
    
    finally:
        session.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت پیام از کاربر"""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_instance_id')
    
    # بررسی انتظار برای کد پیگیری
    if context.user_data.get('waiting_for_tracking_code'):
        await track_contribution(update, context)
        return
    
    # بررسی اینکه آیا منتظر دریافت پیام هستیم
    if context.user_data.get('waiting_for_message'):
        message_text = update.message.text
        
        session = Session()
        try:
            # ذخیره پیام در دیتابیس
            bot_instance = session.query(BotInstance).filter_by(id=bot_id).first()
            candidate = session.query(Candidate).filter_by(id=bot_instance.candidate_id).first()
            
            # بررسی محدودیت پلن
            if not candidate.can_add_message():
                context.user_data['waiting_for_message'] = False
                await update.message.reply_text(
                    "⚠️ متأسفانه ظرفیت دریافت پیام تکمیل شده است.\n"
                    "لطفاً بعداً دوباره تلاش کنید.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back")
                    ]])
                )
                session.close()
                return
            
            message = Message(
                candidate_id=bot_instance.candidate_id,
                user_telegram_id=user.id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                message_text=message_text,
                is_read=False
            )
            
            # AI دسته‌بندی خودکار پیام
            try:
                from ai_services.message_categorization import get_categorizer
                categorizer = get_categorizer(use_ml=False)  # فعلاً rule-based
                category_result = categorizer.categorize(message_text)
                
                message.category = category_result['category']
                message.category_fa = category_result['category_fa']
                message.category_confidence = category_result['confidence']
                message.category_priority = category_result['priority']
            except Exception as e:
                # در صورت خطا، بدون دسته‌بندی ادامه می‌دهد
                import logging
                logging.error(f"AI categorization failed: {e}")
            
            # AI تحلیل احساسات
            try:
                from ai_services.sentiment_analyzer import get_sentiment_analyzer
                sentiment_analyzer = get_sentiment_analyzer(use_ml=False)
                sentiment_result = sentiment_analyzer.analyze(message_text)
                
                message.sentiment_score = sentiment_result['score']
                message.sentiment_label = sentiment_result['label']
            except Exception as e:
                import logging
                logging.error(f"AI sentiment analysis failed: {e}")
            
            session.add(message)
            session.commit()
            
            context.user_data['waiting_for_message'] = False
            
            await update.message.reply_text(
                "✅ پیام شما با موفقیت ارسال شد.\n"
                "نماینده در اسرع وقت به پیام شما پاسخ خواهد داد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back")
                ]])
            )
        finally:
            session.close()
    else:
        await update.message.reply_text(
            "لطفاً از دکمه‌های منو استفاده کنید.\n"
            "برای شروع: /start"
        )


def run_bot(bot_instance_id: int):
    """اجرای بات"""
    import asyncio
    
    # ایجاد event loop جدید برای این thread
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        session = Session()
        
        try:
            bot_instance = session.query(BotInstance).filter_by(id=bot_instance_id).first()
            
            if not bot_instance:
                logger.debug(f"❌ بات با ID {bot_instance_id} یافت نشد")
                return
            
            # ایجاد Application
            application = Application.builder().token(bot_instance.bot_token).build()
            
            # ذخیره bot_instance_id در bot_data
            application.bot_data['bot_instance_id'] = bot_instance_id
            
            # ایجاد ConversationHandler برای مشارکت شهروندی
            contribution_handler = ConversationHandler(
                entry_points=[
                    CommandHandler("contribute", contribute_start),
                    CallbackQueryHandler(contribute_start, pattern="^contribute$")
                ],
                states={
                    CONTRIBUTION_TYPE: [CallbackQueryHandler(contribution_type_selected)],
                    CATEGORY_SELECT: [CallbackQueryHandler(category_selected)],
                    TITLE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_received)],
                    DESCRIPTION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)],
                    LOCATION_INPUT: [
                        MessageHandler(filters.LOCATION, location_received),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, location_received)
                    ],
                    IMAGE_UPLOAD: [
                        MessageHandler(filters.PHOTO, image_received),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, image_received)
                    ],
                    CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, final_confirm)]
                },
                fallbacks=[CommandHandler("cancel", cancel_contribution)]
            )
            
            # افزودن handlers
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("stats", stats_command))
            application.add_handler(CommandHandler("leaderboard", leaderboard_command))
            application.add_handler(contribution_handler)  # اضافه کردن handler مشارکت
            application.add_handler(CallbackQueryHandler(button_callback))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            # به‌روزرسانی وضعیت بات
            bot_instance.is_active = True
            bot_instance.last_active = datetime.utcnow()
            session.commit()
            
            logger.debug(f"✅ بات @{bot_instance.bot_username} در حال اجرا...")
            
            # اجرای بات
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        
        except Exception as e:
            logger.debug(f"❌ خطا در راه‌اندازی بات {bot_instance_id}: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            session.close()
    
    finally:
        try:
            loop.close()
        except Exception as e:
            pass
