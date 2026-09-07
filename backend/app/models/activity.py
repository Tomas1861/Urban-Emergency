from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._common import new_id, utcnow

# 活动状态（第四节·总体业务状态流）
ACTIVITY_STATUSES = ["draft", "active", "ended", "archived"]


class Activity(Base):
    """活动项目（模块2）。"""

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("ACT"))
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(50))
    location: Mapped[str] = mapped_column(String(200))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expected_attendance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    scenes: Mapped[list["Scene"]] = relationship(back_populates="activity")
    activity_roles: Mapped[list["ActivityRole"]] = relationship(back_populates="activity")


class Scene(Base):
    """活动场景（流程一）。MVP 场地区域用结构化文本 + 二维图片表示，不使用 GIS/三维模型。"""

    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("SCENE"))
    activity_id: Mapped[str | None] = mapped_column(String(40), ForeignKey("activities.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    map_file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)  # 关键通道/出入口/关键设施/基本资源
    status: Mapped[str] = mapped_column(String(20), default="active")

    activity: Mapped["Activity | None"] = relationship(back_populates="scenes")
    areas: Mapped[list["SceneArea"]] = relationship(back_populates="scene", cascade="all, delete-orphan")


class SceneArea(Base):
    """场地区域。"""

    __tablename__ = "scene_areas"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("AREA"))
    scene_id: Mapped[str] = mapped_column(String(40), ForeignKey("scenes.id"))
    area_name: Mapped[str] = mapped_column(String(200))
    area_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 通道/出入口/设施/观演区域...
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    scene: Mapped["Scene"] = relationship(back_populates="areas")


class Role(Base):
    """岗位（保安/引导员/保洁/设备保障/总指挥等）。"""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("ROLE"))
    role_code: Mapped[str] = mapped_column(String(50), unique=True)
    role_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibility_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")


class ActivityRole(Base):
    """活动可用岗位及资源数量。"""

    __tablename__ = "activity_roles"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("ACTROLE"))
    activity_id: Mapped[str] = mapped_column(String(40), ForeignKey("activities.id"))
    role_id: Mapped[str] = mapped_column(String(40), ForeignKey("roles.id"))
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    resource_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    activity: Mapped["Activity"] = relationship(back_populates="activity_roles")
    role: Mapped["Role"] = relationship()
