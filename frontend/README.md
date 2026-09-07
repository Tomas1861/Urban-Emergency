# 重大演绎活动应急预案智能生成系统 —— 前端

连接 [../backend](../backend) 的真实可操作前端应用。Vue 3 + Vite + Element Plus，浅色（白底）主题；态势大屏页保留了 canvas 绘制与整体布局，配色也已同步改为浅色系。管理功能（RAG 文件、GraphRAG、系统设置）已拆分到独立的 [../admin](../admin) 项目。

> **注意**：本项目的 `views/KnowledgeAdminView.vue`（侧边栏"知识库后台"）和 admin 项目的"RAG 文件管理"页面调用的是同一套后端接口、管理同一份文档数据，功能有重叠——保留前者是为了方便在演示流程里直接查看知识库，文档的上传/构建图谱等管理操作建议统一去 admin 做，避免两边各改一半。

## 技术栈

- **Vue 3**（`<script setup>`）+ **Vite**
- **Vue Router** + **Pinia**
- **Element Plus**（浅色主题，CSS 变量覆盖为品牌色）
- **Axios**

## 目录结构

```text
src/
├── main.js              # 应用入口，注册 Element Plus / Pinia / Router
├── App.vue               # 侧边栏 + 顶栏布局
├── style.css              # 全局浅色主题变量与工具类
├── api/                    # 每个后端模块一个文件，薄封装 axios 调用
├── router/                 # 路由表
├── stores/app.js            # 岗位列表等跨页共享状态
├── components/
│   ├── StatusChip.vue        # 状态徽标，统一把后端状态码映射为中文
│   └── EventStepper.vue       # 事件六步骤导航条（事件确认→…→复盘报告）
├── views/                     # 对应需求文档第七节的 10 个页面
│   ├── ActivityListView.vue      # 页面2 活动列表
│   ├── ActivityDetailView.vue    # 页面3 活动详情（含场景配置）
│   ├── EventEditorView.vue       # 页面4 事件录入与确认（含新建/编辑两种模式）
│   ├── KnowledgeSelectionView.vue # 页面5 知识检索
│   ├── PlanEditorView.vue        # 页面6 预案生成与编辑
│   ├── TaskBoardView.vue         # 页面7 岗位任务清单
│   ├── ExecutionPanelView.vue    # 页面8 任务执行
│   ├── ReportEditorView.vue      # 页面9 复盘报告
│   ├── KnowledgeAdminView.vue    # 页面10 知识库后台
│   └── DashboardView.vue         # 额外增设的"态势大屏"人群疏散仿真演示
└── sampleData.js               # 演示兜底用的示例预案/任务/复盘内容
```

## 快速开始

```bash
cd frontend
npm install
cp .env.development .env.development.local   # 按需修改 VITE_API_BASE，默认 http://127.0.0.1:8000
npm run dev
```

同时需要启动后端（见 `../backend/README.md`）：

```bash
cd ../backend
.venv/bin/uvicorn app.main:app --reload
```

## 演示兜底机制

后端已接入真实大模型（DeepSeek，见 `../backend/README.md`），「AI 生成」按钮正常情况下会在 10~20 秒内返回真实结果。但现场网络、API 额度、模型限流都可能导致临时失败，所以仍保留了兜底路径：所有生成类页面（预案生成、任务分解、复盘报告）在 AI 调用失败后，都提供一个「载入示例XX（演示兜底）」按钮，会调用后端"保存人工版本"接口写入与需求文档一致的示例内容，确保演示现场无论如何都能不中断地走完整个流程：

```
事件确认 → 知识检索（结果为空，附说明） → 预案生成（AI失败→载入示例） → 任务分解（AI失败→载入示例）
→ 执行跟踪（真实状态机） → 复盘报告（统计数字真实计算，AI失败→载入示例定性内容）→ 沉淀为案例
```

接入真实模型后，「AI 生成」按钮会直接产出结果，兜底按钮不再需要，但不影响其正常工作。

## 与旧演示的关系

`../复兴岛应急决策MVP演示.html` 是独立的人群疏散仿真剧本演示（canvas + 打字机式多智能体会商日志），本次原样移植进 `views/DashboardView.vue`，作为应用内的"态势大屏"页面，逻辑未改动。它与其余页面是并列关系：`态势大屏` 用于开场吸引注意力，其余页面用于展示预案生成这条真实业务闭环。

## 联调中发现并修复的问题

后端问题（详见 `../backend/app/`）：
- `SceneOut` schema 缺少 `activity_id` 字段，导致前端无法把场景关联回活动。
- 需求文档第十节接口清单遗漏了"按 activity 查事件列表"“按 event 查预案/复盘报告”“岗位管理”三类查询，已在 `roles.py` 与 `events.py`/`plans.py`/`reports.py` 中补充最小实现（均已注明来源）。
- `AgentRun` 失败记录曾因外层事务回滚而丢失（见 `../backend/app/agents/base.py`），已修复为独立提交。

前端自身的问题：
- **`api/client.js` 的 axios 响应拦截器有个隐藏 bug**：后端所有业务错误都用非 2xx 状态码返回（400/404/422/503…），但拦截器只在 2xx 响应里把 `code`/`data` 解析到抛出的 Error 上；非 2xx 走的是另一个分支，只弹了通用错误提示、没挂 `code`。结果是页面里所有 `if (e.code === "MODEL_CALL_FAILED")` 这类判断从来没真正生效过，只是被更笼统的错误弹窗盖住了，表现上"看起来能用"但分支代码是死的。已修复为两个分支都解析 `code`/`data`，用 GraphRAG 未连接的场景验证过确实生效。admin 项目的 `client.js` 是从这里复制的，同一个 bug 也一并修了。
