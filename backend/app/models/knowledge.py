from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._common import new_id, utcnow

# 文档分类（模块4）
KNOWLEDGE_CATEGORIES = [
    "scene_material",  # 场景资料
    "emergency_plan",  # 应急预案
    "historical_case",  # 历史案例
    "role_responsibility",  # 岗位职责
    "plan_template",  # 预案模板
    "report_template",  # 复盘模板
]


class KnowledgeDocument(Base):
    """知识文档（模块4）。"""

    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("DOC"))
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(50))
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|parsing|embedding|enabled|disabled
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    """知识切片，供语义检索使用。"""

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("CHUNK"))
    document_id: Mapped[str] = mapped_column(String(40), ForeignKey("knowledge_documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")


class RetrievalRecord(Base):
    """检索记录（流程三）。"""

    __tablename__ = "retrieval_records"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("RETR"))
    event_id: Mapped[str] = mapped_column(String(40), ForeignKey("events.id"))
    query_text: Mapped[str] = mapped_column(Text)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 相关预案/相似案例/岗位职责/场景知识
    selected_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
