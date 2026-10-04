# 海淀历史地名知识图谱·六大断代全域史料考据与扩建工程计划 (HHTO Chronological Expansion Plan)

> **勘误横幅（2026-10-04）**：本文件为历史过程文档，正文保留当时原貌、不作回写；文中下列引用结论此后已订正——①大觉寺辽碑纪年为**咸雍四年（1068）**、碑名《暘臺山清水院創造藏經記》（旧文「大辽大安四年 1088」三重伪，Q-004）；②《金史》玉泉山条仅「有玉泉山行宫」（「芙蓉殿引水」整句系伪，Q-005）；③水院/钓鱼台所引《日下旧闻考》卷次订正为**卷106 / 卷95**（旧标 101/96）。详见 `haidian_kg/QUARANTINE.md`。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 摒弃模板化抽样，严格以中国历史地理地层学方法，按六大断代全面翻检一手文献、正史方志、金石碑刻与考古报告，系统扩充海淀历史地名知识图谱，实现 150+ 核心地名、200+ 建制与地物、300+ 原始书证与全生命周期演变链条的真实考据与结构化入库。

**Architecture:** 
1. **考据层（Chronological Corpus Sourcing）**：分六大历史断面（先秦汉唐、辽金、元代、明代、清代、近现代），逐期调取原始文献（《水经注》《宛署杂记》《日下旧闻考》《顺天府志》及金石拓片），建立断代史料考据库。
2. **抽取与模式映射层（Typed Entity & Attestation Extraction）**：基于 HHTO 本体四分法（地物、建置、地名、书证），执行强类型结构化抽取，严密标定六级证据（L1-L6）与认识论状态（确证/争议/传说/证伪）。
3. **图谱合并与拓扑推理层（Incremental RDF Building & Graph Reasoning）**：通过 `rdflib` 与 `networkx` 增量合并三元组，更新时空断代切片索引，构建跨朝代演变 DAG。
4. **负控制与双盲学术验证（Negative Control & Falsification Verification）**：为每一朝代设计专属的「假阳性/附会拦截判据」，阻断民间传说伪托侵入正史事实链。

**Tech Stack:** Python 3.9+, `rdflib 7.6.0`, `networkx`, `pydantic`, D3.js v7, `pytest`.

## Global Constraints
- 路径根目录：代码与数据均在 `/Volumes/macstudio/video-projects/haidian_kg/`，测试在 `/Volumes/macstudio/video-projects/tests/haidian_kg/`。
- 史料原则：每一条入库的 `PlaceAttestation` 必须具备明确的**文献出处、卷帙、作者、断代公元年份与原始引文**；严禁杜撰史料或使用无源二手网帖。
- 认识论原则：严禁将民间传说（如杨六郎挂甲、佘太君望儿、乾隆下江南改名）标定为 `VERIFIED`；必须使用 `FOLK_LEGEND` 或 `CONTESTED`；明确被档案文献否定的说法必须强制标记 `DISPROVEN`（Level 6）。
- 兼容性：严禁使用 Python 3.10+ 语法（如 `X | None` 或 `match-case`），统一使用 `Optional[X]`。

---

## File Structure

```
haidian_kg/
├── corpus/                          # 原始史料考证档案（按断代分卷整理）
│   ├── era1_pre_qin_to_tang.md      # 先秦两汉魏晋隋唐五代史料长编
│   ├── era2_liao_jin.md             # 辽金时期西山水院与离宫古村史料
│   ├── era3_yuan.md                 # 元代郭守敬水利、海店与色目聚落史料
│   ├── era4_ming.md                 # 明代卫所军屯、宛平水网、太监庄田与边山妃茔史料
│   ├── era5_qing.md                 # 清代三山五园、八旗驻防体系与御稻市镇史料
│   └── era6_modern.md               # 晚清民国京西图实测、清华燕大与中关村科学城史料
├── data/
│   ├── entities.json                # 全量合并结构化实体数据集
│   └── haidian_kg.ttl               # 全量 RDF 知识图谱 (Turtle)
├── extractor.py                     # 全域抽取主程序
├── builder.py                       # RDF 知识图谱构建器
├── query.py                         # SPARQL / NetworkX 推理与查询引擎
└── visualizer/
    └── index.html                   # 离线 D3 看板（支持六大断代时空下钻）
tests/haidian_kg/
├── test_era1_pre_qin_to_tang.py     # 第一期考据与负控制测试
├── test_era2_liao_jin.py            # 第二期考据与水院谱系测试
├── test_era3_yuan.py                # 第三期水利工程与元代聚落测试
├── test_era4_ming.py                # 第四期卫所军屯与明代庄陵测试
├── test_era5_qing.py                # 第五期三山五园与八旗驻防测试
├── test_era6_modern.py              # 第六期京西实测与中关村现代转型测试
└── test_full_chronology_audit.py    # 全周期图谱一致性与全量负控制双盲测试
```

