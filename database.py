import sqlite3
import hashlib

DB_NAME = "news_charity.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bảng tin tức công nghệ
    c.execute('''
        CREATE TABLE IF NOT EXISTS tech_news (
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
            should_publish INTEGER,
            approved INTEGER DEFAULT 0
        )
    ''')
    # Bảng tin tức từ thiện
    c.execute('''
        CREATE TABLE IF NOT EXISTS charity_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            source TEXT,
            url TEXT,
            image_url TEXT,
            published_time TEXT,
            category TEXT,
            urgency_score REAL,
            urgency_reason TEXT,
            ai_summary TEXT,
            approved INTEGER DEFAULT 0
        )
    ''')
    # Bảng quảng cáo
    c.execute('''
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            image_url TEXT,
            link_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Bảng users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    # Thêm user admin mặc định (admin / admin123) nếu chưa có
    hashed = hashlib.sha256("admin123".encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashed))
    except sqlite3.IntegrityError:
        pass  # đã tồn tại

    # Thêm cột image_url nếu chưa có (cho các DB cũ) – cần kiểm tra sự tồn tại của cột
    try:
        c.execute("ALTER TABLE tech_news ADD COLUMN image_url TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE charity_news ADD COLUMN image_url TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def save_tech_news(news):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO tech_news 
        (title, summary, content, author, source, url, image_url, published_time, 
         category, ai_quality_percent, ai_summary, should_publish, approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (
        news['title'], 
        news.get('summary', ''), 
        news['content'],  # Nội dung đầy đủ, KHÔNG cắt
        news.get('author', ''),
        news['source'], 
        news['url'], 
        news.get('image_url', ''), 
        news['published_time'],
        news['category'], 
        news['ai_quality_percent'], 
        news['ai_summary'], 
        1 if news['should_publish'] else 0
    ))
    conn.commit()
    conn.close()
    print(f"  💾 Đã lưu: {news['title'][:50]}... ({len(news['content'])} ký tự)")

def save_charity_news(news):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO charity_news 
        (title, content, source, url, image_url, published_time, category, urgency_score, urgency_reason, ai_summary, approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (
        news['title'], news['content'], news['source'], news['url'], news.get('image_url', ''),
        news['published_time'], news['category'], news['urgency_score'], news['urgency_reason'], news['ai_summary']
    ))
    conn.commit()
    conn.close()

def get_pending_tech_news():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, title, summary, source, published_time, category, ai_quality_percent, should_publish FROM tech_news WHERE approved = 0')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "summary": r[2], "source": r[3], "time": r[4],
             "category": r[5], "quality": r[6], "should_publish": bool(r[7])} for r in rows]

def get_pending_charity_news():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, title, content, source, published_time, category, urgency_score, urgency_reason FROM charity_news WHERE approved = 0')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2], "source": r[3], "time": r[4],
             "category": r[5], "urgency_score": r[6], "reason": r[7]} for r in rows]

def approve_news(table, news_id, approve):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    status = 1 if approve else -1
    c.execute(f'UPDATE {table} SET approved = ? WHERE id = ?', (status, news_id))
    conn.commit()
    conn.close()

def get_approved_tech_news():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Phải lấy cột content (nội dung đầy đủ)
    c.execute('SELECT id, title, summary, content, source, url, image_url, published_time, category, ai_quality_percent FROM tech_news WHERE approved = 1 ORDER BY published_time DESC')
       
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "summary": r[2], "content": r[3] if r[3] else r[2], 
             "source": r[4], "url": r[5], "image_url": r[6], "time": r[7], 
             "category": r[8], "quality": r[9]} for r in rows]
    
def get_approved_charity_news():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, title, content, source, url, image_url, published_time, category, urgency_score, urgency_reason FROM charity_news WHERE approved = 1 ORDER BY urgency_score DESC')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2], "source": r[3], "url": r[4], "image_url": r[5],
             "time": r[6], "category": r[7], "urgency_score": r[8], "reason": r[9]} for r in rows]

def search_charity_by_location(keyword):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT title, content, source, category, urgency_score FROM charity_news WHERE approved = 1 AND (title LIKE ? OR content LIKE ?)',
              (f'%{keyword}%', f'%{keyword}%'))
    rows = c.fetchall()
    conn.close()
    return [{"title": r[0], "content": r[1], "source": r[2], "category": r[3], "urgency_score": r[4]} for r in rows]

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "password_hash": row[2]}
    return None

def add_ad(title, content, image_url, link_url):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO ads (title, content, image_url, link_url) VALUES (?, ?, ?, ?)",
              (title, content, image_url, link_url))
    conn.commit()
    conn.close()

def get_all_ads():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, content, image_url, link_url FROM ads ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2], "image_url": r[3], "link_url": r[4]} for r in rows]

def delete_ad(ad_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
    conn.commit()
    conn.close()

# Khởi tạo DB khi import
init_db()