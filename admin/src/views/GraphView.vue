<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import cytoscape from "cytoscape";
import { getGraph, searchGraph, getGraphStats } from "../api/graph";

const route = useRoute();

const loading = ref(false);
const stats = ref({ entities: 0, relationships: 0, documents: 0 });
const connected = ref(true);
const searchQuery = ref("");
const searchResults = ref([]);
const cyContainer = ref(null);
let cy = null;

const TYPE_COLORS = {
  "岗位": "#2563eb", "设施": "#0d9488", "区域": "#d97706",
  "措施": "#7c3aed", "规范条文": "#dc2626", "事件类型": "#0891b2",
};

function colorFor(type) {
  return TYPE_COLORS[type] || "#64748b";
}

function renderGraph(data) {
  if (cy) cy.destroy();
  cy = cytoscape({
    container: cyContainer.value,
    elements: [
      ...data.nodes.map((n) => ({ data: { id: n.id, label: n.id, type: n.type, description: n.description } })),
      ...data.edges.map((e, i) => ({
        data: { id: `e${i}`, source: e.source, target: e.target, label: e.type },
      })),
    ],
    style: [
      {
        selector: "node",
        style: {
          "background-color": (ele) => colorFor(ele.data("type")),
          label: "data(label)",
          color: "#1e293b",
          "font-size": 11,
          "text-valign": "bottom",
          "text-margin-y": 4,
          width: 26,
          height: 26,
          "border-width": 2,
          "border-color": "#fff",
        },
      },
      {
        selector: "edge",
        style: {
          width: 1.5,
          "line-color": "#cbd5e1",
          "target-arrow-color": "#cbd5e1",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          label: "data(label)",
          "font-size": 9,
          color: "#94a3b8",
          "text-background-color": "#fff",
          "text-background-opacity": 0.8,
        },
      },
    ],
    layout: { name: "cose", animate: false, padding: 30 },
  });
}

async function load() {
  loading.value = true;
  connected.value = true;
  try {
    const documentId = route.query.document_id || undefined;
    const [graphData, statsData] = await Promise.all([getGraph(documentId), getGraphStats()]);
    stats.value = statsData;
    renderGraph(graphData);
  } catch (e) {
    if (e.code === "GRAPH_DB_UNAVAILABLE") connected.value = false;
  } finally {
    loading.value = false;
  }
}

async function doSearch() {
  if (!searchQuery.value.trim()) return;
  try {
    searchResults.value = await searchGraph(searchQuery.value);
  } catch (e) {
    if (e.code === "GRAPH_DB_UNAVAILABLE") connected.value = false;
  }
}

onMounted(load);
onUnmounted(() => { if (cy) cy.destroy(); });
watch(() => route.query.document_id, load);
</script>

<template>
  <div class="page-header">
    <div>
      <h2>知识图谱（GraphRAG）</h2>
      <div class="sub">{{ route.query.document_id ? `仅显示文档 ${route.query.document_id} 的图谱` : '全部知识文档的实体关系图谱' }}</div>
    </div>
    <el-button v-if="route.query.document_id" @click="$router.push({ name: 'graph' })">查看全部</el-button>
  </div>

  <el-alert
    v-if="!connected"
    type="error"
    :closable="false"
    show-icon
    title="Neo4j 未连接"
    description="请在 backend/.env 中配置 NEO4J_PASSWORD 等连接信息后重启后端服务。"
    style="margin-bottom:16px"
  />

  <template v-else>
    <div class="grid-3">
      <div class="card"><div class="card-title">实体总数</div><div style="font-size:24px;font-family:var(--mono)">{{ stats.entities }}</div></div>
      <div class="card"><div class="card-title">关系总数</div><div style="font-size:24px;font-family:var(--mono)">{{ stats.relationships }}</div></div>
      <div class="card"><div class="card-title">已构建文档数</div><div style="font-size:24px;font-family:var(--mono)">{{ stats.documents }}</div></div>
    </div>

    <div class="card">
      <div class="card-title">图谱可视化</div>
      <div ref="cyContainer" v-loading="loading" style="height:480px;background:var(--panel2);border-radius:6px"></div>
      <div style="display:flex;gap:12px;margin-top:10px;flex-wrap:wrap">
        <span v-for="(color, type) in TYPE_COLORS" :key="type" style="font-size:12px;display:flex;align-items:center;gap:5px">
          <span :style="{ background: color, width: '10px', height: '10px', borderRadius: '50%', display: 'inline-block' }"></span>
          {{ type }}
        </span>
      </div>
    </div>

    <div class="card">
      <div class="card-title">基础检索（先查图谱实体，再定位关联文档片段）</div>
      <div style="display:flex;gap:10px;margin-bottom:12px">
        <el-input v-model="searchQuery" placeholder="输入关键词，如岗位名称、设施名称" @keyup.enter="doSearch" />
        <el-button type="primary" @click="doSearch">检索</el-button>
      </div>
      <el-table :data="searchResults" size="small">
        <el-table-column prop="name" label="实体" width="160" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="description" label="描述" />
      </el-table>
      <div v-if="!searchResults.length" class="empty-hint">输入关键词后回车检索</div>
    </div>
  </template>
</template>