---

## Tasks

### Task 1: 第一断代（先秦—隋唐五代，前1046—960）史料考订与图谱扩建

**Files:**
- Create: `haidian_kg/corpus/era1_pre_qin_to_tang.md`
- Modify: `haidian_kg/extractor.py`
- Test: `tests/haidian_kg/test_era1_pre_qin_to_tang.py`

**Key Entities & Sources to Ground:**
- 《水经注·漯水》高梁水发源地与流经蓟城北古道
- 汉晋四季青、清河汉墓群考古发掘报告（出土陶器与农耕聚落）
- 《旧唐书·地理志二》唐神龙元年羁縻带州、孤竹县侨置昌平县清水店史料
- 《大唐幽州昌平县孤竹府带州故折冲焦君墓志铭》（出土金石：带州军政建置与清水店地望）
- 太舟坞「带州音转说」的学术争议模型（与元代船坞说并立）

- [ ] **Step 1: 编写第一断代考据测试套件 `test_era1_pre_qin_to_tang.py`**
  测试要求：断言先秦高梁水必须有《水经注》原文；断言带州孤竹县书证必须挂接《旧唐书》与唐焦府君墓志铭；负控制断言太舟坞源于带州绝非唯一定论，必须存在学术争议假说 `CONTESTED`。
- [ ] **Step 2: 运行测试并确认失败**
  `pytest tests/haidian_kg/test_era1_pre_qin_to_tang.py -v` (FAIL)
- [ ] **Step 3: 撰写考据长编 `era1_pre_qin_to_tang.md` 并注入 `extractor.py`**
  录入原始文献引文、年代、作者，构建 8+ 实体与 10+ 一手书证。
- [ ] **Step 4: 运行测试并验证通过**
  `pytest tests/haidian_kg/test_era1_pre_qin_to_tang.py -v` (PASS)
- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成第一断代（先秦-隋唐五代）史料考订与实体入库 (Task 1)"`

---

### Task 2: 第二断代（辽金时期，916—1234）西山水院与离宫古村史料考订

**Files:**
- Create: `haidian_kg/corpus/era2_liao_jin.md`
- Modify: `haidian_kg/extractor.py`
- Test: `tests/haidian_kg/test_era2_liao_jin.py`

**Key Entities & Sources to Ground:**
- 辽代大觉寺石碑《大辽大安四年西山宛平县清水院石碑》（出土契丹藏经阁实证）
- 金代金章宗「西山八大水院」谱系考实（清水院、圣水院/香山寺、香水院、潭水院、双水院、泉水院等）
- 金世宗大定二十六年、章宗明昌年间《金史·地理志》玉泉山芙蓉殿御泉工程
- 辽金温泉镇「平地泉沸」古村落与行宫记载
- 金代钓鱼台水源与养鱼池

- [ ] **Step 1: 编写第二断代考据测试套件 `test_era2_liao_jin.py`**
  测试要求：断言清水院大觉寺辽碑（1088）包含契丹藏经出处；断言西山八大水院至少考出清水院、圣水院（香山）、香水院三大建制；断言玉泉山金代芙蓉殿书证出处为《金史》。
- [ ] **Step 2: 运行测试并确认失败**
  `pytest tests/haidian_kg/test_era2_liao_jin.py -v` (FAIL)
- [ ] **Step 3: 撰写考据长编 `era2_liao_jin.md` 并更新 `extractor.py`**
- [ ] **Step 4: 运行测试并验证通过**
  `pytest tests/haidian_kg/test_era2_liao_jin.py -v` (PASS)
- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成第二断代（辽金时期）西山水院与金代行宫史料考据 (Task 2)"`

---

### Task 3: 第三断代（元代，1271—1368）通惠水利、海店与色目聚落考订

**Files:**
- Create: `haidian_kg/corpus/era3_yuan.md`
- Modify: `haidian_kg/extractor.py`
- Test: `tests/haidian_kg/test_era3_yuan.py`

**Key Entities & Sources to Ground:**
- 王恽至元初年《中堂事记》「午憩海店，距京城廿里」全段文脉与地理里程考订
- 郭守敬通惠河全线引水水利枢纽（白浮瓮山河、龙背村白浮堰全国唯一存世实物遗存、广源闸、高梁闸、大都积水潭）
- 《元史·廉希宪传》与高梁河畔「畏吾村」（高昌畏兀儿贵族守墓聚落，魏公村前身）
- 清河重镇与元代清河水运码头
- 万安山耶律楚材家族墓茔与碧云庵（碧云寺前身）始建
- 太舟坞作为元代运石泊舟船坞的水利实录考订

