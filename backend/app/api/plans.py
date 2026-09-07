from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.agents.plan_generator import PlanGeneratorAgent
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import ApiResponse, ok
from app.models.activity import Role
from app.models.event import Event
from app.models.knowledge import RetrievalRecord
from app.models.plan import Plan, PlanVersion
from app.schemas.event import EventStructuredData
from app.schemas.knowledge import RetrievalResult
from app.schemas.plan import (
    PlanGenerateRequest,
    PlanOut,
    PlanSectionRegenerateRequest,
    PlanStructuredContent,
    PlanVersionOut,
)
from app.services.export_service import ExportService, render_plan_markdown
from app.services.version_service import next_plan_version_number

router = APIRouter(prefix="/api/plans", tags=["plans"])

# POST /api/events/{event_id}/generate-plan 路径前缀是 events，单独用一个 router 挂载。
event_router = APIRouter(prefix="/api/events", tags=["plans"])


@event_router.post("/{event_id}/generate-plan", response_model=ApiResponse)
def generate_plan(event_id: str, payload: PlanGenerateRequest, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(f"事件不存在: {event_id}")
    # PLAN_GENERATING 也允许重新调用：上一次生成失败时事件会停留在这个状态，
    # 若不放行，用户将永远无法重试（见 app/agents/base.py 生成失败处理）。
    if event.status not in ("EVENT_CONFIRMED", "KNOWLEDGE_SELECTED", "PLAN_GENERATING"):
        raise BusinessError("INVALID_STATE", f"当前事件状态为 {event.status}，事件确认后才能生成预案")

    raw = dict(event.structured_data_json or {})
    raw.pop("raw_text", None)
    structured_event = EventStructuredData.model_validate(raw)

    record = (
        db.query(RetrievalRecord)
        .filter(RetrievalRecord.event_id == event_id)
        .order_by(RetrievalRecord.created_at.desc())
        .first()
    )
    if record:
        full_result = RetrievalResult.model_validate(record.result_json)
        selected_ids = set(record.selected_chunk_ids or [])
        knowledge = RetrievalResult(
            related_plans=[p for p in full_result.related_plans if p.document_id in selected_ids] or full_result.related_plans,
            similar_cases=full_result.similar_cases,
            role_responsibilities=full_result.role_responsibilities,
            scene_knowledge=full_result.scene_knowledge,
        )
    else:
        knowledge = RetrievalResult()

    roles = db.query(Role).filter(Role.status == "active").all()
    role_json = str([{"role_name": r.role_name, "responsibility": r.responsibility_text} for r in roles])

    plan = db.query(Plan).filter(Plan.event_id == event_id).first()
    if not plan:
        plan = Plan(event_id=event_id, status="generating")
        db.add(plan)
        db.flush()

    event.status = "PLAN_GENERATING"
    db.flush()

    agent = PlanGeneratorAgent(db)
    structured_plan = agent.generate(
        event_id=event_id,
        event_json=structured_event.model_dump_json(),
        knowledge=knowledge,
        role_json=role_json,
        supplementary_requirements=payload.supplementary_requirements or "",
    )

    version = PlanVersion(
        plan_id=plan.id,
        version_number=next_plan_version_number(db, plan.id),
        source_type="ai_full",
        structured_content_json=structured_plan.model_dump(mode="json"),
        markdown_content=render_plan_markdown(structured_plan),
        citation_json=[c.model_dump(mode="json") for c in structured_plan.citations],
        change_summary="AI 完整生成",
    )
    db.add(version)
    db.flush()

    plan.title = structured_plan.title
    plan.current_version_id = version.id
    plan.status = "draft"
    event.status = "PLAN_DRAFTED"
    db.commit()
    db.refresh(version)

    return ok(PlanVersionOut.model_validate(_version_out(version)).model_dump(mode="json"))


@router.get("", response_model=ApiResponse)
def find_plan_by_event(event_id: str, db: Session = Depends(get_db)):
    """第十节接口清单未给出"按事件查预案"路径，但前端刷新/直接进入预案页时需要按 event_id 查找，这里补一个最小实现。"""
    plan = db.query(Plan).filter(Plan.event_id == event_id).first()
    return ok(PlanOut.model_validate(plan).model_dump(mode="json") if plan else None)


@router.get("/{plan_id}", response_model=ApiResponse)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = _get_or_404(db, plan_id)
    return ok(PlanOut.model_validate(plan).model_dump(mode="json"))


@router.get("/{plan_id}/versions", response_model=ApiResponse)
def list_versions(plan_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, plan_id)
    versions = db.query(PlanVersion).filter(PlanVersion.plan_id == plan_id).order_by(PlanVersion.version_number).all()
    return ok([PlanVersionOut.model_validate(_version_out(v)).model_dump(mode="json") for v in versions])


@router.post("/{plan_id}/versions", response_model=ApiResponse)
def save_manual_version(plan_id: str, content: PlanStructuredContent, change_summary: str = "", db: Session = Depends(get_db)):
    """人工编辑后保存新版本（第四节·7）。"""
    plan = _get_or_404(db, plan_id)
    version = PlanVersion(
        plan_id=plan_id,
        version_number=next_plan_version_number(db, plan_id),
        source_type="manual_edit",
        structured_content_json=content.model_dump(mode="json"),
        markdown_content=render_plan_markdown(content),
        citation_json=[c.model_dump(mode="json") for c in content.citations],
        change_summary=change_summary,
    )
    db.add(version)
    db.flush()
    plan.title = content.title
    plan.current_version_id = version.id
    plan.status = "revising"
    db.commit()
    db.refresh(version)
    return ok(PlanVersionOut.model_validate(_version_out(version)).model_dump(mode="json"))


@router.post("/{plan_id}/regenerate-section", response_model=ApiResponse)
def regenerate_section(plan_id: str, payload: PlanSectionRegenerateRequest, db: Session = Depends(get_db)):
    """第四节·6 局部重新生成：仅重写指定章节，其余保留。"""
    plan = _get_or_404(db, plan_id)
    current_version = db.get(PlanVersion, plan.current_version_id) if plan.current_version_id else None
    if not current_version:
        raise BusinessError("NO_CURRENT_VERSION", "预案尚无当前版本，无法局部重新生成")

    current_content = PlanStructuredContent.model_validate(current_version.structured_content_json)

    agent = PlanGeneratorAgent(db)
    new_content = agent.regenerate_section(
        plan_id=plan_id,
        section=payload.section,
        current_plan=current_content,
        supplementary_requirements=payload.supplementary_requirements or "",
    )

    version = PlanVersion(
        plan_id=plan_id,
        version_number=next_plan_version_number(db, plan_id),
        source_type="ai_section",
        structured_content_json=new_content.model_dump(mode="json"),
        markdown_content=render_plan_markdown(new_content),
        citation_json=[c.model_dump(mode="json") for c in new_content.citations],
        change_summary=f"局部重新生成：{payload.section}",
    )
    db.add(version)
    db.flush()
    plan.current_version_id = version.id
    plan.status = "revising"
    db.commit()
    db.refresh(version)
    return ok(PlanVersionOut.model_validate(_version_out(version)).model_dump(mode="json"))


@router.post("/{plan_id}/confirm", response_model=ApiResponse)
def confirm_plan(plan_id: str, confirmed_by: str | None = None, db: Session = Depends(get_db)):
    plan = _get_or_404(db, plan_id)
    if not plan.current_version_id:
        raise BusinessError("NO_CURRENT_VERSION", "预案尚无当前版本，无法确认")
    plan.status = "confirmed"
    plan.confirmed_by = confirmed_by
    plan.confirmed_at = datetime.now(timezone.utc)

    event = db.get(Event, plan.event_id)
    if event:
        event.status = "PLAN_CONFIRMED"

    db.commit()
    db.refresh(plan)
    return ok(PlanOut.model_validate(plan).model_dump(mode="json"))


@router.get("/{plan_id}/export")
def export_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = _get_or_404(db, plan_id)
    if not plan.current_version_id:
        raise BusinessError("NO_CURRENT_VERSION", "预案尚无当前版本，无法导出")
    version = db.get(PlanVersion, plan.current_version_id)

    export_service = ExportService()
    file_path = export_service.export_markdown_to_docx(
        title=plan.title or "应急预案", markdown_content=version.markdown_content or ""
    )
    return FileResponse(file_path, filename=f"{plan.title or 'plan'}.docx")


def _get_or_404(db: Session, plan_id: str) -> Plan:
    plan = db.get(Plan, plan_id)
    if not plan:
        raise NotFoundError(f"预案不存在: {plan_id}")
    return plan


def _version_out(version: PlanVersion) -> dict:
    return {
        "id": version.id,
        "plan_id": version.plan_id,
        "version_number": version.version_number,
        "source_type": version.source_type,
        "structured_content": version.structured_content_json or None,
        "markdown_content": version.markdown_content,
        "citations": version.citation_json or [],
        "change_summary": version.change_summary,
        "created_by": version.created_by,
    }
