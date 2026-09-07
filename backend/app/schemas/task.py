"""岗位任务相关 Schema（流程五）。"""
from pydantic import BaseModel, Field, field_validator

# 第五节·3 禁止的模糊表达，基础校验时可用于提示（不做强制拦截，MVP仅做轻量提醒）
VAGUE_ACTION_KEYWORDS = ["做好现场管理", "加强安全保障", "及时处置", "密切关注情况"]


class TaskItem(BaseModel):
    """任务分解Agent输出的单项任务（第五节·4）。"""

    task_id: str
    task_name: str
    role_id: str
    role_name: str
    phase_code: str
    location: str
    action: str
    trigger_condition: str
    planned_start_offset_minutes: int
    deadline_minutes: int
    required_people: int
    required_resources: list[str] = Field(default_factory=list)
    collaborating_roles: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    completion_criteria: str
    feedback_requirement: str
    exception_action: str
    source_plan_section: str | None = None

    @field_validator("action")
    @classmethod
    def warn_if_vague(cls, v: str) -> str:
        # 仅作为生成后校验提示的输入，不在此处抛异常；具体拦截逻辑见 services/version_service 的基础校验。
        return v


class TaskGenerationOutput(BaseModel):
    """任务分解Agent一次生成的完整清单。"""

    tasks: list[TaskItem] = Field(default_factory=list)


class TaskGenerateRequest(BaseModel):
    """plan_id 取自 URL 路径 /api/plans/{plan_id}/generate-tasks，此处无需重复传入。"""

    supplementary_requirements: str | None = None


class TaskUpdate(BaseModel):
    task_name: str | None = None
    action: str | None = None
    role_id: str | None = None
    location: str | None = None
    deadline_minutes: int | None = None
    required_people: int | None = None
    required_resources: list[str] | None = None
    completion_criteria: str | None = None
    exception_action: str | None = None
    dependencies: list[str] | None = None
    sort_order: int | None = None


class TaskValidationIssue(BaseModel):
    """第五节·7 基础校验结果。"""

    task_id: str | None
    rule: str
    message: str


class TaskOut(BaseModel):
    id: str
    plan_id: str
    task_code: str
    task_name: str
    role_id: str
    phase_code: str | None
    location: str | None
    action_text: str
    deadline_minutes: int | None
    completion_criteria: str
    status: str

    model_config = {"from_attributes": True}
