"""事件分析Agent（流程二·1 方式B：自然语言录入 → 结构化事件）。"""
from app.agents.base import BaseAgent
from app.schemas.event import EventStructuredData

PROMPT_VERSION = "event_analyzer.v2"

_JSON_SKELETON = """{
  "event_name": "string",
  "event_type": "string",
  "occurred_at": "2026-07-22T19:30:00+08:00",
  "location": "string",
  "risk_level": "L2",
  "current_impact": "string",
  "estimated_duration_minutes": 20,
  "affected_areas": ["string"],
  "involved_roles": ["string"],
  "available_resources": [{"role": "string", "quantity": 0}],
  "response_objectives": ["string"],
  "missing_information": ["string"]
}"""

_PROMPT_TEMPLATE = """你是重大演绎活动应急指挥系统的事件分析助手。
请将以下自然语言描述的突发事件，转换为结构化 JSON。

必须严格按下面的 JSON 结构输出（字段名、层级、类型都不能更改，occurred_at 用 ISO8601 格式）：
{json_skeleton}

事件描述：
{raw_text}

只输出 JSON，不要输出其他说明文字，不要用 markdown 代码块包裹。
"""


class EventAnalyzerAgent(BaseAgent[EventStructuredData]):
    run_type = "event_analysis"
    output_schema = EventStructuredData

    def build_prompt(self, *, raw_text: str) -> str:
        return _PROMPT_TEMPLATE.format(json_skeleton=_JSON_SKELETON, raw_text=raw_text)

    def analyze(self, *, event_id: str, raw_text: str) -> EventStructuredData:
        prompt = self.build_prompt(raw_text=raw_text)
        return self.run(
            business_object_type="event",
            business_object_id=event_id,
            prompt=prompt,
            prompt_version=PROMPT_VERSION,
        )
