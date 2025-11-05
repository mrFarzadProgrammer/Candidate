"""
WSGI Entry Point برای دیپلوی Production
"""
import os
import sys
from threading import Thread
import time

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, redirect
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Import both panels
from admin_panel.app import app as admin_app
from candidate_panel.app import app as candidate_app

# Create main app
main_app = Flask(__name__)

@main_app.route('/')
def index():
    """صفحه اصلی - راهنما"""
    return """
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>سامانه مدیریت بات‌های انتخاباتی</title>
        <style>
            body { 
                font-family: Tahoma, Arial; 
                text-align: center; 
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: white;
                color: #333;
                padding: 40px;
                border-radius: 15px;
                max-width: 600px;
                margin: 0 auto;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            h1 { color: #667eea; margin-bottom: 30px; }
            .links { margin-top: 30px; }
            .links a {
                display: inline-block;
                margin: 10px;
                padding: 15px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                transition: all 0.3s;
            }
            .links a:hover {
                background: #764ba2;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗳️ سامانه مدیریت بات‌های انتخاباتی</h1>
            <p>به سامانه جامع مدیریت بات‌های تلگرام برای نماینده‌ها خوش آمدید</p>
            <div class="links">
                <a href="/admin/">🔧 پنل مدیریت</a>
                <a href="/candidate/">👤 پنل نماینده</a>
            </div>
        </div>
    </body>
    </html>
    """

# Combine apps with URL prefixes
app = DispatcherMiddleware(main_app, {
    '/admin': admin_app,
    '/candidate': candidate_app
})

def run_bots_in_background():
    """راه‌اندازی بات‌ها در بک‌گراند"""
    time.sleep(10)  # صبر تا سرور آماده بشه
    
    from database.models import BotInstance
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.settings import DATABASE_URI
    from bot_engine.telegram_bot import run_bot
    
    print("🤖 در حال راه‌اندازی بات‌ها...")
    
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        active_bots = session.query(BotInstance).filter_by(is_active=True).all()
        
        for bot in active_bots:
            print(f"🚀 راه‌اندازی بات @{bot.bot_username}...")
            bot_thread = Thread(target=run_bot, args=(bot.id,), daemon=True)
            bot_thread.start()
            time.sleep(2)
        
        if active_bots:
            print(f"✅ {len(active_bots)} بات راه‌اندازی شد")
    finally:
        session.close()

# Start bots in background
bots_thread = Thread(target=run_bots_in_background, daemon=True)
bots_thread.start()

if __name__ == '__main__':
    # For local testing
    run_simple('0.0.0.0', 8000, app, use_reloader=True, use_debugger=True)
