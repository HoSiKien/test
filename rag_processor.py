import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from typing import List, Tuple, Dict
import docx
from PyPDF2 import PdfReader
import nltk
from nltk.tokenize import sent_tokenize
from datetime import datetime
import json

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

class RAGProcessor:
    def __init__(self, index_path="data/faiss.index", 
                 chunks_path="data/chunks.pkl",
                 metadata_path="data/metadata.json"):
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.metadata_path = metadata_path
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.index = None
        self.chunks = []          # List of chunk texts
        self.metadata = []        # List of metadata dict for each chunk
        self.documents = {}       # Dict: {doc_id: {"name": "...", "upload_time": "...", "chunk_indices": []}}
        self.load_index()
    
    def load_index(self):
        """Tải FAISS index, chunks và metadata"""
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = data.get('metadata', [])
                    self.documents = data.get('documents', {})
            print(f"Đã tải {len(self.chunks)} đoạn từ {len(self.documents)} tài liệu")
        else:
            self.index = None
            self.chunks = []
            self.metadata = []
            self.documents = {}
    
    def save_index(self):
        """Lưu FAISS index, chunks và metadata"""
        os.makedirs("data", exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.chunks_path, 'wb') as f:
                pickle.dump(self.chunks, f)
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': self.metadata,
                    'documents': self.documents
                }, f, ensure_ascii=False, indent=2)
    
    def read_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text
    
    def read_pdf(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    
    def chunk_semantic(self, text: str, max_chunk_size: int = 600, overlap_sentences: int = 1) -> List[str]:
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_len = 0
        
        for i, sent in enumerate(sentences):
            sent_len = len(sent)
            if current_len + sent_len <= max_chunk_size:
                current_chunk.append(sent)
                current_len += sent_len
            else:
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(chunk_text)
                overlap = current_chunk[-overlap_sentences:] if overlap_sentences > 0 else []
                current_chunk = overlap + [sent]
                current_len = sum(len(s) for s in current_chunk)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks
    
    def process_document(self, file_path: str, file_name: str) -> int:
        """Xử lý tài liệu và lưu kèm metadata"""
        if file_path.endswith('.docx'):
            text = self.read_docx(file_path)
        elif file_path.endswith('.pdf'):
            text = self.read_pdf(file_path)
        else:
            raise ValueError("Chỉ hỗ trợ file .docx và .pdf")
        
        new_chunks = self.chunk_semantic(text, max_chunk_size=600, overlap_sentences=1)
        
        # Tạo document ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_idx = len(self.chunks)
        
        # Lưu chunks và metadata
        for i, chunk in enumerate(new_chunks):
            self.chunks.append(chunk)
            self.metadata.append({
                'doc_id': doc_id,
                'doc_name': file_name,
                'chunk_index': i,
                'upload_time': datetime.now().isoformat()
            })
        
        # Lưu thông tin document
        self.documents[doc_id] = {
            'name': file_name,
            'upload_time': datetime.now().isoformat(),
            'chunk_indices': list(range(start_idx, start_idx + len(new_chunks))),
            'num_chunks': len(new_chunks)
        }
        
        # Tạo embedding cho chunks mới
        embeddings = self.model.encode(new_chunks, normalize_embeddings=True, show_progress_bar=True)
        
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
        
        self.index.add(embeddings)
        self.save_index()
        
        return len(new_chunks)
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Tìm top_k đoạn liên quan, trả về kèm metadata"""
        if self.index is None or len(self.chunks) == 0:
            return []
        
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.chunks):
                results.append((
                    self.chunks[idx],
                    float(scores[0][i]),
                    self.metadata[idx] if idx < len(self.metadata) else {}
                ))
        return results
    
    def get_all_documents(self) -> List[Dict]:
        """Lấy danh sách tất cả tài liệu đã upload"""
        return [
            {
                'id': doc_id,
                'name': info['name'],
                'upload_time': info['upload_time'],
                'num_chunks': info['num_chunks']
            }
            for doc_id, info in self.documents.items()
        ]
    
    def delete_document(self, doc_id: str) -> bool:
        """Xóa tài liệu theo ID và cập nhật lại FAISS index"""
        if doc_id not in self.documents:
            return False
        
        # Lấy danh sách chunk indices cần xóa
        indices_to_remove = set(self.documents[doc_id]['chunk_indices'])
        
        # Tạo danh sách chunk và metadata mới
        new_chunks = []
        new_metadata = []
        new_documents = {}
        
        # Đánh lại index mapping
        index_mapping = {}
        new_idx = 0
        
        for old_idx in range(len(self.chunks)):
            if old_idx not in indices_to_remove:
                index_mapping[old_idx] = new_idx
                new_chunks.append(self.chunks[old_idx])
                new_metadata.append(self.metadata[old_idx])
                new_idx += 1
        
        # Cập nhật documents
        for d_id, doc_info in self.documents.items():
            if d_id != doc_id:
                new_indices = [index_mapping[idx] for idx in doc_info['chunk_indices'] if idx in index_mapping]
                if new_indices:
                    new_documents[d_id] = {
                        'name': doc_info['name'],
                        'upload_time': doc_info['upload_time'],
                        'chunk_indices': new_indices,
                        'num_chunks': len(new_indices)
                    }
        
        # Cập nhật dữ liệu
        self.chunks = new_chunks
        self.metadata = new_metadata
        self.documents = new_documents
        
        # Tạo lại FAISS index
        if self.chunks:
            embeddings = self.model.encode(self.chunks, normalize_embeddings=True, show_progress_bar=True)
            dimension = embeddings.shape[1]
            new_index = faiss.IndexFlatIP(dimension)
            new_index.add(embeddings)
            self.index = new_index
        else:
            self.index = None
        
        self.save_index()
        return True
    
    def clear(self):
        """Xóa toàn bộ dữ liệu"""
        self.index = None
        self.chunks = []
        self.metadata = []
        self.documents = {}
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.chunks_path):
            os.remove(self.chunks_path)
        if os.path.exists(self.metadata_path):
            os.remove(self.metadata_path)

rag = RAGProcessor()