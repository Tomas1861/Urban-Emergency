"""第八节·2 工作流状态机：贯穿事件从创建到复盘确认的主链路状态。"""

WORKFLOW_STATES = [
    "EVENT_CREATED",
    "EVENT_ANALYZING",
    "EVENT_CONFIRMED",
    "KNOWLEDGE_RETRIEVING",
    "KNOWLEDGE_SELECTED",
    "PLAN_GENERATING",
    "PLAN_DRAFTED",
    "PLAN_CONFIRMED",
    "TASKS_GENERATING",
    "TASKS_DRAFTED",
    "TASKS_CONFIRMED",
    "TASKS_EXECUTING",
    "EVENT_CLOSED",
    "REPORT_GENERATING",
    "REPORT_DRAFTED",
    "REPORT_CONFIRMED",
]

WORKFLOW_TRANSITIONS = {
    a: b for a, b in zip(WORKFLOW_STATES, WORKFLOW_STATES[1:])
}


def is_valid_transition(current: str, target: str) -> bool:
    """主链路是严格线性的；具体 API 是否允许跳转（如管理员提前复盘）由各路由自行放开。"""
    return WORKFLOW_TRANSITIONS.get(current) == target
