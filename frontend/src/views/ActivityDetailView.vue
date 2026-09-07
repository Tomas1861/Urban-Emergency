<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getActivity } from "../api/activities";
import { listScenes, createScene } from "../api/scenes";
import { listRoles } from "../api/roles";
import { listEvents } from "../api/events";
import StatusChip from "../components/StatusChip.vue";

const props = defineProps({ id: { type: String, required: true } });
const router = useRouter();

const activity = ref(null);
const scene = ref(null);
const roles = ref([]);
const events = ref([]);
const loading = ref(false);
const sceneDialogVisible = ref(false);
const submitting = ref(false);

const sceneForm = ref({
  name: "",
  description: "",
  key_channels: "",
  entrances: "",
  key_facilities: "",
  available_roles: [],
  base_resources: "",
  areas: [],
});

async function load() {
  loading.value = true;
  try {
    const [a, scenes, rs, evts] = await Promise.all([
      getActivity(props.id),
      listScenes(),
      listRoles(),
      listEvents(props.id),
    ]);
    activity.value = a;
    roles.value = rs;
    scene.value = scenes.find((s) => s.activity_id === props.id) || null;
    events.value = evts;
  } finally {
    loading.value = false;
  }
}

function openSceneDialog() {
  sceneForm.value = {
    name: `${activity.value?.name || ""}场景`,
    description: "",
    key_channels: "",
    entrances: "",
    key_facilities: "",
    available_roles: [],
    base_resources: "",
    areas: [],
  };
  sceneDialogVisible.value = true;
}

function splitLines(s) {
  return (s || "").split(/[,，\n]/).map((x) => x.trim()).filter(Boolean);
}

async function submitScene() {
  if (!sceneForm.value.name) {
    ElMessage.warning("请填写场景名称");
    return;
  }
  submitting.value = true;
  try {
    await createScene({
      activity_id: props.id,
      name: sceneForm.value.name,
      description: sceneForm.value.description,
      key_channels: splitLines(sceneForm.value.key_channels),
      entrances: splitLines(sceneForm.value.entrances),
      key_facilities: splitLines(sceneForm.value.key_facilities),
      available_roles: sceneForm.value.available_roles,
      base_resources: sceneForm.value.base_resources,
      areas: [],
    });
    sceneDialogVisible.value = false;
    ElMessage.success("场景创建成功");
    await load();
  } finally {
    submitting.value = false;
  }
}

function createEvent() {
  router.push({ name: "event-new", query: { activityId: props.id, sceneId: scene.value?.id || "" } });
}

const roleOptions = computed(() => roles.value.map((r) => r.role_name));

onMounted(load);
</script>

<template>
  <div v-if="activity" class="page-header">
    <div>
      <h2>{{ activity.name }}</h2>
      <div class="sub">{{ activity.type }} · {{ activity.location }} · {{ activity.start_time }} ~ {{ activity.end_time }}</div>
    </div>
    <StatusChip :status="activity.status" context="activity" />
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-title"><span>场景配置</span>
        <el-button v-if="!scene" size="small" type="primary" @click="openSceneDialog">创建场景</el-button>
      </div>
      <template v-if="scene">
        <div class="kv-row"><span class="k">场景名称</span><span class="v">{{ scene.name }}</span></div>
        <div class="kv-row"><span class="k">说明</span><span class="v">{{ scene.description || "—" }}</span></div>
      </template>
      <div v-else class="empty-hint">尚未配置场景，事件发生地点、可用岗位与资源信息依赖场景配置</div>
    </div>

    <div class="card">
      <div class="card-title"><span>可用岗位（管理员预置）</span></div>
      <div v-if="roles.length" style="display:flex;flex-wrap:wrap;gap:8px">
        <el-tag v-for="r in roles" :key="r.id" type="info">{{ r.role_name }}</el-tag>
      </div>
      <div v-else class="empty-hint">暂无岗位数据</div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">
      <span>突发事件</span>
      <el-button size="small" type="primary" :disabled="!scene" @click="createEvent">+ 录入突发事件</el-button>
    </div>
    <div class="empty-hint" v-if="!scene">请先创建场景后再录入事件</div>
    <template v-else>
      <el-table v-if="events.length" :data="events" style="width:100%">
        <el-table-column label="事件名称" min-width="180">
          <template #default="{ row }">
            <router-link :to="{ name: 'event-editor', params: { id: row.id } }">{{ row.event_name }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="event_type" label="类型" width="140" />
        <el-table-column prop="location" label="地点" min-width="140" />
        <el-table-column prop="risk_level" label="风险等级" width="90" />
        <el-table-column label="状态" width="140">
          <template #default="{ row }"><StatusChip :status="row.status" /></template>
        </el-table-column>
      </el-table>
      <div v-else class="empty-hint">
        本活动尚无事件记录 —— 点击右上角"录入突发事件"开始完整的预案生成演示流程
      </div>
    </template>
  </div>

  <el-dialog v-model="sceneDialogVisible" title="创建场景" width="560px">
    <el-form :model="sceneForm" label-width="100px">
      <el-form-item label="场景名称" required>
        <el-input v-model="sceneForm.name" />
      </el-form-item>
      <el-form-item label="场景说明">
        <el-input v-model="sceneForm.description" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="关键通道">
        <el-input v-model="sceneForm.key_channels" placeholder="逗号分隔，如：东侧主要通道，西侧便桥" />
      </el-form-item>
      <el-form-item label="出入口">
        <el-input v-model="sceneForm.entrances" placeholder="逗号分隔" />
      </el-form-item>
      <el-form-item label="关键设施">
        <el-input v-model="sceneForm.key_facilities" placeholder="逗号分隔" />
      </el-form-item>
      <el-form-item label="可参与岗位">
        <el-select v-model="sceneForm.available_roles" multiple style="width:100%">
          <el-option v-for="r in roleOptions" :key="r" :label="r" :value="r" />
        </el-select>
      </el-form-item>
      <el-form-item label="基本资源">
        <el-input v-model="sceneForm.base_resources" type="textarea" :rows="2" placeholder="如：隔离带20条、应急照明10套" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="sceneDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submitScene">创建</el-button>
    </template>
  </el-dialog>
</template>
