from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._common import new_id, utcnow

if TYPE_CHECKING:
    from app.models.activity import Role
    from app.models.plan import Plan

# 任务状态（第四节）
TASK_STATUSES = ["pending_confirm", "not_started", "in_progress", "completed", "incomplete", "cancelled"]
# 合法状态流转（流程六·2）
TASK_TRANSITIONS = {
    "not_started": {"in_progress", "cancelled"},
    "in_progress": {"completed", "incomplete", "cancelled"},
}


class Task(Base):
    """岗位任务（流程五）。字段对齐第五节·4 的任务JSON结构。"""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("TASK"))
    plan_id: Mapped[str] = mapped_column(String(40), ForeignKey("plans.id"))
    plan_version_id: Mapped[str] = mapped_column(String(40), ForeignKey("plan_versions.id"))
    task_code: Mapped[str] = mapped_column(String(50))  # 如 TASK-001
    task_name: Mapped[str] = mapped_column(String(300))
    role_id: Mapped[str] = mapped_column(String(40), ForeignKey("roles.id"))
    phase_code: Mapped[str | None] = mapped_column(String(20), nullable=True)  # P1立即响应/P2现场控制/...
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    action_text: Mapped[str] = mapped_column(Text)
    trigger_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    planned_start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 分钟，T+N
    deadline_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_people: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_resources_json: Mapped[list] = mapped_column(JSON, default=list)
    collaborating_roles_json: Mapped[list] = mapped_column(JSON, default=list)
    dependencies_json: Mapped[list] = mapped_column(JSON, default=list)  # 依赖的其他 task_code
    completion_criteria: Mapped[str] = mapped_column(Text)
    feedback_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    exception_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending_confirm")

    plan: Mapped["Plan"] = relationship()
    role: Mapped["Role"] = relationship()
    executions: Mapped[list["TaskExecution"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskExecution(Base):
    """任务执行记录（流程六）。"""

    __tablename__ = "task_executions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("EXEC"))
    task_id: Mapped[str] = mapped_column(String(40), ForeignKey("tasks.id"))
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execution_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    temporary_adjustments: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[list] = mapped_column(JSON, default=list)  # 图片/附件URL
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    task: Mapped["Task"] = relationship(back_populates="executions")
