# 重大演绎活动应急预案智能生成系统 —— 后端 MVP

面向重大演绎活动的应急预案智能生成教学实践平台后端。围绕"事件识别—预案生成—任务分解—人机协同—复盘沉淀"闭环，实现应急预案的智能编制、执行支撑与案例沉淀。

本仓库是后端服务：数据模型、API、Agent 编排逻辑已实现并通过端到端联调；大模型（DeepSeek/Kimi）已真实接入，向量检索（RAG embedding）是唯一仍留空的部分（见「当前状态与已知缺口」）。

## 技术栈

- **FastAPI** + **Pydantic v2** —— API 与数据校验
- **SQLAlchemy 2.0** + **Alembic** —— ORM 与数据库迁移
- **SQLite**（开发默认，`DATABASE_URL` 可切换为其他数据库）
- **python-docx** / **pypdf** —— 文档导出与解析
- **httpx** —— 调用 DeepSeek / Kimi 的 OpenAI 兼容接口
- **neo4j**（官方驱动） —— GraphRAG 轻量版的图数据库

## 目录结构

```text
backend/
├── app/
│   ├── main.py              # FastAPI 入口，异常处理器与路由挂载
│   ├── core/                # 配置、数据库会话、统一响应体、业务异常
│   ├── models/               # 19 张业务表（SQLAlchemy ORM）
│   ├── schemas/              # Pydantic Schema，对应各 Agent 的结构化输出
│   ├── agents/                # 5 类 Agent 的 prompt 构造 + 调用编排（含 GraphRAG 实体抽取）
│   ├── services/              # LLM/RAG/GraphRAG/文档解析/导出/版本/设置 服务
│   ├── api/                   # 11 个路由模块，对应 7 条业务流程 + 岗位/图谱/设置
│   ├── workflows/             # 事件主链路状态机定义
│   ├── repositories/          # 预留数据访问层（当前直接在 api 层用 ORM）
│   └── prompts/               # 预留 prompt 模板目录
├── migrations/                # Alembic 迁移脚本
├── tests/                     # 预留测试目录
├── pyproject.toml
└── .env.example
```

## 核心业务闭环

```text
创建活动场景 → 录入突发事件 → 事件结构化 → 检索知识 → 生成预案 → 人工审核
→ 确认预案 → 分解岗位任务 → 人工调整任务 → 记录任务执行 → 生成复盘报告
→ 人工修订 → 沉淀为案例
```

事件从创建到复盘确认的状态机（`app/workflows/states.py`）：

```text
EVENT_CREATED → EVENT_ANALYZING → EVENT_CONFIRMED → KNOWLEDGE_RETRIEVING
→ KNOWLEDGE_SELECTED → PLAN_GENERATING → PLAN_DRAFTED → PLAN_CONFIRMED
→ TASKS_GENERATING → TASKS_DRAFTED → TASKS_CONFIRMED → TASKS_EXECUTING
→ EVENT_CLOSED → REPORT_GENERATING → REPORT_DRAFTED → REPORT_CONFIRMED
```

## 数据模型

19 张表，`app/models/__init__.py` 统一导出，核心关系：

```text
Activity ─ Scene ─ SceneArea
    │
  Event ── RetrievalRecord
    │
   Plan ── PlanVersion
    │
   Task ── TaskExecution
    │
  Report ── ReportVersion

KnowledgeDocument ── KnowledgeChunk（支撑事件分析/预案生成/任务分解/复盘改进；实体/关系本身存在 Neo4j，不在这19张表里）
AgentRun（每次大模型调用的完整记录：输入、原始输出、解析结果、耗时、成败）
AuditLog（预留，当前未在业务路由中写入）
SystemSetting（运行时设置覆盖，目前只有 llm_provider 一项，见 admin"其他设置"）
```

## Agent 架构

| Agent | 文件 | 输出 Schema | 说明 |
|---|---|---|---|
| 事件分析 | `agents/event_analyzer.py` | `EventStructuredData` | 自然语言事件描述 → 结构化字段 |
| 知识检索 | `agents/knowledge_retriever.py` | `RetrievalResult` | 构造查询文本，调用 `RagService` 分类返回相关预案/案例/岗位职责/场景知识 |
| 预案生成 | `agents/plan_generator.py` | `PlanStructuredContent` | 九部分结构化预案，支持整体生成与按章节局部重新生成 |
| 任务分解 | `agents/task_generator.py` | `TaskGenerationOutput` | 与预案生成使用同一底层模型，但独立 prompt / schema / 调用记录 |
| 复盘报告 | `agents/report_generator.py` | `ReportStructuredContent` | 统计数字由代码预先算好传入，大模型只做归纳解释，返回后强制以代码结果覆盖，防止模型篡改数字 |
| 实体/关系抽取（GraphRAG） | `agents/entity_extractor.py` | `EntityExtractionOutput` | 从知识文档文本抽取实体与关系，写入 Neo4j，供 admin 平台图谱可视化与检索 |

所有 Agent 继承 `agents/base.py` 的 `BaseAgent`，统一处理：

1. 每次调用写入 `AgentRun` 记录（模型名、prompt 版本、输入摘要、原始输出、耗时、成败），**独立于外层业务事务提交**，即使后续生成失败也可追溯；
2. JSON 解析 + Pydantic Schema 校验，失败自动重试一次；
3. 仍失败则抛出 `AgentGenerationError`，携带 `agent_run_id` 和 `retryable`，由 `main.py` 的异常处理器转换为统一错误响应。

## API 一览

