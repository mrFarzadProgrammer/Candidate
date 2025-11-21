-- اسکریپت افزودن فیلد telegram_id به جدول candidates (برای SQLite/PostgreSQL)
ALTER TABLE candidates ADD COLUMN telegram_id VARCHAR(64);
