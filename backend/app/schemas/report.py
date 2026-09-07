"""复盘报告相关 Schema（流程七）。"""
from pydantic import BaseModel, Field


class TimelineEntry(BaseModel):
    time: str
    type: str
    description: str


class TaskStatistics(BaseModel):
    """第七节·3：由代码计算，大模型只能解释、不得编造数字。"""

    total: int = 0
    completed: int = 0
    incomplete: int = 0
    cancelled: int = 0
    delayed: int = 0
    on_time: int = 0
    with_temporary_adjustment: int = 0
    planned_response_minutes: float | None = None
    actual_response_minutes: float | None = None


class RoleStatistics(BaseModel):
    role_name: str
    total: int
    completed: int
    completion_rate: float


class Recommendations(BaseModel):
    plan: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    knowledge_base: list[str] = Field(default_factory=list)
    teaching: list[str] = Field(default_factory=list)


class CaseSummary(BaseModel):
    """第八部分：案例沉淀摘要，用于回写知识库。"""

    event_features: list[str] = Field(default_factory=list)
    key_actions: list[str] = Field(default_factory=list)
    lessons: list[str] = Field(default_factory=list)
    applicable_conditions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ReportStructuredContent(BaseModel):
    """复盘报告Agent输出的结构化 JSON（第七节·5）。"""

    report_title: str
    event_summary: dict = Field(default_factory=dict)
    plan_summary: dict = Field(default_factory=dict)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    task_statistics: TaskStatistics
    role_statistics: list[RoleStatistics] = Field(default_factory=list)
    effective_practices: list[str] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    recommendations: Recommendations
    case_summary: CaseSummary


class ReportGenerateRequest(BaseModel):
    """event_id 取自 URL 路径 /api/events/{event_id}/generate-report，此处无需重复传入。"""

    supplementary_notes: str | None = None


class ReportVersionOut(BaseModel):
    id: str
    report_id: str
    version_number: int
    structured_content: ReportStructuredContent | None
    markdown_content: str | None
    statistics: TaskStatistics | None
    change_summary: str | None

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: str
    event_id: str
    title: str | None
    status: str
    current_version_id: str | None

    model_config = {"from_attributes": True}
