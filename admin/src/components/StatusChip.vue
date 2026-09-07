<script setup>
import { computed } from "vue";

const props = defineProps({ status: { type: String, default: "" }, context: { type: String, default: "" } });

// 活动状态与预案/报告版本状态共用 "draft"/"active"/"archived" 等字符串，
// 用 context="activity" 区分文案，避免"活动草稿"被误显示成"预案初稿"。
const ACTIVITY_MAP = {
  draft: ["草稿", "dim"],
  active: ["进行中", "teal"],
  ended: ["已结束", "dim"],
  archived: ["已归档", "dim"],
};

const MAP = {
  // 事件主链路
  EVENT_CREATED: ["草稿", "dim"],
  EVENT_ANALYZING: ["待确认", "amber"],
  EVENT_CONFIRMED: ["已确认", "teal"],
  KNOWLEDGE_RETRIEVING: ["检索中/待选择", "amber"],
  KNOWLEDGE_SELECTED: ["知识已选定", "teal"],
  PLAN_GENERATING: ["预案生成中", "amber"],
  PLAN_DRAFTED: ["预案待审核", "amber"],
  PLAN_CONFIRMED: ["预案已确认", "teal"],
  TASKS_GENERATING: ["任务生成中", "amber"],
  TASKS_DRAFTED: ["任务待确认", "amber"],
  TASKS_CONFIRMED: ["任务已确认", "teal"],
  TASKS_EXECUTING: ["执行中", "blue"],
  EVENT_CLOSED: ["事件已结束", "dim"],
  REPORT_GENERATING: ["复盘生成中", "amber"],
  REPORT_DRAFTED: ["复盘待审核", "amber"],
  REPORT_CONFIRMED: ["已复盘", "teal"],
  // 预案/复盘报告
  generating: ["生成中", "amber"],
  draft: ["初稿", "amber"],
  revising: ["人工修订中", "blue"],
  confirmed: ["已确认", "teal"],
  archived: ["已归档", "dim"],
  pending: ["待生成", "dim"],
  // 任务 / 执行记录
  pending_confirm: ["待确认", "dim"],
  not_started: ["未开始", "dim"],
  in_progress: ["执行中", "blue"],
  completed: ["已完成", "teal"],
  incomplete: ["未完成", "red"],
  cancelled: ["已取消", "dim"],
  // 知识文档
  enabled: ["已启用", "teal"],
  disabled: ["已停用", "dim"],
  parsing: ["解析中", "amber"],
};

const info = computed(() => {
  if (props.context === "activity") return ACTIVITY_MAP[props.status] || [props.status || "—", "dim"];
  return MAP[props.status] || [props.status || "—", "dim"];
});
</script>

<template>
  <span class="status-chip" :class="info[1]">{{ info[0] }}</span>
</template>
