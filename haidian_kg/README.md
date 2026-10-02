# 北京历史时空知识图谱 · 海淀第一分卷 (BHKG / HHTO)

基于数字人文、历史地理学与 W3C 语义网标准构建的海淀历史地名时空知识图谱。
宏观母体为 **北京历史时空知识图谱（BHKG）**，海淀为第一分卷；目标是让词条
数据自然生长（地名⇄古书闭包扩展），而非逐条手工堆建。

关联文档（本文只写结论，论证过程见原文）：
- 本体规范：`docs/superpowers/specs/2026-10-02-haidian-kg-ontology-redesign.md`
- 闭包设计：`docs/superpowers/specs/2026-10-02-closure-expansion-design.md`（含外审整改）
- 断代总报告：`haidian_kg/CHRONOLOGY_MASTER_REPORT.md`（Era 0–9 逐层硬证据）
- 调研存档：`.superpowers/sdd/`（tokenizer-research / gazetteer-survey / tgaz-api-findings）

---

## 1. 本体方法论

1. **概念核心四分法**：`PhysicalFeature`（物理地物）/ `AdministrativeUnit`（建置制度）/
   `Toponym`（地名称号）/ `PlaceAttestation`（书证用例）——字符串名不承担实体身份。
2. **事件驱动的地名生命周期**：`CreationEvent`、`ImperialNamingEvent`、`PhoneticShiftEvent`、
   `EuphemisticRenamingEvent`、`FolkAppropriationEvent`、`AdministrativeShiftEvent`、
   `SpatialExtinctionEvent` 七大演变事件。
3. **六级证据分层（内嵌负控制）**：L1 考古硬证据 → L2 一手官刻金石 → L3 正史方志 →
   L4 近代学界考订 → L5 民间口碑（`FOLK_LEGEND`）→ L6 明确证伪伪说（`DISPROVEN`，
   如「西三旗源自满洲八旗说」强制保留为负控制断言）。
4. **十大历史断代地层（Era 0–9，严格互斥无缝）**：史前 → 先秦 → 秦汉六朝 → 隋唐五代 →
   辽金 → 元 → 明 → 清 → 民国 → 当代；逐层考据档案见 `haidian_kg/corpus/era*.md`。

## 2. 词条入库进度

| 状态 | 数量 | 词条（calibration 模块） |
|---|---|---|
| 已入库 | 9/13 | gaoliang（高梁河）、yuanmingyuan（圆明三园）、banners（八旗营房）、settlements（聚落）、dazhongsi（大钟寺）、bridges（E8 高梁桥 + E2 安河桥，双系统与时空冲突判据） |
| 并发入库中 | 2 | suburbs（近郊聚落）、urban（城区地名） |
| 待启动 | 0 | — |

配套三层登记已就绪：人物（people）、书目（bibliography，一书一条 + 作者 + 卷次）、
数字资源（digital_resources，含可靠性说明）。新书进闭包前必须先入书目表；
一亩园/蓝靛厂/苏州街/中关村所涉七书五作者已预置。

## 3. 九维 QA 闸门（qa_gate.py）

入库唯一通道：`QAGate(name, kb, adversarial=...).run()`，`blocking` 非空即不得入库。
每一维都来自一次真实翻车；G7 负控制防「闸门恒真」。

| 闸门 | 防的事故 |
|---|---|
| G1 引文可溯源 | 《水经注》卷十三/卷十四被拼成一句原典 |
| G2 状态有证据 | 形制/材质断言没有出处；身份断言引用不存在的引文 |
| G3 实体无越权属性 | geometry/material/function 挂到 PersistentEntity 上 |
| G4 存疑必须标注 | 推测被当史实；存疑身份未列争议双方；证伪无反驳证据 |
| G5 口径分离 | 雍正二年 1250 间 与 乾隆十二年增建后 1550 楹 被混说 |
| G6 繁简异体 | 消亡/争议断言漏检繁体字形（「不復存在」） |
| G7 假通过可检出 | 注入已知错误断言必须被判 BLOCK/UNTESTABLE，判 PASS 即闸门恒真 |
| G8 跨集不回归 | 改一个词条破坏其它词条（名称重叠指向不同对象） |
| G9 文献实体完整 | 一书一条 HistoricalSource；数字资源必须有可靠性说明与合法 URL |

级别语义：`fail` 阻塞；`warn` 不阻塞；`skip` = 判据未执行，**不算通过**。

## 4. 闭包引擎 v3（expansion.py，miner v3 / rule-profile rp-v3）

人工门控的增量图扩展：循环由人工 admission 事件推进，引擎只做每轮「发现与登记」，
**禁止 `while graph_changed` 式自动迭代**。

