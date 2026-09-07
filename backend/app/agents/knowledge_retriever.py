"""知识检索Agent（流程三）。检索本身走 RagService（向量检索桩），
本 Agent 负责按第三节·1 构造查询文本，以及后续可选的 LLM 摘要/重排。
"""
from sqlalchemy.orm import Session

from app.schemas.event import EventStructuredData
from app.schemas.knowledge import RetrievalResult
from app.services.rag_service import RagService


class KnowledgeRetrieverAgent:
    run_type = "knowledge_retrieval"

    def __init__(self, db: Session, rag_service: RagService | None = None):
        self.db = db
        self.rag_service = rag_service or RagService(db)

    def build_query(self, *, event: EventStructuredData, activity_type: str | None = None) -> str:
        """第三节·1：根据事件类型/地点/风险等级/活动类型/参与岗位/处置目标构造查询。"""
        parts = [
            event.event_type,
            event.location,
            event.risk_level or "",
            activity_type or "",
            "、".join(event.involved_roles),
            "、".join(event.response_objectives),
        ]
        return " ".join(p for p in parts if p)

    def retrieve(self, *, event: EventStructuredData, activity_type: str | None = None) -> RetrievalResult:
        query_text = self.build_query(event=event, activity_type=activity_type)
        return self.rag_service.search(query_text)
