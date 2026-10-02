# 海淀历史地名知识图谱（HHTO）工程实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于《海淀历史地名知识图谱本体设计规范》(HHTO)，构建一个学术严谨、证据可溯源、支持时空推理与离线可视化的海淀历史地名知识图谱系统。

**Architecture:** 
1. **本体层**：基于 W3C OWL 2 / Turtle (`haidian_ontology.ttl`) 形式化定义四分法（物理空间、建制实体、地名符号、史料书证）及演变事件体系与六级证据分层。
2. **知识层**：从已交付 13 集研究档案、54 项地名清单及前沿史料考订中，全面提取先秦至近现代的实体、书证、演变事件与假说三元组。
3. **推理与查询层**：基于 `rdflib` 与 `networkx` 构建图谱查询与沿革推理引擎，支持时间切片、演变链谱系追踪、证据层级过滤与争议假说比对。
4. **可视化与交付层**：输出离线单文件交互式 D3.js 知识图谱面板（力导向图 + 年代游标滑块 + 证据检视抽屉）。

**Tech Stack:** Python 3.9+, `rdflib 7.6.0`, `networkx`, `pydantic`, D3.js v7 (离线单文件/内嵌), `pytest`.

## Global Constraints
- 路径根目录：永久代码与产物存放于 `/Volumes/macstudio/video-projects/haidian_kg/` 与 `tests/`。
- Python 3.9 兼容性：禁止使用 `X | None`（必须用 `Optional[X]`），禁止使用 `match-case` 语法。
- 坐标空间：地理坐标采用 WGS84 经纬度 `[lon, lat]`。
- 负控制纪律：已被证伪的地名学说（如西三旗源自满洲八旗、高梁桥系宋辽战役桥梁）必须强制标注 `Level 6 (Disproven)`，且断言禁止被推理引擎误推为正史前驱实体。
- 严禁空占位符（No TBD/TODO）：所有代码块与测试用例均为完整可运行代码。

---

## File Structure

```
/Volumes/macstudio/video-projects/haidian_kg/
├── __init__.py
├── ontology/
│   ├── haidian_ontology.ttl         # OWL/Turtle 核心本体形式化定义
│   └── schema.py                    # Pydantic 实体与三元组数据模型
├── extractor.py                     # 全区史料文献与研究长编实体抽取器
├── builder.py                       # RDF 知识图谱构建器（实例化三元组）
├── query.py                         # SPARQL / NetworkX 时空推理与查询引擎
├── data/
│   ├── entities.json                # 结构化历史实体与演变事件原始数据
│   └── haidian_kg.ttl               # 最终全量 RDF 图谱 (Turtle 格式)
├── visualizer/
│   ├── generate_html.py             # 离线 D3.js 交互式面板生成脚本
│   └── index.html                   # 离线单文件力导向图 + 时间轴面板
tests/haidian_kg/
├── test_ontology_schema.py          # 本体定义与 Pydantic 校验测试
├── test_data_extraction.py          # 实体与证据层级抽取测试
├── test_kg_builder.py               # RDF 构建与三元组完整性测试
├── test_query_engine.py             # SPARQL 查询与演变链推理测试
└── test_negative_control.py         # 负控制与证伪断言专项测试
```

---

## Tasks

### Task 1: 本体定义文件与 Pydantic 数据模式 (`schema.py` & `haidian_ontology.ttl`)

**Files:**
- Create: `haidian_kg/ontology/haidian_ontology.ttl`
- Create: `haidian_kg/ontology/schema.py`
- Test: `tests/haidian_kg/test_ontology_schema.py`

**Interfaces:**
- Produces: 
  - `haidian_kg.ontology.schema.ToponymEntity`
  - `haidian_kg.ontology.schema.PhysicalFeatureEntity`
  - `haidian_kg.ontology.schema.AdministrativeUnitEntity`
  - `haidian_kg.ontology.schema.PlaceAttestationEntity`
  - `haidian_kg.ontology.schema.ToponymEventEntity`
  - `haidian_kg.ontology.schema.EvidenceLevel` (Enum: L1..L6)
  - `haidian_kg.ontology.schema.EpistemicStatus` (Enum: VERIFIED, CONTESTED, FOLK_LEGEND, DISPROVEN)

