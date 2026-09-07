from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.task_generator import TaskGeneratorAgent
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError, ValidationFailedError
from app.core.response import ApiResponse, ok
from app.models.activity import Role
from app.models.plan import Plan, PlanVersion
from app.models.task import Task
from app.schemas.plan import PlanStructuredContent
from app.schemas.task import TaskGenerateRequest, TaskItem, TaskOut, TaskUpdate
from app.services.version_service import validate_task_list

router = APIRouter(tags=["tasks"])

plan_router = APIRouter(prefix="/api/plans", tags=["tasks"])


@plan_router.post("/{plan_id}/generate-tasks", response_model=ApiResponse)
def generate_tasks(plan_id: str, payload: TaskGenerateRequest, db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise NotFoundError(f"预案不存在: {plan_id}")
    if plan.status != "confirmed":
        raise BusinessError("INVALID_STATE", "只有状态为已确认的预案才能生成岗位任务清单")

    current_version = db.get(PlanVersion, plan.current_version_id)
    plan_content = PlanStructuredContent.model_validate(current_version.structured_content_json)

    roles = db.query(Role).filter(Role.status == "active").all()
    role_by_name = {r.role_name: r for r in roles}
    roles_json = str([r.role_name for r in roles])
    role_responsibility_json = str([{"role_name": r.role_name, "responsibility": r.responsibility_text} for r in roles])

    agent = TaskGeneratorAgent(db)
    generation = agent.generate(
        plan_id=plan_id,
        plan=plan_content,
        roles_json=roles_json,
        role_responsibility_json=role_responsibility_json,
        supplementary_requirements=payload.supplementary_requirements or "",
    )

    # 清空旧的待确认任务，写入新一轮生成结果（MVP 简化：不保留历史任务版本）
    db.query(Task).filter(Task.plan_id == plan_id, Task.status == "pending_confirm").delete()

    created: list[Task] = []
    for idx, item in enumerate(generation.tasks):
        role = role_by_name.get(item.role_name)
        task = Task(
            plan_id=plan_id,
            plan_version_id=plan.current_version_id,
            task_code=item.task_id,
            task_name=item.task_name,
            role_id=role.id if role else item.role_id,
            phase_code=item.phase_code,
            location=item.location,
            action_text=item.action,
            trigger_condition=item.trigger_condition,
            planned_start_offset=item.planned_start_offset_minutes,
            deadline_minutes=item.deadline_minutes,
            required_people=item.required_people,
            required_resources_json=item.required_resources,
            collaborating_roles_json=item.collaborating_roles,
            dependencies_json=item.dependencies,
            completion_criteria=item.completion_criteria,
            feedback_requirement=item.feedback_requirement,
            exception_action=item.exception_action,
            sort_order=idx,
            status="pending_confirm",
        )
        db.add(task)
        created.append(task)

    db.commit()
    return ok([TaskOut.model_validate(t).model_dump(mode="json") for t in created])


@plan_router.get("/{plan_id}/tasks", response_model=ApiResponse)
def list_plan_tasks(plan_id: str, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.plan_id == plan_id).order_by(Task.sort_order).all()
    return ok([TaskOut.model_validate(t).model_dump(mode="json") for t in tasks])


@plan_router.post("/{plan_id}/confirm-tasks", response_model=ApiResponse)
def confirm_tasks(plan_id: str, db: Session = Depends(get_db)):
    """第五节·7 基础校验：存在严重问题时不允许确认任务清单。"""
    plan = db.get(Plan, plan_id)
    if not plan:
        raise NotFoundError(f"预案不存在: {plan_id}")

    tasks = db.query(Task).filter(Task.plan_id == plan_id).all()
    if not tasks:
        raise BusinessError("NO_TASKS", "该预案尚无岗位任务，无法确认")

    known_role_ids = {r.id for r in db.query(Role).all()}
    task_items = [_task_to_item(t) for t in tasks]
    issues = validate_task_list(task_items, known_role_ids=known_role_ids)
    if issues:
        raise ValidationFailedError("任务清单存在严重问题，无法确认", [f"{i.task_id}: {i.message}" for i in issues])

    for task in tasks:
        task.status = "not_started"
    db.commit()
    return ok({"plan_id": plan_id, "confirmed_task_count": len(tasks)})


@router.post("/api/tasks", response_model=ApiResponse)
def create_task(plan_id: str, item: TaskItem, db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise NotFoundError(f"预案不存在: {plan_id}")
    role = db.query(Role).filter(Role.role_name == item.role_name).first()
    task = Task(
        plan_id=plan_id,
        plan_version_id=plan.current_version_id,
        task_code=item.task_id,
        task_name=item.task_name,
        role_id=role.id if role else item.role_id,
        phase_code=item.phase_code,
        location=item.location,
        action_text=item.action,
        trigger_condition=item.trigger_condition,
        planned_start_offset=item.planned_start_offset_minutes,
        deadline_minutes=item.deadline_minutes,
        required_people=item.required_people,
        required_resources_json=item.required_resources,
        collaborating_roles_json=item.collaborating_roles,
        dependencies_json=item.dependencies,
        completion_criteria=item.completion_criteria,
        feedback_requirement=item.feedback_requirement,
        exception_action=item.exception_action,
        status="pending_confirm",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ok(TaskOut.model_validate(task).model_dump(mode="json"))


@router.put("/api/tasks/{task_id}", response_model=ApiResponse)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundError(f"任务不存在: {task_id}")

    updates = payload.model_dump(exclude_none=True)
    if "action" in updates:
        task.action_text = updates.pop("action")
    if "required_resources" in updates:
        task.required_resources_json = updates.pop("required_resources")
    if "dependencies" in updates:
        task.dependencies_json = updates.pop("dependencies")
    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return ok(TaskOut.model_validate(task).model_dump(mode="json"))


@router.delete("/api/tasks/{task_id}", response_model=ApiResponse)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundError(f"任务不存在: {task_id}")
    db.delete(task)
    db.commit()
    return ok({"id": task_id, "deleted": True})


def _task_to_item(task: Task) -> TaskItem:
    return TaskItem(
        task_id=task.task_code,
        task_name=task.task_name,
        role_id=task.role_id,
        role_name=task.role.role_name if task.role else "",
        phase_code=task.phase_code or "",
        location=task.location or "",
        action=task.action_text,
        trigger_condition=task.trigger_condition or "",
        planned_start_offset_minutes=task.planned_start_offset or 0,
        deadline_minutes=task.deadline_minutes or 0,
        required_people=task.required_people or 0,
        required_resources=task.required_resources_json or [],
        collaborating_roles=task.collaborating_roles_json or [],
        dependencies=task.dependencies_json or [],
        completion_criteria=task.completion_criteria,
        feedback_requirement=task.feedback_requirement or "",
        exception_action=task.exception_action or "",
    )
