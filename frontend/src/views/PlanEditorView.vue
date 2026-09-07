<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { generatePlan } from "../api/events";
import { findPlanByEvent, listPlanVersions, saveManualPlanVersion, regeneratePlanSection, confirmPlan, exportPlanUrl } from "../api/plans";
import { SAMPLE_PLAN } from "../sampleData";
import StatusChip from "../components/StatusChip.vue";
import EventStepper from "../components/EventStepper.vue";

const props = defineProps({ id: { type: String, required: true } });
const router = useRouter();

const plan = ref(null);
const versions = ref([]);
const currentContent = ref(null);
const loading = ref(false);
const generating = ref(false);
const confirming = ref(false);

const SECTIONS = [
  "event_summary", "objectives", "principles", "roles", "phases",
  "role_requirements", "reporting", "escalation_conditions", "recovery_conditions",
];
const regenSection = ref("objectives");
const regenNote = ref("");
const regenerating = ref(false);

const showJsonEditor = ref(false);
const jsonDraft = ref("");
const savingManual = ref(false);

async function load() {
  loading.value = true;
  try {
    plan.value = await findPlanByEvent(props.id);
    if (plan.value) {
      versions.value = await listPlanVersions(plan.value.id);
      const current = versions.value.find((v) => v.id === plan.value.current_version_id);
      currentContent.value = current?.structured_content || null;
    }
  } finally {
    loading.value = false;
  }
}

async function doGenerate() {
  generating.value = true;
  try {
    await generatePlan(props.id, {});
    ElMessage.success("预案已生成");
    await load();
  } catch (e) {
    if (e.code === "MODEL_CALL_FAILED") {
      ElMessage.warning('大模型服务尚未接入，可点击下方"载入示例预案"走通后续演示流程');
    }
  } finally {
    generating.value = false;
  }
}

async function loadSample() {
  jsonDraft.value = JSON.stringify(SAMPLE_PLAN, null, 2);
  showJsonEditor.value = true;
  // 若预案对象尚未创建（AI生成失败时后端仍会创建一个 generating 状态的 Plan 壳），
  // 直接尝试保存人工版本；若确实没有 Plan（异常情况）则提示先点一次"生成预案"。
  await load();
  if (!plan.value) {
    ElMessage.warning('请先点击"AI 生成预案"（会失败但会创建预案记录），再载入示例预案保存');
  }
}

async function saveManual() {
  if (!plan.value) return;
  savingManual.value = true;
  try {
    const content = JSON.parse(jsonDraft.value);
    await saveManualPlanVersion(plan.value.id, content, "人工编辑/载入示例");
    ElMessage.success("已保存新版本");
    showJsonEditor.value = false;
    await load();
  } catch (e) {
    if (e instanceof SyntaxError) ElMessage.error("JSON 格式错误：" + e.message);
  } finally {
    savingManual.value = false;
  }
}

async function doRegenerateSection() {
  if (!plan.value) return;
  regenerating.value = true;
  try {
    await regeneratePlanSection(plan.value.id, { section: regenSection.value, supplementary_requirements: regenNote.value });
    ElMessage.success("局部重新生成完成");
    await load();
  } catch (e) {
    if (e.code === "MODEL_CALL_FAILED") ElMessage.warning("大模型服务尚未接入，局部重新生成暂不可用");
  } finally {
    regenerating.value = false;
  }
}

async function doConfirm() {
  confirming.value = true;
  try {
    await confirmPlan(plan.value.id);
    ElMessage.success("预案已确认，可进入下一步：任务分解");
    router.push({ name: "task-board", params: { id: props.id } });
  } finally {
    confirming.value = false;
  }
}

function openJsonEditor() {
  jsonDraft.value = JSON.stringify(currentContent.value || SAMPLE_PLAN, null, 2);
  showJsonEditor.value = true;
}

onMounted(load);
</script>