统一响应体：`{success, code, message, data, request_id}`，业务异常经 `app/core/exceptions.py` 统一转换。

| 模块 | 路由文件 | 端点 |
|---|---|---|
| 活动 | `api/activities.py` | 增删改查 `/api/activities` |
| 场景 | `api/scenes.py` | 增删改查 `/api/scenes`（含区域/通道/岗位配置） |
| 事件 | `api/events.py` | 创建（表单/自然语言）、分析、确认、关闭、执行汇总 |
| 知识库 | `api/knowledge.py` | 文档上传解析切分、检索、检索结果人工选择 |
| 预案 | `api/plans.py` | 生成、版本管理、局部重新生成、确认、导出 |
| 岗位任务 | `api/tasks.py` | 生成、CRUD、基础校验、确认清单 |
| 任务执行 | `api/executions.py` | 状态流转（开始/完成/未完成/取消）、执行记录 |
| 复盘报告 | `api/reports.py` | 生成、版本管理、确认、沉淀为案例、导出 |
| 岗位（补充） | `api/roles.py` | 最小 list + create，供前端角色选择器使用 |
| 知识图谱 GraphRAG | `api/graph.py` | 按文档构建图谱、图谱可视化数据、实体检索、统计 |
| 系统设置 | `api/settings.py` | 大模型 provider 运行时切换（`system_settings` 表，优先级高于 `.env`） |

完整端点清单可运行服务后访问 `/docs`（Swagger UI）查看。

## 快速开始

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env          # 按需修改 DATABASE_URL / LLM_* 等配置

# 首次建表（两种方式二选一）
.venv/bin/python -m alembic upgrade head      # 推荐：走迁移
# 或者直接启动，main.py 的 startup 钩子会自动 create_all（仅适合本地试跑）

.venv/bin/uvicorn app.main:app --reload
```

启动后访问 `http://127.0.0.1:8000/docs` 查看接口文档，`/api/health` 做健康检查。

### 生成新的迁移

修改 `app/models/` 下的表结构后：

```bash
.venv/bin/python -m alembic revision --autogenerate -m "描述改动"
.venv/bin/python -m alembic upgrade head
```

## 当前状态与已知缺口

### 已验证可用
数据模型、API 路由、状态机、版本管理、任务基础校验、Word 导出、案例沉淀回写知识库均已实现，并跑通了从建活动到导出复盘报告的完整链路（含正常路径与异常路径，如非法状态跳转、无效任务转换会被正确拦截）。

**大模型已真实接入并联调通过**：`app/services/llm_service.py` 支持 DeepSeek / Kimi(Moonshot) 两个 OpenAI 兼容 provider，通过 `.env` 的 `LLM_PROVIDER` 切换，配置见 `.env.example`。四个 Agent（事件分析/预案生成/任务分解/复盘报告）已用真实 API 跑通完整链路：事件分析→预案生成（9部分结构化，~10s）→任务分解（9项任务，~17s）→复盘报告（统计数字保持代码计算结果，定性内容由模型生成，~10s），均一次通过 Schema 校验。

关键经验：
- prompt 里只用中文描述"九个部分"是不够的——模型会自创英文字段名（如 `event_overview`、`disposal_process`），必须在 prompt 里给出逐字段 JSON 骨架（骨架字段名需与对应 Pydantic Schema 完全一致），才能稳定通过校验。四个 Agent 的 prompt 模板（`app/agents/*.py`）均已包含骨架，供后续调整参考。
- Kimi 的 `kimi-k3` 是推理模型，只接受 `temperature=1`，传其他值会直接 400；`llm_service.py` 已按 provider 做了区分。

provider 可在运行时切换，不需要改 `.env` 重启：`system_settings` 表存了一条 `llm_provider` 覆盖值，优先级高于 `.env`，通过 `PUT /api/settings/llm`（admin 平台"其他设置"页）修改，`LLMService` 每次实例化时会先查这张表。

### GraphRAG（轻量版，admin 平台）
`app/services/graph_service.py` 封装 Neo4j 读写，`app/agents/entity_extractor.py` 用大模型从文档文本抽取实体/关系。流程：文档解析文本 → `EntityExtractorAgent` 结构化抽取 → 写入 Neo4j → admin 平台可视化/检索。**需要 `.env` 中配置 `NEO4J_PASSWORD`**（建议为本项目单独建库/建用户，与其他项目的图数据隔离），未配置时 `/api/graph/*` 统一返回 `GRAPH_DB_UNAVAILABLE`（503），不影响其余功能。

### 有意留空
- **`app/services/rag_service.py`**：`search()` 恒返回空结果，向量检索/embedding 未接入，事件页"知识检索"步骤命中不了知识库内容。GraphRAG（见上）是当前唯一已联调的检索增强路径，两者是独立机制，尚未打通。
- **PDF 导出**：`export_service.py` 中 `export_markdown_to_pdf()` 未实现，仅 Word 导出可用。

### 原始需求文档接口清单本身的缺口
以下功能在需求文档的模块清单中提到，但接口清单（第十节）未给出具体路径。岗位与事件/预案/复盘的查询类接口已补最小实现（见各 `api/*.py` 文件内注释），登录鉴权与系统日志仍未实现：
- 用户登录与权限管理（`users` 表已建，无 `/api/auth/*`，**当前无任何权限控制，不要直接暴露给不受信任的网络**）
- 系统日志查询（`audit_logs` 表已建，当前业务路由未写入任何记录）

接入公开网络前，建议先补齐登录鉴权。
