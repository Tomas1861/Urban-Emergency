"""任务分解Agent（流程五）。与预案生成Agent使用同一底层模型，但独立的
prompt、输出Schema与调用记录（第八节·1）。"""
from app.agents.base import BaseAgent
from app.schemas.plan import PlanStructuredContent
from app.schemas.task import TaskGenerationOutput, VAGUE_ACTION_KEYWORDS

PROMPT_VERSION = "task_generator.v2"

# 同 plan_generator：必须给出逐字段骨架，否则模型会自创字段名。
_JSON_SKELETON = """{
  "tasks": [
    {
      "task_id": "TASK-001",
      "task_name": "string",
      "role_id": "string",
      "role_name": "string",
      "phase_code": "P1",
      "location": "string",
      "action": "string",
      "trigger_condition": "string",
      "planned_start_offset_minutes": 0,
      "deadline_minutes": 5,
      "required_people": 1,
      "required_resources": ["string"],
      "collaborating_roles": ["string"],
      "dependencies": [],
      "completion_criteria": "string",
      "feedback_requirement": "string",
      "exception_action": "string",
      "source_plan_section": "string"
    }
  ]
}"""

_PROMPT_TEMPLATE = """你是重大演绎活动应急岗位任务分解助手。请将以下已确认的应急预案，
分解为各岗位可直接执行的结构化任务清单。

每项任务必须满足：责任主体明确、动作具体、地点明确、时间要求明确、完成标准明确、
反馈方式明确、异常处理明确。禁止出现以下模糊表达：{vague_keywords}。

必须严格按下面的 JSON 结构输出（顶层字段固定为 tasks，字段名、层级、类型都不能更改）：
{json_skeleton}

最终确认预案：
{plan_json}

场景可用岗位：
{roles_json}

岗位职责参考：
{role_responsibility_json}

用户补充要求：
{supplementary_requirements}

只输出 JSON，不要输出其他说明文字，不要用 markdown 代码块包裹。
"""


class TaskGeneratorAgent(BaseAgent[TaskGenerationOutput]):
    run_type = "task_generation"
    output_schema = TaskGenerationOutput

    def build_prompt(
        self,
        *,
        plan: PlanStructuredContent,
        roles_json: str,
        role_responsibility_json: str,
        supplementary_requirements: str = "",
    ) -> str:
        return _PROMPT_TEMPLATE.format(
            vague_keywords="、".join(VAGUE_ACTION_KEYWORDS),
            json_skeleton=_JSON_SKELETON,
            plan_json=plan.model_dump_json(),
            roles_json=roles_json,
            role_responsibility_json=role_responsibility_json,
            supplementary_requirements=supplementary_requirements or "无",
        )

    def generate(
        self,
        *,
        plan_id: str,
        plan: PlanStructuredContent,
        roles_json: str,
        role_responsibility_json: str,
        supplementary_requirements: str = "",
    ) -> TaskGenerationOutput:
        prompt = self.build_prompt(
            plan=plan,
            roles_json=roles_json,
            role_responsibility_json=role_responsibility_json,
            supplementary_requirements=supplementary_requirements,
        )
        return self.run(
            business_object_type="plan",
            business_object_id=plan_id,
            prompt=prompt,
            prompt_version=PROMPT_VERSION,
        )
