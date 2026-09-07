from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._common import new_id, utcnow

# 调用类型，对应第八节·1 的四个Agent（预案生成与任务分解共用模型，不同prompt/schema）
AGENT_RUN_TYPES = ["event_analysis", "knowledge_retrieval", "plan_generation", "task_generation", "report_generation"]


class AgentRun(Base):
    """Agent调用记录（第八节·3），用于可追溯性（第十二节·1）。"""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("RUN"))
    run_type: Mapped[str] = mapped_column(String(30))
    business_object_type: Mapped[str] = mapped_column(String(30))  # event|plan|task|report
    business_object_id: Mapped[str] = mapped_column(String(40))
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|success|failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
