"""知识文档服务（模块4）：上传保存、文本解析、切分。

TODO: 向量化（embedding）与向量库写入尚未接入，chunk() 产出的切片
embedding_reference 留空，接入向量库后在 KnowledgeChunk.embedding_reference 回填。
"""
import os
import uuid

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.core.config import get_settings


class DocumentService:
    def __init__(self):
        settings = get_settings()
        self.storage_dir = settings.storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> str:
        ext = os.path.splitext(filename)[1]
        stored_name = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(self.storage_dir, stored_name)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def parse_document(self, file_path: str) -> str:
        """按扩展名解析为纯文本，供后续切分与检索使用。"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path)
        if ext == ".docx":
            return self._parse_docx(file_path)
        if ext in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        raise ValueError(f"不支持的文档格式: {ext}")

    def _parse_pdf(self, file_path: str) -> str:
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _parse_docx(self, file_path: str) -> str:
        doc = DocxDocument(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    def chunk_text(self, text: str, *, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """按字符数做滑动窗口切分（MVP 简化实现，未来可替换为按语义/标题切分）。"""
        if chunk_size <= overlap:
            raise ValueError("chunk_size 必须大于 overlap")

        chunks = []
        start = 0
        text = text.strip()
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks
