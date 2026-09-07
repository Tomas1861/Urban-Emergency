"""活动与场景相关 Schema（流程一）。"""
from datetime import datetime

from pydantic import BaseModel, Field


class ActivityCreate(BaseModel):
    name: str
    type: str
    location: str
    start_time: datetime
    end_time: datetime
    expected_attendance: int | None = None
    description: str | None = None


class ActivityOut(BaseModel):
    id: str
    name: str
    type: str
    location: str
    start_time: datetime
    end_time: datetime
    status: str

    model_config = {"from_attributes": True}


class SceneAreaInput(BaseModel):
    area_name: str
    area_type: str | None = None
    description: str | None = None


class SceneCreate(BaseModel):
    """场景配置（流程一·2）：MVP 场地区域用结构化文本+二维图片表示，不要求 GIS/三维模型。"""

    activity_id: str | None = None
    name: str
    description: str | None = None
    map_file_url: str | None = None
    areas: list[SceneAreaInput] = Field(default_factory=list)
    key_channels: list[str] = Field(default_factory=list)
    entrances: list[str] = Field(default_factory=list)
    key_facilities: list[str] = Field(default_factory=list)
    available_roles: list[str] = Field(default_factory=list)
    base_resources: str | None = None


class SceneOut(BaseModel):
    id: str
    activity_id: str | None
    name: str
    description: str | None
    map_file_url: str | None
    status: str

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    """岗位（模块2 模块清单提到但第十节接口清单未给出路径，此处补一个最小可用版本）。"""

    role_code: str
    role_name: str
    description: str | None = None
    responsibility_text: str | None = None


class RoleOut(BaseModel):
    id: str
    role_code: str
    role_name: str
    responsibility_text: str | None
    status: str

    model_config = {"from_attributes": True}
