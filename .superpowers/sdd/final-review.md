# QA v2 整支 Code Review（合并前分诊结论）

- **范围**：`f548ec2..517576d`（18 commit，25 文件，+2675/−324）
- **依据**：完整 diff（4485 行）、spec `docs/superpowers/specs/2026-10-01-qa-v2-design.md`、实现计划、E11 验收报告；另用真实 E11 数据（`slots.json` / `narration/all.json`）做了针对性实证，未重跑 113 个测试（报告已载明全过）。
- **结论先行**：**不建议按当前状态合并**。跨层几何/归一化地基基本干净（坐标换算四路一致、`text_at` 无缩放），但有一个 **Critical**：`NEGATIVE_CONTROL_FAIL` 在真实 E11 `--full` 上是**结构性假阳性**（8 页全报，36 个 fail 的主因），把本系统最核心的设计（每条判据有负控制）变成了噪声源；另有 L4-a 归一口径不对称的 Critical、spec 明列的 L1 第 6 项检查缺失。

---

## 1. 跨 task 一致性检查

### 1.1 坐标空间一致性（最高优先）

| 检查点 | 结论 | 位置 |
|---|---|---|
| `checks_render.check_l3` | ✅ 一致：`plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)` 单次换算后交 `text_at` | `qa_v2/checks_render.py:41` |
| `checks_render.check_l5` | ✅ 一致：单次换算，画布空间切图 | `qa_v2/checks_render.py:127` |
| `checks_render.check_l6` | ✅ 一致：单次换算 | `qa_v2/checks_render.py:178` |
| `checks_content._ocr_text_for` | ✅ 一致：单次换算后直接喂 `text_at`，OCR 框未再乘缩放 | `qa_v2/checks_content.py:51` |
| `frames.text_at` | ✅ 纯画布空间几何，无任何缩放；中心点判定 + `pad=25` 容差 | `qa_v2/frames.py:151-172` |
| `checks_render.assert_negative_control` | ✅ 换算本身一致，但**平移落点有缺陷**（见 C1） | `qa_v2/checks_render.py:55-80` |
| `geometry.plate_to_canvas` | ✅ 全仓唯一定义，无第二实现 | `qa_v2/geometry.py:29-41` |

**结论**：四路 `plate_to_canvas` 用法一致、无漏换算、无双重换算。用户全局约束「OCR `rec_boxes` 已在画布空间、禁止再乘缩放」在所有消费点都遵守。旧 QA 事故根因（坐标空间混用）没有回归。

### 1.2 命名与接口一致性

| 检查点 | 结论 |
|---|---|
| `Finding` 字段 | ✅ 七层统一 `layer/page/slot/level/code/message/detail`，无 `code`/`id` 混用，单一定义于 `report.py` |
| `check_l*` 签名 | ✅ 全部返回 `List[Finding]`：`check_l1/l2(ep)`、`check_l3(page, ocr)`、`check_l5/l6(page, png)`、`check_l4a(page, ocr)`、`check_l4b(page, ocr, names)`、`check_l4c(ep, ocr_by_page)`，与计划接口一致 |
| 层号标记 | ✅ 逐一核对：`"L1"/"L2"/"L3"/"L4-a"/"L4-b"/"L4-c"/"L5"/"L6"` 无写错。两处约定成事实：`RENDER_FAILED`、`NEGATIVE_CONTROL_FAIL` 标 `"L3"`（run.py:78/96），属运行层异常借道 L3 汇报，语义可接受 |
| 导入 | ⚠ Minor：`checks_render.py:14-18` 对 `qa_v2.geometry` 两条独立导入未合并（见 §3 新增项） |

### 1.3 负控制的调用一致性

`assert_negative_control` 仅在 `run.py:93`（`--ocr`/`--full` 档）调用，快档不跑。与 E11 报告执行方式自洽，但见 C1。

---

## 2. Spec 覆盖度

