<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getExecutionSummary, closeEvent } from "../api/events";
import { findPlanByEvent } from "../api/plans";
import { listPlanTasks } from "../api/tasks";
import { startTask, completeTask, failTask, cancelTask, updateExecution } from "../api/executions";
import { listRoles } from "../api/roles";
import StatusChip from "../components/StatusChip.vue";
import EventStepper from "../components/EventStepper.vue";

const props = defineProps({ id: { type: String, required: true } });
const router = useRouter();

const plan = ref(null);
const tasks = ref([]);
const roles = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const activeTask = ref(null);
const execForm = ref({ executor: "", execution_result: "", issues: "", temporary_adjustments: "", remarks: "" });

async function load() {
  loading.value = true;
  try {
    plan.value = await findPlanByEvent(props.id);
    roles.value = await listRoles();
    if (plan.value) tasks.value = await listPlanTasks(plan.value.id);
  } finally {
    loading.value = false;
  }
}

function roleName(id) {
  return roles.value.find((r) => r.id === id)?.role_name || id;
}

const completedCount = computed(() => tasks.value.filter((t) => t.status === "completed").length);
const completionRate = computed(() => (tasks.value.length ? Math.round((completedCount.value / tasks.value.length) * 100) : 0));

const byRole = computed(() => {
  const groups = {};
  for (const t of tasks.value) {
    const key = roleName(t.role_id);
    const g = (groups[key] ||= { total: 0, completed: 0 });
    g.total++;
    if (t.status === "completed") g.completed++;
  }
  return groups;
});

function openExec(task) {
  activeTask.value = task;
  execForm.value = { executor: "", execution_result: "", issues: "", temporary_adjustments: "", remarks: "" };
  dialogVisible.value = true;
}

async function saveExec() {
  await updateExecution(activeTask.value.id, execForm.value);
  ElMessage.success("已保存执行记录");
  dialogVisible.value = false;
  await load();
}

async function transition(task, action) {
  const fn = { start: startTask, complete: completeTask, fail: failTask, cancel: cancelTask }[action];
  try {
    await fn(task.id);
    await load();
  } catch (e) {
    if (e.code === "INVALID_TRANSITION") ElMessage.error(e.message);
  }
}

async function doClose() {
  const summary = await getExecutionSummary(props.id);
  await ElMessageBox.confirm(
    `未开始 ${summary.not_started_count} · 执行中 ${summary.in_progress_count} · 未完成 ${summary.incomplete_count} · 已完成 ${summary.completed_count} · 已取消 ${summary.cancelled_count}\n确认结束事件？`,
    "结束事件前确认",
    { confirmButtonText: "确认结束", cancelButtonText: "取消" }
  );
  await closeEvent(props.id);
  ElMessage.success("事件已结束，可进入复盘报告");
  router.push({ name: "report-editor", params: { id: props.id } });
}

onMounted(load);
</script>

<template>
  <EventStepper :event-id="id" />
  <div class="page-header">
    <div>
      <h2>任务执行</h2>
      <div class="sub">模拟记录各岗位任务的实际执行情况</div>
    </div>
    <el-button type="danger" plain @click="doClose">结束事件</el-button>
  </div>

  <div v-if="!plan || !tasks.length" class="empty-hint">请先完成岗位任务清单确认</div>

  <template v-else>
    <div class="grid-3">
      <div class="card">
        <div class="card-title">总体完成率</div>
        <div style="font-size:28px;font-weight:600;font-family:var(--mono)">{{ completionRate }}%</div>
        <div class="sub">{{ completedCount }} / {{ tasks.length }} 已完成</div>
      </div>
      <div class="card" style="grid-column: span 2">
        <div class="card-title">各岗位进度</div>
        <div v-for="(g, name) in byRole" :key="name" style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:3px">
            <span>{{ name }}</span><span>{{ g.completed }}/{{ g.total }}</span>
          </div>
          <el-progress :percentage="Math.round((g.completed / g.total) * 100)" :stroke-width="6" color="var(--teal)" />
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">任务列表</div>
      <el-table :data="tasks" size="small">
        <el-table-column prop="task_code" label="编号" width="110" />
        <el-table-column prop="task_name" label="任务" min-width="180" />
        <el-table-column label="岗位" width="90"><template #default="{ row }">{{ roleName(row.role_id) }}</template></el-table-column>
        <el-table-column label="状态" width="110"><template #default="{ row }"><StatusChip :status="row.status" /></template></el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text :disabled="row.status !== 'not_started'" @click="transition(row, 'start')">开始</el-button>
            <el-button size="small" text :disabled="row.status !== 'in_progress'" @click="transition(row, 'complete')">完成</el-button>
            <el-button size="small" text :disabled="row.status !== 'in_progress'" @click="transition(row, 'fail')">未完成</el-button>
            <el-button size="small" text :disabled="!['not_started','in_progress'].includes(row.status)" @click="transition(row, 'cancel')">取消</el-button>
            <el-button size="small" text @click="openExec(row)">记录</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </template>

  <el-dialog v-model="dialogVisible" title="任务执行记录" width="480px">
    <el-form v-if="activeTask" :model="execForm" label-width="90px">
      <div class="sub" style="margin-bottom:10px">{{ activeTask.task_name }}</div>
      <el-form-item label="执行人"><el-input v-model="execForm.executor" /></el-form-item>
      <el-form-item label="执行结果"><el-input v-model="execForm.execution_result" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="问题"><el-input v-model="execForm.issues" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="临时调整"><el-input v-model="execForm.temporary_adjustments" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="execForm.remarks" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="saveExec">保存</el-button>
    </template>
  </el-dialog>
</template>
