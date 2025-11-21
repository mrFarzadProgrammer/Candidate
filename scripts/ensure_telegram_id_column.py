import sqlite3

conn = sqlite3.connect('election_bot.db')
c = conn.cursor()

c.execute("PRAGMA table_info(candidates)")
columns = c.fetchall()
print('COLUMNS:', columns)

try:
    c.execute("ALTER TABLE candidates ADD COLUMN telegram_id VARCHAR(64)")
    print('telegram_id column added.')
except Exception as e:
    print('Error:', e)

conn.commit()
conn.close()
