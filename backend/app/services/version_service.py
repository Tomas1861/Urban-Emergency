"""版本管理与基础校验服务。

- 预案/复盘报告版本规则（第四节·7）：完整重新生成/保存新版本/局部重新生成确认/最终确认 均产生新版本。
- 岗位任务基础校验（第五节·7）：MVP 仅做轻量规则校验，不做优化求解；
  存在严重问题时不允许确认任务清单（由调用方在校验结果非空时拒绝确认）。
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.plan import PlanVersion
from app.models.report import ReportVersion
from app.schemas.task import TaskItem, TaskValidationIssue


def next_plan_version_number(db: Session, plan_id: str) -> int:
    current_max = db.query(func.max(PlanVersion.version_number)).filter(PlanVersion.plan_id == plan_id).scalar()
    return (current_max or 0) + 1


def next_report_version_number(db: Session, report_id: str) -> int:
    current_max = (
        db.query(func.max(ReportVersion.version_number)).filter(ReportVersion.report_id == report_id).scalar()
    )
    return (current_max or 0) + 1


def validate_task_list(tasks: list[TaskItem], *, known_role_ids: set[str]) -> list[TaskValidationIssue]:
    """第五节·7 基础校验，返回问题列表；调用方在列表非空时应拒绝确认任务清单。"""
    issues: list[TaskValidationIssue] = []
    seen_ids: set[str] = set()

    for task in tasks:
        if not task.role_id:
            issues.append(TaskValidationIssue(task_id=task.task_id, rule="missing_role", message="任务缺少责任岗位"))
        elif task.role_id not in known_role_ids:
            issues.append(
                TaskValidationIssue(
                    task_id=task.task_id, rule="unknown_role", message=f"任务引用了不存在的岗位: {task.role_id}"
                )
            )

        if not task.completion_criteria.strip():
            issues.append(
                TaskValidationIssue(task_id=task.task_id, rule="missing_completion_criteria", message="任务缺少完成标准")
            )

        if not task.phase_code:
            issues.append(TaskValidationIssue(task_id=task.task_id, rule="missing_phase", message="任务缺少处置阶段"))

        if task.task_id in task.dependencies:
            issues.append(TaskValidationIssue(task_id=task.task_id, rule="self_dependency", message="任务依赖了自身"))

        if not task.action.strip() or not task.task_name.strip():
            issues.append(TaskValidationIssue(task_id=task.task_id, rule="empty_content", message="任务名称或动作内容为空"))

        if task.task_id in seen_ids:
            issues.append(TaskValidationIssue(task_id=task.task_id, rule="duplicate_id", message="任务ID重复"))
        seen_ids.add(task.task_id)

    return issues
