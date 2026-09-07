<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { findPlanByEvent } from "../api/plans";
import { generateTasks, listPlanTasks, confirmTasks, createTask, updateTask, deleteTask } from "../api/tasks";
import { listRoles } from "../api/roles";
import { SAMPLE_TASKS } from "../sampleData";
import StatusChip from "../components/StatusChip.vue";
import EventStepper from "../components/EventStepper.vue";

const props = defineProps({ id: { type: String, required: true } });
const router = useRouter();

const plan = ref(null);
const tasks = ref([]);
const roles = ref([]);
const groupBy = ref("role"); // role | phase | time
const loading = ref(false);
const generating = ref(false);
const confirming = ref(false);

const editDialog = ref(false);
const editing = ref(null);
const form = ref({});

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

const grouped = computed(() => {
  const groups = {};
  for (const t of tasks.value) {
    const key =
      groupBy.value === "role" ? roleName(t.role_id) :
      groupBy.value === "phase" ? (t.phase_code || "未分阶段") :
      `T+${t.deadline_minutes ?? "?"}`;
    (groups[key] ||= []).push(t);
  }
  return groups;
});

async function doGenerate() {
  generating.value = true;
  try {
    await generateTasks(plan.value.id, {});
    ElMessage.success("岗位任务清单已生成");
    await load();
  } catch (e) {
    if (e.code === "MODEL_CALL_FAILED") ElMessage.warning('大模型服务尚未接入，可点击"载入示例任务清单"走通演示流程');
  } finally {
    generating.value = false;
  }
}

async function loadSample() {
  for (const t of SAMPLE_TASKS) {
    const role = roles.value.find((r) => r.role_name === t.role_name);
    await createTask(plan.value.id, { ...t, role_id: role?.id || "" });
  }
  ElMessage.success("已载入示例任务");
  await load();
}

function openCreate() {
  editing.value = null;
  form.value = {
    task_id: `TASK-${Date.now().toString().slice(-6)}`,
    task_name: "", role_id: "", role_name: "", phase_code: "P1", location: "",
    action: "", trigger_condition: "", planned_start_offset_minutes: 0, deadline_minutes: 5,
    required_people: 1, required_resources: [], collaborating_roles: [], dependencies: [],
    completion_criteria: "", feedback_requirement: "", exception_action: "",
  };
  editDialog.value = true;
}

function openEdit(row) {
  editing.value = row;
  form.value = {
    task_name: row.task_name, role_id: row.role_id, location: row.location,
    action: row.action_text, deadline_minutes: row.deadline_minutes,
    completion_criteria: row.completion_criteria,
  };
  editDialog.value = true;
}

async function submitForm() {
  if (editing.value) {
    await updateTask(editing.value.id, form.value);
    ElMessage.success("已保存");
  } else {
    const role = roles.value.find((r) => r.id === form.value.role_id);
    await createTask(plan.value.id, { ...form.value, role_name: role?.role_name || "" });
    ElMessage.success("已新增任务");
  }
  editDialog.value = false;
  await load();
}

async function removeTask(row) {
  await deleteTask(row.id);
  ElMessage.success("已删除");
  await load();
}

async function doConfirm() {
  confirming.value = true;
  try {
    await confirmTasks(plan.value.id);
    ElMessage.success("任务清单已确认，可进入下一步：执行跟踪");
    router.push({ name: "execution-panel", params: { id: props.id } });
  } catch (e) {
    if (e.code === "VALIDATION_FAILED") {
      ElMessage.error({ message: `校验未通过：\n${(e.data?.violations || []).join("\n")}`, dangerouslyUseHTMLString: false });
    }
  } finally {
    confirming.value = false;
  }
}

onMounted(load);
</script>

<template>
  <EventStepper :event-id="id" />
  <div class="page-header">
    <div>
      <h2>岗位任务清单</h2>
      <div class="sub">将预案分解为责任主体、动作、地点、时限、完成标准均明确的可执行任务</div>
    </div>
  </div>

  <div v-if="!plan" class="empty-hint">请先完成预案生成与确认</div>

  <template v-else>
    <div v-if="!tasks.length" class="card">
      <div class="card-title">尚未生成岗位任务</div>
      <div style="display:flex;gap:10px">
        <el-button type="primary" :loading="generating" @click="doGenerate">AI 生成任务清单</el-button>
        <el-button @click="loadSample">载入示例任务（演示兜底）</el-button>
      </div>
    </div>

    <template v-else>
      <div class="page-header">
        <el-radio-group v-model="groupBy" size="small">
          <el-radio-button value="role">按岗位</el-radio-button>
          <el-radio-button value="phase">按阶段</el-radio-button>
          <el-radio-button value="time">按计划时间</el-radio-button>
        </el-radio-group>
        <div>
          <el-button size="small" @click="openCreate">+ 新增任务</el-button>
          <el-button size="small" type="primary" :loading="confirming" @click="doConfirm">确认任务清单</el-button>
        </div>
      </div>

      <div v-for="(items, key) in grouped" :key="key" class="card">
        <div class="card-title">{{ key }}（{{ items.length }}）</div>
        <el-table :data="items" size="small">
          <el-table-column prop="task_code" label="编号" width="110" />
          <el-table-column prop="task_name" label="任务" min-width="180" />
          <el-table-column label="岗位" width="90">
            <template #default="{ row }">{{ roleName(row.role_id) }}</template>
          </el-table-column>
          <el-table-column prop="phase_code" label="阶段" width="70" />
          <el-table-column prop="location" label="地点" width="140" />
          <el-table-column prop="deadline_minutes" label="时限(分)" width="90" />
          <el-table-column prop="completion_criteria" label="完成标准" min-width="200" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }"><StatusChip :status="row.status" /></template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text @click="openEdit(row)">编辑</el-button>
              <el-button size="small" text type="danger" @click="removeTask(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>
  </template>

  <el-dialog v-model="editDialog" :title="editing ? '编辑任务' : '新增任务'" width="560px">
    <el-form :model="form" label-width="90px">
      <el-form-item label="任务名称"><el-input v-model="form.task_name" /></el-form-item>
      <el-form-item label="责任岗位">
        <el-select v-model="form.role_id" style="width:100%">
          <el-option v-for="r in roles" :key="r.id" :label="r.role_name" :value="r.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="!editing" label="处置阶段">
        <el-select v-model="form.phase_code" style="width:100%">
          <el-option v-for="p in ['P1','P2','P3','P4']" :key="p" :label="p" :value="p" />
        </el-select>
      </el-form-item>
      <el-form-item label="地点"><el-input v-model="form.location" /></el-form-item>
      <el-form-item label="动作"><el-input v-model="form.action" type="textarea" :rows="2" /></el-form-item>
      <el-form-item v-if="!editing" label="触发条件"><el-input v-model="form.trigger_condition" /></el-form-item>
      <el-form-item label="时限(分)"><el-input-number v-model="form.deadline_minutes" :min="0" /></el-form-item>
      <el-form-item v-if="!editing" label="所需人数"><el-input-number v-model="form.required_people" :min="0" /></el-form-item>
      <el-form-item label="完成标准"><el-input v-model="form.completion_criteria" type="textarea" :rows="2" /></el-form-item>
      <el-form-item v-if="!editing" label="反馈方式"><el-input v-model="form.feedback_requirement" /></el-form-item>
      <el-form-item label="异常处理"><el-input v-model="form.exception_action" type="textarea" :rows="2" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editDialog = false">取消</el-button>
      <el-button type="primary" @click="submitForm">保存</el-button>
    </template>
  </el-dialog>
</template>
