# Holdout 基准冻结设计与分层抽样框架

> 状态：**已冻结 v1**（2026-10-02）· 对应 spec：`docs/superpowers/specs/2026-10-02-closure-expansion-design.md` §5.3
> 纪律来源：spec §七 P0-3 —— holdout 冻结语料必须在接入《日下旧闻考》**之前**完成。
> 产物：`haidian_kg/evaluation/holdout_sampler.py`（抽样器）、
> `haidian_kg/evaluation/holdout_v1.jsonl`（冻结快照）、
> `haidian_kg/evaluation/holdout_v1.report.json`（抽样报告）、
> `tests/haidian_kg/test_holdout_sampler.py`（17 项验收测试，全绿）。

---

## 1. 目的与冻结纪律

闭包挖掘管线（ToponymMiner → occurrence → 假说聚类）在接入《日下旧闻考》
原文后将进入高地名密度文本。spec §5.3 判定：现有「11候选/0噪声」只是
smoke test——样本小且**参与过规则迭代**，不得当 validation 引用。

本框架在接入原文前锁死四样东西：

| 冻结项 | 内容 | 锁死位置 |
|---|---|---|
| 分层轴 | 朝代 × 文献类型 × 繁简/异体 × 地名类型 | 本文 §4，代码 `strata_of()` |
| 抽样框架 | 段定义、相关性判据、比例配额、种子 | 本文 §5，代码 `sample_holdout()` |
| 标注手册 | 三层身份标注字段与流程 | 本文 §6 |
| 判定标准与验收阈值 | 五指标公式与门槛数值 | 本文 §7 |

**为什么现在冻结**：规则作者一旦看过评测集，后续所有 P/R 都是「在考卷上
调参」。冻结 = 抽样器先跑、金标后标、引擎后改；三方只通过本文档的契约
交互。

**抽样器与挖掘器故意不共享词表**（不 import `expansion.PLACE_SUFFIXES`）：
holdout 判据若复用被测系统的启发式，就测不出系统自身盲区。地名类型层
使用独立冻结的后缀表 `TOPO_SUFFIXES`，与挖掘器语义对齐、文本独立。

## 2. 三层身份定义（复用 spec §2.1 / `expansion.py`，标注与判定共用）

| 层 | 定义 | 代码对应 | 标注角色 |
|---|---|---|---|
| **Occurrence**（文本事实层） | 「某文献某位置出现了形状为 X 的字串，上下文像地名」。机器可自动产生，但它**不是事实**（spec §2.5.2） | `expansion.ToponymOccurrence` | 标注员在段内逐个圈 mention：span、surface_form、normalized_form、cue |
| **Hypothesis**（实体假说层） | 「这批 occurrence 可能指向同一个历史地点」。保守聚类：每 normalized_form 一假说 | `expansion.CandidatePlaceHypothesis` | 标注员裁定 occurrence 聚簇；碰撞/重复在此层显影 |
| **Entity**（实体层） | 经过闸门的知识库实体（`ent_*`） | `haidian_kg` KB | 裁定假说挂接：既有实体 / 新实体 / 不可辨识 |

评估的全部指标（§7）都落在「引擎输出的三层」对照「金标的三层」上。

## 3. 抽样脚本契约（`haidian_kg/evaluation/holdout_sampler.py`）

```bash
# 在仓库根 /Volumes/macstudio/video-projects 执行（-m 依赖 cwd 上的包，仓库惯例）
python3 -m haidian_kg.evaluation.holdout_sampler \
    --n 120 --seed 20261002 \
    --out holdout.jsonl [--report report.json] [--corpus-dir <dir>]
```

- **只读** `haidian_kg/corpus/era*.md`（测试 `test_corpus_is_read_only` 钉死）；
- 输出 JSONL，每行一段，字段：`segment_id`（`文件名:L起-L止`）、
  `source_file`、`line_start/line_end`、`heading_path`、`text`（逐字原文）、
  `strata{dynasty,doc_type,script,toponym_type}`、`rxjwkc_cue_scope`
  （direct/section/file）、`rxjwkc_juan`（相关篇卷号，升序去重）、
  `text_sha1`（语料漂移检测）、`n_chars`；
- **确定性**：固定 seed + 全序化（无 set 迭代/时间戳进输出路径），两次
  运行字节级一致（测试 `test_fixed_seed_two_runs_identical`、
  `test_cli_deterministic_bytes` 钉死）；
- N 默认 120；总体不足时抽满总体并在报告记 `frame_shortfall`（§8 缺口清单）。

## 4. 分层方案（四轴）

