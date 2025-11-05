"""
بات تلگرام اختصاصی نماینده
"""
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, BotInstance, Candidate, Resume, Program, Headquarters, Message, BotUser, Analytics
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
                bot_instance_id=bot_id
            )
            session.add(bot_user)
            session.commit()
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
        [InlineKeyboardButton("💬 ارسال پیام", callback_data="send_message")]
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت پیام از کاربر"""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_instance_id')
    
    # بررسی اینکه آیا منتظر دریافت پیام هستیم
    if context.user_data.get('waiting_for_message'):
        message_text = update.message.text
        
        session = Session()
        try:
            # ذخیره پیام در دیتابیس
            bot_instance = session.query(BotInstance).filter_by(id=bot_id).first()
            
            message = Message(
                candidate_id=bot_instance.candidate_id,
                user_telegram_id=user.id,
                user_name=f"{user.first_name} {user.last_name or ''}",
                message_text=message_text,
                is_read=False
            )
            
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
                print(f"❌ بات با ID {bot_instance_id} یافت نشد")
                return
            
            # ایجاد Application
            application = Application.builder().token(bot_instance.bot_token).build()
            
            # ذخیره bot_instance_id در bot_data
            application.bot_data['bot_instance_id'] = bot_instance_id
            
            # افزودن handlers
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CallbackQueryHandler(button_callback))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            # به‌روزرسانی وضعیت بات
            bot_instance.is_active = True
            bot_instance.last_active = datetime.utcnow()
            session.commit()
            
            print(f"✅ بات @{bot_instance.bot_username} در حال اجرا...")
            
            # اجرای بات
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        
        except Exception as e:
            print(f"❌ خطا در راه‌اندازی بات {bot_instance_id}: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            session.close()
    
    finally:
        try:
            loop.close()
        except:
            pass