**身份三层（spec §2.1）**——字符串名不承担实体身份：

```
ToponymOccurrence          文本事实层（机器可自动产生）
 → CandidatePlaceHypothesis 实体假说层（保守聚类：每 normalized_form 一假说）
 → CanonicalPlaceEntity     正式词条（只有人工九维闸门能产生，引擎永不写入）
```

- **SourceVisitKey 六元组去重**（书, 版本, 篇卷, miner_version, rule_profile_version,
  kb_id）：先查后加再挖掘；版本化保证挖掘器升级不锁死旧篇卷；kb_id 防 M5
  （两词条共引同卷不同切片时，第二个 KB 的独有引文不是环，是必须保留的书证）。
- **置信分级**：high（双证）/ mid（单证）/ low；机器观察记录 ≠ 事实，
  observation 层可自动持久化，fact 层只经闸门。
- **ToponymMiner 四法混合**：A 线索词锚点（為/曰/坐落…）+ B 短语匹配 +
  C 方位后缀剥离（樹村西邊→樹村）+ D 置信分级；词表全部繁简双字形。
  实测 15 候选/8 噪声 → 11 候选/0 噪声（仅 smoke，样本小且参与过规则迭代，
  不得当 validation 引用）。FullTextMiner 接口预留（转录本≠校勘本，edition_id 必须区分）。

## 5. AuthorityResolver 多源外部裁决（authority_resolver.py）

不再以单一 TGAZ 为绝对裁决源，升级为多源异构联邦：

| Provider | 角色 / 粒度 | 许可证 | 纪律 |
|---|---|---|---|
| TGAZ (复旦/CHGIS) | 官方政区与村镇基准（1820/1911 年层） | CC BY-NC 4.0 | REST API 已验证（`GET /tgaz/placename?fmt=json&n=<名>`，前缀 LIKE，繁简均收）；**未命中不否决**（小村落常未收录） |
| DILA (法鼓文理学院) | 异源微观聚落与寺庙山泉 | CC BY-SA 3.0 | 允许建立本地离线镜像索引（工程风险最低） |
| CCTS_MHPNAME | 读史方舆纪要 61,685 条明代县级以下地名（村庄店寨桥闸铺） | 非开放 | **REFERENCE_ONLY_UNLESS_LICENSED**：仅匹配留证与 URI 记录，绝不全量复制入公开库 |
| MCGD (Aix-Marseille) | 近代外文转写与异名消歧（47.3 万条中西文映射） | Zenodo Open（条款待核） | CSV 批量下载离线检索 |

外部网络波动不阻塞闭包流水线；所有外部查询在 machine_observation 层带版本缓存。

### 5.1 引文本地化纪律（2026-10-02 用户指令，永续）

**凡引用的古文原文，必须在仓库内保有本地副本；在线源只作检索与裁决，不作运行时依赖。**

1. **书证层**：KB 每条 `verbatim_quote` 本身就在库里（已合规）；凡 research/registry 引用的古文，`research.md` 内必须存原文，不得只留「见某 URL」。
2. **语料层**：整书/整卷接入（如《日下旧闻考》卷 76-104 原文）必须**先落盘再挖矿**——存 `haidian_kg/corpus/<书名>/`，带 manifest（edition_id/卷次/来源 URL/抓取日期/text_sha1），FullTextMiner **只读本地**，禁止运行时抓维基文库。
3. **裁决层**：TGAZ/DILA/CCVG/MCGD 查询结果按 machine_observation 版本缓存（已实现）；CCVG 原始 CSV/KMZ 已本地留存（gitignored）。
4. **已合规项**：holdout_v1.jsonl（text+text_sha1 本地快照）、corpus/era*.md、KB verbatim_quote、CCVG 索引。
5. **理由**：在线文本可被修订/下线，引文必须可离线回查到与入库时逐字节一致（sha1）；同本古籍的挖掘以本地快照为唯一底本，防止底本漂移导致书证不可复现。

## 6. 分词/NER 调研决策：不上

结论（2026-10-02，证据链 `.superpowers/sdd/tokenizer-research.md`）：现代分词器
文言适配无公开量化证据；古籍 NER（SikuBERT/GujiBERT）F1 83–86.5% 但评测类不含
LOC，历史地名 LOC 无公开 benchmark。四环节逐一否决：边界切分（白名单查表更便宜）/
新词发现（互信息 n-gram 自算即可）/ NER 直出（OOD + 重依赖 + 自标语料）/
同名消歧（用 TGAZ gazetteer 而非分词）。