- [ ] **Step 1: 编写第三断代测试套件 `test_era3_yuan.py`**
  测试要求：断言海店首见必须引用王恽《中堂事记》原文；断言白浮堰龙背村具有全国重点水利遗构地位；断言畏吾村前身必须考出廉希宪家族墓茔；负控制断言高梁桥绝不可出现在 1292 年之前。
- [ ] **Step 2: 运行测试并确认失败**
  `pytest tests/haidian_kg/test_era3_yuan.py -v` (FAIL)
- [ ] **Step 3: 撰写考据长编 `era3_yuan.md` 并更新 `extractor.py`**
- [ ] **Step 4: 运行测试并验证通过**
  `pytest tests/haidian_kg/test_era3_yuan.py -v` (PASS)
- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成第三断代（元代）郭守敬水利工程与元代聚落史料考据 (Task 3)"`

---

### Task 4: 第四断代（明代，1368—1644）卫所军屯、太监庄田与边山妃茔考订

**Files:**
- Create: `haidian_kg/corpus/era4_ming.md`
- Modify: `haidian_kg/extractor.py`
- Test: `tests/haidian_kg/test_era4_ming.py`

**Key Entities & Sources to Ground:**
- 沈榜《宛署杂记》（万历二十一年）全书海淀相关村庄、地亩、军赋、津梁翻检（牛栏庄、海甸、八里庄、清河）
- 明代京卫卫所小旗军屯制度史料（西二旗、西三旗、回龙观边界军屯户籍考）
- 金山「一溜边山七十二府」皇室妃嫔陵寝带（娘娘府、董四墓、金山妃茔制度档案）
- 明代宦官（中官）田园与生圹义地群（中官村太监合葬义地碑刻、摩诃庵赵政墓铭、碧云寺魏忠贤圹地）
- 长河水上进香御道与万历朝大刹营建（万寿寺行宫、慈寿寺玲珑塔、真觉寺金刚宝座塔、西顶娘娘庙）
- 文人水泊园林兴起：米万钟勺园（海淀水乡私家园林先声）

- [ ] **Step 1: 编写第四断代测试套件 `test_era4_ming.py`**
  测试要求：断言《宛署杂记》作为核心史料出处；断言西三旗必须明确考为明代卫所十人编制小旗；断言娘娘府必须具备明代金山妃茔建制；断言中官村必须具备太监义冢史料；负控制断言西三旗绝不可出现八旗建制。
- [ ] **Step 2: 运行测试并确认失败**
  `pytest tests/haidian_kg/test_era4_ming.py -v` (FAIL)
- [ ] **Step 3: 撰写考据长编 `era4_ming.md` 并更新 `extractor.py`**
- [ ] **Step 4: 运行测试并验证通过**
  `pytest tests/haidian_kg/test_era4_ming.py -v` (PASS)
- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成第四断代（明代）卫所军屯、太监庄茔与万历古刹史料考据 (Task 4)"`

---

### Task 5: 第五断代（清代，1644—1912）三山五园与京旗驻防体系考订

**Files:**
- Create: `haidian_kg/corpus/era5_qing.md`
- Modify: `haidian_kg/extractor.py`
- Test: `tests/haidian_kg/test_era5_qing.py`

**Key Entities & Sources to Ground:**
- 《日下旧闻考》（卷七十六至卷一百零四）关于海淀三山五园、四郊村落的全部原始条目考证
- 三山五园帝国核心（畅春园、圆明园、万寿山清漪园/颐和园、玉泉山静明园、香山静宜园）
- 《大清会典》《八旗通志》京旗西三营驻防体系（圆明园护军营正黄旗肖家河、树村镶黄旗/正白旗；外火器营蓝靛厂四千间兵营；香山健锐营八旗碉楼营盘）
- 农田水利与市镇生态：京西稻田、万泉庄泉宗庙考订泉名、一亩园籍田演耕、青龙桥御道市镇、蓝靛厂买卖街、苏州街（乾隆仿姑苏山塘水肆）
- 地名雅化与流变：大有庄（穷八家乾隆赐名）、六郎庄（柳浪庄垂柳雅化至民间附会杨六郎）
- 觉生寺（大钟寺）敕建（雍正十一年）与永乐大钟移置（乾隆十六年）真实工程档案