- [ ] **Step 1: 编写测试用例 `tests/haidian_kg/test_ontology_schema.py`**
  验证 OWL 本体能被 rdflib 正常解析，验证 Pydantic 模型能正确约束核心四分法实体与六级证据枚举。

- [ ] **Step 2: 运行测试并确认失败**
  `pytest tests/haidian_kg/test_ontology_schema.py -v` (FAIL: 模块不存在)

- [ ] **Step 3: 编写 `haidian_ontology.ttl` 与 `schema.py`**
  实现完整的 OWL/Turtle 本体定义与强类型 Pydantic 类。

- [ ] **Step 4: 运行测试并验证通过**
  `pytest tests/haidian_kg/test_ontology_schema.py -v` (PASS)

- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成海淀历史地名本体定义与模式规范 (Task 1)"`

---

### Task 2: 全域史料抽取与结构化实体数据集 (`extractor.py` & `entities.json`)

**Files:**
- Create: `haidian_kg/extractor.py`
- Create: `haidian_kg/data/entities.json`
- Test: `tests/haidian_kg/test_data_extraction.py`

**Interfaces:**
- Consumes: `haidian_kg.ontology.schema`
- Produces: 
  - `HaidianCorpusExtractor.extract_all() -> Dict[str, List[BaseModel]]`
  - `entities.json` (覆盖先秦至近现代的 50+ 核心地名、80+ 书证、40+ 演变事件)

- [ ] **Step 1: 编写数据抽取与完整性测试**
  测试要求：覆盖先秦/唐/辽金/元/明/清/近现代全部地层；断言西三旗、六郎庄、中关村、树村、太舟坞等关键实体具备完整的证据评级与演变链。

- [ ] **Step 2: 运行测试确认失败**
  `pytest tests/haidian_kg/test_data_extraction.py -v` (FAIL)

- [ ] **Step 3: 实现 `extractor.py` 并生成 `entities.json`**
  系统整合已交付 13 集研究档案、地名长编、方志书证与考订结论。

- [ ] **Step 4: 运行测试验证通过**
  `pytest tests/haidian_kg/test_data_extraction.py -v` (PASS)

- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成全域六大历史地层实体与书证抽取 (Task 2)"`

---

### Task 3: RDF 知识图谱构建器与全量 Turtle 导出 (`builder.py` & `haidian_kg.ttl`)

**Files:**
- Create: `haidian_kg/builder.py`
- Create: `haidian_kg/data/haidian_kg.ttl`
- Test: `tests/haidian_kg/test_kg_builder.py`

**Interfaces:**
- Consumes: `haidian_kg/data/entities.json`, `haidian_ontology.ttl`
- Produces: `haidian_kg.builder.HaidianKGBuilder.build_graph() -> rdflib.Graph`

- [ ] **Step 1: 编写 RDF 图谱构建测试**
  断言三元组数量 > 800，验证无未绑定命名空间的悬挂 URI，验证所有 Toponym 均有对应的 PhysicalFeature 或 AdministrativeUnit 关联。

- [ ] **Step 2: 运行测试确认失败**
  `pytest tests/haidian_kg/test_kg_builder.py -v` (FAIL)

- [ ] **Step 3: 编写 `builder.py` 并导出 `haidian_kg.ttl`**
  实现标准 RDF/OWL 序列化逻辑，导出全量三元组文件。

- [ ] **Step 4: 运行测试验证通过**
  `pytest tests/haidian_kg/test_kg_builder.py -v` (PASS)

- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 实现 RDF 知识图谱构建器与 Turtle 全量导出 (Task 3)"`

---

### Task 4: 时空推理、演变追溯与证据查询引擎 (`query.py`)

**Files:**
- Create: `haidian_kg/query.py`
- Test: `tests/haidian_kg/test_query_engine.py`

**Interfaces:**
- Consumes: `haidian_kg.data.haidian_kg.ttl`
- Produces:
  - `KGQueryEngine.trace_evolution(toponym_label: str) -> List[EvolutionHop]`
  - `KGQueryEngine.query_by_period(dynasty: str) -> List[ToponymSummary]`
  - `KGQueryEngine.get_attestations(toponym_label: str) -> List[AttestationInfo]`
  - `KGQueryEngine.find_contested_hypotheses() -> List[ContestedCase]`

