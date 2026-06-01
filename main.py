from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Depends, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import hashlib
import uuid
import sqlite3
from starlette.middleware.sessions import SessionMiddleware
from learning_ai import learning_ai
# Import các module hiện có
import database
import scraper
import ai_utils
from rag_processor import rag
from datetime import datetime, timedelta

app = FastAPI(title="AI Smart News & Charity Hub + TDTU Chatbot")
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Tạo thư mục cho RAG và upload ảnh
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
UPLOAD_IMAGE_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)

# --- Models ---
class ApproveRequest(BaseModel):
    table: str
    ids: List[int]
    approve: bool

class ChatRequest(BaseModel):
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AdRequest(BaseModel):
    title: str
    content: str
    image_url: str
    link_url: str

class RAGQuestion(BaseModel):
    question: str

class RAGChatResponse(BaseModel):
    answer: str
    sources: List[str]

class LearningRequest(BaseModel):
    content: str
    title: str = "Bài viết học tập"

# Helper: kiểm tra đăng nhập
def require_login(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    return True

# --- Trang chính ---
@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))
# ========== API UPLOAD ẢNH (QUAN TRỌNG) ==========
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload ảnh cho quảng cáo"""
    print(f"📸 Nhận file ảnh: {file.filename}")
    
    if not file.filename:
        raise HTTPException(400, "Chưa chọn file")
    
    # Kiểm tra định dạng ảnh
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"Chỉ hỗ trợ các định dạng: {', '.join(allowed_extensions)}")
    
    try:
        # Đọc nội dung file
        content = await file.read()
        
        # Tạo tên file duy nhất
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(UPLOAD_IMAGE_DIR, unique_filename)
        
        # Lưu file
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Trả về URL để truy cập
        image_url = f"/static/uploads/{unique_filename}"
        print(f"✅ Ảnh đã lưu: {image_url}")
        
        return {"url": image_url}
    except Exception as e:
        print(f"❌ Lỗi lưu ảnh: {str(e)}")
        raise HTTPException(500, f"Lỗi lưu ảnh: {str(e)}")

# ========== PHẦN 1: NEWS & CHARITY (giữ nguyên từ dự án cũ) ==========
# ... (giữ nguyên các API: login, logout, scrape-tech, scrape-charity, 
#      pending/tech, pending/charity, approve, approved/tech, approved/charity, 
#      ads, add-ad, delete-ad, check-auth, clear)

# Tôi sẽ viết lại phần quan trọng, bạn có thể copy từ main.py cũ

@app.post("/login")
async def login(data: LoginRequest, request: Request):
    user = database.get_user(data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập")
    hashed = hashlib.sha256(data.password.encode()).hexdigest()
    if user["password_hash"] != hashed:
        raise HTTPException(status_code=401, detail="Sai mật khẩu")
    request.session["user"] = user["username"]
    return {"message": "Đăng nhập thành công"}

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Đã đăng xuất"}

@app.get("/check-auth")
async def check_auth(request: Request):
    return {"authenticated": "user" in request.session}

@app.post("/scrape-tech")
async def scrape_tech():
    """Scrape tin công nghệ - Xóa tin cũ và thêm tin mới"""
    try:
        # 1. Xóa tất cả tin công nghệ cũ
        conn = sqlite3.connect('news_charity.db')
        c = conn.cursor()
        c.execute("DELETE FROM tech_news")
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        print(f"🗑️ Đã xóa {deleted_count} tin cũ")
        
        # 2. Scrape tin mới
        news_list = scraper.scrape_tech_news()
        count = 0
        
        for news in news_list:
            analysis = ai_utils.analyze_tech_news(news['title'], news['content'])
            news['category'] = analysis['category']
            news['ai_quality_percent'] = analysis['quality_percent']
            news['ai_summary'] = analysis['summary']
            news['should_publish'] = analysis['should_publish']
            database.save_tech_news(news)
            count += 1
        
        return {
            "message": f"✅ Đã scrape {count} tin mới (xóa {deleted_count} tin cũ)",
            "new_count": count,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        print(f"Lỗi: {e}")
        raise HTTPException(500, f"Lỗi scrape: {str(e)}")

@app.post("/delete-all-tech-news")
async def delete_all_tech_news():
    """Xóa toàn bộ tin công nghệ"""
    try:
        conn = sqlite3.connect('news_charity.db')
        c = conn.cursor()
        c.execute("DELETE FROM tech_news")
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        return {
            "message": f"Đã xóa {deleted_count} tin công nghệ",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(500, f"Lỗi: {str(e)}")

@app.post("/delete-selected-tech-news")
async def delete_selected_tech_news(ids: List[int]):
    """Xóa các tin công nghệ được chọn"""
    try:
        conn = sqlite3.connect('news_charity.db')
        c = conn.cursor()
        
        # Tạo câu lệnh DELETE với các id
        placeholders = ','.join(['?' for _ in ids])
        c.execute(f"DELETE FROM tech_news WHERE id IN ({placeholders})", ids)
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        return {
            "message": f"Đã xóa {deleted_count} tin được chọn",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(500, f"Lỗi: {str(e)}")

@app.post("/scrape-charity")
async def scrape_charity():
    """Scrape tin từ thiện - Xóa tin cũ trước khi scrape"""
    try:
        # Xóa tin cũ
        conn = sqlite3.connect('news_charity.db')
        c = conn.cursor()
        c.execute("DELETE FROM charity_news")
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        # Scrape tin mới
        #news_list = scraper.scrape_charity_news()
        #count = 0
        
        #for news in news_list:
        #    analysis = ai_utils.analyze_charity_news(news['title'], news['content'])
        #    news['category'] = analysis['category']
        #    news['urgency_score'] = analysis['urgency_score']
        #    news['urgency_reason'] = analysis['urgency_reason']
        #    news['ai_summary'] = analysis['summary']
        #    database.save_charity_news(news)
        #    count += 1
        
        return {
            "message": f"✅ Đã scrape và lưu {count} tin từ thiện mới (đã xóa {deleted_count} tin cũ)",
            "new_count": count,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        print(f"Lỗi: {e}")
        raise HTTPException(500, f"Lỗi scrape: {str(e)}")

@app.get("/pending/tech")
async def get_pending_tech():
    return {"pending": database.get_pending_tech_news()}

@app.get("/pending/charity")
async def get_pending_charity():
    return {"pending": database.get_pending_charity_news()}

@app.post("/approve")
async def approve_items(req: ApproveRequest):
    table = "tech_news" if req.table == "tech" else "charity_news"
    for news_id in req.ids:
        database.approve_news(table, news_id, req.approve)
    return {"message": f"Đã cập nhật {len(req.ids)} bài viết"}

@app.post("/clear-old-news")
async def clear_old_news():
    """Xóa tin tức cũ hơn 2 ngày"""
    conn = sqlite3.connect('news_charity.db')
    c = conn.cursor()
    
    # Xóa tin cũ hơn 2 ngày trong bảng tech_news
    c.execute("DELETE FROM tech_news WHERE published_time < datetime('now', '-2 days')")
    deleted_tech = c.rowcount
    
    # Xóa tin cũ hơn 2 ngày trong bảng charity_news
    c.execute("DELETE FROM charity_news WHERE published_time < datetime('now', '-2 days')")
    deleted_charity = c.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        "message": f"Đã xóa {deleted_tech} tin công nghệ và {deleted_charity} tin từ thiện cũ hơn 2 ngày",
        "deleted_tech": deleted_tech,
        "deleted_charity": deleted_charity
    }

@app.get("/approved/tech")
async def get_approved_tech():
    """Lấy danh sách tin công nghệ đã duyệt (kèm nội dung đầy đủ)"""
    conn = sqlite3.connect('news_charity.db')
    c = conn.cursor()
    # Lấy đầy đủ các trường
    c.execute(''' 
        SELECT id, title, summary, content, source, url, image_url, published_time, 
               category, ai_quality_percent 
        FROM tech_news 
        WHERE approved = 1 
        ORDER BY published_time DESC
    ''')
    rows = c.fetchall()
    conn.close()
    
    news_list = []
    for r in rows:
        content_text = r[3] if r[3] else r[2]  # Lấy content, nếu không có thì dùng summary
        print(f"📚 Bài: {r[1][:50]}... -> {len(content_text)} ký tự")  # Debug
        news_list.append({
            "id": r[0], 
            "title": r[1], 
            "summary": r[2], 
            "content": content_text,  # Trả về nội dung đầy đủ
            "source": r[4], 
            "url": r[5], 
            "image_url": r[6], 
            "time": r[7], 
            "category": r[8], 
            "quality": r[9]
        })
    
    return {"news": news_list}

@app.get("/approved/charity")
async def get_approved_charity():
    return {"news": database.get_approved_charity_news()}

# API quảng cáo
@app.post("/add-ad")
async def add_ad(ad: AdRequest, request: Request, _=Depends(require_login)):
    database.add_ad(ad.title, ad.content, ad.image_url, ad.link_url)
    return {"message": "Đã thêm quảng cáo"}

@app.get("/ads")
async def get_ads():
    return {"ads": database.get_all_ads()}

@app.delete("/ads/{ad_id}")
async def delete_ad(ad_id: int, request: Request, _=Depends(require_login)):
    database.delete_ad(ad_id)
    return {"message": "Đã xóa"}

@app.post("/clear-data")
async def clear_news_data():
    """Xóa toàn bộ dữ liệu news và charity"""
    # Tùy chọn: xóa bảng
    return {"message": "Tính năng đang phát triển"}
# ========== PHẦN 2: RAG CHATBOT (từ tdtu_chatbot) ==========
def generate_answer(question: str, contexts: List[tuple]) -> str:
    if not contexts:
        return "❌ Không tìm thấy thông tin trong tài liệu."
    
    combined = "\n".join([ctx[0] for ctx in contexts])
    keywords = question.lower().split()
    relevant = []
    
    for sent in combined.split('.'):
        if any(kw in sent.lower() for kw in keywords):
            relevant.append(sent.strip())
    
    if relevant:
        answer = ". ".join(relevant[:3]) + "."
        return answer[:500] + ("..." if len(answer) > 500 else "")
    return contexts[0][0][:500] + ("..." if len(contexts[0][0]) > 500 else "")

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload và xử lý tài liệu cho RAG chatbot"""
    print(f"Received file: {file.filename}")  # Debug
    
    if not file.filename:
        raise HTTPException(400, "Chưa chọn file")
    
    if not file.filename.endswith(('.docx', '.pdf')):
        raise HTTPException(400, "Chỉ hỗ trợ file .docx và .pdf")
    
    # Đọc nội dung file
    content = await file.read()
    
    # Lưu file tạm
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    try:
        # Xử lý tài liệu
        num_chunks = rag.process_document(file_path, file.filename)
        return {
            "message": f"Đã xử lý {file.filename} ({num_chunks} đoạn)",
            "total_chunks": len(rag.chunks),
            "documents": rag.get_all_documents()
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug
        raise HTTPException(500, f"Lỗi xử lý: {str(e)}")
    finally:
        # Xóa file tạm
        if os.path.exists(file_path):
            os.remove(file_path)
            
@app.post("/rag-chat", response_model=RAGChatResponse)
async def rag_chat(question: RAGQuestion):
    results = rag.search(question.question, top_k=5)
    if not results:
        return RAGChatResponse(
            answer="❌ Chưa có dữ liệu. Hãy upload tài liệu về trường Tôn Đức Thắng trước.",
            sources=[]
        )
    
    answer = generate_answer(question.question, results)
    sources = [f"[{r[2].get('doc_name', 'Unknown')}]: {r[0][:150]}..." for r in results[:3]]
    return RAGChatResponse(answer=answer, sources=sources)

@app.get("/documents")
async def get_documents():
    return {"documents": rag.get_all_documents()}

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    success = rag.delete_document(doc_id)
    if not success:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    return {"message": "Đã xóa tài liệu", "documents": rag.get_all_documents()}

@app.get("/rag-stats")
async def get_rag_stats():
    return {
        "total_chunks": len(rag.chunks),
        "total_documents": len(rag.documents),
        "has_data": rag.index is not None
    }

@app.post("/add-ad")
async def add_ad(ad: AdRequest, request: Request, _=Depends(require_login)):
    """Thêm quảng cáo mới"""
    try:
        database.add_ad(ad.title, ad.content, ad.image_url, ad.link_url)
        return {"message": "Đã thêm quảng cáo thành công"}
    except Exception as e:
        print(f"Error adding ad: {str(e)}")
        raise HTTPException(500, f"Lỗi: {str(e)}")

@app.post("/clear-rag")
async def clear_rag_data():
    rag.clear()
    return {"message": "Đã xóa toàn bộ dữ liệu RAG"}

# ========== PHẦN 3: HỌC TẬP THÔNG MINH ==========
class LearningRequest(BaseModel):
    content: str
    title: str = "Bài viết học tập"

@app.post("/learning/summarize")
async def learning_summarize(request: LearningRequest):
    """Module 1: Tóm tắt + giải thích"""
    try:
        result = learning_ai.summarize_and_explain(request.content, request.title)
        return result
    except Exception as e:
        raise HTTPException(500, f"Lỗi xử lý tóm tắt: {str(e)}")

@app.post("/learning/suggest")
async def learning_suggest(request: LearningRequest):
    """Module 2: Gợi ý học tập"""
    try:
        category = learning_ai._identify_main_topic(request.content)
        result = learning_ai.suggest_learning_path(request.content, category)
        return result
    except Exception as e:
        raise HTTPException(500, f"Lỗi xử lý gợi ý: {str(e)}")

@app.post("/learning/questions")
async def learning_questions(request: LearningRequest):
    """Module 3: Sinh câu hỏi ôn tập"""
    try:
        questions = learning_ai.generate_questions(request.content, num_questions=5)
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(500, f"Lỗi sinh câu hỏi: {str(e)}")

@app.post("/learning/process")
async def learning_process(request: LearningRequest):
    """Xử lý toàn bộ 3 module"""
    try:
        print(f"📚 Nhận yêu cầu học tập: {request.title[:50]}...")  # Debug
        
        # Module 1: Tóm tắt
        summary_result = learning_ai.summarize_and_explain(request.content, request.title)
        
        # Module 2: Gợi ý
        category = learning_ai._identify_main_topic(request.content)
        suggest_result = learning_ai.suggest_learning_path(request.content, category)
        
        # Module 3: Câu hỏi
        questions = learning_ai.generate_questions(request.content, num_questions=5)
        
        print("✅ Xử lý thành công")  # Debug
        
        return {
            "summary": summary_result,
            "suggestions": suggest_result,
            "questions": questions
        }
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")  # Debug
        raise HTTPException(500, f"Lỗi xử lý: {str(e)}")
# ========== API CHO LUỒNG DUYỆT TIN MỚI ==========

@app.post("/scrape-to-temp")
async def scrape_to_temp():
    """Scrape tin và lưu vào bảng tạm thời"""
    try:
        # Xóa tin tạm cũ
        database.clear_temp_tech_news()
        
        # Scrape tin mới
        news_list = scraper.scrape_tech_news()
        count = 0
        
        for news in news_list:
            analysis = ai_utils.analyze_tech_news(news['title'], news['content'])
            news['category'] = analysis['category']
            news['ai_quality_percent'] = analysis['quality_percent']
            news['ai_summary'] = analysis['summary']
            news['should_publish'] = analysis['should_publish']
            database.save_temp_tech_news(news)
            count += 1
        
        return {
            "message": f"✅ Đã scrape {count} tin mới. Vui lòng chọn tin để đăng!",
            "new_count": count
        }
        
    except Exception as e:
        print(f"Lỗi: {e}")
        raise HTTPException(500, f"Lỗi scrape: {str(e)}")

@app.get("/temp-tech-news")
async def get_temp_tech_news():
    """Lấy danh sách tin tạm thời để duyệt"""
    news_list = database.get_temp_tech_news()
    return {"news": news_list}

@app.post("/approve-selected-temp-news")
async def approve_selected_temp_news(selected_ids: List[int]):
    """Duyệt các tin đã chọn và chuyển vào bảng chính"""
    if not selected_ids:
        raise HTTPException(400, "Chưa chọn tin nào")
    
    # Chuyển tin được chọn vào bảng chính
    database.move_selected_temp_to_tech(selected_ids)
    
    # Xóa các tin còn lại trong bảng tạm
    conn = sqlite3.connect('news_charity.db')
    c = conn.cursor()
    placeholders = ','.join(['?' for _ in selected_ids])
    c.execute(f"DELETE FROM temp_tech_news WHERE id NOT IN ({placeholders})", selected_ids)
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    
    return {
        "message": f"✅ Đã duyệt {len(selected_ids)} tin và xóa {deleted_count} tin không chọn",
        "approved_count": len(selected_ids),
        "deleted_count": deleted_count
    }

@app.post("/clear-temp-news")
async def clear_temp_news():
    """Xóa toàn bộ tin tạm thời (không lưu)"""
    database.clear_temp_tech_news()
    return {"message": "Đã xóa toàn bộ tin tạm thời"}

# Các API xóa tin chính (giữ nguyên)
@app.post("/delete-all-tech-news")
async def delete_all_tech_news():
    """Xóa toàn bộ tin công nghệ"""
    conn = sqlite3.connect('news_charity.db')
    c = conn.cursor()
    c.execute("DELETE FROM tech_news")
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    return {"message": f"Đã xóa {deleted_count} tin công nghệ", "deleted_count": deleted_count}

@app.post("/delete-selected-tech-news")
async def delete_selected_tech_news(ids: List[int]):
    """Xóa các tin công nghệ được chọn"""
    conn = sqlite3.connect('news_charity.db')
    c = conn.cursor()
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"DELETE FROM tech_news WHERE id IN ({placeholders})", ids)
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    return {"message": f"Đã xóa {deleted_count} tin được chọn", "deleted_count": deleted_count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)