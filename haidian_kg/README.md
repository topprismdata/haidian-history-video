# 海淀历史地名知识图谱系统 (Haidian Historical Toponym Ontology, HHTO)

基于数字人文、历史地理学与 W3C 语义网标准构建的北京市海淀区历史地名时空知识图谱系统。

## 1. 核心方法论与本体设计

本项目严格遵循《海淀历史地名知识图谱本体设计规范》（HHTO）：
1. **概念核心四分法（The Quadruple Separation）**：
   - `PhysicalFeature`（物理空间地物，如高梁河古道、万泉河湿地、瓮山）
   - `AdministrativeUnit`（建置制度实体，如宛平县、圆明园八旗护军营正黄旗营房、蓝靛厂外火器营、中关村高新区）
   - `Toponym`（地名称号实体，如海店/海甸/海淀；牛栏庄/柳浪庄/六郎庄）
   - `PlaceAttestation`（史料书证用例实体，具体文献在特定断代的用例实录）
2. **事件驱动的地名生命周期模型**：
   - 建立 `CreationEvent`、`ImperialNamingEvent`、`PhoneticShiftEvent`、`EuphemisticRenamingEvent`、`FolkAppropriationEvent`、`AdministrativeShiftEvent`、`SpatialExtinctionEvent` 七大演变事件体系。
3. **认识论与六级证据分层（内嵌负控制）**：
   - `Level 1 (考古硬证据)`：如安河桥下出土明代碳十四定年木桩 BA10291、白浮堰元代引水古堰
   - `Level 2 (一手官刻金石)`：如《中堂事记》元代海店记录、天启六年大钟铭文、乾隆御制诗碑
   - `Level 3 (正史方志纪实)`：如《元史》《日下旧闻考》《光绪顺天府志》
   - `Level 4 (近代学界考订)`：如侯仁之水文考证、红学界白家疃考证
   - `Level 5 (民间口碑传说)`：如杨六郎挂甲传说（严格标记为 `FOLK_LEGEND`）
   - `Level 6 (明确证伪伪说)`：如西三旗源自满洲八旗说、高梁桥系宋辽战役桥说（强制标记为 `DISPROVEN` 负控制断言）

---

## 2. 工程目录结构

```
haidian_kg/
├── __init__.py
├── ontology/
│   ├── __init__.py
│   ├── haidian_ontology.ttl    # W3C OWL 2/Turtle 核心领域本体
│   └── schema.py               # Pydantic 强类型实体数据规范
├── extractor.py                # 历史档案与方志全域知识抽取器
├── builder.py                  # RDF 知识图谱构建与 Turtle 序列化器
├── query.py                    # SPARQL 与 NetworkX 演变推理引擎
├── data/
│   ├── entities.json           # 结构化实体原始数据集 (170 节点)
│   └── haidian_kg.ttl          # 全量 RDF 知识图谱 (1283 三元组)
└── visualizer/
    ├── d3.v7.min.js            # 本地离线 D3.js v7 库
    ├── generate_html.py        # 可视化看板生成脚本
    └── index.html              # 离线交互式力导向图 + 时间轴游标看板
```

---

## 3. Python 核心使用范例

### 3.1 地名演变全生命周期追踪
```python
from haidian_kg.query import KGQueryEngine

engine = KGQueryEngine()

# 追踪六郎庄的千年演变脉络
lineage = engine.trace_evolution("六郎庄")
print([hop["label"] for hop in lineage])
# 输出: ['牛栏庄', '柳浪庄', '六郎庄']
# (牛栏庄[明代放牧] -> 柳浪庄[清代文人雅化] -> 六郎庄[民间附会杨家将])
```

### 3.2 证据链溯源与负控制检视
```python
# 获取西三旗的全部书证与真伪状态
atts = engine.get_attestations("西三旗")
for a in atts:
    print(f"[{a['epistemic_status']}] {a['attested_name']}: {a['quote']}")
# 输出:
# [VERIFIED] 西三旗: 宛平北乡有西三旗、西二旗，相传明代卫所小旗分屯之地
# [DISPROVEN] 西三旗源自满洲八旗三旗说: 俗传西三旗为清代正黄、正白、正蓝上三旗驻军之地
```

---

## 4. 离线交互看板使用

在浏览器中直接打开 `haidian_kg/visualizer/index.html`：
- 支持鼠标滚轮缩放、节点拖拽、图谱平移；
- 底部时间轴滑块可切换 9 个历史地层（先秦、唐、辽金、元、明、清初、清盛、民国、当代）；
- 顶部搜索框支持实时地名高亮与链路定位；
- 点击任意节点在右侧抽屉展示原始引文、断代出处与证据层级徽章。
