"""事件相关 Schema（流程二）。"""
from datetime import datetime

from pydantic import BaseModel, Field


class AvailableResource(BaseModel):
    role: str
    quantity: int


class EventStructuredData(BaseModel):
    """事件分析Agent输出（第二节·4），JSON Schema 校验通过后写入 events.structured_data_json。"""

    event_name: str
    event_type: str
    occurred_at: datetime
    location: str
    risk_level: str | None = None
    current_impact: str
    estimated_duration_minutes: int | None = None
    affected_areas: list[str] = Field(default_factory=list)
    involved_roles: list[str] = Field(default_factory=list)
    available_resources: list[AvailableResource] = Field(default_factory=list)
    response_objectives: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class EventNLInput(BaseModel):
    """方式B：自然语言录入。"""

    activity_id: str
    scene_id: str | None = None
    raw_text: str


class EventFormInput(BaseModel):
    """方式A：表单录入（必填字段见第二节·2，选填见第二节·3）。"""

    activity_id: str
    scene_id: str | None = None
    event_name: str
    event_type: str
    occurred_at: datetime
    location: str
    description: str
    current_impact: str
    achieved_measures: str | None = None

    risk_level: str | None = None
    estimated_duration_minutes: int | None = None
    affected_people: int | None = None
    affected_areas: list[str] = Field(default_factory=list)
    involved_roles: list[str] = Field(default_factory=list)
    available_resources: list[AvailableResource] = Field(default_factory=list)
    supplementary_material: str | None = None
    attachments: list[str] = Field(default_factory=list)


class EventCreateRequest(BaseModel):
    """流程二·1：支持表单录入(form)或自然语言录入(raw_text)两种方式之一。"""

    activity_id: str
    scene_id: str | None = None
    input_mode: str  # "form" | "natural_language"
    raw_text: str | None = None
    form: EventFormInput | None = None


class EventConfirmUpdate(BaseModel):
    """人工确认前可修改的字段（第二节·5）。"""

    event_type: str | None = None
    risk_level: str | None = None
    affected_areas: list[str] | None = None
    involved_roles: list[str] | None = None
    available_resources: list[AvailableResource] | None = None
    response_objectives: list[str] | None = None
    missing_information: list[str] | None = None


class EventOut(BaseModel):
    id: str
    activity_id: str
    scene_id: str | None
    event_name: str
    event_type: str | None
    occurred_at: datetime | None
    location: str | None
    risk_level: str | None
    current_impact: str | None
    structured_data: EventStructuredData | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
