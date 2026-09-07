<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { listDocuments, uploadDocument, updateDocument, deleteDocument } from "../api/knowledge";
import StatusChip from "../components/StatusChip.vue";

const CATEGORIES = [
  ["scene_material", "场景资料"],
  ["emergency_plan", "应急预案"],
  ["historical_case", "历史案例"],
  ["role_responsibility", "岗位职责"],
  ["plan_template", "预案模板"],
  ["report_template", "复盘模板"],
];

const documents = ref([]);
const loading = ref(false);
const uploadDialog = ref(false);
const uploading = ref(false);
const uploadForm = ref({ title: "", category: "emergency_plan", file: null });

async function load() {
  loading.value = true;
  try {
    documents.value = await listDocuments();
  } finally {
    loading.value = false;
  }
}

function categoryLabel(v) {
  return CATEGORIES.find((c) => c[0] === v)?.[1] || v;
}

function handleFileChange(uploadFile) {
  uploadForm.value.file = uploadFile.raw;
}

async function submitUpload() {
  if (!uploadForm.value.file || !uploadForm.value.title) {
    ElMessage.warning("请填写标题并选择文件");
    return;
  }
  uploading.value = true;
  try {
    await uploadDocument(uploadForm.value.file, uploadForm.value.title, uploadForm.value.category);
    ElMessage.success("上传并解析成功");
    uploadDialog.value = false;
    uploadForm.value = { title: "", category: "emergency_plan", file: null };
    await load();
  } finally {
    uploading.value = false;
  }
}

async function toggleStatus(row) {
  const next = row.status === "enabled" ? "disabled" : "enabled";
  await updateDocument(row.id, { status: next });
  ElMessage.success(next === "enabled" ? "已启用" : "已停用");
  await load();
}

async function remove(row) {
  await deleteDocument(row.id);
  ElMessage.success("已删除");
  await load();
}

onMounted(load);
</script>

<template>
  <div class="page-header">
    <div>
      <h2>知识库后台</h2>
      <div class="sub">应急预案、历史案例、岗位职责、场景资料等知识文档管理</div>
    </div>
    <el-button type="primary" @click="uploadDialog = true">+ 上传文档</el-button>
  </div>

  <div class="card">
    <el-table :data="documents" v-loading="loading">
      <el-table-column prop="title" label="文档名称" min-width="220" />
      <el-table-column label="分类" width="120">
        <template #default="{ row }">{{ categoryLabel(row.category) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }"><StatusChip :status="row.status" /></template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="70" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text @click="toggleStatus(row)">{{ row.status === 'enabled' ? '停用' : '启用' }}</el-button>
          <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div v-if="!loading && !documents.length" class="empty-hint">暂无知识文档，点击右上角上传</div>
  </div>

  <el-alert
    type="info"
    :closable="false"
    show-icon
    title="关于知识检索"
    description="文档上传后会自动解析并切分为片段，但向量检索（RAG）尚未接入 embedding，事件页「知识检索」步骤暂时无法命中这里的内容，仅作为知识库沉淀展示。"
    style="margin-top:16px"
  />

  <el-dialog v-model="uploadDialog" title="上传知识文档" width="480px">
    <el-form label-width="80px">
      <el-form-item label="标题"><el-input v-model="uploadForm.title" /></el-form-item>
      <el-form-item label="分类">
        <el-select v-model="uploadForm.category" style="width:100%">
          <el-option v-for="c in CATEGORIES" :key="c[0]" :label="c[1]" :value="c[0]" />
        </el-select>
      </el-form-item>
      <el-form-item label="文件">
        <el-upload :auto-upload="false" :limit="1" :on-change="handleFileChange" :show-file-list="true">
          <el-button>选择文件（.pdf / .docx / .txt / .md）</el-button>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="uploadDialog = false">取消</el-button>
      <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
    </template>
  </el-dialog>
</template>
