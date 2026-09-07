<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { listActivities, createActivity } from "../api/activities";
import StatusChip from "../components/StatusChip.vue";

const router = useRouter();
const activities = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const submitting = ref(false);

const form = ref({
  name: "",
  type: "演出",
  location: "",
  start_time: "",
  end_time: "",
  expected_attendance: null,
  description: "",
});

async function load() {
  loading.value = true;
  try {
    activities.value = await listActivities();
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  form.value = {
    name: "",
    type: "演出",
    location: "",
    start_time: "",
    end_time: "",
    expected_attendance: null,
    description: "",
  };
  dialogVisible.value = true;
}

async function submit() {
  if (!form.value.name || !form.value.start_time || !form.value.end_time) {
    ElMessage.warning("请填写活动名称与起止时间");
    return;
  }
  submitting.value = true;
  try {
    const activity = await createActivity(form.value);
    dialogVisible.value = false;
    ElMessage.success("活动创建成功");
    await load();
    router.push({ name: "activity-detail", params: { id: activity.id } });
  } finally {
    submitting.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page-header">
    <div>
      <h2>活动列表</h2>
      <div class="sub">创建重大演绎活动，绑定场景，作为后续事件处置的载体</div>
    </div>
    <el-button type="primary" @click="openCreate">+ 新建活动</el-button>
  </div>

  <div class="card">
    <el-table :data="activities" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="活动名称" min-width="200">
        <template #default="{ row }">
          <router-link :to="{ name: 'activity-detail', params: { id: row.id } }">{{ row.name }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="location" label="地点" min-width="160" />
      <el-table-column label="时间" min-width="220">
        <template #default="{ row }">{{ row.start_time }} ~ {{ row.end_time }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }"><StatusChip :status="row.status" context="activity" /></template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <router-link :to="{ name: 'activity-detail', params: { id: row.id } }">查看详情</router-link>
        </template>
      </el-table-column>
    </el-table>
    <div v-if="!loading && !activities.length" class="empty-hint">暂无活动，点击右上角新建</div>
  </div>

  <el-dialog v-model="dialogVisible" title="新建活动" width="520px">
    <el-form :model="form" label-width="90px">
      <el-form-item label="活动名称" required>
        <el-input v-model="form.name" placeholder="如：复兴岛船台公园重大演绎活动" />
      </el-form-item>
      <el-form-item label="活动类型">
        <el-select v-model="form.type" style="width:100%">
          <el-option label="演出" value="演出" />
          <el-option label="展会" value="展会" />
          <el-option label="节庆活动" value="节庆活动" />
          <el-option label="体育赛事" value="体育赛事" />
        </el-select>
      </el-form-item>
      <el-form-item label="活动地点">
        <el-input v-model="form.location" placeholder="如：复兴岛船台公园" />
      </el-form-item>
      <el-form-item label="开始时间" required>
        <el-date-picker v-model="form.start_time" type="datetime" style="width:100%" value-format="YYYY-MM-DDTHH:mm:ss" />
      </el-form-item>
      <el-form-item label="结束时间" required>
        <el-date-picker v-model="form.end_time" type="datetime" style="width:100%" value-format="YYYY-MM-DDTHH:mm:ss" />
      </el-form-item>
      <el-form-item label="预计人数">
        <el-input-number v-model="form.expected_attendance" :min="0" style="width:100%" />
      </el-form-item>
      <el-form-item label="说明">
        <el-input v-model="form.description" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">创建</el-button>
    </template>
  </el-dialog>
</template>