| spec 章节 | spec 要求 | 实现位置 | 状态 |
|---|---| `run.py` CLI + `scripts/qa_all.py` 薄壳 | ✅ 实现并实测可用（工程副本下 `fail 0/warn 3/退出码 0`） |
| §5.1 开关 | 默认快档、`--ocr`/`--full`/`--json` | `run.py:110-125` | ✅ |
| §5.1 快档层集 | 快档 = L1+L2+**L3**+L5+L6 | `run.py:85-88` | ⚠ **偏差**：快档实际只跑 L1/L2/L5/L6，L3 不跑（`if ocr is None: continue`）。spec 与 run.py docstring（run.py:3）都承诺含 L3。语义上有理由（L3 需 OCR），但文档与实现矛盾；且快档对「非 tag 槽没渲出内容」完全不设防（L6 只管 tag，L5 只管触边） |
| §5.2 L1（6 项） | 文案→槽位、槽位→文案、越界、异常尺寸、重叠、**平台一致性（subtitles.ts/pageMap.ts 存在且页数=槽数）** | `checks_data.py:23-82` | ⚠ **缺 1 项**：前 5 项已实现，「平台一致性」缺失（qa_v2/ 下对 subtitles 的引用仅存在于注释）。已实现的 `PAGE_COUNT_MISMATCH` 是「页数 vs layout 项数」，与 spec 所指是两回事 |
| §5.2 L2 | 行数估算 + 1.15 容差 warn | `checks_data.py:86-135` | ✅（E11 实测 3 条 warn 与报告吻合） |
| §5.2 L3 | 槽内须有 OCR 文本框（中心点 + 25px 容差） | `checks_render.py:32-52` | ✅（仅 `--ocr` 档生效） |
| §5.2 L4-a | **两侧用同一函数**归一、OCR ⊇ 原文、unknown>20% warn | `checks_content.py:55-83` | ❌ **两侧不同口径**：want 侧 `extract_numbers(item.text)`（原文），got 侧 `extract_numbers(normalize_punct(got_raw))`（先剥标点）。实证：`"1799 → 1800 → 1801"` 两侧分别得 `{1799,1800,1801}` vs `{179918001801}` → 必报 NUMBER_MISMATCH。E11 报告 `P7/title` 的 fail 即此病（detail 里 `ocr=1799 → 1800 → 1801`，OCR 读回正确仍 fail） |
| §5.2 L4-b | 专名表命中项逐个出现；缺表 skip | `checks_content.py:85-110` | ✅（E11 实测抓到的「正黄旗」缺失是真实 OCR 漏读，属真阳性） |
| §5.2 L4-c | 口播稿上对**数字与专名**交叉（语音形式归一） | `checks_content.py:128-178` | ⚠ 弱实现：只交叉数字，专名未交叉；`_is_volume_ref`（`1<=n<=200`，checks_content.py:118-127）把 P3 表格的 26/39/65 等真实内容数字全豁免 → L4-c 对 ≤200 的数字形同虚设（报告 22 条 L4-c fail 全是 ≥200 的数）。报告「已知限制」第 5 条已披露口语化差异，但 ≤200 全豁免未披露 |
| §5.2 L5 | 底板分离 + 腐蚀 + 连通域 + 触边 fail | `checks_render.py:84-158` | ✅（E11 快档 0 fail） |
| §5.2 L6 | 白字块 1%~40% 占比 | `checks_render.py:160-194` | ✅（8/8 有值，负控制留证） |
| §5.3 报告 | 判据 ID、槽位 id、期望 vs 实测、**正/负控制状态** | `report.py:60-96` | ⚠ 负控制状态未作为报告字段：Finding 无 control 相关字段，控制结果只能以 fail 形式出现。简化可接受（Minor） |
| §6/§6.1 负控制 | **L3 与 L4 各自**构造平移负控制并留日志 | `checks_render.py:55-80`、`run.py:93-99` | ❌ ① 只有 L3 有平移负控制，L4-a/b/c 无（spec §6.1 明文「对 L3 与 L4 各自」）；② 平移 `x+300` 在真实板面上结构性假阳性，E11 `--full` 8 页全报 NEGATIVE_CONTROL_FAIL（fail 36 的主因）——见 C1 |
| §7 实现顺序 | 7 步依赖序 | 18 commit | ✅ |
| §8 风险缓解 | `rec_boxes` 格式断言、缺表 skip、warn 不阻塞 | `frames.py:98-115` 等 | ✅ |
| §9 验收标准 | E11 `--full`：L1–L6 全部通过 | E11 报告 | ❌ **未达成**：`--full` 实测 `fail 36 / warn 3 / 不通过`。36 个 fail 中至少 9 条（8 页负控制 + P7/title）是实现 bug 而非 OCR 已知限制。报告把交付结论落在「快档通过」上（见 I3） |
| §10.2 warn 不阻塞 | fail 才非零退出 | `run.py:107-109` | ✅ 实测退出码 0（warn 3） |
| L7 | 复用既有脚本 | `run.py:136-139` 提示命令 | ✅（路径硬编码见 M4） |

