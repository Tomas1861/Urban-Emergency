"""任务执行记录相关 Schema（流程六）。"""
from datetime import datetime

from pydantic import BaseModel, Field


class TaskExecutionUpdate(BaseModel):
    actual_start_time: datetime | None = None
    actual_end_time: datetime | None = None
    executor: str | None = None
    execution_result: str | None = None
    issues: str | None = None
    temporary_adjustments: str | None = None
    evidence: list[str] = Field(default_factory=list)
    remarks: str | None = None


class TaskExecutionOut(BaseModel):
    execution_id: str
    task_id: str
    status: str
    actual_start_time: datetime | None
    actual_end_time: datetime | None
    executor: str | None
    execution_result: str | None
    issues: str | None
    temporary_adjustments: str | None
    evidence: list[str] = Field(default_factory=list)
    remarks: str | None

    model_config = {"from_attributes": True}


class ExecutionSummary(BaseModel):
    """流程六·5 事件结束前提示。"""

    not_started_count: int
    in_progress_count: int
    incomplete_count: int
    completed_count: int
    cancelled_count: int