<template>
  <EventStepper :event-id="id" />
  <div class="page-header">
    <div>
      <h2>预案生成</h2>
      <div class="sub">九部分结构化应急预案：事件概况/处置目标/响应原则/组织与职责/处置流程/岗位处置要求/信息报告机制/升级恢复终止条件/知识引用</div>
    </div>
    <StatusChip v-if="plan" :status="plan.status" />
  </div>

  <div v-if="!currentContent" class="card">
    <div class="card-title">尚未生成预案</div>
    <div style="display:flex;gap:10px">
      <el-button type="primary" :loading="generating" @click="doGenerate">AI 生成预案</el-button>
      <el-button @click="loadSample">载入示例预案（演示兜底）</el-button>
    </div>
  </div>

  <template v-if="currentContent">
    <div class="card">
      <div class="card-title"><span>{{ currentContent.title }}</span>
        <div>
          <el-button size="small" @click="openJsonEditor">高级编辑</el-button>
          <el-button size="small" type="primary" :loading="confirming" :disabled="plan.status === 'confirmed'" @click="doConfirm">确认预案</el-button>
          <el-button size="small" tag="a" :href="exportPlanUrl(plan.id)" target="_blank">导出 Word</el-button>
        </div>
      </div>

      <div class="grid-2">
        <div>
          <h4>① 事件概况</h4>
          <p class="sub">{{ currentContent.event_summary.description }}</p>
          <div class="kv-row"><span class="k">时间</span><span class="v">{{ currentContent.event_summary.time }}</span></div>
          <div class="kv-row"><span class="k">地点</span><span class="v">{{ currentContent.event_summary.location }}</span></div>
          <div class="kv-row"><span class="k">影响</span><span class="v">{{ currentContent.event_summary.impact }}</span></div>

          <h4>② 处置目标</h4>
          <ol><li v-for="o in currentContent.objectives" :key="o.priority">{{ o.content }}</li></ol>

          <h4>③ 响应原则</h4>
          <div style="display:flex;flex-wrap:wrap;gap:6px">
            <el-tag v-for="p in currentContent.principles" :key="p" size="small">{{ p }}</el-tag>
          </div>

          <h4>④ 组织与职责</h4>
          <div v-for="r in currentContent.roles" :key="r.role_name" style="margin-bottom:6px">
            <b>{{ r.role_name }}</b>
            <ul><li v-for="(item, i) in r.responsibilities" :key="i">{{ item }}</li></ul>
          </div>
        </div>

        <div>
          <h4>⑤ 处置流程</h4>
          <div v-for="ph in currentContent.phases" :key="ph.phase_code" style="margin-bottom:6px">
            <b>{{ ph.phase_code }} · {{ ph.phase_name }}</b>（{{ ph.target }}）
            <ul><li v-for="(a, i) in ph.actions" :key="i">{{ a }}</li></ul>
          </div>

          <h4>⑥ 岗位处置要求</h4>
          <div v-for="rr in currentContent.role_requirements" :key="rr.role_name" style="margin-bottom:6px">
            <b>{{ rr.role_name }}</b>
            <ul><li v-for="(req, i) in rr.requirements" :key="i">{{ req }}</li></ul>
          </div>

          <h4>⑦ 信息报告机制</h4>
          <div class="kv-row"><span class="k">报告人</span><span class="v">{{ currentContent.reporting.report_to }}</span></div>
          <div class="kv-row"><span class="k">频率</span><span class="v">{{ currentContent.reporting.frequency }}</span></div>

          <h4>⑧ 升级/恢复/终止条件</h4>
          <p class="sub" v-if="currentContent.escalation_conditions.length">升级：{{ currentContent.escalation_conditions.join('；') }}</p>
          <p class="sub" v-if="currentContent.recovery_conditions.length">恢复：{{ currentContent.recovery_conditions.join('；') }}</p>
          <p class="sub" v-if="currentContent.termination_conditions.length">终止：{{ currentContent.termination_conditions.join('；') }}</p>

          <h4>⑨ 知识引用</h4>
          <span v-for="c in currentContent.citations" :key="c.document_id" class="cite-tag" style="margin-right:6px">
            {{ c.document_title }}
          </span>
          <span v-if="!currentContent.citations.length" class="empty-hint">无引用</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">局部重新生成</div>
      <div style="display:flex;gap:10px;align-items:center">
        <el-select v-model="regenSection" style="width:200px">
          <el-option v-for="s in SECTIONS" :key="s" :label="s" :value="s" />
        </el-select>
        <el-input v-model="regenNote" placeholder="补充要求（可选）" style="flex:1" />
        <el-button :loading="regenerating" @click="doRegenerateSection">重新生成该部分</el-button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">版本记录（{{ versions.length }}）</div>
      <el-table :data="versions" size="small">
        <el-table-column prop="version_number" label="版本" width="70" />
        <el-table-column prop="source_type" label="来源" width="120" />
        <el-table-column prop="change_summary" label="说明" />
      </el-table>
    </div>
  </template>

  <el-dialog v-model="showJsonEditor" title="高级编辑（结构化 JSON）" width="720px">
    <el-input v-model="jsonDraft" type="textarea" :rows="20" style="font-family:var(--mono)" />
    <template #footer>
      <el-button @click="showJsonEditor = false">取消</el-button>
      <el-button type="primary" :loading="savingManual" @click="saveManual">保存为新版本</el-button>
    </template>
  </el-dialog>
</template>
