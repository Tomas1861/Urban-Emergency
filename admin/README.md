# 重大演绎活动应急预案智能生成系统 —— 管理后台

独立于 [../frontend](../frontend) 的管理平台，连接同一个 [../backend](../backend)。浅色（白底）主题，与 frontend 的浅色主题保持视觉一致，但两个前端项目彼此完全解耦、可独立部署。

## 功能

- **RAG 文件管理**（`/documents`）：知识文档上传/分类/启用停用/删除，并可一键触发该文档的知识图谱构建。
- **知识图谱 GraphRAG**（`/graph`）：Cytoscape.js 可视化实体关系图，支持按文档筛选、关键词检索实体。
- **其他设置**（`/settings`）：大模型 provider（DeepSeek / Kimi）切换，运行时生效、无需重启后端。

## 技术栈

Vue 3 + Vite + Element Plus（浅色主题）+ Cytoscape.js（图谱可视化）。

## 目录结构

```text
src/
├── main.js              # 应用入口
├── App.vue               # 侧边栏 + 顶栏布局
├── style.css              # 全局浅色主题变量（与 frontend 共用同一套配色，各自独立一份文件）
├── api/                    # client.js（含错误拦截）、knowledge.js、graph.js、settings.js
├── router/                 # 路由表：/documents /graph /settings
├── components/StatusChip.vue  # 从 frontend 复制的状态徽标组件
└── views/
    ├── DocumentsView.vue      # RAG 文件管理 + 触发图谱构建
    ├── GraphView.vue          # GraphRAG 可视化 + 检索
    └── SettingsView.vue       # 大模型 provider 切换
```

## 快速开始

```bash
cd admin
npm install
npm run dev -- --port 5174
```

需要 backend 已启动（见 `../backend/README.md`），且 `.env.development` 中 `VITE_API_BASE` 指向正确的后端地址。

## GraphRAG 说明（轻量版）

- 抽取流程：文档解析文本（`KnowledgeDocument.parsed_text`，取前 6000 字）→ `EntityExtractorAgent`（LLM 结构化抽取实体/关系）→ 写入 Neo4j。
- 未做真正 GraphRAG 的社区检测/摘要（Microsoft GraphRAG 的 community summarization），仅做实体级别的抽取、存储、可视化与关键词检索，满足"轻量版"验收目标。
- 需要在 `backend/.env` 配置 `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` / `NEO4J_DATABASE`，建议使用独立数据库（Neo4j 企业版支持同实例多库），与其他项目（如 HazmatAI_v2）的图数据隔离。
- Neo4j 未连接时，相关接口返回 `GRAPH_DB_UNAVAILABLE`（HTTP 503），前端会展示明确的配置指引而不是报错崩溃。

## 与 frontend 的关系

两个项目各自独立打包部署，通过 `VITE_API_BASE` 共享同一个后端。frontend 面向"教学演示/操作"场景（活动、事件、预案生成全流程），admin 面向"知识库与系统管理"场景。没有共享登录态或权限隔离——后端目前没有鉴权（见 backend/README.md），生产部署前需要补上。

`api/client.js` 是从 frontend 复制过来的，包含同一处已修复的 bug：axios 拦截器之前只在 2xx 响应里解析后端错误体的 `code`/`data`，但后端所有业务错误都是非 2xx 状态码，导致页面里 `e.code === "GRAPH_DB_UNAVAILABLE"` 这类判断从未真正生效（详见 `../frontend/README.md`"联调中发现并修复的问题"）。两边的 `client.js` 已同步修复并用 Neo4j 未连接场景验证过。
