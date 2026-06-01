import sqlite3

conn = sqlite3.connect('news_charity.db')
c = conn.cursor()

# Tạo bảng tạm thời
c.execute('''
    CREATE TABLE IF NOT EXISTS temp_tech_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        summary TEXT,
        content TEXT,
        author TEXT,
        source TEXT,
        url TEXT,
        image_url TEXT,
        published_time TEXT,
        category TEXT,
        ai_quality_percent REAL,
        ai_summary TEXT,
        should_publish INTEGER
    )
''')

conn.commit()
conn.close()
print("✅ Đã tạo bảng temp_tech_news thành công!")