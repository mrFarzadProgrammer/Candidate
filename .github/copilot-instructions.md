# Election Bot Management System - Project Instructions

## Project Overview
A comprehensive Telegram bot management system for election candidates with:
- Super admin panel for managing candidates
- Individual candidate panels
- Automatic bot deployment for each candidate
- Plan-based feature system
- Central database architecture

## Technology Stack
- **Backend**: Python (Flask), python-telegram-bot
- **Database**: SQLite/PostgreSQL with SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript (RTL support)
- **Language**: Persian/Farsi (RTL)

## Project Structure
```
candidate/
├── admin_panel/          # Super admin panel
├── candidate_panel/      # Candidate management panel
├── bot_engine/          # Telegram bot core
├── database/            # Database models and migrations
├── config/              # Configuration files
├── static/              # CSS, JS, images
├── templates/           # HTML templates (RTL)
└── requirements.txt     # Python dependencies
```

## Development Guidelines
- Use Persian/Farsi language for all UI
- Support RTL layout
- Modular bot architecture for easy deployment
- Secure authentication for panels
- Scalable database design

## Next Steps
1. ✅ Create project structure
2. ⏳ Implement database models
3. ⏳ Build bot engine
4. ⏳ Create admin panel
5. ⏳ Create candidate panel
6. ⏳ Test and deploy
