from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._common import new_id, utcnow

# 预案状态（第四节）：生成中→初稿→人工修订中→已确认→已归档
PLAN_STATUSES = ["generating", "draft", "revising", "confirmed", "archived"]


class Plan(Base):
    """应急预案（流程四）。"""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("PLAN"))
    event_id: Mapped[str] = mapped_column(String(40), ForeignKey("events.id"))
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    current_version_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="generating")
    created_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    versions: Mapped[list["PlanVersion"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class PlanVersion(Base):
    """预案版本（第四节·版本规则）。structured_content_json 遵循预案九部分Schema。"""

    __tablename__ = "plan_versions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("PLANV"))
    plan_id: Mapped[str] = mapped_column(String(40), ForeignKey("plans.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(String(30))  # ai_full | ai_section | manual_edit | confirm
    structured_content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    markdown_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_json: Mapped[list] = mapped_column(JSON, default=list)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    plan: Mapped["Plan"] = relationship(back_populates="versions")
