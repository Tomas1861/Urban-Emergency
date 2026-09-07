"""复盘报告Agent（流程七）。第七节·3：统计指标必须由代码预先计算好传入，
大模型只负责基于统计结果做解释、归纳有效做法/问题/改进建议，不得自行编造数字。
"""
from app.agents.base import BaseAgent
from app.schemas.report import ReportStructuredContent, TaskStatistics

PROMPT_VERSION = "report_generator.v2"

# 同 plan_generator：必须给出逐字段骨架，否则模型会自创字段名。
_JSON_SKELETON = """{
  "report_title": "string",
  "event_summary": {},
  "plan_summary": {},
  "timeline": [{"time": "string", "type": "string", "description": "string"}],
  "task_statistics": {"total": 0, "completed": 0, "incomplete": 0, "cancelled": 0, "delayed": 0,
    "on_time": 0, "with_temporary_adjustment": 0, "planned_response_minutes": 0, "actual_response_minutes": 0},
  "role_statistics": [{"role_name": "string", "total": 0, "completed": 0, "completion_rate": 0.0}],
  "effective_practices": ["string"],
  "problems": ["string"],
  "recommendations": {"plan": ["string"], "tasks": ["string"], "knowledge_base": ["string"], "teaching": ["string"]},
  "case_summary": {"event_features": ["string"], "key_actions": ["string"], "lessons": ["string"],
    "applicable_conditions": ["string"], "tags": ["string"]}
}"""

_PROMPT_TEMPLATE = """你是重大演绎活动应急复盘助手。请基于以下已由系统计算好的统计数据和过程记录，
生成结构完整的复盘报告。

重要约束：task_statistics 与 role_statistics 必须原样使用下面给定的系统计算结果，
不得修改任何数字，不得自行推算或编造。

必须严格按下面的 JSON 结构输出（字段名、层级、类型都不能更改）：
{json_skeleton}

活动与事件信息：
{event_json}

最终确认预案：
{plan_json}

最终任务清单与执行记录：
{tasks_json}

系统计算的任务统计（必须原样使用）：
{task_statistics_json}

各岗位统计（必须原样使用）：
{role_statistics_json}

版本记录（预案版本/任务修改记录）：
{version_history_json}

相似历史案例：
{similar_cases_json}

用户补充复盘说明：
{supplementary_notes}

只输出 JSON，不要输出其他说明文字，不要用 markdown 代码块包裹。
"""


class ReportGeneratorAgent(BaseAgent[ReportStructuredContent]):
    run_type = "report_generation"
    output_schema = ReportStructuredContent

    def build_prompt(
        self,
        *,
        event_json: str,
        plan_json: str,
        tasks_json: str,
        task_statistics: TaskStatistics,
        role_statistics_json: str,
        version_history_json: str,
        similar_cases_json: str,
        supplementary_notes: str = "",
    ) -> str:
        return _PROMPT_TEMPLATE.format(
            json_skeleton=_JSON_SKELETON,
            event_json=event_json,
            plan_json=plan_json,
            tasks_json=tasks_json,
            task_statistics_json=task_statistics.model_dump_json(),
            role_statistics_json=role_statistics_json,
            version_history_json=version_history_json,
            similar_cases_json=similar_cases_json,
            supplementary_notes=supplementary_notes or "无",
        )

    def generate(
        self,
        *,
        event_id: str,
        event_json: str,
        plan_json: str,
        tasks_json: str,
        task_statistics: TaskStatistics,
        role_statistics_json: str,
        version_history_json: str,
        similar_cases_json: str,
        supplementary_notes: str = "",
    ) -> ReportStructuredContent:
        prompt = self.build_prompt(
            event_json=event_json,
            plan_json=plan_json,
            tasks_json=tasks_json,
            task_statistics=task_statistics,
            role_statistics_json=role_statistics_json,
            version_history_json=version_history_json,
            similar_cases_json=similar_cases_json,
            supplementary_notes=supplementary_notes,
        )
        result = self.run(
            business_object_type="event",
            business_object_id=event_id,
            prompt=prompt,
            prompt_version=PROMPT_VERSION,
        )
        # 防御性校验：即便模型篡改了统计数字，也强制以系统计算结果为准。
        result.task_statistics = task_statistics
        return result