| 轴 | 层值 | 推导规则（机械、可复现） |
|---|---|---|
| **朝代** | 史前/先秦/秦汉魏晋南北朝/隋唐五代/辽金/元/明/清/近现代 | 文件名 `eraN_*` → `ERA_DYNASTY` 表 |
| **文献类型** | L1 考古实物 / L2 一手官书档案文集 / L3 正史方志纪实 / L4 现代学界考订 / L5 民间传说 / L6 证伪伪说 / unattributed | 段内 `Level N` 标记；无则继承所在节全部标记；多级并存取**最强**（数字最小） |
| **繁简/异体** | trad / simp / mixed | 冻结的单字形字符表（繁体-only / 简体-only），两表都命中=mixed。粗判粒度：足以分层，不用于判定 |
| **地名类型** | settlement / hydraulic(含桥闸) / garden / temple / military / landscape(含陵墓) / pass / none | 段内**最先命中**的通名后缀 → 类；后缀表 `TOPO_SUFFIXES` 独立冻结（§1 纪律） |

四轴叉积为层键 `strata_key`。已知取舍（冻结决定，勿擅自改）：
桥闸并入 hydraulic 不单列；script 判定是字符表粗判，繁简**异体**细类
（髙/高、資/资 类 OCR 变体）留待原文接入后在标注层处理，不在分层层展开。

## 5. 抽样总体与相关性

- **段（segment）**：顶层列表项/散文块 + 其嵌套续行（标注最小自洽单元）；
  `##` 下无 `###` 的负控制节按 `##` 节归段，不得整节丢弃（era7 §2 即此形态）。
- **《日下旧闻考》相关性**（cue，三档优先级 direct > section > file）：
  1. `direct`：段文本含书名（变体表：日下旧闻考/日下旧聞考/日下舊聞考）；
  2. `section`：所在 `###` 节（缺则 `##` 节）内任一段含书名——长编的
     「文献出处」bullet 常与正文 bullet 同节并列，兄弟段同属该书证；
  3. `file`：文件前导引用块（`>` 整理原则）把书名列为核心凭证（era7 整卷）。
  4. `none`：三档皆无 → **不入总体**。
- **篇卷号**（`rxjwkc_juan`）：书名后白名单字符（书名号/括号/空白/第）
  须紧跟「卷」，取完整数字 token（简繁数字/阿拉伯），区间「至/—/～」读
  第二端点。**禁止窗口截取**——40 字窗口曾把「一百零一」拦腰截成
  「一百」→假卷号 100（实现注释留档，测试 `test_juan_extraction_no_window_truncation`
  回归钉死）。畸形 token 恒拒绝，不猜（`chinese_num_to_int` → None）。
- **配额**：非空层比例分配 + 最大余数法；非空层数 ≤ N 时每层保底 1；
  余数并列按层名字典序（确定性）。
- **calibration 语料禁入**：`calibration/*.py` 的 verbatim_quote 是种子词条，
  参与过规则迭代，spec §5.3 红线，永不入 holdout。

## 6. 标注手册骨架

金标文件：`holdout_gold.jsonl`，按 `segment_id` 对齐冻结快照；
`text_sha1` 不一致 = 语料漂移，该段作废重抽（不许就地改金标）。

### 6.1 Occurrence 层（逐 mention）

| 字段 | 说明 |
|---|---|
| `span` | 段文本内字符区间 [start, end) |
| `surface_form` | 逐字原样（繁体引文保留繁体） |
| `normalized_form` | 归一形（繁→简，聚类的唯一键） |
| `cue` | 為/曰/有/坐落/即/跨其上/后缀扫描/无 |
| `is_toponym` | gold 布尔：真地名候选（含 §5.2-C 同名异地各算各） |
| `is_generic` | 通名假命中（御道/仓署/护军校/旗名/营造司……形状像地名 gold=non-toponym，spec §5.2-A） |
| `direction_suffix_stripped` | 「树村西边」剥「西边」记「树村」 |
| `note` | 存疑标注（异体/OCR/断行） |

### 6.2 Hypothesis 层（聚簇裁定）

- 按归一形聚类后逐簇裁定：簇内 occurrence 是否同一历史地点；
- `collision`：一簇合并 ≥2 个 gold 不同地点（§5.2-C，硬闸=0 容忍）；
- `duplication`：同一 gold 地点被拆进 ≥2 簇。

### 6.3 Entity 层（挂接）

每簇裁定：挂既有 KB `ent_*` / 新实体（待建）/ 不可辨识（保留为假说）。

### 6.4 流程

1. 两遍独立标注（同一标注者间隔 ≥48h，或两人分标）；
2. 分歧逐条仲裁（仲裁记录入金标 `note`）；
3. 金标先于引擎改动冻结——**金标文件一经提交，规则迭代不得回看**；
4. 每个新判据先在负控制段（era7 §2 两段已在快照内）上验证非恒真。

## 7. 判定标准与验收阈值（冻结）

引擎在快照上跑完后，对照金标计算（spec §5.3 最低报告集）：