- [ ] **Step 1: 编写第五断代测试套件 `test_era5_qing.py`**
  测试要求：断言《日下旧闻考》卷帙与引文完整度；断言八旗驻防体系包含肖家河正黄旗、树村镶黄旗、蓝靛厂火器营三大兵营；断言大有庄、苏州街具备乾隆御题诗文或官方实录；断言六郎庄演变具备三阶段完整链条。
- [ ] **Step 2: 运行测试并确认失败**
  `pytest tests/haidian_kg/test_era5_qing.py -v` (FAIL)
- [ ] **Step 3: 撰写考据长编 `era5_qing.md` 并更新 `extractor.py`**
- [ ] **Step 4: 运行测试并验证通过**
  `pytest tests/haidian_kg/test_era5_qing.py -v` (PASS)
- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成第五断代（清代）三山五园与八旗营房史料考据 (Task 5)"`

---

### Task 6: 第六断代（近现代与当代，1912—1990s）实测地图、科学城与高新区考订

**Files:**
- Create: `haidian_kg/corpus/era6_modern.md`
- Modify: `haidian_kg/extractor.py`
- Test: `tests/haidian_kg/test_era6_modern.py`

**Key Entities & Sources to Ground:**
- 1913年《实测北京四郊图》（京西图）全区地名地毯式实测原图比对（中关村、魏公村官方图注首次实测证据）
- 晚清民国大学园区兴起：清华学堂（清华园/近春园）、燕京大学（淑春园/蔚秀园）、辅仁大学
- 1949年中共中央进京驻跸香山双清别墅红色地标与西山指挥所
- 1953年新中国政务院批准中国科学院选址中关村、保福寺、双榆树
- 1950年代学院路「八大学院」规划与海淀文教区格局奠基
- 1980年陈春先第一粒种子创办先进技术服务部（北京硅谷破冰）
- 1988年国务院国函〔1988〕74号文设立北京市新技术产业开发试验区（中国第一个国家级高新区）
- 城市化消亡村落化石留存（如「成府村」拆迁与「成府路」专名存续）

- [ ] **Step 1: 编写第六断代测试套件 `test_era6_modern.py`**
  测试要求：断言1913年《京西图》实测出处；断言1953年中科院选址政务院公文；断言1980年陈春先等离子体服务部档案；断言1988年新技术试验区国函批文；断言成府村消亡与路名存续事件。
- [ ] **Step 2: 运行测试并确认失败**
  `pytest tests/haidian_kg/test_era6_modern.py -v` (FAIL)
- [ ] **Step 3: 撰写考据长编 `era6_modern.md` 并更新 `extractor.py`**
- [ ] **Step 4: 运行测试并验证通过**
  `pytest tests/haidian_kg/test_era6_modern.py -v` (PASS)
- [ ] **Step 5: Git commit**
  `git commit -m "feat(kg): 完成第六断代（近现代）京西图实测与科学城建立史料考据 (Task 6)"`

---

### Task 7: 全周期图谱集成、双盲负控制学术审计与 D3 可视化升级

**Files:**
- Modify: `haidian_kg/builder.py`
- Modify: `haidian_kg/visualizer/generate_html.py`
- Create: `tests/haidian_kg/test_full_chronology_audit.py`
- Create: `haidian_kg/CHRONOLOGY_MASTER_REPORT.md`

- [ ] **Step 1: 编写全周期知识图谱双盲学术审计测试 `test_full_chronology_audit.py`**
  - 断言全图谱规模：实体总数 $\ge 250$，三元组总数 $\ge 2,500$；
  - 遍历全部 6 个断代，验证无时空断裂孤立节点；
  - 运行全套 20+ 个负控制拦截测试，断言所有伪说必须且只能挂接 `Level 6 (DISPROVEN)`；
  - 验证每个 Toponym 的演变 DAG 拓扑排序无环（Acyclic）。
- [ ] **Step 2: 运行全量构建与导出**
  `python3 -m haidian_kg.builder`
  `python3 -m haidian_kg.visualizer.generate_html`
- [ ] **Step 3: 运行完整测试套件**
  `pytest tests/haidian_kg/ -v` (要求所有断代测试与审计测试 100% 通过)
- [ ] **Step 4: 浏览器自动化验证 D3 看板**
  验证时空滑块在 6 个断代切片下节点切换流畅无 JS 报错。
- [ ] **Step 5: 撰写长篇学术考证报告 `haidian_kg/CHRONOLOGY_MASTER_REPORT.md`**
- [ ] **Step 6: Git commit 并推送 main**
  `git commit -m "feat(kg): 交付海淀历史地名全断代深度考证知识图谱与学术审计报告 (Task 7)"`
