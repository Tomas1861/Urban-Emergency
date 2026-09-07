from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.agents.report_generator import ReportGeneratorAgent
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import ApiResponse, ok
from app.models.event import Event
from app.models.knowledge import KnowledgeDocument
from app.models.plan import Plan, PlanVersion
from app.models.report import Report, ReportVersion
from app.models.task import Task, TaskExecution
from app.schemas.plan import PlanStructuredContent
from app.schemas.report import (
    ReportGenerateRequest,
    ReportOut,
    ReportStructuredContent,
    ReportVersionOut,
    RoleStatistics,
    TaskStatistics,
)
from app.services.export_service import ExportService, render_report_markdown
from app.services.version_service import next_report_version_number

router = APIRouter(prefix="/api/reports", tags=["reports"])
event_router = APIRouter(prefix="/api/events", tags=["reports"])


def _compute_task_statistics(tasks: list[Task], executions_by_task: dict[str, TaskExecution]) -> TaskStatistics:
    """第七节·3：由代码计算，禁止交给大模型计算。"""
    stats = TaskStatistics(total=len(tasks))
    durations = []
    for task in tasks:
        execution = executions_by_task.get(task.id)
        status = execution.status if execution else "not_started"
        if status == "completed":
            stats.completed += 1
            if execution.actual_start_time and execution.actual_end_time:
                elapsed_minutes = (execution.actual_end_time - execution.actual_start_time).total_seconds() / 60
                durations.append(elapsed_minutes)
                if task.deadline_minutes is not None and elapsed_minutes <= task.deadline_minutes:
                    stats.on_time += 1
                elif task.deadline_minutes is not None:
                    stats.delayed += 1
        elif status == "incomplete":
            stats.incomplete += 1
        elif status == "cancelled":
            stats.cancelled += 1
        if execution and (execution.temporary_adjustments or "").strip():
            stats.with_temporary_adjustment += 1

    if durations:
        stats.actual_response_minutes = sum(durations) / len(durations)
    deadlines = [t.deadline_minutes for t in tasks if t.deadline_minutes is not None]
    if deadlines:
        stats.planned_response_minutes = sum(deadlines) / len(deadlines)
    return stats


def _compute_role_statistics(tasks: list[Task], executions_by_task: dict[str, TaskExecution]) -> list[RoleStatistics]:
    by_role: dict[str, dict[str, int]] = {}
    for task in tasks:
        role_name = task.role.role_name if task.role else task.role_id
        bucket = by_role.setdefault(role_name, {"total": 0, "completed": 0})
        bucket["total"] += 1
        execution = executions_by_task.get(task.id)
        if execution and execution.status == "completed":
            bucket["completed"] += 1

    return [
        RoleStatistics(role_name=name, total=v["total"], completed=v["completed"],
                        completion_rate=(v["completed"] / v["total"]) if v["total"] else 0.0)
        for name, v in by_role.items()
    ]


