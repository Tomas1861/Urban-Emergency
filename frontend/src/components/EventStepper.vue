<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const props = defineProps({ eventId: { type: String, required: true } });

const STEPS = [
  { key: "event-editor", label: "① 事件确认" },
  { key: "knowledge-selection", label: "② 知识检索" },
  { key: "plan-editor", label: "③ 预案生成" },
  { key: "task-board", label: "④ 任务分解" },
  { key: "execution-panel", label: "⑤ 执行跟踪" },
  { key: "report-editor", label: "⑥ 复盘报告" },
];

const route = useRoute();
const activeKey = computed(() => route.name);
</script>

<template>
  <div class="stepper">
    <router-link
      v-for="s in STEPS"
      :key="s.key"
      :to="{ name: s.key, params: { id: eventId } }"
      class="step"
      :class="{ active: activeKey === s.key }"
    >
      {{ s.label }}
    </router-link>
  </div>
</template>

<style scoped>
.stepper {
  display: flex; gap: 6px; margin-bottom: 18px; flex-wrap: wrap;
}
.step {
  font-size: 12.5px; color: var(--muted); text-decoration: none;
  padding: 7px 14px; border: 1px solid var(--line); border-radius: 4px; background: var(--panel);
}
.step:hover { color: var(--ink); border-color: var(--dim); }
.step.active { color: var(--amber); border-color: var(--amber); background: rgba(242,181,68,.08); }
</style>
