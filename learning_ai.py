import re
import random
from typing import Dict, List, Tuple

class LearningAI:
    """AI xử lý nội dung học tập"""
    
    def __init__(self):
        # Từ khóa chuyên ngành
        self.tech_keywords = {
            "AI/ML": ["AI", "trí tuệ nhân tạo", "machine learning", "deep learning", "neural network", 
                      "học sâu", "mạng nơ-ron", "computer vision", "xử lý ảnh"],
            "Lập trình": ["python", "java", "c++", "javascript", "algorithm", "thuật toán", 
                          "data structure", "cấu trúc dữ liệu", "code", "lập trình"],
            "Web/Cloud": ["web", "cloud", "aws", "azure", "docker", "kubernetes", "api", "rest", 
                          "frontend", "backend", "database", "cơ sở dữ liệu"],
            "Blockchain": ["blockchain", "bitcoin", "ethereum", "crypto", "smart contract", 
                           "web3", "nft", "chuỗi khối"],
            "IoT/5G": ["iot", "5g", "internet of things", "vạn vật kết nối", "mạng", "sensor"]
        }
        
    def summarize_and_explain(self, content: str, title: str) -> Dict:
        """Module 1: Tóm tắt + giải thích"""
        # Tóm tắt (lấy 3-5 câu đầu)
        sentences = re.split(r'[.!?]', content)
        summary_sentences = sentences[:4] if len(sentences) > 4 else sentences
        summary = '. '.join(summary_sentences).strip()
        if len(summary) > 500:
            summary = summary[:500] + "..."
        
        # Giải thích các thuật ngữ chuyên ngành
        tech_terms = self._extract_tech_terms(content)
        explanations = self._explain_terms(tech_terms)
        
        # Độ khó (dựa trên độ dài và từ chuyên ngành)
        difficulty = "Cơ bản" if len(content) < 1000 else "Trung cấp" if len(content) < 3000 else "Nâng cao"
        
        return {
            "title": title,
            "summary": summary,
            "difficulty": difficulty,
            "tech_terms": tech_terms[:5],  # Tối đa 5 thuật ngữ
            "explanations": explanations,
            "key_points": self._extract_key_points(content)
        }
    
    def suggest_learning_path(self, content: str, category: str) -> Dict:
        """Module 2: Gợi ý học tập"""
        # Xác định chủ đề chính
        main_topic = self._identify_main_topic(content)
        
        # Đề xuất kỹ năng cần học
        skills = self._suggest_skills(main_topic, category)
        
        # Tài nguyên học tập
        resources = self._suggest_resources(main_topic)
        
        # Lộ trình học (theo tuần)
        roadmap = self._create_roadmap(main_topic, skills)
        
        return {
            "main_topic": main_topic,
            "category": category,
            "skills_to_learn": skills,
            "resources": resources,
            "roadmap": roadmap,
            "estimated_time": self._estimate_time(content)
        }
    
    def generate_questions(self, content: str, num_questions: int = 5) -> List[Dict]:
        """Module 3: Sinh câu hỏi ôn tập"""
        questions = []
        
        # Trích xuất các câu quan trọng
        sentences = re.split(r'[.!?]', content)
        important_sentences = [s for s in sentences if len(s) > 50 and any(kw in s.lower() for kw in ['là', 'có', 'được', 'gồm', 'bao gồm'])]
        
        if not important_sentences:
            important_sentences = sentences[:10]
        
        # Tạo câu hỏi từ các câu quan trọng
        for i, sent in enumerate(important_sentences[:num_questions]):
            # Loại câu hỏi
            q_type = random.choice(["Hiểu", "Phân tích", "Ứng dụng", "So sánh"])
            
            # Tạo câu hỏi dựa trên nội dung
            if q_type == "Hiểu":
                question_text = f"Theo bài viết, {sent[:50]}... là gì? Hãy giải thích."
            elif q_type == "Phân tích":
                question_text = f"Phân tích ý nghĩa của: '{sent[:80]}...' trong bối cảnh công nghệ hiện nay."
            elif q_type == "Ứng dụng":
                question_text = f"Làm thế nào để áp dụng kiến thức về '{sent[:60]}...' vào thực tế?"
            else:
                question_text = f"So sánh nội dung '{sent[:60]}...' với các công nghệ/cách tiếp cận khác mà bạn biết."
            
            # Gợi ý trả lời (lấy từ câu gốc)
            sample_answer = sent[:200] + "..." if len(sent) > 200 else sent
            
            questions.append({
                "id": i + 1,
                "type": q_type,
                "question": question_text,
                "sample_answer": sample_answer,
                "difficulty": random.choice(["Dễ", "Trung bình", "Khó"])
            })
        
        return questions
    
    # === Các hàm hỗ trợ ===
    def _extract_tech_terms(self, text: str) -> List[str]:
        """Trích xuất thuật ngữ chuyên ngành"""
        terms = []
        for category, keywords in self.tech_keywords.items():
            for kw in keywords:
                if kw.lower() in text.lower() and kw not in terms:
                    terms.append(kw)
        return terms
    
    def _explain_terms(self, terms: List[str]) -> Dict[str, str]:
        """Giải thích thuật ngữ"""
        explanations = {}
        basic_explanations = {
            "AI": "Trí tuệ nhân tạo - mô phỏng trí thông minh con người bằng máy tính",
            "machine learning": "Học máy - cho phép máy tính học từ dữ liệu mà không cần lập trình rõ ràng",
            "deep learning": "Học sâu - một nhánh của machine learning sử dụng mạng nơ-ron nhiều lớp",
            "blockchain": "Chuỗi khối - công nghệ lưu trữ dữ liệu phân tán, an toàn và minh bạch",
            "python": "Ngôn ngữ lập trình phổ biến, dễ học, được dùng nhiều trong AI và data science",
            "algorithm": "Thuật toán - tập hợp các bước có thứ tự để giải quyết một vấn đề",
            "api": "Giao diện lập trình ứng dụng - cho phép các ứng dụng giao tiếp với nhau",
            "database": "Cơ sở dữ liệu - nơi lưu trữ và quản lý dữ liệu có cấu trúc"
        }
        
        for term in terms:
            term_lower = term.lower()
            if term_lower in basic_explanations:
                explanations[term] = basic_explanations[term_lower]
            else:
                explanations[term] = f"{term} là một khái niệm quan trọng trong lĩnh vực công nghệ thông tin, liên quan đến {self._find_category(term)}."
        
        return explanations
    
    def _find_category(self, term: str) -> str:
        """Tìm danh mục của thuật ngữ"""
        for category, keywords in self.tech_keywords.items():
            if term.lower() in [k.lower() for k in keywords]:
                return category
        return "công nghệ"
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Trích xuất các điểm chính"""
        sentences = re.split(r'[.!?]', text)
        key_points = []
        for sent in sentences:
            if len(sent) > 30 and len(sent) < 200:
                if any(word in sent.lower() for word in ['quan trọng', 'chính', 'then chốt', 'cần lưu ý', 'đặc biệt']):
                    key_points.append(sent.strip())
        return key_points[:3] if key_points else [sentences[i].strip() for i in range(min(3, len(sentences)))]
    
    def _identify_main_topic(self, text: str) -> str:
        """Xác định chủ đề chính"""
        for category, keywords in self.tech_keywords.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    return category
        return "Công nghệ thông tin"
    
    def _suggest_skills(self, topic: str, category: str) -> List[str]:
        """Đề xuất kỹ năng cần học"""
        skills_map = {
            "AI/ML": ["Python", "Linear Algebra", "Statistics", "TensorFlow/PyTorch", "Data Processing"],
            "Lập trình": ["Python/Java", "Data Structures", "Algorithms", "Git", "Problem Solving"],
            "Web/Cloud": ["HTML/CSS", "JavaScript", "React/Vue", "Node.js", "Docker", "AWS/Azure"],
            "Blockchain": ["Solidity", "Smart Contracts", "Cryptography", "Web3.js", "Ethereum"],
            "IoT/5G": ["C/C++", "Embedded Systems", "Network Protocols", "Sensor Technology"]
        }
        return skills_map.get(topic, ["Lập trình cơ bản", "Tư duy logic", "Giải quyết vấn đề"])
    
    def _suggest_resources(self, topic: str) -> List[Dict]:
        """Đề xuất tài nguyên học tập"""
        resources = {
            "AI/ML": [
                {"name": "Machine Learning Coursera (Andrew Ng)", "type": "Khóa học", "url": "https://www.coursera.org/learn/machine-learning"},
                {"name": "Fast.ai - Practical Deep Learning", "type": "Khóa học miễn phí", "url": "https://course.fast.ai/"}
            ],
            "Lập trình": [
                {"name": "LeetCode", "type": "Luyện tập", "url": "https://leetcode.com/"},
                {"name": "GeeksforGeeks", "type": "Tài liệu", "url": "https://www.geeksforgeeks.org/"}
            ],
            "Web/Cloud": [
                {"name": "The Odin Project", "type": "Khóa học", "url": "https://www.theodinproject.com/"},
                {"name": "FreeCodeCamp", "type": "Thực hành", "url": "https://www.freecodecamp.org/"}
            ]
        }
        return resources.get(topic, [
            {"name": "YouTube - Công nghệ thông tin", "type": "Video", "url": "https://youtube.com"},
            {"name": "Stack Overflow", "type": "Cộng đồng", "url": "https://stackoverflow.com/"}
        ])
    
    def _create_roadmap(self, topic: str, skills: List[str]) -> List[Dict]:
        """Tạo lộ trình học"""
        roadmap = []
        weeks = ["Tuần 1-2", "Tuần 3-4", "Tuần 5-6", "Tuần 7-8"]
        for i, week in enumerate(weeks):
            if i < len(skills):
                roadmap.append({
                    "week": week,
                    "focus": skills[i],
                    "activities": f"Học các khái niệm cơ bản về {skills[i]}, thực hành qua bài tập nhỏ"
                })
        return roadmap
    
    def _estimate_time(self, content: str) -> str:
        """Ước lượng thời gian học"""
        word_count = len(content.split())
        if word_count < 500:
            return "30 phút - 1 giờ"
        elif word_count < 1500:
            return "1-2 giờ"
        else:
            return "2-3 giờ"

# Khởi tạo global instance
learning_ai = LearningAI()