| 指标 | 公式 | 阈值 |
|---|---|---|
| **mention precision** | TP / (TP+FP)；TP = 引擎 occurrence 与金标 mention 归一形一致且 span 相互包含 | **≥ 0.90** |
| **mention recall** | TP / (TP+FN)，FN = 金标有而引擎漏 | **≥ 0.85** |
| **high-confidence precision** | 引擎自标 `confidence=high` 的 occurrence 中 TP 占比（提示词+通名双证，spec §2.1） | **≥ 0.95** |
| **candidate duplication rate** | 被 ≥2 个假说覆盖的 gold 实体数 / gold 实体总数 | **≤ 0.05** |
| **entity-collision rate** | 覆盖 ≥2 个 gold 实体的假说数 / 假说总数 | **= 0（硬闸）** |

- 阈值是**接入《日下旧闻考》原文的放行闸门**：五项全过才允许 FullTextMiner
  消费原文；任一不过 → 修规则重跑（holdout 不变）。
- collision=0 直接继承 spec §5.2-C（「不得把两个历史地点合并为一个
  candidate」，无容忍空间）。
- §5.2 控制对 A/E（Hard FP / Mutation）是独立闸门，不在本表内；本表
  只管 holdout。

## 8. 缺口清单（v1 快照实测，2026-10-02）

冻结时语料只能支撑部分分层覆盖，以下缺口**逐条量化**，接入原文后按 §8.7
扩展协议补齐：

| # | 缺口 | 实测 |
|---|---|---|
| 8.1 | **原文未接入**（这正是冻结前置条件的根因）：总体仅覆盖长编转述层，33 段 / 平均 65 字，请求 120 段缺口 87 | `frame_shortfall=87` |
| 8.2 | **朝代层**：史前/先秦/秦汉魏晋南北朝/隋唐五代/近现代 5 朝 frame=0。RXJWK 体例本就略于先秦、详于辽金以降，era0-3 语料未引、era8_9 不属其适用域；该 5 层不得用其他朝代段顶替 | 冻结快照仅含 辽金7/元3/明3/清20 |
| 8.3 | **繁简层**：33 段 script 全为 simp——长编引文已转写为简体；繁体原字形（護軍校/東邉/資安 类）目前只在 calibration 引文中，而 calibration 参与过规则迭代禁入。trad/mixed 层当前为 0，原文（繁体）接入后才会出现 | `script set = {simp}` |
| 8.4 | **文献类型层**：仅 L2/L3/unattributed；L1/L4/L5/L6 = 0。era7 §2 负控制两段（六郎庄传说防线/苏州街禁区）已入快照可作 L5/L6 性质判定材料，但其 Level 标记缺席 | `doc_type set = {L2, L3, unattributed}` |
| 8.5 | **篇卷覆盖**：快照联系到的篇卷 = 76–104（区间）与 96/98/101/103/104 单卷，其余 150+ 卷无样本 | `rxjwkc_juan` 分布 |
| 8.6 | **段长分布**：长编 bullet 平均 65 字（≤205），原文卷段密度远高于此——mention 密度不可比，P/R 阈值放行仅对「长编层」有效，原文层需重估 | `n_chars` 分布 |
| 8.7 | **扩展协议**：原文入库后用同一脚本 `--corpus-dir <原文库>` 重抽，段 schema/分层轴/阈值/种子纪律不变；v1 快照保留为长编层基准，v2 起合并报告，两快照不得混算 | 本文 §5 CLI |

### 8.8 v1 冻结记录

- seed `20261002`，N 请求 `120`，实抽 `33`（总体=frame=33，全收）；
- 抽样输出：`haidian_kg/evaluation/holdout_v1.jsonl`（33 行）；
- 报告：`haidian_kg/evaluation/holdout_v1.report.json`
  （含 9 个 era 文件的 SHA256 全量摘要——语料任何漂移都会使
  `segment_id + text_sha1` 失配而暴露）；
- cue 构成：direct 7 / section 16 / file 10；层键 18 个非空层；
- 复现：`python3 -m haidian_kg.evaluation.holdout_sampler --out <p>`
  输出与快照字节级一致（CI/测试钉死）。

### 8.9 v2 冻结记录(2026-10-02)

- 快照:`haidian_kg/evaluation/holdout_v2.jsonl`(60 段,《日下旧闻考》四库本原典域,
  138→140 金标,12 实体)。源卷 `holdout_v2_pilot_labeled.jsonl` 同步修正后一致。
- 标注:规则作者标注(60 段)+ 独立第二遍重标(分层抽查 20 段,seed=20261002,
  卷 `.superpowers/sdd/holdout-v2-spotcheck-ballot.md`)。双标注一致性 19/20;
  唯一分歧 = 「髙梁橋」因变体字 髙 缺失漏标(2 段各 1 处,已修正补标)。
  用户对抽查卷回复「继续」,记为抽查让渡给双标注一致性程序;让渡事实与 seed
  一并留证。
- 冻结修正:`_VARIANT_MAP` 补 髙→高(评估器真值层;miner 侧暂缺,引擎修复是
  冻结后第一道被测题,不得预修)。
- v2 阈值:沿用 §7 冻结阈值不动;run7 为 v2 域基线,只记录不判优。
