# Ontology 基座技术方案

> 写给成员A（本体与行动工程），也是三个月冲刺计划"流程0·本体维护"的具体技术落地。
> 前提：不是从零设计一套通用本体系统，是在现有 `backend/app/models/`（Activity/Scene/Event/Plan/Task）基础上做最小扩展，撑起"东侧通道故障"这一个场景。

## 一、技术选型：关系数据库，不上图数据库

需求重构稿 2.1 节原话："首期可用关系数据库、显式关系表、类型化接口和规则服务实现本体……本方案不绑定具体供应商。"

**结论：继续用 SQLAlchemy + SQLite（现有技术栈），不接入已装但未使用的 Neo4j 驱动。**

理由：
- 一个场地的通道、区域、岗位撑死几十个实例，关系查询用 SQL JOIN 完全够用，用不上图数据库的多跳遍历性能优势。
- 团队已经熟悉 SQLAlchemy，引入图数据库意味着多学一套查询语言（Cypher）、多运维一个服务——对 3 人团队、一年期项目是不必要的复杂度。
- 只要服务层做了抽象（见下），以后查询真的变复杂了再换存储方案，不影响调用方代码。

## 二、分三层，不要让 Agent 直接查表

```
Agent / API
     │  只调用下面这层暴露的方法
     ▼
OntologyService（服务层）—— 本体的唯一入口
     │
     ▼
数据层：对象实例表 + 关系表 + 别名表（SQLAlchemy models）
```

**关键规矩：Agent 代码里不允许出现直接查 `Passage`、`Zone` 等表的 SQL/ORM 查询。** 所有读写走 `OntologyService`。这不是洁癖，是因为一旦 Agent 代码里散落着裸查询，以后想加一条校验规则（比如"证据过期不能当已确认用"）就要满代码库去改，迟早漏掉一处。

## 三、数据模型：定义与实例分开，状态与证据分开

### 3.1 对象类型：不建表，用代码常量就够

需求重构稿 4.1 节要求"对象类型是统一定义……定义和实例分别管理"。但对象类型（通道、区域、岗位……）这几年内不会新增新种类，不需要做成用户可动态定义的元数据表——那是过度设计。直接用一个枚举：

```python
class ObjectType(str, Enum):
    ACTIVITY = "activity"
    ZONE = "zone"
    PASSAGE = "passage"
    TEAM_MEMBER = "team_member"
    TASK = "task"
    # 三个月冲刺只需要这 5 种，其余（Facility/Device/Resource...）等真正用到再加
```

### 3.2 对象实例表：每个状态字段必须配一个证据字段

以新建的 `Passage`（通道）表为例，这是本方案最重要的一条设计规则：

```python
class Passage(Base):
    __tablename__ = "passages"

    id: Mapped[str] = mapped_column(primary_key=True)          # "PASS-E"，人可读编号，不用自增ID
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id"))
    name: Mapped[str]                                            # "东侧主通道"
    direction: Mapped[str]                                       # 双向/单向

    # ---- 业务状态 ----
    passability_status: Mapped[str]         # 可通行 / 受限 / 不可通行

    # ---- 证据状态：和上面的字段成对出现，缺一不可 ----
    passability_evidence: Mapped[str]       # 已确认 / 待核实 / 多源冲突 / 已过期 / 未知
    passability_observed_at: Mapped[datetime | None]
    passability_source: Mapped[str | None]  # 这个判断是谁/什么设备给的

    version: Mapped[int] = mapped_column(default=1)  # 乐观锁，见五、
```

**为什么不能只存 `passability_status` 一个字段**：需求重构稿 4.4 节的例子——"备用通道最近记录为可通行，但检查记录已过期"——如果只有一个状态字段，系统没有任何办法表达"这个结论已经不新鲜了"，AI 和人都会把过期信息当成当前事实用。这是本体设计里唯一不能省的一条。

### 3.3 关系表：显式建表，不要塞进 JSON 字段

需求重构稿 4.3 节列的关系（"通道→连接→区域"等）要建成单独的表，不要图省事存成一个 JSON 字段：

```python
class PassageConnection(Base):
    __tablename__ = "passage_connections"

    id: Mapped[str] = mapped_column(primary_key=True)
    passage_id: Mapped[str] = mapped_column(ForeignKey("passages.id"))
    from_zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"))
    to_zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"))
    effective_from: Mapped[datetime]
    effective_to: Mapped[datetime | None]   # 需求稿4.3节要求关系带生效时间
```

用 JSON 字段存关系，短期写起来快，但查"哪些任务依赖这条通道"这种问题时，数据库帮不了你做 JOIN 和约束校验，全部要在应用层手写，迟早出 bug 且难维护。三个月冲刺阶段对象数量不大，多建几张表的成本完全可以接受。

