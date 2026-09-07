from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._common import new_id, utcnow

# 复盘报告状态（第四节）：待生成→生成中→初稿→人工修订中→已确认→已归档
REPORT_STATUSES = ["pending", "generating", "draft", "revising", "confirmed", "archived"]


class Report(Base):
    """复盘报告（流程七）。"""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("RPT"))
    event_id: Mapped[str] = mapped_column(String(40), ForeignKey("events.id"))
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    current_version_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    confirmed_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    versions: Mapped[list["ReportVersion"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class ReportVersion(Base):
    """复盘报告版本。structured_content_json 遵循第七节·5 的复盘报告Schema，
    statistics_json 存放第七节·3 中由代码计算（非大模型编造）的统计指标。"""

    __tablename__ = "report_versions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("RPTV"))
    report_id: Mapped[str] = mapped_column(String(40), ForeignKey("reports.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    structured_content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    markdown_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    statistics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped["Report"] = relationship(back_populates="versions")