---

## 3. Scope 检查

**多做（scope creep）**：

1. `checks_data.item_lh`（checks_data.py:96-106）——为「未来可能有的 lh 字段」做防御性 `getattr`，当前恒走 default=1.4，死路径。Minor，可留。
2. `checks_content._VOLUME_RE = None`（checks_content.py:112）——死常量，`_is_volume_ref` 不使用它，只会误导。Minor，应删。
3. `run.py:13` `from typing import Dict` ——未使用导入。Minor（Task 7 刚清过 frames.py 的同类问题，新代码又出现一处）。

**漏做**：L1 平台一致性（I1）、L4 三路负控制（I4）、L4-c 专名交叉（弱实现）。除此之外无漏做。整体 scope 克制：没做史实校验、没做历史集回溯、没做 L7 重造——spec 非目标全部遵守。

**路径副作用**：`.gitignore` 由 `!/qa/` 改 `!/qa_v2/`。已核实 `/Volumes/macstudio/video-projects/qa`（仓库根）不存在，旧 `qa/` 缓存在工程副本 `chemistry-video/qa/`（不受 git 管理），改动无副作用。✅

---

## 4. Minor findings 分诊（累积 5 条）

| # | 来源 | 内容 | 分诊 | 理由 |
|---|---|---|---|---|
| 1 | Task 1 | 实现者修正 brief 里 `test_out_of_bounds_detects_overflow` 断言矛盾（`1672+10 > 1672` 原判 False 不自洽） | **可留（无需动作）** | 是修正计划笔误而非引入缺陷；当前断言（test_geometry.py:60-63）自洽且正确 |
| 2 | Task 4 | `Finding.__init__` 用 `assert` 校验 level，`python -O` 下被剥掉 | **可留** | 本项目运行命令均为 `python3 -m qa_v2.run`，无 `-O`；`test_finding_invalid_level` 已钉住常态行为。若未来 CI 加 `-O` 再改 `raise ValueError`（1 行） |
| 3 | Task 7 | frames.py 冗余导入 | **已消解**（commit 1428f66） | —。但同类问题在新代码重现：run.py:13 `Dict` 未用（§3），合并前顺手清 |
| 4 | Task 8 | checks_render docstring「不用 OCR」与 L3 依赖 OCR 矛盾 | **已消解**（commit 02081a0） | 现 docstring 为「L3 额外依赖 OCR」 |
| 5 | Task 9 | 测试文件 import 位置（L5 测试前 import 在第 69 行） | **可留** | 纯风格，import 均在使用点之前，行为无影响 |

**分诊结论**：5 条累积 Minor 中 2 条已消解、3 条可留合并后；本次整支 review 另新增 8 条（§5），其中 M8 一条建议升级为合并前应修（理由见该条）。

---

## 5. 新发现的问题

### Critical

**C1. 负控制「x+300 平移」在真实板面上结构性假阳性 —— `--full` 8 页全报 NEGATIVE_CONTROL_FAIL，是 fail 36 的最大来源**
- 位置：`qa_v2/checks_render.py:55-80`（`assert_negative_control`）；调用点 `qa_v2/run.py:93-99`
- 机制（已用真实 `src/shucun/data/slots.json` 实证，两层假阳性）：
  1. **宽槽自碰撞**：平移仅 x 方向 300px；`text_at` 判「OCR 框中心 ∈ 矩形±25px」。E11 每页的 `title`/`sub` 槽宽 ≥ ~556px（1672 板面），平移 300px 后矩形**仍罩住自己的文字** → 该槽被计入「负控制未命中」。每页命中 2~3 个（p01/p02/p04/p05/p08 的全部来源）。
  2. **邻槽碰撞**：平移后矩形中心落入**邻槽**（含 25px 容差）→ `text_at` 返回邻槽文字 → 计入未命中。密集表格页 p03 有 36 个、p07 有 3 个。
