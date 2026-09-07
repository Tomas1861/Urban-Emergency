<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { createEvent, getEvent, updateEvent, analyzeEvent, confirmEvent } from "../api/events";
import { listRoles } from "../api/roles";
import StatusChip from "../components/StatusChip.vue";
import EventStepper from "../components/EventStepper.vue";

const props = defineProps({
  id: { type: String, required: true },
  activityId: { type: String, default: "" },
  sceneId: { type: String, default: "" },
});
const router = useRouter();

const isNew = computed(() => props.id === "new");
const event = ref(null);
const loading = ref(false);
const analyzing = ref(false);
const saving = ref(false);
const roles = ref([]);

// ---- 创建模式 ----
const inputMode = ref("natural_language");
const rawText = ref(
  "演出开始30分钟后，东侧主要通道因临时设施故障无法通行，预计20分钟内无法恢复。目前东侧附近观众较多，现场已有4名保安、3名引导员和2名设备保障人员。"
);
const form = ref({
  event_name: "",
  event_type: "",
  occurred_at: "",
  location: "",
  description: "",
  current_impact: "",
  risk_level: "L2",
  estimated_duration_minutes: null,
  affected_areas: [],
  involved_roles: [],
});
const submittingCreate = ref(false);

async function submitCreate() {
  submittingCreate.value = true;
  try {
    let payload;
    if (inputMode.value === "natural_language") {
      if (!rawText.value.trim()) return ElMessage.warning("请填写事件描述");
      payload = {
        activity_id: props.activityId,
        scene_id: props.sceneId || null,
        input_mode: "natural_language",
        raw_text: rawText.value,
      };
    } else {
      if (!form.value.event_name || !form.value.occurred_at) return ElMessage.warning("请填写必填字段");
      payload = {
        activity_id: props.activityId,
        scene_id: props.sceneId || null,
        input_mode: "form",
        form: { ...form.value, activity_id: props.activityId, scene_id: props.sceneId || null },
      };
    }
    const created = await createEvent(payload);
    ElMessage.success("事件已创建");
    router.replace({ name: "event-editor", params: { id: created.id } });
  } finally {
    submittingCreate.value = false;
  }
}

// ---- 编辑/确认模式 ----
const editable = ref({
  event_type: "",
  risk_level: "",
  affected_areas: [],
  involved_roles: [],
  available_resources: [],
  response_objectives: [],
  missing_information: [],
});

function syncEditable() {
  const sd = event.value?.structured_data;
  if (!sd) return;
  editable.value = {
    event_type: sd.event_type,
    risk_level: sd.risk_level,
    affected_areas: [...(sd.affected_areas || [])],
    involved_roles: [...(sd.involved_roles || [])],
    available_resources: (sd.available_resources || []).map((r) => ({ ...r })),
    response_objectives: [...(sd.response_objectives || [])],
    missing_information: [...(sd.missing_information || [])],
  };
}

async function load() {
  if (isNew.value) return;
  loading.value = true;
  try {
    event.value = await getEvent(props.id);
    syncEditable();
  } finally {
    loading.value = false;
  }
}

async function doAnalyze() {
  analyzing.value = true;
  try {
    event.value = await analyzeEvent(props.id);
    syncEditable();
    ElMessage.success("事件分析Agent已生成结构化结果");
  } catch (e) {
    // 常见于 LLM 尚未接入：错误已由全局拦截器提示，这里追加更明确的引导
    if (e.code === "MODEL_CALL_FAILED") {
      ElMessage.warning("大模型服务尚未接入（llm_service.py），可改用表单录入方式手动填写结构化结果");
    }
  } finally {
    analyzing.value = false;
  }
}

function addResource() {
  editable.value.available_resources.push({ role: "", quantity: 1 });
}
function removeResource(i) {
  editable.value.available_resources.splice(i, 1);
}

async function saveEdits() {
  saving.value = true;
  try {
    event.value = await updateEvent(props.id, editable.value);
    syncEditable();
    ElMessage.success("已保存修改");
  } finally {
    saving.value = false;
  }
}

async function doConfirm() {
  await saveEdits();
  event.value = await confirmEvent(props.id);
  ElMessage.success("事件已确认，可进入下一步：知识检索");
  router.push({ name: "knowledge-selection", params: { id: props.id } });
}

onMounted(async () => {
  roles.value = await listRoles();
  await load();
});
watch(() => props.id, load);
</script>

