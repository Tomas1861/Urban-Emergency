<script setup>
import { ref, onMounted } from "vue";
import { getEvent, generateReport } from "../api/events";
import { findPlanByEvent } from "../api/plans";
import { listPlanTasks } from "../api/tasks";
import { findReportByEvent, listReportVersions, saveManualReportVersion, confirmReport, saveAsCase, exportReportUrl } from "../api/reports";
import { listRoles } from "../api/roles";
import { SAMPLE_REPORT_EXTRA } from "../sampleData";
import { ElMessage } from "element-plus";
import StatusChip from "../components/StatusChip.vue";
import EventStepper from "../components/EventStepper.vue";

const props = defineProps({ id: { type: String, required: true } });

const event = ref(null);
const report = ref(null);
const versions = ref([]);
const currentContent = ref(null);
const tasks = ref([]);
const roles = ref([]);
const generating = ref(false);
const confirming = ref(false);
const savingCase = ref(false);

async function load() {
  event.value = await getEvent(props.id);
  const plan = await findPlanByEvent(props.id);
  if (plan) tasks.value = await listPlanTasks(plan.id);
  roles.value = await listRoles();
  report.value = await findReportByEvent(props.id);
  if (report.value) {
    versions.value = await listReportVersions(report.value.id);
    const current = versions.value.find((v) => v.id === report.value.current_version_id);
    currentContent.value = current?.structured_content || null;
  }
}

function roleName(id) {
  return roles.value.find((r) => r.id === id)?.role_name || id;
}

async function doGenerate() {
  generating.value = true;
  try {
    await generateReport(props.id, {});
    ElMessage.success("复盘报告已生成");
    await load();
  } catch (e) {
    if (e.code === "MODEL_CALL_FAILED") ElMessage.warning('大模型服务尚未接入，可点击"载入示例复盘报告"走通演示流程');
  } finally {
    generating.value = false;
  }
}

async function loadSample() {
  await load();
  if (!report.value) {
    ElMessage.warning('请先点击"AI 生成复盘报告"（会失败但会创建报告记录），再载入示例内容');
    return;
  }
  const completed = tasks.value.filter((t) => t.status === "completed").length;
  const roleStats = {};
  for (const t of tasks.value) {
    const key = roleName(t.role_id);
    const g = (roleStats[key] ||= { total: 0, completed: 0 });
    g.total++;
    if (t.status === "completed") g.completed++;
  }
  const content = {
    report_title: `${event.value.event_name}事件复盘报告`,
    event_summary: {},
    plan_summary: {},
    timeline: [
      { time: event.value.occurred_at, type: "event_occurred", description: `发现${event.value.event_name}` },
      { time: "—", type: "plan_confirmed", description: "应急预案确认" },
      { time: "—", type: "tasks_confirmed", description: "岗位任务清单确认" },
      { time: "—", type: "event_closed", description: "事件结束" },
    ],
    task_statistics: {
      total: tasks.value.length,
      completed,
      incomplete: tasks.value.filter((t) => t.status === "incomplete").length,
      cancelled: tasks.value.filter((t) => t.status === "cancelled").length,
      delayed: 0,
    },
    role_statistics: Object.entries(roleStats).map(([role_name, g]) => ({
      role_name, total: g.total, completed: g.completed, completion_rate: g.total ? g.completed / g.total : 0,
    })),
    ...SAMPLE_REPORT_EXTRA,
  };
  await saveManualReportVersion(report.value.id, content, "载入示例复盘内容");
  ElMessage.success("已保存示例复盘报告");
  await load();
}

async function doConfirm() {
  confirming.value = true;
  try {
    await confirmReport(report.value.id);
    ElMessage.success("复盘报告已确认");
    await load();
  } finally {
    confirming.value = false;
  }
}

async function doSaveAsCase() {
  savingCase.value = true;
  try {
    await saveAsCase(report.value.id);
    ElMessage.success("已沉淀为案例，写入知识库");
  } finally {
    savingCase.value = false;
  }
}

