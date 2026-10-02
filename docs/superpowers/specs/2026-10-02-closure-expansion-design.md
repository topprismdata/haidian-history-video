# 地名⇄古书闭包扩展方法 · 设计规范
## 2026-10-02-closure-expansion-design.md

> 状态：v3（已吸收 GPT 外审 + architect 内审，CONDITIONAL GO → 修正后执行）
> 提出：用户（2026-10-02）「初始地名→引用古书→古书里又有地名→循环」
> 目标：北京全域词条（海淀为第一分卷）不可能全手工建，必须靠数据自然生长。
>
> **版本履历**
> v1：初稿（三层队列 + 提示词挖掘 + 只发现不入库）。
> v2：实现先行验证——挖掘器升级混合策略（提示词+通名后缀+置信分级+方位剥离），
> 真实语料 15 候选/8 噪声 → 11 候选/0 噪声；登记 TGAZ/CHGIS 词库（API 端点 404 待核验）。
> v3：GPT 外审裁决 CONDITIONAL GO，三条 P0 落地——
> 身份模型三层拆分（P0-1）、验证体系重写为可证伪控制（P0-2）、
> SourceVisitKey 版本化与防环执行（P0-3）；
> P1 落地——状态机与优先级、machine_observation 分层、外部服务韧性、术语修正。

---

## 0. 术语修正（v3，回应外审「闭包」误导）

本系统**不是**自动跑到 fixpoint 的 closure loop。它是
**人工 admission 事件驱动的增量图扩展**（human-gated incremental expansion）：

```
entry admitted（人工）
  → 其引用篇卷进入 frontier
  → 篇卷被挖掘，产出 mention（机器）
  → mention 聚类为 candidate hypothesis（机器+人工）
  → candidate 经研究、过闸门，成为新 entry（人工）
  → 新 entry 的篇卷进入下一轮 frontier
```

「循环」由人工 admission 事件推进；引擎做每轮的发现与登记。
禁止实现 `while graph_changed: ...` 式自动迭代。

---

## 一、问题定义

海淀系列 E1-E11 只覆盖十几个地名。北京历史地名数以千计，每个词条的
人工成本（research→考据→三轮自审→GPT审核→闸门）极高。
但词条之间天然互联：**每条引文都是一部书的切片，每部书里都埋着
我们还没建的地名**。

例：八旗营房词条引《八旗通志》卷116「鑲黄旗營房坐落樹村西邊，
正白旗營房坐落樹村東邊，正黄旗營房坐落蕭家河，正红旗營房坐落安河橋」——
一句话里就有萧家河（E1 主题）、安河桥（E2 主题）、水礳（未建档）。

**方法**：把「词条⇄书」当成二部图，做人工门控的增量扩展。

---

## 二、架构

### 2.1 身份模型三层拆分（v3 P0-1，回应外审「cand.name 不能承担实体身份」）

**不要用字符串名称同时承担发现、假说、实体三个角色。**同名异地、
异名同地、地名随时代迁移、同字在不同语境是地点/机构/普通名词——
这四种情况在历史地名里都是常态。

```
ToponymOccurrence          文本事实层（机器可自动产生）
  「某文献某位置出现了形状为X的字串，上下文像地名」
        ↓ 聚类（同源归并）
CandidatePlaceHypothesis   实体假说层（机器聚类 + 人工triage）
  「这批 occurrence 可能指向同一个历史地点」
        ↓ 研究 + 九维闸门（人工裁决）
CanonicalPlaceEntity       正式知识库对象（只有人工闸门能产生）
```

ToponymOccurrence 必备字段：
`occurrence_id / surface_form / normalized_form / source_id /
edition_id / division_id / text_span / evidence_fact_id /
extractor_method / extractor_version / confidence`

### 2.2 队列与去重键（v3 P0-3，回应外审「seen_sources 写了但没执行」）

```
frontier_sources   已建档词条引用过的篇卷（待挖）
observations       机器观察记录（ToponymOccurrence 持久化，可自动写入）
candidates         聚类后的假说（triage 工作台）
admitted           正式词条（恒为人工产出，引擎永不写入）
```

**去重单位是 SourceVisitKey，不是裸 (source_id, division_id)**：

```python
SourceVisitKey = (
    work_id,                 # 哪部书
    edition_or_transcription_id,  # 哪个版本（维基文库转录≠校勘本，须分开）
    division_id,             # 哪篇卷
    miner_version,           # 挖掘器版本——v2挖过≠v3不重挖
    rule_profile_version,    # 词表/规则档版本
)
```

遍历伪代码（**先查后加，再挖掘**——v1 伪代码的硬错误是写了
seen_sources 却没在循环里执行）：

```python
for (source, division, kb) in worklist:
    key = SourceVisitKey(...)
    if key in seen_visits:
        revisited += 1
        continue
    seen_visits.add(key)          # 立即登记，再挖
    for occ in miner.mine(source, division, kb.facts):
        store_observation(occ)    # 写观察记录（自动，安全）
        if occ.normalized_form in known_forms:
            continue              # 字符串已知晓，仅计数
        candidates.offer(occ)     # 进 triage 工作台（非入库）
```

注意：seen_visits + known_forms 解决的是**有限重复计算**，
不是图论意义的无环。知识图谱允许 A→书1→B→书2→A，
需要的是 bounded revisitation，不是 cycle 恐慌。

### 2.3 状态机（v3 P1，回应外审「FIFO 会爆炸」）

候选不是全部立即研究。工作台按状态机管理：

```
NEW → TRIAGED → RESEARCHING → ADMITTED / REJECTED / DEFERRED
                （聚类时 MERGED / SPLIT 可发生在任何状态）
```

- **优先级**：extractor confidence、source quality、独立 mention 数、
  与既有 KB 的邻近度、海淀/北京相关性、当前纪录片制作需要、
  词库命中（TGAZ）、新颖度、审阅成本。
- **预算**：每轮 expansion 有 budget（篇卷数上限/新候选上限），
  frontier 按 best-first 出队，不是无限 breadth-first。
- **停止条件**：budget 耗尽或 frontier 为空。
  backlog 可以无限大，active review queue 必须有界。

### 2.4 挖书器接口（SourceMiner）

```python
class SourceMiner:
    def mine(self, source_id, division_id, facts) -> List[ToponymOccurrence]
```

- **ToponymMiner v3（已实现，MINER_VERSION="v3"）**：混合策略——
  - A. 提示词模式（「為」「曰」「有」「坐落」「跨其上」）
  - B. 通名后缀扫描——「专名+通名」结构（树「村」、安河「橋」、七里「泊」），
    召回无线索词地名
  - C. 方位后缀剥离——「樹村西邊」→「樹村」
  - D. 置信分级 high（双证）/ mid（单证）/ low
  - 词表全部繁简双字形
  - 实测：15 候选/8 噪声 → 11 候选/0 噪声；水礳（生僻通名）由提示词保住、
    永定河（无线索词）由后缀扫描保住——两法互补。
  - **为什么不上分词/NER（2026-10-02 调研，证据见
    `.superpowers/sdd/tokenizer-research.md`）**：现代分词器文言适配
    无公开量化证据；古籍 NER（SikuBERT/GujiBERT）F1 83-86.5% 但评测类
    不含 LOC 为主，历史地名 LOC 无公开 benchmark。四环节逐一否决：
    边界切分（白名单查表更便宜）/新词发现（互信息 n-gram 自算即可）/
    NER 直出（OOD+重依赖+自标语料）/同名消歧（用 TGAZ gazetteer 而非分词）。
    重新评估触发条件：①FullTextMiner 噪声率>20% 且人工过滤>每集1小时
    ②目标文本变为无标点原刻本 ③出现 LOC benchmark（F1≥85%）。
- **FullTextMiner（接口预留）**：接入维基文库/ctext 全文。
  ⚠️ 转录本≠校勘本；edition_id 必须区分，verbatim_quote 走 G9 校勘声明。
- **候选裁决外部依据**：TGAZ/CHGIS（已登记书目表）。
  命中→置信 mid→high；未命中不否决（CHGIS 收政区级，
  樹村实测 0 条——小村落未收录）。
  词库 `is_citable_for_verbatim=False`。
  ✅ API 已验证（2026-10-02，官方文档 indexAPI.html）：
  搜索 `GET /tgaz/placename?fmt=json&n=<UTF8名>`（前缀 LIKE，繁简均收），
  精准 `GET /tgaz/placename/json/hvd_<id>`，license CC BY-NC 4.0。
  接入须按 §六 缓存 lookup 结果，provider 故障不阻塞。

### 2.5 纪律（不可妥协）

1. **引擎只发现，不入库。** `admitted` 恒为人工产出。
   入库路径：人工 triage → research → 词条 → 九维闸门。
2. **机器观察记录可以自动持久化，但它不是事实。**
   「《八旗通志》卷116 出现字串『安河橋』，算法v2判 high」是
   machine_observation（安全自动写）；
   「安河桥是一个历史地点」是 entity/fact（禁止自动产生）。
   两层物理分开，观察层可无限增长，事实层只经闸门。
3. **可溯源**：每个 occurrence 带 evidence_fact_id。
4. **词表/规则档繁简双字形**（G6/G7/挖掘器三次教训，硬性规定）。
5. **版本化**：miner_version、rule_profile_version 进 SourceVisitKey，
   升级不锁死旧篇卷。