### 3.4 别名映射表：解决"东通道"和"PASS-E"是不是一回事

对应需求重构稿 4.6 节步骤3："将各来源中的编号、名称和别名映射到统一身份，歧义由人工确认"：

```python
class ObjectAlias(Base):
    __tablename__ = "object_aliases"

    id: Mapped[str] = mapped_column(primary_key=True)
    object_type: Mapped[str]
    object_id: Mapped[str]       # 指向真正的对象，如 "PASS-E"
    alias_text: Mapped[str]      # "东通道"、"东侧主要通道"……
    source: Mapped[str]          # 这个别名是人工录入的还是文档抽取的
```

这张表就是验收用例 AC01（"用两个别名上报同一通道，应关联同一对象"）的实现依据。

## 四、服务层：OntologyService 提供哪几个方法

对应需求重构稿 7.2 节的工具接口设计，直接把这几个方法做成 Agent 可调用的工具：

```python
class OntologyService:

    def resolve_objects(self, query_text: str, activity_id: str) -> list[ResolvedObject]:
        """输入一段文字/名称，先查 ObjectAlias 做匹配。
        多个候选时返回歧义列表，绝不擅自选一个——歧义必须交回给上层请求人工确认。"""

    def get_context_snapshot(self, object_ids: list[str]) -> ContextSnapshot:
        """返回对象当前状态、证据时效、关联的任务/方案版本。
        这是 Agent 拿到"现在现场是什么样"的唯一入口。"""

    def trace_impacts(self, object_id: str, changed_field: str) -> ImpactReport:
        """给定一个对象的某个字段变化，查询依赖它的任务、方案、审批。
        三个月冲刺阶段只需要支持"通道→连接区域→依赖该通道的任务"这一条链路，
        不追求通用图遍历——够用就行，不要在这上面过度设计。"""

    def update_object_status(self, object_id: str, field: str, value, evidence: Evidence) -> None:
        """更新状态时，evidence 参数是必填的，不是可选的。
        从函数签名层面就不允许"裸写状态"——这比指望开发者自觉遵守规范更可靠。"""
```

`update_object_status` 强制要求 `evidence` 参数，是把需求重构稿 4.4 节的原则直接刻进代码接口里，而不是写在文档里靠自觉。

## 五、两个容易漏掉的工程细节

**乐观锁（14.3 节要求）**：多个请求可能同时基于同一个旧状态改通道状态，`version` 字段在每次更新时校验并 +1，版本号不匹配就拒绝更新、返回冲突错误。这个不做，两个 Agent 同时处理一个事件时会互相覆盖对方的判断。

**别名解析的歧义必须真的"卡住"，不能静默兜底**：`resolve_objects` 遇到多个候选或零候选时，不要为了让流程走下去就随便选一个或自动新建对象——这正是 AC01 验收用例要卡的行为。宁可让上层报错、请求人工确认，也不要让本体层自己悄悄"猜"。

## 六、四周实施步骤（给成员A）

不要一开始就把需求重构稿 4.2 节列的 16 种对象类型全部建表——那是三到五年的完整愿景。三个月冲刺只需要 `Activity / Zone / Passage / TeamMember / Task` 这 5 种，够撑起"东侧通道故障"这一个场景。

| 周 | 目标 | 对应验收用例 |
|---|---|---|
| 第1周 | 建 `Zone`、`Passage`、`ObjectAlias` 三张表，跑通"用不同别名查到同一条通道" | AC01 |
| 第2周 | 给 `Passage` 加状态/证据分离字段，实现"证据过期不能当已确认用"的校验 | AC02 |
| 第3周 | 建 `PassageConnection` 关系表，实现 `trace_impacts`（只做通道→区域→任务这一条链路） | — |
| 第4周 | 包装 `OntologyService` 三个核心方法为 Agent 工具函数，接给态势研判 Agent 试用 | 对应三个月计划第2月"两个Agent接入端到端链路" |

## 七、要避免的三个坑

1. **不要用一张万能"对象表" + JSON 字段存所有类型**——看起来灵活，实际会让关系查询和状态校验全部失去数据库约束保护，退化成应用层手写校验，容易漏、难维护。
2. **不要把关系存成"外键指向通用object表"**——为每种关系单独建表，虽然多写几张表，但查询效率和约束清晰度都好得多，现在的对象数量级完全负担得起。
3. **不要在 Agent 代码里直接写查询**——全部走 `OntologyService`，否则以后想加校验规则或换存储方案，要满代码库找散落的查询逐个改。