- [ ] **Step 1: 编写查询与推理引擎测试**
  测试「牛栏庄」能沿着 `euphemism` 与 `folkEtymology` 正确推理至「六郎庄」；测试通过 SPARQL 能准确检出所有 Level 1 考古证据实体。

- [ ] **Step 2: 运行测试确认失败**
  `pytest tests/haidian_kg/test_query_engine.py -v` (FAIL)

- [ ] **Step 3: 实现 `query.py`**
  使用 rdflib SPARQL 查询与 NetworkX 有向无环图（DAG）追踪地名生命周期谱系。

- [ ] **Step 4: 运行测试验证通过**
  `pytest tests/haidian_kg/test_query_engine.py -v` (PASS)

- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 实现 SPARQL 与沿革推理查询引擎 (Task 4)"`

---

### Task 5: 负控制与证伪断言专项测试套件 (`test_negative_control.py`)

**Files:**
- Create: `tests/haidian_kg/test_negative_control.py`

**Interfaces:**
- Consumes: `haidian_kg.query.KGQueryEngine`

- [ ] **Step 1: 编写负控制测试用例**
  - **断言 1 (西三旗)**：查询「西三旗」的正史源流时，必须且只能命中明代军屯小旗（Level 2/3），不得命中满洲八旗；若查询满洲八旗说法，必须返回 `DISPROVEN` 状态与证伪依据。
  - **断言 2 (高梁桥)**：查询 979 年宋辽高梁河之战时，桥梁实体的创建事件必须严格定于 1292 年元代郭守敬建闸，不得提前至宋辽。
  - **断言 3 (中官村)**：中关村的太监义地前身必须有确凿清末民国文献凭证，改名陈垣说必须标注为 `CONTESTED (争议说)` 并附 1913 京西图更早印制反证。

- [ ] **Step 2: 运行测试并保证全绿**
  `pytest tests/haidian_kg/test_negative_control.py -v` (PASS)

- [ ] **Step 3: Git commit**
  `git commit -m "test(kg): 添加历史地名知识图谱负控制与证伪断言测试 (Task 5)"`

---

### Task 6: 离线交互式可视化面板 (`generate_html.py` & `index.html`)

**Files:**
- Create: `haidian_kg/visualizer/generate_html.py`
- Create: `haidian_kg/visualizer/index.html`

**Interfaces:**
- Consumes: `haidian_kg/data/entities.json`
- Produces: 离线独立 HTML 文件（单文件无外部网络依赖，内嵌 D3.js v7 力导向图、时间滑块、实体类型筛选、证据抽屉）。

- [ ] **Step 1: 编写 HTML 生成脚本 `generate_html.py`**
  将图谱节点与边注入单文件 HTML 模板中，提供朝代滑块（先秦-唐-辽金-元-明-清-民国-当代）、节点聚类色彩与点击出证详情。

- [ ] **Step 2: 运行脚本生成 `index.html`**
  `python3 haidian_kg/visualizer/generate_html.py`

- [ ] **Step 3: 验证 HTML 可访问性与离线渲染**
  通过 headless 浏览器或静态检查验证节点数 > 100，边数 > 150，无控制台 JS 语法错误。

- [ ] **Step 4: Git commit**
  `git commit -m "feat(kg): 生成离线交互式 D3.js 知识图谱与时空地层看板 (Task 6)"`

---

### Task 7: 端到端综合验收与交付报告

**Files:**
- Create: `haidian_kg/README.md`
- Create: `docs/qa/2026-10-02-haidian-kg-delivery-report.md`

- [ ] **Step 1: 运行完整测试套件**
  `pytest tests/haidian_kg/ -v` (断言所有测试 100% 通过)

- [ ] **Step 2: 生成最终统计与交付文档**
  统计实体数、三元组数、书证数、事件数，撰写使用手册与方法论综述。

- [ ] **Step 3: Git commit**
  `git commit -m "docs(kg): 交付海淀历史地名知识图谱系统与验收报告 (Task 7)"`