<template>
  <EventStepper v-if="!isNew" :event-id="id" />

  <!-- ============ 创建模式 ============ -->
  <template v-if="isNew">
    <div class="page-header">
      <div>
        <h2>录入突发事件</h2>
        <div class="sub">支持自然语言描述或结构化表单两种录入方式</div>
      </div>
    </div>

    <el-radio-group v-model="inputMode" style="margin-bottom:16px">
      <el-radio-button value="natural_language">自然语言录入</el-radio-button>
      <el-radio-button value="form">表单录入</el-radio-button>
    </el-radio-group>

    <div class="card" v-if="inputMode === 'natural_language'">
      <div class="card-title">事件描述</div>
      <el-input v-model="rawText" type="textarea" :rows="6" placeholder="用自然语言描述发生的突发事件……" />
      <p class="sub" style="margin-top:8px">提交后由「事件分析Agent」自动提取结构化字段，可在下一步重新分析或人工修改</p>
    </div>

    <div class="card" v-else>
      <div class="card-title">事件表单</div>
      <el-form :model="form" label-width="110px">
        <el-form-item label="事件名称" required><el-input v-model="form.event_name" /></el-form-item>
        <el-form-item label="事件类型" required><el-input v-model="form.event_type" placeholder="如 facility_failure" /></el-form-item>
        <el-form-item label="发生时间" required>
          <el-date-picker v-model="form.occurred_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="发生地点" required><el-input v-model="form.location" /></el-form-item>
        <el-form-item label="事件描述" required><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="当前影响" required><el-input v-model="form.current_impact" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="form.risk_level" style="width:100%">
            <el-option v-for="l in ['L1','L2','L3','L4']" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="预计持续(分钟)"><el-input-number v-model="form.estimated_duration_minutes" :min="0" /></el-form-item>
        <el-form-item label="涉及区域">
          <el-select v-model="form.affected_areas" multiple filterable allow-create default-first-option style="width:100%" />
        </el-form-item>
        <el-form-item label="涉及岗位">
          <el-select v-model="form.involved_roles" multiple style="width:100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.role_name" :value="r.role_name" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <el-button type="primary" :loading="submittingCreate" @click="submitCreate">提交</el-button>
  </template>

  <!-- ============ 编辑/确认模式 ============ -->
  <template v-else-if="event">
    <div class="page-header">
      <div>
        <h2>{{ event.event_name }}</h2>
        <div class="sub">{{ event.event_type }} · {{ event.location }} · {{ event.occurred_at }}</div>
      </div>
      <StatusChip :status="event.status" />
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">原始信息</div>
        <div class="kv-row"><span class="k">事件描述</span><span class="v">{{ event.current_impact }}</span></div>
        <el-button
          v-if="event.status === 'EVENT_CREATED' || event.status === 'EVENT_ANALYZING'"
          size="small"
          :loading="analyzing"
          style="margin-top:10px"
          @click="doAnalyze"
        >
          {{ event.status === 'EVENT_CREATED' ? '运行事件分析 Agent' : '重新分析' }}
        </el-button>
      </div>

      <div class="card">
        <div class="card-title">AI 提取结果（可人工修改）</div>
        <el-form label-width="90px" size="small">
          <el-form-item label="事件类型"><el-input v-model="editable.event_type" /></el-form-item>
          <el-form-item label="风险等级">
            <el-select v-model="editable.risk_level" style="width:100%">
              <el-option v-for="l in ['L1','L2','L3','L4']" :key="l" :label="l" :value="l" />
            </el-select>
          </el-form-item>
          <el-form-item label="影响范围">
            <el-select v-model="editable.affected_areas" multiple filterable allow-create default-first-option style="width:100%" />
          </el-form-item>
          <el-form-item label="参与岗位">
            <el-select v-model="editable.involved_roles" multiple style="width:100%">
              <el-option v-for="r in roles" :key="r.id" :label="r.role_name" :value="r.role_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="处置目标">
            <el-select v-model="editable.response_objectives" multiple filterable allow-create default-first-option style="width:100%" />
          </el-form-item>
          <el-form-item label="信息缺口">
            <el-select v-model="editable.missing_information" multiple filterable allow-create default-first-option style="width:100%" />
          </el-form-item>
          <el-form-item label="资源情况">
            <div v-for="(r, i) in editable.available_resources" :key="i" style="display:flex;gap:8px;margin-bottom:6px">
              <el-select v-model="r.role" placeholder="岗位" style="flex:1">
                <el-option v-for="ro in roles" :key="ro.id" :label="ro.role_name" :value="ro.role_name" />
              </el-select>
              <el-input-number v-model="r.quantity" :min="0" style="width:100px" />
              <el-button size="small" text @click="removeResource(i)">删除</el-button>
            </div>
            <el-button size="small" @click="addResource">+ 添加资源</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <div style="display:flex;gap:10px">
      <el-button :loading="saving" @click="saveEdits">保存修改</el-button>
      <el-button type="primary" :disabled="event.status !== 'EVENT_ANALYZING'" @click="doConfirm">确认事件</el-button>
      <span v-if="event.status === 'EVENT_CONFIRMED' || (event.status && event.status !== 'EVENT_CREATED' && event.status !== 'EVENT_ANALYZING')" class="sub" style="align-self:center">
        事件已确认，可前往下一步「知识检索」
      </span>
    </div>
  </template>
</template>
