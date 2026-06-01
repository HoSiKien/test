import sqlite3

conn = sqlite3.connect('news_charity.db')
c = conn.cursor()

# Xóa dữ liệu trong bảng tech_news
c.execute("DELETE FROM tech_news")
print("✅ Đã xóa dữ liệu tech_news")

# Xóa dữ liệu trong bảng temp_tech_news (nếu tồn tại)
try:
    c.execute("DELETE FROM temp_tech_news")
    print("✅ Đã xóa dữ liệu temp_tech_news")
except sqlite3.OperationalError:
    print("⚠️ Bảng temp_tech_news chưa tồn tại, bỏ qua")

conn.commit()
conn.close()
print("✅ Hoàn thành!")