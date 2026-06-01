#Crawl tin tức từ danh sách website (demo: dùng RSS hoặc HTML)
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from dateutil import parser
import html
# Danh sách website công nghệ (có thể thêm)
TECH_SOURCES = [
    {
        "name": "VnExpress - Công nghệ",
        "url": "https://vnexpress.net/rss/cong-nghe.rss",
        "type": "rss"
    },
    {
        "name": "GenK.vn",
        "url": "https://genk.vn/trangchu.rss",
        "type": "rss"
    }
]

# Danh sách website từ thiện (dùng RSS hoặc crawl)
CHARITY_SOURCES = [
    {
        "name": "VnExpress - Công nghệ",
        "url": "https://vnexpress.net/rss/cong-nghe.rss",
        "type": "rss"
    },
    {
        "name": "GenK.vn",
        "url": "https://genk.vn/trangchu.rss",
        "type": "rss"
    }
]
def fetch_rss_feed(url):
    """Lấy dữ liệu từ RSS feed, trả về list các item kèm image_url và nội dung đầy đủ"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""
            
            # Lấy nội dung đầy đủ (ưu tiên content:encoded)
            content_encoded = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            if content_encoded is not None:
                content = content_encoded.text
            else:
                # Nếu không có content:encoded, lấy description và làm sạch
                content = description
            
            # Lấy ảnh
            image_url = ""
            enclosure = item.find('enclosure')
            if enclosure is not None and enclosure.get('type', '').startswith('image'):
                image_url = enclosure.get('url')
            if not image_url:
                # Tìm ảnh trong nội dung
                soup = BeautifulSoup(content, 'html.parser')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag['src']
            
            items.append({
                "title": title,
                "link": link,
                "pubDate": pub_date,
                "description": description,
                "content": content,  # Nội dung đầy đủ
                "image_url": image_url
            })
        return items
    except Exception as e:
        print(f"Lỗi RSS {url}: {e}")
        return []

def scrape_tech_news():
    """Thu thập tin tức công nghệ với nội dung đầy đủ (không giới hạn)"""
    today = datetime.now().date()
    all_news = []
    for source in TECH_SOURCES:
        if source['type'] == 'rss':
            items = fetch_rss_feed(source['url'])
            for item in items:
                try:
                    pub_date = parser.parse(item['pubDate']) if item['pubDate'] else datetime.now()
                except:
                    pub_date = datetime.now()
                
                    # Lấy tin trong 2 ngày
                if (today - pub_date.date()).days <= 2:
                    content_text = fetch_full_article(item['link'])

                    if not content_text or len(content_text) < 500:
                        print("⚠️ Fallback RSS:", item['title'])
                        raw_content = item['content'] if item['content'] else item['description']
                        soup = BeautifulSoup(raw_content, 'html.parser')
                        content_text = soup.get_text(separator='\n', strip=True)
   
                                        
                    # Xóa các thẻ không cần thiết
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # Lấy nội dung text (KHÔNG GIỚI HẠN)
                    content_text = soup.get_text(separator='\n', strip=True)
                    
                    # Nếu nội dung quá ngắn, thử lấy từ description
                    if len(content_text) < 200:
                        desc_soup = BeautifulSoup(item['description'], 'html.parser')
                        content_text = desc_soup.get_text(separator='\n', strip=True)
                    
                    # Tóm tắt (lấy 2 câu đầu cho phần hiển thị)
                    sentences = re.split(r'[.!?]', content_text)
                    summary = '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else content_text[:300]
                    if len(summary) > 400:
                        summary = summary[:400] + '...'
                    
                    print(f"  📰 {item['title'][:50]}... -> {len(content_text)} ký tự")  # Debug
                    
                    news = {
                        "title": item['title'],
                        "summary": summary,
                        "content": content_text,  # Nội dung ĐẦY ĐỦ
                        "author": "Unknown",
                        "source": source['name'],
                        "url": item['link'],
                        "image_url": item['image_url'],
                        "published_time": pub_date.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    all_news.append(news)
    return all_news

def fetch_full_article(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # ===== THỬ NHIỀU SELECTOR =====
        selectors = [
            "article.fck_detail",          # VNExpress cũ
            "article",                     # VNExpress mới
            "div.fck_detail",
            "div.kbwc-content",            # GenK
            "div.detail-content",
            "div#main-detail-body",
            "div.article-content",
        ]

        content = ""

        for selector in selectors:
            article = soup.select_one(selector)
            if article:
                paragraphs = article.find_all("p")
                text = "\n".join([p.get_text(strip=True) for p in paragraphs])

                if len(text) > 500:   # đủ dài thì dùng
                    content = text
                    break

        # ===== FALLBACK CUỐI =====
        if not content:
            paragraphs = soup.find_all("p")
            text = "\n".join([p.get_text(strip=True) for p in paragraphs])
            if len(text) > 500:
                content = text

        print(f"✅ Crawl full: {len(content)} ký tự | {url}")

        return content

    except Exception as e:
        print(f"❌ Lỗi crawl full {url}: {e}")
        return ""


def scrape_tech_news():
    """Thu thập tin tức công nghệ với nội dung đầy đủ (không giới hạn)"""
    today = datetime.now().date()
    all_news = []
    for source in TECH_SOURCES:
        if source['type'] == 'rss':
            items = fetch_rss_feed(source['url'])
            for item in items:
                try:
                    pub_date = parser.parse(item['pubDate']) if item['pubDate'] else datetime.now()
                except:
                    pub_date = datetime.now()
                
                # Lấy tin trong 2 ngày
                if (today - pub_date.date()).days <= 2:
                    content_text = fetch_full_article(item['link'])

                    # FALLBACK: Nếu cào full article thất bại, mới dùng nội dung RSS
                    if not content_text or len(content_text) < 500:
                        print("⚠️ Fallback RSS:", item['title'])
                        raw_content = item['content'] if item['content'] else item['description']
                        
                        # Khởi tạo soup và XÓA thẻ CÙNG BÊN TRONG khối if này
                        soup = BeautifulSoup(raw_content, 'html.parser')
                        
                        # Xóa các thẻ không cần thiết
                        for script in soup(["script", "style", "nav", "footer", "header"]):
                            script.decompose()
                            
                        # Lấy nội dung text sạch
                        content_text = soup.get_text(separator='\n', strip=True)
                    
                    # Nếu nội dung vẫn quá ngắn, thử lấy từ description
                    if len(content_text) < 200:
                        desc_soup = BeautifulSoup(item['description'], 'html.parser')
                        content_text = desc_soup.get_text(separator='\n', strip=True)
                    
                    # Tóm tắt (lấy 2 câu đầu cho phần hiển thị)
                    sentences = re.split(r'[.!?]', content_text)
                    summary = '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else content_text[:300]
                    if len(summary) > 400:
                        summary = summary[:400] + '...'
                    
                    print(f"  📰 {item['title'][:50]}... -> {len(content_text)} ký tự")  # Debug
                    
                    news = {
                        "title": item['title'],
                        "summary": summary,
                        "content": content_text,  # Nội dung ĐẦY ĐỦ
                        "author": "Unknown",
                        "source": source['name'],
                        "url": item['link'],
                        "image_url": item['image_url'],
                        "published_time": pub_date.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    all_news.append(news)
    return all_news


def scrape_charity_news():
    """Thu thập tin tức từ thiện từ các nguồn"""
    today = datetime.now().date()
    all_news = []
    
    # Đã dọn dẹp đoạn code test thừa ở đây
    
    for source in CHARITY_SOURCES:
        if source['type'] == 'rss':
            items = fetch_rss_feed(source['url'])
            for item in items:
                try:
                    pub_date = parser.parse(item['pubDate']) if item['pubDate'] else datetime.now()
                except:
                    pub_date = datetime.now()
                    
                if (today - pub_date.date()).days <= 2:
                    raw_content = item['content'] if item['content'] else item['description']
                    content_text = BeautifulSoup(raw_content, 'html.parser').get_text(separator='\n', strip=True)
                    
                    if len(content_text) < 100:
                        content_text = BeautifulSoup(item['description'], 'html.parser').get_text(separator='\n', strip=True)
                        
                    news = {
                        "title": item['title'],
                        "content": content_text,
                        "source": source['name'],
                        "url": item['link'],
                        "image_url": item['image_url'],
                        "published_time": pub_date.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    all_news.append(news)
    return all_news