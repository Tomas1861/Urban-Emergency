"""应急预案相关 Schema（流程四）。structured_content 覆盖第五节·2 固定的九个部分。"""
from pydantic import BaseModel, Field


class EventSummary(BaseModel):
    """第一部分：事件概况。"""

    time: str
    location: str
    description: str
    impact: str


class Objective(BaseModel):
    priority: int
    content: str


class RoleResponsibility(BaseModel):
    role_name: str
    responsibilities: list[str] = Field(default_factory=list)


class Phase(BaseModel):
    phase_code: str
    phase_name: str
    target: str
    actions: list[str] = Field(default_factory=list)


class RoleRequirement(BaseModel):
    """第六部分：岗位处置要求。"""

    role_name: str
    requirements: list[str] = Field(default_factory=list)


class ReportingMechanism(BaseModel):
    """第七部分：信息报告机制。"""

    report_to: str
    frequency: str
    required_fields: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    document_id: str
    document_title: str
    section: str | None = None


class PlanStructuredContent(BaseModel):
    """预案生成Agent必须输出的结构化 JSON（第四节·3）。"""

    title: str
    event_summary: EventSummary
    objectives: list[Objective] = Field(default_factory=list)
    principles: list[str] = Field(default_factory=list)
    roles: list[RoleResponsibility] = Field(default_factory=list)
    phases: list[Phase] = Field(default_factory=list)
    role_requirements: list[RoleRequirement] = Field(default_factory=list)
    reporting: ReportingMechanism
    escalation_conditions: list[str] = Field(default_factory=list)
    reinforcement_conditions: list[str] = Field(default_factory=list)
    recovery_conditions: list[str] = Field(default_factory=list)
    termination_conditions: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class PlanGenerateRequest(BaseModel):
    """event_id 取自 URL 路径 /api/events/{event_id}/generate-plan，此处无需重复传入。"""

    template_id: str | None = None
    supplementary_requirements: str | None = None


class PlanSectionRegenerateRequest(BaseModel):
    """局部重新生成（第四节·6），仅重写指定字段，其余章节保留。"""

    section: str  # 如 objectives / role_requirements / recovery_conditions
    supplementary_requirements: str | None = None


class PlanVersionOut(BaseModel):
    id: str
    plan_id: str
    version_number: int
    source_type: str
    structured_content: PlanStructuredContent | None
    markdown_content: str | None
    citations: list[Citation] = Field(default_factory=list)
    change_summary: str | None
    created_by: str | None

    model_config = {"from_attributes": True}


class PlanOut(BaseModel):
    id: str
    event_id: str
    title: str | None
    status: str
    current_version_id: str | None

    model_config = {"from_attributes": True}