@event_router.post("/{event_id}/generate-report", response_model=ApiResponse)
def generate_report(event_id: str, payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(f"事件不存在: {event_id}")
    # REPORT_GENERATING 也允许重新调用：同 plans.generate_plan 的重试放行逻辑。
    if event.status not in ("EVENT_CLOSED", "REPORT_GENERATING"):
        raise BusinessError("INVALID_STATE", "事件需状态为已结束才能生成复盘报告（管理员可另行放开）")

    plan = db.query(Plan).filter(Plan.event_id == event_id).first()
    if not plan or not plan.current_version_id:
        raise BusinessError("NO_CONFIRMED_PLAN", "该事件尚无已确认预案，无法生成复盘报告")
    plan_version = db.get(PlanVersion, plan.current_version_id)
    plan_content = PlanStructuredContent.model_validate(plan_version.structured_content_json)

    tasks = db.query(Task).filter(Task.plan_id == plan.id).all()
    executions = db.query(TaskExecution).filter(TaskExecution.task_id.in_([t.id for t in tasks])).all()
    executions_by_task = {e.task_id: e for e in executions}

    task_statistics = _compute_task_statistics(tasks, executions_by_task)
    role_statistics = _compute_role_statistics(tasks, executions_by_task)

    report = db.query(Report).filter(Report.event_id == event_id).first()
    if not report:
        report = Report(event_id=event_id, status="generating")
        db.add(report)
        db.flush()

    event.status = "REPORT_GENERATING"
    db.flush()

    agent = ReportGeneratorAgent(db)
    structured_report = agent.generate(
        event_id=event_id,
        event_json=str(event.structured_data_json),
        plan_json=plan_content.model_dump_json(),
        tasks_json=str([t.task_name for t in tasks]),
        task_statistics=task_statistics,
        role_statistics_json=str([r.model_dump() for r in role_statistics]),
        version_history_json="[]",
        similar_cases_json="[]",
        supplementary_notes=payload.supplementary_notes or "",
    )
    structured_report.role_statistics = role_statistics

    version = ReportVersion(
        report_id=report.id,
        version_number=next_report_version_number(db, report.id),
        structured_content_json=structured_report.model_dump(mode="json"),
        markdown_content=render_report_markdown(structured_report),
        statistics_json=task_statistics.model_dump(mode="json"),
        change_summary="AI 完整生成",
    )
    db.add(version)
    db.flush()

    report.title = structured_report.report_title
    report.current_version_id = version.id
    report.status = "draft"
    event.status = "REPORT_DRAFTED"
    db.commit()
    db.refresh(version)
    return ok(ReportVersionOut.model_validate(_version_out(version)).model_dump(mode="json"))


@router.get("", response_model=ApiResponse)
def find_report_by_event(event_id: str, db: Session = Depends(get_db)):
    """同 plans.find_plan_by_event：第十节未给出按事件查复盘报告的路径，这里补一个最小实现。"""
    report = db.query(Report).filter(Report.event_id == event_id).first()
    return ok(ReportOut.model_validate(report).model_dump(mode="json") if report else None)


@router.get("/{report_id}", response_model=ApiResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = _get_or_404(db, report_id)
    return ok(ReportOut.model_validate(report).model_dump(mode="json"))


@router.get("/{report_id}/versions", response_model=ApiResponse)
def list_versions(report_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, report_id)
    versions = db.query(ReportVersion).filter(ReportVersion.report_id == report_id).order_by(ReportVersion.version_number).all()
    return ok([ReportVersionOut.model_validate(_version_out(v)).model_dump(mode="json") for v in versions])


@router.post("/{report_id}/versions", response_model=ApiResponse)
def save_manual_version(report_id: str, content: ReportStructuredContent, change_summary: str = "", db: Session = Depends(get_db)):
    report = _get_or_404(db, report_id)
    version = ReportVersion(
        report_id=report_id,
        version_number=next_report_version_number(db, report_id),
        structured_content_json=content.model_dump(mode="json"),
        markdown_content=render_report_markdown(content),
        statistics_json=content.task_statistics.model_dump(mode="json"),
        change_summary=change_summary,
    )
    db.add(version)
    db.flush()
    report.title = content.report_title
    report.current_version_id = version.id
    report.status = "revising"
    db.commit()
    db.refresh(version)
    return ok(ReportVersionOut.model_validate(_version_out(version)).model_dump(mode="json"))


@router.post("/{report_id}/confirm", response_model=ApiResponse)
def confirm_report(report_id: str, confirmed_by: str | None = None, db: Session = Depends(get_db)):
    report = _get_or_404(db, report_id)
    if not report.current_version_id:
        raise BusinessError("NO_CURRENT_VERSION", "复盘报告尚无当前版本，无法确认")
    report.status = "confirmed"
    report.confirmed_by = confirmed_by
    report.confirmed_at = datetime.now(timezone.utc)

    event = db.get(Event, report.event_id)
    if event:
        event.status = "REPORT_CONFIRMED"

    db.commit()
    db.refresh(report)
    return ok(ReportOut.model_validate(report).model_dump(mode="json"))


@router.post("/{report_id}/save-as-case", response_model=ApiResponse)
def save_as_case(report_id: str, db: Session = Depends(get_db)):
    """第七节·8 案例沉淀摘要 回写知识库，闭合"生成—验证—优化—沉淀"闭环。"""
    report = _get_or_404(db, report_id)
    if not report.current_version_id:
        raise BusinessError("NO_CURRENT_VERSION", "复盘报告尚无当前版本，无法沉淀为案例")
    version = db.get(ReportVersion, report.current_version_id)
    structured = ReportStructuredContent.model_validate(version.structured_content_json)

    case_doc = KnowledgeDocument(
        title=f"【案例】{report.title or structured.report_title}",
        category="historical_case",
        parsed_text=render_report_markdown(structured),
        status="enabled",
    )
    db.add(case_doc)
    db.commit()
    db.refresh(case_doc)
    return ok({"knowledge_document_id": case_doc.id, "tags": structured.case_summary.tags})


@router.get("/{report_id}/export")
def export_report(report_id: str, db: Session = Depends(get_db)):
    report = _get_or_404(db, report_id)
    if not report.current_version_id:
        raise BusinessError("NO_CURRENT_VERSION", "复盘报告尚无当前版本，无法导出")
    version = db.get(ReportVersion, report.current_version_id)

    export_service = ExportService()
    file_path = export_service.export_markdown_to_docx(
        title=report.title or "复盘报告", markdown_content=version.markdown_content or ""
    )
    return FileResponse(file_path, filename=f"{report.title or 'report'}.docx")


def _get_or_404(db: Session, report_id: str) -> Report:
    report = db.get(Report, report_id)
    if not report:
        raise NotFoundError(f"复盘报告不存在: {report_id}")
    return report


def _version_out(version: ReportVersion) -> dict:
    return {
        "id": version.id,
        "report_id": version.report_id,
        "version_number": version.version_number,
        "structured_content": version.structured_content_json or None,
        "markdown_content": version.markdown_content,
        "statistics": version.statistics_json or None,
        "change_summary": version.change_summary,
    }