- **吻合度证据**：我用 25px/0.8703≈28.7px 板面空间容差模拟，期望命中数为 2/2/39/2/2/3/5/3，与 E11 报告的 `NEGATIVE_CONTROL_FAIL` 计数（2/2/39/3/2/3/5/3）逐页吻合（p04 一槽之差属容差边界与 OCR 框实际位置的偏差）。**报告里那 8 条 fail 不是「判据恒真」，而是平移落点撞了邻槽/自身**。把容差置 0 重算：p01/02/04/05/06/08 全清零，仅 p03=36、p07=3 残留（纯几何重叠）。
- 为什么是 Critical：负控制是 spec §6「与旧 QA 的核心区别」、本系统的立身设计。它在标定集 E11 上跑出 8 页全 fail，意味着 `--full` 档不可用（永远不通过），而报告仍以「快档通过」交付。更隐蔽的是：**真恒真的判据也会淹没在这批假阳性里**——负控制从此失去区分度。
- 修复建议（离散）：① 平移后矩形须与**所有真槽及自身原矩形**都不相交（交叠则换 y 方向或加大位移，找不到安全落点就对该槽报「负控制不可用」而非「失败」）；② 负控制路径 `text_at` 的 pad 置 0（消 6/8 页）；③ 补一条单测：平移落点与邻槽重叠时不得计为「未命中」——现有 `test_negative_control_detects_always_true_detector` 只测了 shift=0 被拒，恰好漏掉这个形态。

**C2. L4-a 两侧归一口径不一致 —— 含 `→`/`·` 分隔数字的文案恒报 NUMBER_MISMATCH（spec 明文「两侧用同一函数」被违反）**
- 位置：`qa_v2/checks_content.py:61-65`
- want 侧 `extract_numbers(item.text)` 在**原始文本**上抽数（`→` 分隔保留，token 边界有效）；got 侧 `extract_numbers(normalize_punct(got_raw))` 先剥标点再抽数（`1799 → 1800 → 1801` → `179918001801` 单 token）。
- 实证：同一字符串两侧分别得 `{1799,1800,1801}` 与 `{179918001801}` → `missing=[1799,1800,1801]` → fail。E11 报告 `P7/title` 即此病实锤：detail 显示 `ocr=1799 → 1800 → 1801`（**OCR 读回完全正确**）仍 fail。
- 同机制也放大了 P3 的粘连误报：OCR 把 `65`+`39` 粘成 `6539` 时报 `期望[65] 读回[6539]`。粘连本身是 PaddleOCR 已知限制，但「65 ⊄ {6539}」的判定方式让误报形态变成数字 mismatch 而非可归因的粘连提示。
- 修复（离散，1-3 行）：got 侧改为 `extract_numbers(got_raw)`（与 want 同口径、不 normalize）；或判据改为「原文每个数字是 OCR 读回数字串的**子串**」（兼容粘连与分隔两种形态）。任选其一，两侧必须同口径。

### Important

**I1. L1「平台一致性」检查缺失（spec 6 项只实现 5 项）**
- 位置：`qa_v2/checks_data.py`（全文件无此检查；qa_v2/ 内 subtitles 仅出现在注释里）
- spec §5.2 L1 第 6 行：`subtitles.ts`/`pageMap.ts` 存在且页数 = 槽数。已实现的 `PAGE_COUNT_MISMATCH` 是页数 vs layout 项数，不是这项目。修法：`check_l1` 补 ~15 行（读 `src/<ep>/data/subtitles.ts`、`pageMap.ts` 存在性 + 页数/槽数比对）。

**I2. 快档跳过 L3，与 spec §5.1 及 run.py docstring 矛盾**
- 位置：`run.py:3`（「L1/L2/L3/L5/L6」）vs `run.py:85-88`（`if ocr is None: continue` → 快档无 L3）
- 实测快档（`python3 qa_all.py shucun`）：`fail 0/warn 3`，跑的是 L1/L2/L5/L6。后果：快档对「非 tag 槽没渲出内容」零检测。E11 报告耗时表自述快档=L1,L2,L5,L6，说明实现者知道取舍但文档未同步。修法（二选一）：快档跑无 OCR 的 L3 下限判据（复用 `text_bbox_in_slot` non-None）；或同步改 spec 与 docstring，明示「快档不含 L3」。

**I3. `--full` 36 个 fail 未做归因，「快档通过」掩盖了实现 bug**
- 位置：`docs/qa/2026-10-01-qa-v2-e11-report.md`
- spec §9 第一条「E11 `--full` L1–L6 全部通过」未达成。报告以快档结论为主体，`--full` 的 36 fail 罗列后整体归入「密集表格粘连」等已知限制——其中 8 条负控制假阳性（C1）+ 1 条 P7/title 归一不对称（C2）是**实现 bug**，与 OCR 噪声混在一起未分诊。合并决策依赖这个区分。修法：报告补「36 fail 归因」一节（≈9 实现 bug / ≈16 表格粘连 / ≈11 口播稿差异类）。

