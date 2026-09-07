<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getEvent, retrieveKnowledge, updateRetrievalSelection } from "../api/events";
import EventStepper from "../components/EventStepper.vue";

const props = defineProps({ id: { type: String, required: true } });
const router = useRouter();

const event = ref(null);
const result = ref(null);
const retrieving = ref(false);
const submitting = ref(false);
const selected = ref(new Set());

async function load() {
  event.value = await getEvent(props.id);
}

async function doRetrieve() {
  retrieving.value = true;
  try {
    const res = await retrieveKnowledge(props.id);
    result.value = res.result;
    selected.value = new Set(res.result.related_plans.map((p) => p.document_id));
  } finally {
    retrieving.value = false;
  }
}

function toggle(id) {
  if (selected.value.has(id)) selected.value.delete(id);
  else selected.value.add(id);
}

async function submitAndNext() {
  submitting.value = true;
  try {
    await updateRetrievalSelection(props.id, { selected_chunk_ids: [...selected.value] });
    ElMessage.success("已保存知识选择，进入预案生成");
    router.push({ name: "plan-editor", params: { id: props.id } });
  } finally {
    submitting.value = false;
  }
}

onMounted(load);
</script>

<template>
  <EventStepper :event-id="id" />
  <div class="page-header">
    <div>
      <h2>知识检索</h2>
      <div class="sub">根据事件类型/地点/风险等级/参与岗位构造查询，检索相关预案、案例、岗位职责与场景知识</div>
    </div>
    <el-button type="primary" :loading="retrieving" @click="doRetrieve">检索相关知识</el-button>
  </div>

  <el-alert
    v-if="result && !result.related_plans.length && !result.similar_cases.length"
    type="warning"
    :closable="false"
    show-icon
    style="margin-bottom:16px"
    title="检索结果为空"
    description="向量检索服务（RAG）尚未接入 embedding，知识库文档已解析入库但暂时无法被语义检索命中。可直接跳过本步，预案生成 Agent 仍会正常运行，只是不会附带知识引用。"
  />

  <template v-if="result">
    <div class="grid-2">
      <div class="card">
        <div class="card-title">相关预案（{{ result.related_plans.length }}）</div>
        <div v-if="!result.related_plans.length" class="empty-hint">无结果</div>
        <div v-for="p in result.related_plans" :key="p.document_id" class="card" style="background:var(--panel2);margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <b>{{ p.document_title }}</b>
            <el-checkbox :model-value="selected.has(p.document_id)" @change="toggle(p.document_id)">选用</el-checkbox>
          </div>
          <p class="sub">{{ p.summary }}（相似度 {{ p.similarity }}）</p>
        </div>
      </div>
      <div class="card">
        <div class="card-title">相似案例（{{ result.similar_cases.length }}）</div>
        <div v-if="!result.similar_cases.length" class="empty-hint">无结果</div>
        <div v-for="c in result.similar_cases" :key="c.document_id" class="card" style="background:var(--panel2);margin-bottom:8px">
          <b>{{ c.case_name }}</b>
          <p class="sub">{{ c.main_measures }}</p>
        </div>
      </div>
      <div class="card">
        <div class="card-title">岗位职责（{{ result.role_responsibilities.length }}）</div>
        <div v-if="!result.role_responsibilities.length" class="empty-hint">无结果</div>
        <div v-for="(r, i) in result.role_responsibilities" :key="i" class="card" style="background:var(--panel2);margin-bottom:8px">
          <b>{{ r.role_name }}</b>
          <p class="sub">{{ r.standard_responsibility }}</p>
        </div>
      </div>
      <div class="card">
        <div class="card-title">场景知识（{{ result.scene_knowledge.length }}）</div>
        <div v-if="!result.scene_knowledge.length" class="empty-hint">无结果</div>
        <div v-for="(s, i) in result.scene_knowledge" :key="i" class="card" style="background:var(--panel2);margin-bottom:8px">
          <b>{{ s.related_area }}</b>
          <p class="sub">{{ s.channels_and_facilities }}</p>
        </div>
      </div>
    </div>

    <el-button type="primary" :loading="submitting" @click="submitAndNext">保存选择，进入预案生成 →</el-button>
  </template>
</template>
