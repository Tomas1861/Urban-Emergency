"""预案/复盘报告导出服务（模块5·6·8：导出Word或PDF）。

TODO: PDF 导出未接入（需要额外的排版依赖，如 weasyprint），当前仅实现 Word(.docx) 导出。
"""
import os
import uuid

from docx import Document as DocxDocument

from app.core.config import get_settings
from app.schemas.plan import PlanStructuredContent
from app.schemas.report import ReportStructuredContent


def render_plan_markdown(plan: PlanStructuredContent) -> str:
    """将结构化预案渲染为 Markdown，供预览/导出使用（第四节·2 九部分结构）。"""
    lines = [f"# {plan.title}", ""]
    lines += ["## 第一部分：事件概况", plan.event_summary.description,
              f"时间：{plan.event_summary.time}  地点：{plan.event_summary.location}  影响：{plan.event_summary.impact}", ""]
    lines += ["## 第二部分：处置目标"]
    lines += [f"{o.priority}. {o.content}" for o in plan.objectives] + [""]
    lines += ["## 第三部分：响应原则"]
    lines += [f"- {p}" for p in plan.principles] + [""]
    lines += ["## 第四部分：组织与职责"]
    for r in plan.roles:
        lines.append(f"### {r.role_name}")
        lines += [f"- {item}" for item in r.responsibilities]
    lines.append("")
    lines += ["## 第五部分：处置流程"]
    for ph in plan.phases:
        lines.append(f"### {ph.phase_code} {ph.phase_name}（目标：{ph.target}）")
        lines += [f"- {a}" for a in ph.actions]
    lines.append("")
    lines += ["## 第六部分：岗位处置要求"]
    for rr in plan.role_requirements:
        lines.append(f"### {rr.role_name}")
        lines += [f"- {req}" for req in rr.requirements]
    lines.append("")
    lines += ["## 第七部分：信息报告机制",
               f"报告人->{plan.reporting.report_to}，频率：{plan.reporting.frequency}",
               f"必报字段：{'、'.join(plan.reporting.required_fields)}", ""]
    lines += ["## 第八部分：升级、恢复与终止条件"]
    lines += [f"- 升级条件：{c}" for c in plan.escalation_conditions]
    lines += [f"- 增援条件：{c}" for c in plan.reinforcement_conditions]
    lines += [f"- 恢复条件：{c}" for c in plan.recovery_conditions]
    lines += [f"- 终止条件：{c}" for c in plan.termination_conditions]
    lines.append("")
    lines += ["## 第九部分：知识引用"]
    lines += [f"- {c.document_title}（{c.section or '全文'}）" for c in plan.citations]
    return "\n".join(lines)


def render_report_markdown(report: ReportStructuredContent) -> str:
    """将结构化复盘报告渲染为 Markdown（第七节·4 八部分结构）。"""
    lines = [f"# {report.report_title}", ""]
    lines += ["## 第三部分：应急处置时间线"]
    lines += [f"- {t.time} [{t.type}] {t.description}" for t in report.timeline] + [""]
    stats = report.task_statistics
    lines += ["## 第四部分：岗位任务执行情况",
              f"任务总数：{stats.total}，已完成：{stats.completed}，未完成：{stats.incomplete}，"
              f"已取消：{stats.cancelled}，延误：{stats.delayed}", ""]
    for rs in report.role_statistics:
        lines.append(f"- {rs.role_name}：{rs.completed}/{rs.total}（完成率 {rs.completion_rate:.0%}）")
    lines.append("")
    lines += ["## 第五部分：有效做法"] + [f"- {p}" for p in report.effective_practices] + [""]
    lines += ["## 第六部分：存在问题"] + [f"- {p}" for p in report.problems] + [""]
    lines += ["## 第七部分：改进建议"]
    lines += [f"- 【预案】{r}" for r in report.recommendations.plan]
    lines += [f"- 【任务】{r}" for r in report.recommendations.tasks]
    lines += [f"- 【知识库】{r}" for r in report.recommendations.knowledge_base]
    lines += [f"- 【教学】{r}" for r in report.recommendations.teaching]
    return "\n".join(lines)


class ExportService:
    def __init__(self):
        settings = get_settings()
        self.storage_dir = settings.storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def export_markdown_to_docx(self, *, title: str, markdown_content: str) -> str:
        """将 Markdown 正文按行粗略映射为 Word 段落/标题，返回生成文件路径。"""
        doc = DocxDocument()
        doc.add_heading(title, level=0)

        for line in markdown_content.splitlines():
            stripped = line.strip()
            if not stripped:
                doc.add_paragraph()
                continue
            if stripped.startswith("### "):
                doc.add_heading(stripped[4:], level=3)
            elif stripped.startswith("## "):
                doc.add_heading(stripped[3:], level=2)
            elif stripped.startswith("# "):
                doc.add_heading(stripped[2:], level=1)
            elif stripped.startswith(("- ", "* ")):
                doc.add_paragraph(stripped[2:], style="List Bullet")
            else:
                doc.add_paragraph(stripped)

        file_path = os.path.join(self.storage_dir, f"{uuid.uuid4().hex}.docx")
        doc.save(file_path)
        return file_path

    def export_markdown_to_pdf(self, *, title: str, markdown_content: str) -> str:
        raise NotImplementedError("PDF 导出尚未实现，MVP 阶段请使用 export_markdown_to_docx()")