**重新评估触发条件（任一满足）**：① FullTextMiner 噪声率 >20% 且人工过滤 >每集 1 小时；
② 目标文本变为无标点原刻本；③ 出现 LOC benchmark（F1≥85%）。
届时优先 TGAZ/CHGIS gazetteer 消歧，仍非分词器。

## 7. 工程目录结构

```
haidian_kg/
├── ontology/                  # 本体与强类型规范
│   ├── haidian_ontology.ttl   #   W3C OWL 2 / Turtle 核心领域本体
│   ├── schema.py              #   Pydantic 实体规范
│   ├── epistemic.py           #   书证/事实/采信与认识论状态（L1-L6）
│   ├── spatiotemporal.py / temporal.py      # 时空实体与历时状态层
│   └── video_contracts.py     # 视频管线契约（Storyboard/VisualConstraints/审计）
├── extractor.py               # 挖掘器 v2：混合策略 + 置信分级 + 方位剥离/后缀扫描
├── expansion.py               # 闭包扩展引擎 v3（身份三层 / VisitKey / 只发现不入库）
├── authority_resolver.py      # 多源外部权威裁决（TGAZ+DILA+CCTS_MHPNAME+MCGD）
├── qa_gate.py                 # 九维词条入库闸门（fail 阻塞 / 负控制防恒真）
├── calibration/               # 已入库词条（gaoliang/yuanmingyuan/banners/settlements/
│                              #   dazhongsi/bridges + people/bibliography/digital_resources）
├── production_exports.py      # export_storyboard / export_visual_constraints → 视频管线
├── builder.py / query.py      # RDF 构建序列化；SPARQL + NetworkX 演变推理
├── corpus/era*.md             # Era 0–9 逐断代考据档案
├── data/                      # entities.json（224 实体）+ haidian_kg.ttl（1,581 三元组）
├── CHRONOLOGY_MASTER_REPORT.md
└── visualizer/                # 离线 D3 力导向图 + Era 时间轴游标看板
```

测试：`tests/haidian_kg/` 24 个文件（闸门/词条/闭包/本体/负控制/断代审计）。

## 8. Python 使用范例

```python
from haidian_kg.query import KGQueryEngine

engine = KGQueryEngine()
lineage = engine.trace_evolution("六郎庄")
# ['牛栏庄', '柳浪庄', '六郎庄']（明代放牧 → 清代雅化 → 民间附会杨家将）
engine.find_disproven_myths()      # 负控制检视：DISPROVEN 伪说清单
engine.get_attestations("西三旗")   # 证据链：VERIFIED 与 DISPROVEN 并列呈现

# 词条入库闸门（未入库词条的最后一步）
from haidian_kg.qa_gate import QAGate
report = QAGate("bridges", kb, adversarial=(bad_claim, why)).run()
assert report.blocking == [], report.render()

# 闭包扩展（只发现，不入库）
from haidian_kg.expansion import ClosureExpander
rep = ClosureExpander(seed_kbs=[kb]).expand()
print(rep.render())                # 候选清单 + 重访篇卷计数，人工 triage 后走词条路径
```

## 9. 已知限制（spec §四，诚实边界）

1. **当前实现是单层扩展，不是完整闭包**：循环由人工 admission 驱动。
2. **正则/词表挖掘有天花板**：停用词永远追不上噪声；引擎输出定位是
   「发现清单」而非「事实清单」。
3. **lexicalized 方位词误伤面**：名称本身含「东/西」的地名（如「山东」）
   是后缀剥离规则的已知误伤对象，须负控制覆盖。
4. **候选爆炸**：《日下旧闻考》《八旗通志》类高地名密度文献单篇卷可带出
   数十至数百 occurrence；已用状态机 + budget + best-first 应对。
5. **转录质量**：OCR 错字/异体/断行/串行在 FullTextMiner 上线后会超过正则
   噪声本身；edition_id 区分 + 文本污染控制覆盖。
6. **source-network bias**：闭包天然偏向高连接度官书，视角单向膨胀；
   候选优先级必须保留「文献类型多样性」权重。
7. **holdout benchmark 未建**：冻结分层语料（朝代×文献类型×繁简×地名类型）
   与 mention/high-confidence precision 报告尚待落地。

## 10. 离线交互看板

浏览器直接打开 `haidian_kg/visualizer/index.html`（内嵌本地 D3 v7，无网络依赖）：
滚轮缩放/拖拽/平移；底部时间轴游标切换 Era 0–9 地层；搜索高亮与链路定位；
点击节点在抽屉展示原始引文、断代出处与证据等级徽章，DISPROVEN 伪说红色警示。