**I4. L4 三路（a/b/c）没有负控制，违反 spec §6.1「对 L3 与 L4 各自构造」**
- 位置：`qa_v2/checks_content.py` 全文件、`run.py:89-91`
- E11 报告「负控制留证」表只覆盖 L3/L1/L4-a，且 L4-a 那条（1485→1486）是**破坏实验**（正向变异），不是 spec §6.1 定义的平移式负控制。间接缓解：槽位平移到空白区后 L4-a/b 会因读回为空而报 fail（E11 报告 L3 负控制实测确实连带触发）——算部分覆盖。分诊：**可留**，但报告应说明「L4 负控制以 L3 平移连带触发的方式满足」，或补一个直接负控制（对 L4 判据喂空 OCR，断言报 fail 而非 pass——现有 `test_l4_handles_missing_slot_gracefully` 已接近此形态，补断言即可）。

### Minor

**M1. `run.py:13` 未使用导入 `Dict`** —— Task 7 刚清完 frames.py 冗余导入，新代码又引入同类。1 行。

**M2. `checks_render.py:14-18` 同模块双导入**（`geometry` 的 `Rect` 与 `plate_to_canvas` 分两条 import）。合并顺手修。

**M3. `_ocr_text_for` 槽缺失时返回空串**（checks_content.py:48-50）→ L1 的 `TEXT_REFERENCES_MISSING_SLOT` 根因会在 L4-a/L4-b 重复报 `NUMBER_MISMATCH`/`PROPER_NAME_MISSING`，findings 有重复噪声。语义无害（都 fail、且「不崩」是有测试钉住的意图）。可留。

**M4. 路径可移植性不对称**：`ROOT`（data.py:24）可被参数覆盖，`VIDEO_ROOT`（data.py:25）与 L7 提示命令（run.py:136-139）硬编码绝对路径。换机器需多处同改。单机项目可留。

**M5. `render_text` 排序键 `x.page or 0`**（report.py:76-78）：page=None 的 finding（NO_NAMES_TABLE/NO_NARRATION）排序在 P0 位置，同 key 间依赖稳定排序。行为可接受，仅提示。

**M6. 约 6 个测试依赖真实 E11 数据/渲染帧**（test_data.py:56-73、test_checks_data.py:96-99、test_checks_render.py:185-190、test_checks_content.py:127-129）：需要 `/tmp/chemistry-video` 特定内容；`test_real_shucun_passes_l6` 首次冷跑会真调 remotion（~36s）。「克隆即绿」不成立。计划约束「测试不得依赖成片渲染」被部分突破。分诊：可留（E11 是标定集），建议给这些测试加 `pytest.mark.skipif`（环境缺失时跳过），否则 CI/新机器上会假红。

**M7. `test_frames.py` 的 `test_ocr_cached_reads_cache`** 钉住了缓存命中语义（有价值），同时顺带钉死了「缓存不随内容失效」行为（见 M8）。

**M8.（建议升级为合并前应修）OCR 缓存键仅 `(ep, page)`，与破坏实验 SOP 耦合**
- 位置：`qa_v2/frames.py:125-149`
- 已知限制本身已披露（改文案后需手动 `rm /tmp/qa_cache`）。**升级理由**：破坏实验是这套系统的可信度凭证，其 SOP（改 pages.config.ts → 跑 `--ocr` → 恢复 → 重跑验证恢复）恰好踩在缓存上——破坏时 OCR 结果落缓存，恢复后若不清缓存，重跑读的是**破坏时的 OCR**，「恢复后无此报错」的验证可能被旧缓存污染成假阴性。E11 报告的恢复步骤未提清缓存。修法（二选一）：缓存键加入 png 的 mtime 或内容哈希（~5 行）；或破坏实验 SOP 明确加 `rm -f /tmp/qa_cache/<ep>_*.json` 步骤并写进报告。

### 维护性总评

- **结构**：16 文件单向依赖（geometry/normalize/data/frames 底座 → checks 三件 → report/run 汇聚），无循环导入；`Finding` 与 `check_l*` 签名全仓统一，跨层接缝干净。对 E12+ 的扩展（新集三份数据 + names.txt 增补）足够。
- **重复逻辑**：实质重复没有；注释级重复一处（「不认 subtitles.ts」的两条理由在 data.py:236 与 checks_content.py:131 各写一遍，无害）。
- **测试质量**：主体测行为（判 fail/skip/None），parametrize 用得好；E11 实测锚点测试（test_geometry 的 (246,897)、test_normalize 的口播年份）价值最高。两个弱点：M6 的真数据依赖；负控制测试只测 shift=0 被拒、**没测「平移撞邻槽」的假阳性形态**——恰好漏掉 C1，这是「测了实现细节、漏掉行为边界」的实例。
- **文档**：module docstring 把 E11 踩坑史写在代码旁，是这套代码最大的可维护性资产。

