from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.event_analyzer import EventAnalyzerAgent
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import ApiResponse, ok
from app.models.event import Event
from app.models.task import Task, TaskExecution
from app.schemas.event import EventConfirmUpdate, EventCreateRequest, EventOut, EventStructuredData
from app.schemas.execution import ExecutionSummary

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=ApiResponse)
def list_events(activity_id: str | None = None, db: Session = Depends(get_db)):
    """第十节接口清单未给出事件列表路径，但页面3"活动详情"需要展示事件列表，这里补一个最小实现。"""
    query = db.query(Event)
    if activity_id:
        query = query.filter(Event.activity_id == activity_id)
    events = query.order_by(Event.created_at.desc()).all()
    return ok([_to_event_out(e).model_dump(mode="json") for e in events])


@router.post("", response_model=ApiResponse)
def create_event(payload: EventCreateRequest, db: Session = Depends(get_db)):
    if payload.input_mode not in ("form", "natural_language"):
        raise BusinessError("INVALID_INPUT_MODE", "input_mode 必须为 form 或 natural_language")

    if payload.input_mode == "natural_language":
        if not payload.raw_text:
            raise BusinessError("MISSING_RAW_TEXT", "自然语言录入方式下 raw_text 不能为空")
        event = Event(
            activity_id=payload.activity_id,
            scene_id=payload.scene_id,
            event_name="待AI分析",
            structured_data_json={"raw_text": payload.raw_text},
            status="EVENT_CREATED",
        )
    else:
        if not payload.form:
            raise BusinessError("MISSING_FORM", "表单录入方式下 form 不能为空")
        form = payload.form
        structured = EventStructuredData(
            event_name=form.event_name,
            event_type=form.event_type,
            occurred_at=form.occurred_at,
            location=form.location,
            current_impact=form.current_impact,
            risk_level=form.risk_level,
            estimated_duration_minutes=form.estimated_duration_minutes,
            affected_areas=form.affected_areas,
            involved_roles=form.involved_roles,
            available_resources=form.available_resources,
            response_objectives=[],
            missing_information=[],
        )
        event = Event(
            activity_id=payload.activity_id,
            scene_id=payload.scene_id,
            event_name=form.event_name,
            event_type=form.event_type,
            occurred_at=form.occurred_at,
            location=form.location,
            description=form.description,
            current_impact=form.current_impact,
            risk_level=form.risk_level,
            estimated_duration=form.estimated_duration_minutes,
            structured_data_json=structured.model_dump(mode="json"),
            status="EVENT_ANALYZING",  # 表单录入无需AI分析，直接进入"待确认"
        )

    db.add(event)
    db.commit()
    db.refresh(event)
    return ok(_to_event_out(event).model_dump(mode="json"))


@router.get("/{event_id}", response_model=ApiResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = _get_or_404(db, event_id)
    return ok(_to_event_out(event).model_dump(mode="json"))


@router.put("/{event_id}", response_model=ApiResponse)
def update_event(event_id: str, payload: EventConfirmUpdate, db: Session = Depends(get_db)):
    """第二节·5：人工确认前可修改事件类型/风险等级/影响范围/参与岗位/资源情况/处置目标/信息缺口。"""
    event = _get_or_404(db, event_id)
    structured = dict(event.structured_data_json or {})
    for field, value in payload.model_dump(exclude_none=True).items():
        structured[field] = value
    event.structured_data_json = structured
    if payload.event_type:
        event.event_type = payload.event_type
    if payload.risk_level:
        event.risk_level = payload.risk_level
    db.commit()
    db.refresh(event)
    return ok(_to_event_out(event).model_dump(mode="json"))


@router.post("/{event_id}/analyze", response_model=ApiResponse)
def analyze_event(event_id: str, db: Session = Depends(get_db)):
    event = _get_or_404(db, event_id)
    raw_text = (event.structured_data_json or {}).get("raw_text")
    if not raw_text:
        raise BusinessError("NO_RAW_TEXT", "该事件不是自然语言录入，无需调用事件分析Agent")

    agent = EventAnalyzerAgent(db)
    structured = agent.analyze(event_id=event_id, raw_text=raw_text)

    event.event_name = structured.event_name
    event.event_type = structured.event_type
    event.occurred_at = structured.occurred_at
    event.location = structured.location
    event.risk_level = structured.risk_level
    event.current_impact = structured.current_impact
    event.estimated_duration = structured.estimated_duration_minutes
    event.structured_data_json = structured.model_dump(mode="json")
    event.status = "EVENT_ANALYZING"
    db.commit()
    db.refresh(event)
    return ok(_to_event_out(event).model_dump(mode="json"))


@router.post("/{event_id}/confirm", response_model=ApiResponse)
def confirm_event(event_id: str, db: Session = Depends(get_db)):
    event = _get_or_404(db, event_id)
    if event.status != "EVENT_ANALYZING":
        raise BusinessError("INVALID_STATE", f"当前状态为 {event.status}，无法确认事件")
    event.status = "EVENT_CONFIRMED"
    db.commit()
    db.refresh(event)
    return ok(_to_event_out(event).model_dump(mode="json"))


@router.post("/{event_id}/close", response_model=ApiResponse)
def close_event(event_id: str, db: Session = Depends(get_db)):
    """流程六·5：结束事件前提示未开始/执行中/未完成任务数量。"""
    event = _get_or_404(db, event_id)
    event.status = "EVENT_CLOSED"
    db.commit()
    db.refresh(event)
    return ok(_to_event_out(event).model_dump(mode="json"))


@router.get("/{event_id}/execution-summary", response_model=ApiResponse)
def execution_summary(event_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, event_id)
    tasks = db.query(Task).filter(Task.plan.has(event_id=event_id)).all()
    task_ids = [t.id for t in tasks]
    executions = db.query(TaskExecution).filter(TaskExecution.task_id.in_(task_ids)).all()
    latest_by_task = {e.task_id: e for e in executions}

    summary = ExecutionSummary(
        not_started_count=sum(1 for t in tasks if latest_by_task.get(t.id, None) is None
                               or latest_by_task[t.id].status == "not_started"),
        in_progress_count=sum(1 for e in latest_by_task.values() if e.status == "in_progress"),
        incomplete_count=sum(1 for e in latest_by_task.values() if e.status == "incomplete"),
        completed_count=sum(1 for e in latest_by_task.values() if e.status == "completed"),
        cancelled_count=sum(1 for e in latest_by_task.values() if e.status == "cancelled"),
    )
    return ok(summary.model_dump())


def _get_or_404(db: Session, event_id: str) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(f"事件不存在: {event_id}")
    return event


def _to_event_out(event: Event) -> EventOut:
    structured = None
    try:
        raw = dict(event.structured_data_json or {})
        raw.pop("raw_text", None)
        if raw.get("event_name"):
            structured = EventStructuredData.model_validate(raw)
    except Exception:
        structured = None

    return EventOut(
        id=event.id,
        activity_id=event.activity_id,
        scene_id=event.scene_id,
        event_name=event.event_name,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        location=event.location,
        risk_level=event.risk_level,
        current_impact=event.current_impact,
        structured_data=structured,
        status=event.status,
        created_at=event.created_at,
    )
