from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.agents.knowledge_retriever import KnowledgeRetrieverAgent
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import ApiResponse, ok
from app.models.event import Event
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument, RetrievalRecord
from app.schemas.event import EventStructuredData
from app.schemas.knowledge import RetrievalSelection
from app.services.document_service import DocumentService

router = APIRouter(tags=["knowledge"])


@router.post("/api/knowledge/documents", response_model=ApiResponse)
def upload_document(
    title: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    service = DocumentService()
    content = file.file.read()
    file_path = service.save_upload(file.filename, content)

    document = KnowledgeDocument(title=title, category=category, file_url=file_path, status="parsing")
    db.add(document)
    db.flush()

    try:
        text = service.parse_document(file_path)
        chunks = service.chunk_text(text)
        document.parsed_text = text
        for idx, chunk_content in enumerate(chunks):
            db.add(KnowledgeChunk(document_id=document.id, chunk_index=idx, content=chunk_content))
        document.status = "enabled"  # TODO: 向量化完成后再置为 enabled，当前跳过向量化
    except Exception as exc:  # noqa: BLE001
        document.status = "pending"
        db.commit()
        raise BusinessError("DOCUMENT_PARSE_FAILED", f"文档解析失败: {exc}") from exc

    db.commit()
    db.refresh(document)
    return ok({"id": document.id, "title": document.title, "status": document.status, "chunk_count": len(chunks)})


@router.get("/api/knowledge/documents", response_model=ApiResponse)
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(KnowledgeDocument).all()
    return ok(
        [
            {"id": d.id, "title": d.title, "category": d.category, "status": d.status, "version": d.version}
            for d in documents
        ]
    )


@router.get("/api/knowledge/documents/{document_id}", response_model=ApiResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    document = db.get(KnowledgeDocument, document_id)
    if not document:
        raise NotFoundError(f"知识文档不存在: {document_id}")
    return ok(
        {
            "id": document.id,
            "title": document.title,
            "category": document.category,
            "status": document.status,
            "parsed_text": document.parsed_text,
        }
    )


@router.put("/api/knowledge/documents/{document_id}", response_model=ApiResponse)
def update_document(document_id: str, title: str | None = None, category: str | None = None,
                     status: str | None = None, db: Session = Depends(get_db)):
    document = db.get(KnowledgeDocument, document_id)
    if not document:
        raise NotFoundError(f"知识文档不存在: {document_id}")
    if title:
        document.title = title
    if category:
        document.category = category
    if status:
        document.status = status
    db.commit()
    db.refresh(document)
    return ok({"id": document.id, "title": document.title, "category": document.category, "status": document.status})


@router.delete("/api/knowledge/documents/{document_id}", response_model=ApiResponse)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document = db.get(KnowledgeDocument, document_id)
    if not document:
        raise NotFoundError(f"知识文档不存在: {document_id}")
    db.delete(document)
    db.commit()
    return ok({"id": document_id, "deleted": True})


@router.post("/api/events/{event_id}/retrieve-knowledge", response_model=ApiResponse)
def retrieve_knowledge(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(f"事件不存在: {event_id}")

    raw = dict(event.structured_data_json or {})
    raw.pop("raw_text", None)
    structured = EventStructuredData.model_validate(raw)

    agent = KnowledgeRetrieverAgent(db)
    result = agent.retrieve(event=structured, activity_type=event.activity.type if event.activity else None)

    record = RetrievalRecord(
        event_id=event_id,
        query_text=agent.build_query(event=structured, activity_type=event.activity.type if event.activity else None),
        result_json=result.model_dump(mode="json"),
        selected_chunk_ids=[],
    )
    db.add(record)
    event.status = "KNOWLEDGE_RETRIEVING"
    db.commit()
    db.refresh(record)
    return ok({"retrieval_record_id": record.id, "result": result.model_dump(mode="json")})


@router.put("/api/events/{event_id}/retrieval-selection", response_model=ApiResponse)
def update_retrieval_selection(event_id: str, payload: RetrievalSelection, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(f"事件不存在: {event_id}")

    record = (
        db.query(RetrievalRecord)
        .filter(RetrievalRecord.event_id == event_id)
        .order_by(RetrievalRecord.created_at.desc())
        .first()
    )
    if not record:
        raise BusinessError("NO_RETRIEVAL_RECORD", "请先调用知识检索")

    record.selected_chunk_ids = payload.selected_chunk_ids
    event.status = "KNOWLEDGE_SELECTED"
    db.commit()
    return ok({"retrieval_record_id": record.id, "selected_chunk_ids": payload.selected_chunk_ids})
