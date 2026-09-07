<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { getLlmSettings, updateLlmSettings } from "../api/settings";

const active = ref("");
const providers = ref([]);
const loading = ref(false);
const switching = ref(false);

async function load() {
  loading.value = true;
  try {
    const data = await getLlmSettings();
    active.value = data.active_provider;
    providers.value = data.providers;
  } finally {
    loading.value = false;
  }
}

async function switchProvider(providerId) {
  if (providerId === active.value) return;
  switching.value = true;
  try {
    await updateLlmSettings(providerId);
    active.value = providerId;
    ElMessage.success(`已切换为 ${providerId}，立即对下一次生成请求生效`);
  } finally {
    switching.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-header">
    <div>
      <h2>其他设置</h2>
      <div class="sub">大模型 provider 切换等运行时设置，优先级高于 .env，立即生效无需重启</div>
    </div>
  </div>

  <div class="card" v-loading="loading">
    <div class="card-title">大模型 Provider</div>
    <div v-for="p in providers" :key="p.id" style="display:flex;align-items:center;gap:16px;padding:12px 0;border-bottom:1px solid var(--line)">
      <el-radio :model-value="active" :value="p.id" @change="switchProvider(p.id)" :disabled="!p.configured || switching">
        {{ p.id === 'deepseek' ? 'DeepSeek' : 'Kimi (Moonshot)' }}
      </el-radio>
      <span class="sub" style="flex:1">模型：{{ p.model }} · Key：{{ p.api_key_masked || '未配置' }}</span>
      <el-tag v-if="!p.configured" type="info" size="small">未配置</el-tag>
      <el-tag v-else-if="p.id === active" type="success" size="small">当前使用中</el-tag>
    </div>
    <p class="sub" style="margin-top:12px">API Key 需要在 backend/.env 中配置（DEEPSEEK_API_KEY / KIMI_API_KEY），此页只负责切换哪一个生效。</p>
  </div>

  <el-alert
    type="info"
    :closable="false"
    show-icon
    title="更多设置"
    description="Neo4j 连接（NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD）、超时与重试次数等目前仍需在 backend/.env 中配置，暂未提供界面化管理。"
    style="margin-top:16px"
  />
</template>