---

## 三、与既有体系的关系

| 组件 | 关系 |
|---|---|
| 九维 QA 闸门 | 候选升 entry 的唯一通道（人工触发） |
| 人名/书目/数字资源三层 | 新书进闭包前必须先入书目表 |
| TGAZ/CHGIS | 候选裁决外部依据（缓存 lookup，见 §六） |
| BHKG 十大断代 | entry 入库时必须挂 Era |
| 视频管线 | 词条直接喂 E12+ 的 research 骨架 |

---

## 四、诚实的边界声明（含外审补充）

1. **当前实现是单层扩展，不是完整闭包。**循环由人工 admission 驱动。
2. **正则/词表挖掘有天花板。**停用词永远追不上噪声；
   引擎输出定位是「发现清单」不是「事实清单」。
3. **方位短语污染**已用后缀剥离处理（樹村西邊→樹村），
   但 lexicalized 方位词（名称本身含「东」「西」的，如「山东」）是
   剥离规则的已知误伤面，须负控制覆盖。
4. **候选爆炸**（外审补充，已采纳）：《日下旧闻考》《八旗通志》类
   高地名密度文献，单篇卷可带出数十至数百 occurrence；
   已用 §2.3 状态机 + budget + best-first 应对。
5. **转录质量**（外审补充，已采纳）：OCR 错字/异体/断行/串行
   在 FullTextMiner 上线后会超过正则噪声本身；
   edition_id 区分 + §5.D 文本污染控制覆盖。
6. **source-network bias**（外审补充，已登记）：闭包天然偏向
   高连接度文献（官书被引最多→官书视角地名优先膨胀），
   优先级里必须保留「文献类型多样性」权重，防单一史观。

---

## 五、Verification, Controls & Falsification（v3 P0-2 全节重写）

外审裁决：原四条**降级为 System invariants**（证明系统纪律），
它们不能证明抽取判据非恒真——「返回文本中所有2-4字串」的坏模型
也能四条全过。真验证 = 下列控制对。

### 5.1 System invariants（保留，原有四条）
环避让计数、provenance 外键完整、admitted==[]、繁简过滤。

### 5.2 五类控制对

| 类 | 攻击什么 | 样例 | 期望 |
|---|---|---|---|
| **A. Hard FP** | 专名+通名规则的恒真风险 | 御道/仓署/护军校/营造司/桥梁/河工——都有通名形状但 gold=non-toponym | rejected 或 low；pattern hit=yes 但 gold=no 时必须能拒绝 |
| **B. Positive control** | 提示词法漏召回 | 无「曰/坐落/有」但确是地名（永定河样例），须独立集非开发样例 | 后缀路径命中 |
| **C. Entity collision** | 字符串去重的身份混淆 | 同名异地/异名同地/古今名/异体俗称 | 不得把两个历史地点合并为一个 candidate |
| **D. Text corruption** | 转录层污染 | 高梁河/高粱河/髙梁河、OCR错字、缺字断行 | 三个 occurrence、一个 normalized candidate（而非三个实体，亦非静默丢失） |
| **E. Mutation** | 规则靠文本形状碰巧工作 | 「安河橋」→「護軍校/東邊/八處」必须从 positive 变 negative；删「坐落」后后缀路径仍应召回 | 双向翻转 |

### 5.3 Holdout benchmark

冻结一套**从未参与规则迭代**的语料，按
朝代 × 文献类型 × 繁简/异体 × 地名类型分层，最低报告：
mention precision / mention recall / high-confidence precision /
candidate duplication rate / entity-collision rate。

当前「11候选/0噪声」只是 smoke test（样本小且参与过规则迭代），
不得当 validation 引用。

---

## 六、外部服务韧性（v3 P1，TGAZ 教训）

- TGAZ/CHGIS lookup **必须缓存**：query、timestamp、provider、
  response/version 全存（machine_observation 层）。
- provider 不可用 → 闭包**继续**，该候选标 `gazetteer_unchecked`。
  外部服务故障不得阻塞管线。
- API 端点未人工核验前**不写接入代码**（2026-10-02 实测 404）。

---

## 七、实施顺序（P0 先行）

1. **P0-1** 重构 CandidateName → ToponymOccurrence（字段全表）+
   聚类占位（C 类控制通过前，聚类允许保守=每 occurrence 一假说）
2. **P0-3** SourceVisitKey 版本化 + 遍历先查后加 + revisited 计数
3. **P0-2** §5.2 控制对 A/E 先落（成本最低、证伪力最高），
   B/C/D 随 FullTextMiner 落地；holdout 冻结语料在接入
   《日下旧闻考》前完成
4. **P1** 状态机 + priority + budget；machine_observation 落库；
   TGAZ 缓存层
