from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._common import new_id, utcnow

if TYPE_CHECKING:
    from app.models.activity import Activity, Scene


class Event(Base):
    """突发事件（流程二）。

    status 取值见 app.workflows.states.WORKFLOW_STATES（第八节工作流状态机），
    与第四节"事件状态"业务名一一对应：
    草稿=EVENT_CREATED, 待确认=EVENT_ANALYZING, 已确认=EVENT_CONFIRMED,
    预案生成中=PLAN_GENERATING, 预案待审核=PLAN_DRAFTED, 预案已确认=PLAN_CONFIRMED,
    任务执行中=TASKS_EXECUTING, 事件已结束=EVENT_CLOSED, 已复盘=REPORT_CONFIRMED。
    """

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("EVT"))
    activity_id: Mapped[str] = mapped_column(String(40), ForeignKey("activities.id"))
    scene_id: Mapped[str | None] = mapped_column(String(40), ForeignKey("scenes.id"), nullable=True)

    event_name: Mapped[str] = mapped_column(String(200))
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True)  # L1/L2/L3...
    estimated_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 分钟

    # 事件分析Agent的结构化输出（第二节·事件分析Agent输出），人工确认后写回本字段
    structured_data_json: Mapped[dict] = mapped_column(JSON, default=dict)

    status: Mapped[str] = mapped_column(String(30), default="EVENT_CREATED")
    created_by: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    activity: Mapped["Activity"] = relationship("Activity")
    scene: Mapped["Scene | None"] = relationship("Scene")
