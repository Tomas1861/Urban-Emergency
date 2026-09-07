"""预案生成Agent（流程四）。"""
from app.agents.base import BaseAgent
from app.schemas.knowledge import RetrievalResult
from app.schemas.plan import PlanStructuredContent

PROMPT_VERSION = "plan_generator.v2"

# 必须给模型一份逐字段的 JSON 骨架——只用中文描述"九个部分"，模型会自创字段名
# （event_overview / disposal_process 等），导致 Schema 校验失败。骨架里的字段名
# 必须和 app/schemas/plan.py 的 PlanStructuredContent 完全一致。
_JSON_SKELETON = """{
  "title": "string",
  "event_summary": {"time": "string", "location": "string", "description": "string", "impact": "string"},
  "objectives": [{"priority": 1, "content": "string"}],
  "principles": ["string"],
  "roles": [{"role_name": "string", "responsibilities": ["string"]}],
  "phases": [{"phase_code": "P1", "phase_name": "string", "target": "string", "actions": ["string"]}],
  "role_requirements": [{"role_name": "string", "requirements": ["string"]}],
  "reporting": {"report_to": "string", "frequency": "string", "required_fields": ["string"]},
  "escalation_conditions": ["string"],
  "reinforcement_conditions": ["string"],
  "recovery_conditions": ["string"],
  "termination_conditions": ["string"],
  "citations": [{"document_id": "string", "document_title": "string", "section": "string"}]
}"""

_FULL_PROMPT_TEMPLATE = """你是重大演绎活动应急预案编制助手。请综合以下信息，生成结构完整、依据可追溯的应急预案，
对应九个部分：事件概况(event_summary)/处置目标(objectives)/响应原则(principles)/组织与职责(roles)/
处置流程(phases)/岗位处置要求(role_requirements)/信息报告机制(reporting)/升级恢复终止条件
(escalation_conditions/reinforcement_conditions/recovery_conditions/termination_conditions)/知识引用(citations)。

必须严格按下面的 JSON 结构输出，字段名、层级、类型都不能更改，也不能新增或省略字段：
{json_skeleton}

事件信息：
{event_json}

选中的知识内容（仅可引用以下内容，不得编造引用来源）：
{knowledge_json}

岗位职责参考：
{role_json}

用户补充要求：
{supplementary_requirements}

只输出 JSON，不要输出其他说明文字，不要用 markdown 代码块包裹。
"""

_SECTION_PROMPT_TEMPLATE = """你是重大演绎活动应急预案编制助手。请仅重新生成预案中的「{section}」部分，
其余部分保持不变、原样输出。当前预案完整内容如下（供你参考上下文，不要改动 {section} 以外的字段）：

{current_plan_json}

用户补充要求：
{supplementary_requirements}

必须严格按下面的 JSON 结构输出完整预案（字段名、层级、类型都不能更改）：
{json_skeleton}

只输出完整的 JSON（包含未改动的其他部分与重新生成后的 {section}），不要用 markdown 代码块包裹。
"""


class PlanGeneratorAgent(BaseAgent[PlanStructuredContent]):
    run_type = "plan_generation"
    output_schema = PlanStructuredContent

    def build_prompt(
        self,
        *,
        event_json: str,
        knowledge_json: str,
        role_json: str,
        supplementary_requirements: str = "",
    ) -> str:
        return _FULL_PROMPT_TEMPLATE.format(
            json_skeleton=_JSON_SKELETON,
            event_json=event_json,
            knowledge_json=knowledge_json,
            role_json=role_json,
            supplementary_requirements=supplementary_requirements or "无",
        )

    def generate(
        self,
        *,
        event_id: str,
        event_json: str,
        knowledge: RetrievalResult,
        role_json: str,
        supplementary_requirements: str = "",
    ) -> PlanStructuredContent:
        prompt = self.build_prompt(
            event_json=event_json,
            knowledge_json=knowledge.model_dump_json(),
            role_json=role_json,
            supplementary_requirements=supplementary_requirements,
        )
        return self.run(
            business_object_type="event",
            business_object_id=event_id,
            prompt=prompt,
            prompt_version=PROMPT_VERSION,
        )

    def regenerate_section(
        self,
        *,
        plan_id: str,
        section: str,
        current_plan: PlanStructuredContent,
        supplementary_requirements: str = "",
    ) -> PlanStructuredContent:
        """第四节·6 局部重新生成：仅重写指定字段，其余章节保留。"""
        prompt = _SECTION_PROMPT_TEMPLATE.format(
            section=section,
            current_plan_json=current_plan.model_dump_json(),
            supplementary_requirements=supplementary_requirements or "无",
            json_skeleton=_JSON_SKELETON,
        )
        return self.run(
            business_object_type="plan",
            business_object_id=plan_id,
            prompt=prompt,
            prompt_version=f"{PROMPT_VERSION}.section",
        )
