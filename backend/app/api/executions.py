from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError
from app.core.response import ApiResponse, ok
from app.models.task import TASK_TRANSITIONS, Task, TaskExecution
from app.schemas.execution import TaskExecutionOut, TaskExecutionUpdate

router = APIRouter(prefix="/api/tasks", tags=["executions"])


def _get_task_and_execution(db: Session, task_id: str) -> tuple[Task, TaskExecution]:
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundError(f"任务不存在: {task_id}")
    execution = db.query(TaskExecution).filter(TaskExecution.task_id == task_id).first()
    if not execution:
        execution = TaskExecution(task_id=task_id, status="not_started")
        db.add(execution)
        db.flush()
    return task, execution


def _transition(db: Session, task_id: str, target_status: str, **execution_fields) -> TaskExecutionOut:
    task, execution = _get_task_and_execution(db, task_id)

    current = execution.status
    allowed = TASK_TRANSITIONS.get(current, set())
    if target_status not in allowed:
        raise BusinessError(
            "INVALID_TRANSITION", f"任务当前状态为 {current}，不允许直接转换为 {target_status}"
        )

    execution.status = target_status
    task.status = target_status
    for field, value in execution_fields.items():
        setattr(execution, field, value)
    db.commit()
    db.refresh(execution)
    return _to_out(execution)


@router.post("/{task_id}/start", response_model=ApiResponse)
def start_task(task_id: str, db: Session = Depends(get_db)):
    out = _transition(db, task_id, "in_progress", actual_start_time=datetime.now(timezone.utc))
    return ok(out.model_dump(mode="json"))


@router.post("/{task_id}/complete", response_model=ApiResponse)
def complete_task(task_id: str, db: Session = Depends(get_db)):
    out = _transition(db, task_id, "completed", actual_end_time=datetime.now(timezone.utc))
    return ok(out.model_dump(mode="json"))


@router.post("/{task_id}/fail", response_model=ApiResponse)
def fail_task(task_id: str, db: Session = Depends(get_db)):
    """对应第四节任务状态中的"未完成"。"""
    out = _transition(db, task_id, "incomplete", actual_end_time=datetime.now(timezone.utc))
    return ok(out.model_dump(mode="json"))


@router.post("/{task_id}/cancel", response_model=ApiResponse)
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    out = _transition(db, task_id, "cancelled")
    return ok(out.model_dump(mode="json"))


@router.put("/{task_id}/execution", response_model=ApiResponse)
def update_execution(task_id: str, payload: TaskExecutionUpdate, db: Session = Depends(get_db)):
    _, execution = _get_task_and_execution(db, task_id)
    updates = payload.model_dump(exclude_none=True)
    if "evidence" in updates:
        execution.evidence_json = updates.pop("evidence")
    for field, value in updates.items():
        setattr(execution, field, value)
    db.commit()
    db.refresh(execution)
    return ok(_to_out(execution).model_dump(mode="json"))


def _to_out(execution: TaskExecution) -> TaskExecutionOut:
    return TaskExecutionOut(
        execution_id=execution.id,
        task_id=execution.task_id,
        status=execution.status,
        actual_start_time=execution.actual_start_time,
        actual_end_time=execution.actual_end_time,
        executor=execution.executor,
        execution_result=execution.execution_result,
        issues=execution.issues,
        temporary_adjustments=execution.temporary_adjustments,
        evidence=execution.evidence_json or [],
        remarks=execution.remarks,
    )
