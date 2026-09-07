// 演示用示例数据：当大模型服务尚未接入时，可一键载入示例内容，
// 保证"生成→人工确认→导出"整条链路在展示现场始终可以走通。

export const SAMPLE_PLAN = {
  title: "东侧通道设施故障应急处置预案",
  event_summary: {
    time: "演出开始后30分钟",
    location: "东侧主要通道",
    description: "临时设施故障导致通道无法通行",
    impact: "可能造成东侧区域人员聚集",
  },
  objectives: [
    { priority: 1, content: "立即控制故障区域并阻止人员进入" },
    { priority: 2, content: "引导观众使用备用通道" },
  ],
  principles: ["统一指挥", "安全优先", "岗位协同", "及时反馈"],
  roles: [
    { role_name: "总指挥", responsibilities: ["确认预案启动", "协调各岗位行动", "决定是否升级响应"] },
    { role_name: "保安", responsibilities: ["设置隔离带", "维持现场秩序"] },
  ],
  phases: [
    { phase_code: "P1", phase_name: "立即响应", target: "控制现场并启动信息报告", actions: ["设置临时隔离", "发布通道关闭提示"] },
    { phase_code: "P2", phase_name: "现场控制", target: "分流观众、稳定现场秩序", actions: ["引导至备用通道", "增派人员值守"] },
  ],
  role_requirements: [
    { role_name: "保安", requirements: ["设置隔离带", "维持现场秩序"] },
    { role_name: "引导员", requirements: ["引导观众前往备用通道", "解答现场观众询问"] },
  ],
  reporting: {
    report_to: "现场总指挥",
    frequency: "关键状态变化时立即报告",
    required_fields: ["现场状态", "任务进展", "异常情况"],
  },
  escalation_conditions: ["备用通道无法使用", "现场出现明显聚集", "设施短时间内无法恢复"],
  reinforcement_conditions: ["现场人员不足以维持秩序"],
  recovery_conditions: ["故障排除", "通道安全检查完成", "总指挥确认恢复开放"],
  termination_conditions: ["通道恢复正常通行超过30分钟"],
  citations: [{ document_id: "doc_001", document_title: "重大演绎活动现场应急预案", section: "设施故障处置" }],
};

export const SAMPLE_TASKS = [
  {
    task_id: "TASK-001",
    task_name: "设置东侧通道临时隔离",
    role_name: "保安",
    phase_code: "P1",
    location: "东侧主要通道入口",
    action: "使用隔离带封闭故障通道入口，阻止观众继续进入",
    trigger_condition: "预案确认启动后立即执行",
    planned_start_offset_minutes: 0,
    deadline_minutes: 3,
    required_people: 2,
    required_resources: ["隔离带", "警示标识"],
    collaborating_roles: ["引导员"],
    dependencies: [],
    completion_criteria: "故障通道入口完成封闭，无新增观众进入",
    feedback_requirement: "完成后向总指挥报告并填写执行结果",
    exception_action: "隔离设施不足时，立即请求补充物资并安排人工值守",
  },
  {
    task_id: "TASK-002",
    task_name: "引导观众前往备用通道",
    role_name: "引导员",
    phase_code: "P2",
    location: "东侧观演区域",
    action: "在东侧观演区域举牌引导观众改道至备用通道",
    trigger_condition: "东侧通道封闭后立即执行",
    planned_start_offset_minutes: 1,
    deadline_minutes: 5,
    required_people: 3,
    required_resources: ["引导指示牌", "扩音器"],
    collaborating_roles: ["保安"],
    dependencies: ["TASK-001"],
    completion_criteria: "东侧观众流量明显下降，备用通道通行顺畅",
    feedback_requirement: "每5分钟向总指挥反馈观众分流情况",
    exception_action: "观众不配合引导时请求保安支援维持秩序",
  },
];

export const SAMPLE_REPORT_EXTRA = {
  effective_practices: ["隔离带设置及时", "引导员分流响应迅速"],
  problems: ["隔离带物资储备不足"],
  recommendations: {
    plan: ["预案中增加物资冗余要求"],
    tasks: [],
    knowledge_base: ["补充同类设施故障历史案例"],
    teaching: ["可作为教学案例展示临时调整决策"],
  },
  case_summary: {
    event_features: ["设施故障", "通道拥堵风险"],
    key_actions: ["设置隔离带", "引导分流"],
    lessons: ["物资储备需留余量"],
    applicable_conditions: ["通道类设施故障场景"],
    tags: ["设施故障", "保安", "引导员"],
  },
};