---

## 6. 总结论

**不能按当前状态合并。**

问题不是风格或小 bug，而是这套系统的两条立身腿各断了半条：① 负控制（spec §6 核心差异化设计）在标定集上 8 页全 fail 的假阳性（C1）——它制造噪声而非可信度；② `--full` 36 fail 里至少 9 条是实现 bug，交付结论却落在「快档通过」（I3）。

同时要强调：**地基是好的**。本次 review 最高优先项——坐标空间一致性——完全通过（四路单次换算、`text_at` 零缩放、无双重换算）；Finding/签名/层号跨层统一；113 个测试主体测行为。C1/C2/I1 都是单函数内的离散修复，不牵动架构。

### 合并前必须修（阻塞清单）

| # | 问题 | 位置 | 修复量 |
|---|---|---|---|
| C1 | 负控制平移假阳性（宽槽自碰撞 + 邻槽碰撞） | `checks_render.py:55-80` | 单函数重设计平移落点 + pad 置 0 + 补邻槽单测 |
| C2 | L4-a 两侧归一口径不一致（`→` 分隔数字恒 fail） | `checks_content.py:61-65` | 1-3 行（got 侧同口径，或改子串判据） |
| I1 | L1 平台一致性检查缺失（spec 6 项只做 5 项） | `checks_data.py` | ~15 行 |
| M8 | 破坏实验 SOP 与 OCR 缓存失效耦合（可信度凭证可被旧缓存污染） | `frames.py:125-149` + E11 报告 | 缓存键加 mtime/哈希，或 SOP 加清缓存并留证 |

### 建议合并前顺手修（非阻塞）

I2（快档 L3 与 docstring/spec 矛盾——至少改文档）、I3（报告补 36 fail 归因）、I4（报告说明 L4 负控制的连带覆盖方式）、M1/M2（导入清理）、M6（真数据测试加 skipif）、删 `_VOLUME_RE = None` 死常量。

### 修完后重跑什么（验收口径）

- `python3 -m qa_v2.run shucun --full`：预期负控制 0 fail；P7/title 不再 false-fail；残余 fail 应降到个位数且逐条可归因于已披露的 OCR 粘连/口播差异。
- 破坏实验重做时**先清 `/tmp/qa_cache/<ep>_*.json`**，恢复后同样先清再验证（M8 落地前这是 SOP 硬步骤）。

---

### 附：本次 review 的实证清单

1. 通读 4485 行完整 diff、spec 311 行全文、实现计划、E11 报告。
2. 用真实 `src/shucun/data/slots.json` 模拟负控制平移碰撞：期望命中数 2/2/39/2/2/3/5/3 与 E11 报告 `NEGATIVE_CONTROL_FAIL` 逐页吻合（p04 一槽之差属容差边界）；pad=0 重算后 6/8 页清零、仅 p03=36、p07=3 残留（纯几何重叠）。
3. 实证 `extract_numbers` 两侧口径差异：`"1799 → 1800 → 1801"` want={1799,1800,1801}，got={179918001801}。
4. 实测薄壳：`cd /tmp/chemistry-video && python3 qa_all.py shucun` → `fail 0 / warn 3 / 退出码 0`（1s）；实测在仓库根直接 `python3 scripts/qa_all.py shucun` 因 `qa_v2` 不在 sys.path 报 ModuleNotFoundError——薄壳**必须在工程副本下或以 `python3 -m qa_v2.run` 执行**（双仓库布局的既有形态，非本 diff 引入，但值得记录：spec §5.1 承诺的「沿用 qa_all.py 入口」仅在工程副本目录成立）。
5. 核实 `/Volumes/macstudio/video-projects/qa`（仓库根）不存在，`.gitignore` 由 `!/qa/` 改 `!/qa_v2/` 无副作用；`qa_all.py` 两份拷贝（scripts/ 与工程副本）内容一致。
6. 未重跑 113 个测试（任务明确要求基于 diff 审查、报告已载明全过）。