onMounted(load);
</script>

<template>
  <EventStepper :event-id="id" />
  <div class="page-header">
    <div>
      <h2>复盘报告</h2>
      <div class="sub">基于事件、预案、任务执行记录自动生成复盘报告与改进建议</div>
    </div>
    <StatusChip v-if="report" :status="report.status" />
  </div>

  <div v-if="!currentContent" class="card">
    <div class="card-title">尚未生成复盘报告</div>
    <div style="display:flex;gap:10px">
      <el-button type="primary" :loading="generating" @click="doGenerate">AI 生成复盘报告</el-button>
      <el-button @click="loadSample">载入示例复盘内容（演示兜底）</el-button>
    </div>
  </div>

  <template v-else>
    <div class="grid-3">
      <div class="card">
        <div class="card-title">任务总数</div>
        <div style="font-size:24px;font-family:var(--mono)">{{ currentContent.task_statistics.total }}</div>
      </div>
      <div class="card">
        <div class="card-title">已完成</div>
        <div style="font-size:24px;font-family:var(--mono);color:var(--teal)">{{ currentContent.task_statistics.completed }}</div>
      </div>
      <div class="card">
        <div class="card-title">未完成 / 已取消</div>
        <div style="font-size:24px;font-family:var(--mono);color:var(--red)">
          {{ currentContent.task_statistics.incomplete }} / {{ currentContent.task_statistics.cancelled }}
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span>{{ currentContent.report_title }}</span>
        <div>
          <el-button size="small" type="primary" :loading="confirming" :disabled="report.status === 'confirmed'" @click="doConfirm">确认报告</el-button>
          <el-button size="small" :loading="savingCase" @click="doSaveAsCase">沉淀为案例</el-button>
          <el-button size="small" tag="a" :href="exportReportUrl(report.id)" target="_blank">导出 Word</el-button>
        </div>
      </div>

      <h4>事件处置时间线</h4>
      <ul>
        <li v-for="(t, i) in currentContent.timeline" :key="i">{{ t.time }} · {{ t.description }}</li>
      </ul>

      <h4>岗位任务执行情况</h4>
      <el-table :data="currentContent.role_statistics" size="small">
        <el-table-column prop="role_name" label="岗位" width="100" />
        <el-table-column prop="total" label="任务数" width="80" />
        <el-table-column prop="completed" label="完成数" width="80" />
        <el-table-column label="完成率">
          <template #default="{ row }"><el-progress :percentage="Math.round(row.completion_rate*100)" :stroke-width="6" color="var(--teal)" /></template>
        </el-table-column>
      </el-table>

      <div class="grid-2" style="margin-top:12px">
        <div>
          <h4>有效做法</h4>
          <ul><li v-for="(p,i) in currentContent.effective_practices" :key="i">{{ p }}</li></ul>
          <h4>存在问题</h4>
          <ul><li v-for="(p,i) in currentContent.problems" :key="i">{{ p }}</li></ul>
        </div>
        <div>
          <h4>改进建议</h4>
          <p class="sub" v-if="currentContent.recommendations.plan.length">预案：{{ currentContent.recommendations.plan.join('；') }}</p>
          <p class="sub" v-if="currentContent.recommendations.knowledge_base.length">知识库：{{ currentContent.recommendations.knowledge_base.join('；') }}</p>
          <p class="sub" v-if="currentContent.recommendations.teaching.length">教学：{{ currentContent.recommendations.teaching.join('；') }}</p>

          <h4>案例沉淀摘要</h4>
          <div style="display:flex;flex-wrap:wrap;gap:6px">
            <el-tag v-for="tg in currentContent.case_summary.tags" :key="tg" size="small">{{ tg }}</el-tag>
          </div>
        </div>
      </div>
    </div>
  </template>
</template>
