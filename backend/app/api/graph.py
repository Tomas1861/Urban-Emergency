"""GraphRAG 轻量版接口：知识文档 → 实体/关系抽取 → Neo4j → 图谱可视化与基础检索。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.entity_extractor import EntityExtractorAgent
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import ApiResponse, ok
from app.models.knowledge import KnowledgeDocument
from app.services.graph_service import GraphService

router = APIRouter(prefix="/api/graph", tags=["graph"])

_MAX_CHARS = 6000  # 单次抽取的文本上限，避免超长文档一次性喂给模型


def _get_graph_service() -> GraphService:
    try:
        service = GraphService()
        service.verify_connectivity()
        return service
    except Exception as exc:  # noqa: BLE001
        raise BusinessError(
            "GRAPH_DB_UNAVAILABLE", f"无法连接 Neo4j，请检查 .env 中的 NEO4J_* 配置：{exc}", status_code=503
        ) from exc


@router.post("/documents/{document_id}/build", response_model=ApiResponse)
def build_document_graph(document_id: str, db: Session = Depends(get_db)):
    document = db.get(KnowledgeDocument, document_id)
    if not document:
        raise NotFoundError(f"知识文档不存在: {document_id}")
    if not document.parsed_text:
        raise BusinessError("NO_PARSED_TEXT", "该文档尚未解析出文本内容，无法构建图谱")

    graph = _get_graph_service()
    try:
        graph.clear_document(document_id)
        agent = EntityExtractorAgent(db)
        result = agent.extract(document_id=document_id, text=document.parsed_text[:_MAX_CHARS])

        chunk_id = f"{document_id}-full"
        for entity in result.entities:
            graph.upsert_entity(
                name=entity.name, entity_type=entity.type, description=entity.description,
                document_id=document_id, chunk_id=chunk_id,
            )
        for rel in result.relationships:
            graph.upsert_relationship(
                source=rel.source, target=rel.target, rel_type=rel.type, description=rel.description
            )
    finally:
        graph.close()

    return ok({
        "document_id": document_id,
        "entity_count": len(result.entities),
        "relationship_count": len(result.relationships),
    })


@router.get("/graph", response_model=ApiResponse)
def get_graph(document_id: str | None = None):
    graph = _get_graph_service()
    try:
        data = graph.get_graph(document_id=document_id)
    finally:
        graph.close()
    return ok(data)


@router.get("/search", response_model=ApiResponse)
def search_graph(q: str):
    graph = _get_graph_service()
    try:
        results = graph.search_entities(q)
    finally:
        graph.close()
    return ok(results)


@router.get("/stats", response_model=ApiResponse)
def graph_stats():
    graph = _get_graph_service()
    try:
        data = graph.stats()
    finally:
        graph.close()
    return ok(data)
