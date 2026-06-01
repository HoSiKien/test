#Các hàm phân tích AI (rule‑based + keyword)
import re
def analyze_tech_news(title, content):
    """Phân tích tin tức khoa học công nghệ: chủ đề, % chất lượng, tóm tắt, có nên đăng"""
    text = (title + " " + content).lower()
    tech_keywords = ['ai', 'trí tuệ nhân tạo', 'machine learning', 'deep learning', 'blockchain', 'iot', '5g',
                     'robot', 'công nghệ', 'phần mềm', 'ứng dụng', 'khoa học', 'nghiên cứu', 'phát minh',
                     'dữ liệu lớn', 'cloud', 'cyber security', 'lượng tử']
    score = 0
    for kw in tech_keywords:
        if kw in text:
            score += 10
    # Giới hạn 0-100
    quality_percent = min(100, score)
    
    # Xác định chủ đề con
    category = "Công nghệ AI" if any(k in text for k in ['ai', 'trí tuệ']) else \
               "Blockchain" if 'blockchain' in text else \
               "IoT" if 'iot' in text else \
               "Khoa học cơ bản" if any(k in text for k in ['nghiên cứu', 'khoa học']) else \
               "Công nghệ thông tin"
    
    # Tóm tắt: lấy 2 câu đầu của content
    sentences = re.split(r'[.!?]', content)
    summary = '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else content[:200]
    if len(summary) > 300:
        summary = summary[:300] + '...'
    
    should_publish = quality_percent >= 30  # đăng nếu % công nghệ >= 30%
    
    return {
        "category": category,
        "quality_percent": quality_percent,
        "summary": summary,
        "should_publish": should_publish
    }

def analyze_charity_news(title, content):
    """Phân loại từ thiện, đánh giá mức độ khẩn cấp (0-10)"""
    text = (title + " " + content).lower()
    
    # Phân loại
    if any(kw in text for kw in ['ung thư', 'bệnh hiểm nghèo', 'tim bẩm sinh', 'phẫu thuật', 'cứu chữa', 'bệnh nặng']):
        category = "bệnh hiểm nghèo"
        base_score = 9.0
    elif any(kw in text for kw in ['trẻ em', 'mồ côi', 'bé', 'trẻ nhỏ', 'học sinh', 'không nơi nương tựa']):
        category = "trẻ em mồ côi"
        base_score = 7.5
    elif any(kw in text for kw in ['bão', 'lũ', 'động đất', 'thiên tai', 'sạt lở', 'hạn hán']):
        category = "thiên tai"
        base_score = 8.5
    elif any(kw in text for kw in ['người già', 'cụ già', 'neo đơn', 'không nơi nương tựa']):
        category = "người già neo đơn"
        base_score = 6.0
    else:
        category = "hoàn cảnh khó khăn"
        base_score = 5.0
    
    # Điều chỉnh theo từ khẩn cấp
    urgency_words = ['cấp cứu', 'gấp', 'ngay lập tức', 'nguy kịch', 'khẩn cấp', 'cần gấp', 'kêu cứu', 'cứu giúp']
    bonus = sum(1.0 for w in urgency_words if w in text) * 0.8
    urgency_score = min(10.0, base_score + bonus)
    
    reason = f"Phân loại: {category}. Mức độ cơ bản {base_score} điểm, thêm {bonus:.1f} điểm do từ khẩn cấp."
    
    # Tóm tắt ngắn
    sentences = re.split(r'[.!?]', content)
    summary = '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else content[:200]
    if len(summary) > 300:
        summary = summary[:300] + '...'
    
    return {
        "category": category,
        "urgency_score": round(urgency_score, 1),
        "urgency_reason": reason,
        "summary": summary
    }

def chatbot_response(query):
    """Chatbot tìm kiếm hoàn cảnh từ thiện theo địa điểm"""
    from database import search_charity_by_location
    # Trích xuất địa danh (đơn giản: từ sau "ở", "tại", hoặc cụm từ viết hoa)
    import re
    patterns = [r'(?:ở|tại)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)',
                r'(?:giúp\s+)?người\s+nghèo\s+(?:ở|tại)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+)']
    location = None
    for p in patterns:
        m = re.search(p, query)
        if m:
            location = m.group(1)
            break
    if not location:
        # Thử tìm bất kỳ tỉnh thành (từ danh sách mẫu)
        provinces = ['hà nội', 'hồ chí minh', 'đà nẵng', 'hải phòng', 'cần thơ', 'gia lai', 'đắk lắk', 'nghệ an']
        for prov in provinces:
            if prov in query.lower():
                location = prov.title()
                break
    if location:
        results = search_charity_by_location(location)
        if results:
            reply = f"📢 Tìm thấy {len(results)} trường hợp tại {location}:\n"
            for r in results[:5]:
                reply += f"- {r['title']} (Độ khẩn cấp: {r['urgency_score']}/10)\n"
            reply += "Hãy vào tab 'Tin từ thiện' để xem chi tiết và hỗ trợ."
        else:
            reply = f"Rất tiếc, chưa có trường hợp nào tại {location}. Bạn có thể gửi thông tin hoàn cảnh để chúng tôi đăng tải (qua tab Quản trị)."
    else:
        reply = ("Chào bạn! Tôi có thể giúp tìm các hoàn cảnh khó khăn theo địa điểm. "
                 "Hãy hỏi: 'Tôi muốn giúp người nghèo ở Gia Lai' hoặc 'Có trường hợp nào tại Hà Nội không?'")
    return reply