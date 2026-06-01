import sqlite3
conn = sqlite3.connect('news_charity.db')
c = conn.cursor()
c.execute("SELECT id, title, LENGTH(content) as content_len FROM tech_news WHERE approved = 1 LIMIT 5")
for row in c.fetchall():
    print(f"ID: {row[0]}, Title: {row[1][:50]}..., Content length: {row[2]} chars")
conn.close()