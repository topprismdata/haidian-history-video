# E30《十七孔桥》e30-bridge-body 合并前终审报告

- 审查对象：分支 `e30-bridge-body` 全 44 commit（merge-base `1bcf644`，HEAD `a5ff321`，47 文件 +6355/-26）
- 审查人：omp 终审 agent（只读；仓库文件未改动，除本报告）
- 日期：2026-10-05

## 0. 裁定

**修复后可合并（fix-then-merge）。**

本体几何、事实层、L1/L2 判据的工程质量和"自证非恒真"纪律总体是达标的：1555 测试全绿、
框架零项目常数、等级造假与三条禁令的负控经我独立破坏实验确认**能被抓住**（见 §4）。
但存在 1 条 Critical + 5 条 Important 会在合并后立刻伤害项目两条目标之一，须先修：

| 阻塞合并（必须合并前处理） | 理由 |
|---|---|
| **C1** 冻结生成器链的两个模块未入库 | M2.5"冷启动重建验证（G3 硬门）"的结论在干净克隆上**不可复现**，克隆里 `blender --python build_scene2.py` 直接 `ModuleNotFoundError`；修复量 = `git add` 两个文件 |
| **I2** freeze_manifest 里 `render_shot.py` 哈希与盘上不符，且闸门只覆盖 8/15 项 | 冻结完整性测试的锁定清单（8 个）窄于 manifest 自己的哈希表（15 个），漂移无牙 |
| **I3** L3 券洞布置闸门只写在文档里，代码里不存在 | 我实测：填掉一个券洞 → `VERDICT PASS`（IoU=1.0000）；`VOID_XC_TOL` 在整个仓库里只有定义、零消费 |
| **I4** L2 判据未执行时仍报 `ok: true` | 我用真 blend 实测：采样零命中 → `QA_L2_OK`，与项目信条"skip=未执行不算通过"直接冲突；这正是当年"8/8 通过"假绿的形状 |
| **I1** 框架契约把"对称 + 奇数孔"当普适律 | 接不了本项目自己的蓝本（卢沟桥左右不对称），也接不了任何偶数孔桥；第二个项目目标受威胁 |

不阻塞合并、但须在合并后第一个迭代内清掉：I6–I16 + §3 的 11 条 Minor。

## 1. Critical

### C1 — 冻结链依赖的 `materials.py` / `lions.py` 从未入库，干净克隆无法重建（`3d/build_scene2.py:5-6`）

- `build_scene2.py:5-6` = `import materials as MAT` / `import lions as LIONS`；两文件在 `git status` 中为 `??`（未跟踪），且 `refs/freeze_manifest.md:30-31` 还专门给它们记了 SHA256 并说明"无 random / seed 显式入参，确定"。
- 实测：`git archive HEAD | tar -x` 到 `/tmp/e30sab/clone`，克隆树 `3d/` 只有 11 个 .py（无 materials/lions）；以桩掉 bpy 的方式 `import build_scene2` → `ModuleNotFoundError: No module named 'materials'`。
- 影响：`freeze_manifest.md` §7 "冷启动重建验证（G3 硬门）…状态: 几何硬门已通过（2026-10-04 实测执行）"、"真相源=脚本+数据"这两条声明，只在当前工作站成立；合并后的仓库按 §7 的命令重跑必失败。测试也抓不到：53 条 e30 测试在克隆树里全绿，因为没有任何测试 import 生成器链（`test_freeze_manifest.py:32-40` 只比哈希，不查依赖是否入库）。
- 建议：①`git add e30_shikongqiao_video/3d/{materials.py,lions.py}`（manifest §30-31 的哈希已能对上盘，说明是漏 add 不是版本漂移）；②在 `test_freeze_manifest.py` 增一条"manifest §2 记哈希的每个文件必须 `git ls-files` 可见 + 生成器链每个 `import` 的本地模块必须被跟踪"的可执行闸门，否则同类漏项还会再发生。
- 顺带（不属本补丁，仅提示）：`bridge_geom.py`/`build_scene.py`/`report.py`/`compare.py` 等 v1 链同样未入库，`report.py` 还 import 着硬编码尺寸（150.0/6.56/14.6/7.0/2.50）的 v1 几何——要么随 C1 一起入库并在 manifest 标注其为 v1 遗留，要么删除，别留下"本地能跑、库里没有"的第二条几何链。

## 2. Important 全表

| # | 一句话 | 位置 | 级别 |
|---|---|---|---|
| I1 | 框架把"半侧序列 + 镜像展开 + 回文"当拓扑普适律：偶数孔桥结构性不可表达（展开恒为 2n−1），不对称桥（卢沟桥）无字段可表达；合成基线 5/23 孔均对称，故框架"通用性证明"看不见这个问题 | `bridge3d/derive.py:33-42`、`bridge3d/schema.py:28-31`、`bridge3d/checks_l1.py:91-110`、`tests/bridge3d/facts_synth.py:28-45,68-84`、`docs/bridge3d.md:29` | P1 |
| I2 | 冻结哈希闸门只覆盖 manifest 15 个记录中的 8 个；`render_shot.py` 记录值 `9573226…` 与盘上 `bef2368…` 不符（文件在 23:18 被 `cf11ac3` 改过，manifest 23:43 才回填），漂移无人守 | `e30_shikongqiao_video/tests/test_freeze_manifest.py:32-40` ↔ `3d/refs/freeze_manifest.md:33` | P1 |
| I3 | L3 的"券洞布置"硬判只存在于文档：`VERDICT` 仅取 IoU，`solidify()` 双侧填实使缺洞免疫（实测缺 1 孔 IoU=1.0000 PASS）；`VOID_XC_TOL` 全仓仅 1 处定义、0 处消费 | `e30_shikongqiao_video/3d/register_overlay.py:31,155-162`；声称见 `3d/refs/FACTS.md:276`、`3d/refs/freeze_manifest.md:71,182` | P1 |
| I4 | L2 "判据未执行"报成通过：`tot==0` 只记 warn，`ok = not fails` 仍 true；真 blend + 改坏采样带的副本实测输出 `QA_L2_OK / ok:true` | `e30_shikongqiao_video/3d/qa_l2.py:115-118,138-145` | P1 |
| I5 | 恒真检测器只查"能不能红"、不查"合法基线该不该绿"：过度约束判据（把某项目构型当普适律，MET_TAPER 原病）在 `assert_no_always_true` 下 kills 非空 → 放行（实测）；聚合级 `codes=None` 时永不触发的死判据被静默忽略（实测） | `bridge3d/negative_control.py:282-308`（`baseline_fail_codes` 记录但不断言）；`tests/bridge3d/test_checks_l1.py:295-307` | P1 |
| I6 | L2 负控零命中不被显式拒绝：翻转目标一旦脱离被测总体，`--negative` 仍 `ok:true`（实测复刻 D4 事故，打印文案还谎称"翻转 10 个采样带拱腹面"） | `e30_shikongqiao_video/3d/qa_l2.py:95-103` | P2 |
| I7 | 等级造假只锁"官方"：工作值→`测绘` 并把注释改写成正面出处 → 15 条全绿；框架 `check_official_citation` 也只对 `官方` 生效，最高两档（测绘/档案）无任何出处要求 | `bridge3d/facts_schema.py:136-150,152-176`；实测 §4 表 X-B7 | P2 |
| I8 | 来源等级注释与 SOURCES 登记无交叉核对：inline `[工作值]` + SOURCES `官方`(URL) → 全绿；反向 inline 改 `[测绘]` → 也全绿（"历史上 6 处不一致"仍靠手工） | `e30_shikongqiao_video/tests/test_facts.py:81-96`；实测 §4 表 X-X1/X2 | P2 |
| I9 | AST 字面量锁看不见整数且只检一个文件：注入 `= 3` / `= 17` 到 `bridge_geom2.py` 全绿，注入 `14.6`/`6.56` 才红；`build_scene2.py` 不在检查范围（`:10` 桥轴 112.0、`:166` 狮 1.15–1.35m、`:368` 长堤 42.0m 等） | `e30_shikongqiao_video/tests/test_no_literals.py:19-29`；对照框架 `tests/bridge3d/test_no_project_literals.py:52-58` 收 int+float | P2 |
| I10 | "反事实值锁"是死测试：条件带 `and f not in ALLOW` ⇒ 其 fail 集是上一条测试的真子集；实测把 `0.50` 放回 ALLOW 并让生成器出现 `0.50` 字面量（3353b3d 正是为堵这条逃逸加的测试）两测全绿 | `e30_shikongqiao_video/tests/test_no_literals.py:44-54`（第 52 行） | P2 |
| I11 | E30 L1 判据"崩溃而非报告"：短 `SPAN_DISTINCT` → `IndexError`，`DECK_Z_TOP` 非数 → `TypeError`；同一 facts 交框架 `run_l1` 正常报 `INV_SPANS_LEN`/skip（框架注释自称"E30 崩溃路径不再继承"，项目侧未修） | `e30_shikongqiao_video/3d/qa_bridge.py:9-27`；实测 §4 | P2 |
| I12 | 阈值"必须有依据"在 E30 侧未落地：`framework-report.md:50` 规定进 facts 的 `CLOSURE_TOL/ARCH_RATIO_TARGET/ARCH_RATIO_TOL` 三项不存在 ⇒ `bridge3d.audit(E30 facts)` 的 MET_CLOSURE/MET_ARCH_RATIO 双双 skip；实际把关的 `qa_bridge.py:65,85` 把 0.5m、0.50±0.05 硬写进判据源码、不进 SOURCES | `e30_shikongqiao_video/3d/qa_bridge.py:65,85`；`3d/facts.py:21-47` | P2 |
| I13 | C6 裁决"统一 1.35、删除双值"未执行：`assumptions.py:10` 仍留 `BRIDGE_ABUT_TARGET=2.00` 且注释称"未裁决"，`bridge_geom2.py:31` 死透传并谎称 `build_scene2` 依赖它（实际 `build_scene2.py:279` 用 `G.BRIDGE_ABUT`），`freeze_manifest.md:73` 把 2.00 记为"未裁决提案" | `3d/assumptions.py:10-12`、`3d/bridge_geom2.py:31` | P2 |
| I14 | 生成器闭合断言写死 `16*PIER_W` 而非 `(N_SPAN-1)`——正是当年 -2.50m 假闭合差的数字形状；判据侧已改 `N_SPAN-1`，生成器侧没改，且被 I9 的整数盲区放过 | `e30_shikongqiao_video/3d/bridge_geom2.py:178` | P2 |
| I15 | 冻结闸门的 spec §9 推导值断言存在**假通过项**：`SPRINGER=2.50` 检查 `"2.5" in sec9`，而 §9 全文只有标题"（M2.5 冻结包…）"里的 `2.5` 子串，根本没有起拱线条目 ⇒ 该断言恒真；改成 9.17 才红（说明它只可能因"别的文本含此子串"而假绿） | `e30_shikongqiao_video/tests/test_freeze_manifest.py:167-186` ↔ `docs/superpowers/specs/2026-10-04-e30-bridge-facts-design.md:§9` | P2 |
| I16 | 框架自称"中国古建通用"但契约是拱桥专用：`REQUIRED=(BRIDGE_LEN,N_SPAN,SPRINGER,PIER_W,BRIDGE_ABUT)` 对牌楼/亭/塔/闸无意义，第二个项目要么编假事实要么必红；且 `audit()` 无 `checks=` 出口（`met_deck_camber` 要求严格 `>`，平桥实测被判 fail），文档里"自选判据集"的逃生门在推荐入口上不可用 | `bridge3d/schema.py:28-31`、`bridge3d/__init__.py:64-67`、`bridge3d/checks_l1.py:172-186`；实测 §4 | P2 |

## 3. Minor（11 条，不阻塞）

1. `tests/bridge3d/test_no_project_literals.py:88-92`：特征数正则只扫 `FEATURE_NUMBERS[0]/[1]`（5/17），`23` 从未被该测试扫（仅靠第三条测试间接兜住），与函数文档"不得以任何形态出现"不符。
2. `3d/qa_bridge.py:80-92`：`MET_ARCH_RATIO/MET_RING_FIT/MET_SPRINGER` 在逐孔循环内，一处 facts 错最多产 17 条重复 fail（噪音，非误判）。
3. `3d/ortho.py:38`：同文件注释仍写"桥轴(世界-103.15°)"，而 `:22` 已声明 103.15 为过时值并取 112.0 —— 冻结文件内部自相矛盾。
4. `3d/refs/FACTS.md:41`（C4）：桥走向只登记 90/112/135 三值，未登记仓库实际在用的第四值 103.15（`research/research.md:162-177` 为其出处，3D 层无任何来源登记；桥轴也未进 facts/SOURCES）。
5. `3d/register_overlay.py:33` + `refs/FACTS.md:259` 称标定基线为 `86fe24ec…`，`refs/freeze_manifest.md:89` 称 T7 标定所用为 `58db0658…`；虽以"重渲前后 0.8070 不变"调和，但归因两处不一致。
6. `3d/bridge_geom2.py:27` 导入 `DECK_Z_AT_PIER` 后零消费（`deck_z` 实为抛物线），而该数组作为 [工作值] 进冻结 §9 清单——声称受治却无人使用的尺寸。
7. `3d/bridge_geom2.py:32` `SEG = 40` 为死变量；`NSEG_ARC/NSEG_X` 在 `assumptions.py:8-9` 与 `bridge_geom2.py:33-34` 双源。
8. `bridge3d/facts_schema.py:33`（`_SELF_NO_SOURCE` 含"工作值"、`_NEGATION` 含"未注明"）与 `tests/test_facts.py:191,203` 的词表不一致 —— 同一条规则两份实现，将来必然漂移。
9. `3d/register_overlay.py:45`：`VOID_MIN_WNORM = 0.01` 注释自称 [工作值]，但不进 SOURCES、也不进 manifest §5 阈值表。
10. `3d/register_overlay.py:112` `overlay()` 默认 `a_is_ref=False`，而 `tests/test_register.py` 全部传 `a_is_ref=True` —— 渲染侧 alpha 载入路径在 pytest 中从未被执行。
11. `bridge3d/negative_control.py:193-197`：`list:swap` 破坏在 `len(SPAN_DISTINCT)==1` 时产出与原序列相同的"破坏"（当前合成 facts 长度≥3 未触发，属潜伏的假破坏）。

## 4. 恒真审计结论（本审查的独立结论，非转述）

方法：不采信任何"已配负控"的声明，逐层用**破坏实验**问同一句话——"把被测对象改坏，它会不会失败？"
所有破坏都在 `/tmp` 副本（`git archive` 克隆 / `cp -r` 沙箱 / 真 blend + 改坏脚本副本）上进行，仓库文件零改动。
共执行 3 轮 pytest（全仓 1555 passed；沙箱 15×12 例；克隆树 53 passed）、1 次真 Blender L2 正检 + 2 次改坏副本、
以及 26 个手工构造的破坏（下表）。

### 4.1 框架 L1（`bridge3d/checks_l1.py` 18 条 + `facts_schema.py` 10 条）

| 判据 | 我怎么验的 | 结论 |
|---|---|---|
| INV_N_SPAN / INV_SPANS_LEN / INV_SPANS_POS / IMP_DIM / IMP_TOLERANCE / IMP_SOURCES_COVER / IMP_GRADES_LEGAL / IMP_ASSUMPTION_ISOLATED / 6×MET / IMP_RELATIONS（15 条） | 复核 `test_checks_l1.py` 每条的 `assert_criterion_rejects`（该工具把"判据崩溃"也判为失败，我读源码确认非自欺）；抽 6 条重跑套件绿 | **非恒真 ✔** |
| INV_SPANS_SYM | 亲自跑 `patched_derive(spans=skew)` → 红；基线（n5/n23）→ 静默 | 非恒真 ✔，**但只对"推导规则被改坏"成立**；经由 facts 的不对称输入不可达（⇒ I1） |
| INV_SUPPORTS_LEN | `patched_derive(pier_x=截短)` → 红 | 非恒真 ✔ |
| IMP_CONTRACT | 由 `test_facts_schema.py`（14 个 test）逐条破坏 | 非恒真 ✔ |
| MET_DECK_DIR / MET_TAPER / MET_ARCH_RATIO 的"过严方向" | 我构造合法替代构型：等宽桥 → 放行 ✔（回归测试已补）；**平桥（顶=端）→ 误判 fail ✘** | 收分已修，**纵坡方向仍把拱桥构型当普适律 ⇒ I16** |
| 恒真检测器 `assert_no_always_true` | (a) 喂"永不红"判据 → 报警 ✔；(b) 喂"基线就红"的过度约束判据 → **放行 ✘**（`baseline_fail_codes` 只记录不断言）；(c) 聚合级混入死判据 + `codes=None` → **静默忽略 ✘** | 检测器只覆盖"测不出东西"，不覆盖"见谁都咬" ⇒ **I5**（这也是 MET_TAPER 当时能过审的机制，同理 I1 现在也过审） |

### 4.2 E30 事实层（`tests/test_facts.py` 15 条）— 12 个破坏实测

| 破坏 | 期望 | 实测 |
|---|---|---|
| S1 `PIER_W` 工作值→官方（注释不动） | 红 | **红**：`test_grades_are_not_inflated` + `test_official_grade_requires_citation_in_note` ✔ |
| S2 `DECK_UP_W` 官方注释→"据说如此" | 红 | **红**（正面出处锁）✔ |
| S3 `DECK_UP_W` 官方注释→"北京青年报2019原始页未检回"（年份+机构全在否定语境） | 红 | **红** ✔（这条是 2026-10-04 补严的真效果，我独立复现了"据说全绿"的反例已不存在） |
| S5 删除 `PIER_W` 登记 / S6 新增常量不登记 | 红 | 均红 ✔ |
| B1–B3 三条禁令逐条删除 | 各红 | 全部红（含 `test_prohibitions_are_three_distinct_sentences`）✔ |
| B4/B5 禁令②③换词（放大代超分、公制代米制） | — | 红 ——方向是**假红不是假绿**，保守可接受 |
| B7/X1 工作值→**测绘** + 注释改写成正面出处 | 期望红 | **全绿 ✘** ⇒ I7 |
| X1/X2 inline 等级注释与 SOURCES 互相矛盾 | 期望红 | **全绿 ✘** ⇒ I8 |
| X3 三条禁令糊成一句（关键词齐在） | — | 红 ✔（关键词锁在此形状上仍有效） |

### 4.3 L2 / L3 / 冻结闸门

| 层 | 实测 | 结论 |
|---|---|---|
| L2 正检 | 真 `e30_bridge.blend` 跑 shipped 脚本：`QA_L2_OK`，fail/warn 皆空，`refs/l2_baseline.json` 同形 | 判据**确实执行**且有判别力（历史上抓过 494/494 背心） ✔ |
| L2 零采样 | /tmp 副本把采样带过滤收紧到不可能命中 → 打印 `QA_L2_OK`、`ok:true`、warn 仅 `L2_SAMPLE` | **skip 被当通过 ✘ ⇒ I4** |
| L2 负控 | /tmp 副本把翻转目标挪到桥面（脱离被测总体） → `翻转 10 个…` + `ok:true` | 负控可零命中而自称成功 ✘ ⇒ I6（D4 事故无代码护栏） |
| L3 IoU | 复核反恒真负控（驼峰平移 40px → <0.95）成立；刚体平移/等比缩放被归一化吸收（设计特性，已声明） | ✔ 有判别力 |
| L3 券洞 | 合成"少一个券洞"→ `overlay()` IoU=**1.0000** → `VERDICT PASS`；`void_table` 自己检出 3→2 但无人比较 | **文档声称的硬判在代码里不存在 ✘ ⇒ I3** |
| L3 阈值可分性 | E2 可接受 [0.8046,0.8373] vs 不可接受 [0.0030,0.7216] 不重叠 ✔；Δw 轴两区间重叠 → 只报告不硬判 ✔（诚实）；四个无判别力轴逐条归因（跨缩放→L1、矢高比→L2、闭合补偿→L1、缺孔→本应 L3 但见 I3） | 标定方法成立；但"缺孔归 L3 守"这一条现在是空的 |
| 冻结闸门 | 篡改 manifest 一位哈希 → `test_manifest_hashes_detect_tampering` 红 ✔；但 `_LOCKED_FILES` 只 8/15，且 spec §9 的 SPRINGER 行以 "M2.5" 子串假通过（改 9.17 才红） | 部分有效 ✘ ⇒ I2/I15 |
| xfail | `grep -rn xfail tests/ e30_shikongqiao_video/tests/` → 仅剩注释，无标记 | ✔ 无"意外 XPASS 静默"风险 |
| 框架零项目常数 | `grep -rn "\b17\b\|\b53\b" bridge3d/*.py` → 零命中；AST 锁另扫 int/float 全集 | ✔ |

### 4.4 独立结论（一句话）

**这套判据整体上不是恒真的**——L1 的 18 条、E30 事实层的等级/禁令锁、L2 的 WALL_NORMAL、L3 的 IoU 轴，
我都用独立破坏验证过"改坏会红"；**但有四类真实空转**：(1) L3 券洞硬判只有文档没有代码（实测缺孔 PASS）；
(2) L2 未执行/负控零命中都报 `ok:true`；(3) 恒真检测器只防"永不红"、不防"基线就红"与"死判据"，
所以 MET_TAPER 那类过度约束能过审，同类的对称/奇数孔约束至今仍在 schema 层；
(4) 三处"检查存在但为子串/真子集"的假通过（spec §9 SPRINGER、反事实值锁、特征数 23）。

## 5. 框架通用性结论

- 已修的 MET_TAPER 不是孤例：**同一机制（把首项目构型当普适律、且恒真检测看不见）还剩三处**——
  ①schema/derive 的对称+奇数孔契约（I1，影响最大，写进了契约层）；②`met_deck_camber` 严格中央最高（平桥/开启桥，I16）；
  ③`REQUIRED` 的拱桥专用字段（牌楼/亭/塔/闸，I16）。
- `TARGET` 语义本身没问题：`met_arch_ratio` 用项目自声明 `ARCH_RATIO_TARGET±TOL`，未声明即 skip ✔（已实测 skip 路径）。
- `met_closure`/`met_ring_fit`/`met_springer` 无项目常数 ✔；`derive.geometry_closure` 的 (n−1) 拓扑 ✔ 通用。
- 建议的修法与主控线索一致：对称性降级为 `facts.RELATIONS`（`imp_relations` 机制现成），
  `SPAN_DISTINCT` 允许全长列表（`derive.spans` 改成"长度==N_SPAN 直接用，否则按半侧镜像展开"，
  并让 `INV_SPANS_SYM` 只在项目声明对称时生效），同时把 `facts_synth` 增补 **不对称桥 / 偶数孔桥 / 平桥 / 等宽桥**
  四个"合法替代构型"基线 —— 否则下一个同类错误照样过审。

## 6. 事实层诚实性结论

- `facts.py` 17 个条目的 inline `[等级]` 与 `SOURCES` 等级**当前逐条一致**（我手工比对全表）；但无交叉核对测试（I8）。
- 12 条 [工作值] 与 `freeze_manifest.md` §9 清单一致，且 `test_freeze_manifest` 逐条核名 ✔；
  冻结状态 `CONDITIONAL_RECONSTRUCTION_FREEZE` 由 `test_freeze_state_matches_facts_reality` 与 facts 实况双向锁 ✔。
- 三条禁令均写在 docstring 且逐条可证伪 ✔（B1–B5 实测）；关键词锁的失败方向是假红不是假绿。
- "工作值谎标官方"能被抓 ✔（S1）；但**谎标"测绘/档案"不能被抓** ✘（I7）——按项目自己的分级，
  这是比谎标官方更严重的等级（测绘为最高级），却是唯一无人守的一档。
- 未发现"把 GPT 聊天当来源"的漏网：`DECK_Z_TOP` 的 inline 明确披露 "(GPT建议)" 并落 [工作值]；
  ESRGAN 在 `ARCH_RATIO` 注释与 SOURCES 双向声明"已退出计量链" ✔。

## 7. 并发一致性结论

- 测试全绿 ≠ 一致：见 I2（manifest 哈希漂移）、I13（C6 裁决未执行）、I12（阈值未进 facts）、I1（框架修订未回灌项目判据）、
  Minor 3/5/7/8（同值多源、注释残留、词表分叉）。
- 未见"两个 agent 对同一物理量写出两个互相矛盾的**生效值**"：桥台生效值统一为 1.35（生成器/判据/闭合三处同口径）；
  L3 阈值 IOU_MIN=0.76 / VOID_XC_TOL=0.02 在代码与文档数值一致；法线阈值 THETA=6°、采样带参数与 manifest §5 一致。
  风险都在"死值/注释/归因"层，不在生效路径层。

## 8. 修复清单（按优先级，最小改动）

1. `git add e30_shikongqiao_video/3d/materials.py lions.py`（C1），并加一条"生成器链 import 的本地模块必须被跟踪"闸门。
2. `test_freeze_manifest.py` 的锁定清单改为**从 manifest 表格反推**（凡 manifest 记哈希的文件都进 `_LOCKED_FILES`），并回填 `render_shot.py` 哈希（I2）。
3. L3：在 `register_overlay.py` 的判定路径里把 `void_table` 结果与 `facts.N_SPAN` / 期望 xc 表比，`|Δxc|≤VOID_XC_TOL` 不满足即 fail；同步 §7 文档措辞（I3）。
4. `qa_l2._emit`：加 `"skip"` 键，`ok = not fails and not skipped`；负控模式 `flipped == 0` 或负控跑出 `ok:true` 一律 exit 1（I4/I6）。
5. `negative_control.assert_no_always_true`：默认断言 `not rep["baseline_fail_codes"]`；并提供逐判据入口（显式 `codes=[该判据全部代码]`）防死判据（I5）。
6. 框架对称性降级 + `derive.spans` 支持全长列表 + `facts_synth` 增 4 个合法替代构型基线（I1/I16）；`audit()` 增 `checks=` 透传（I16）。
7. 等级锁扩到全部非工作值等级：任何 测绘/档案/官方/图像推导 都须正面出处；新增 inline↔SOURCES 交叉核对测试（I7/I8）。
8. `test_no_literals.py`：`_floats` 改收 `(int, float)`（结构白名单另列）、把 `build_scene2.py` 纳入扫描、删掉 `and f not in ALLOW` 使反事实锁真正独立生效（I9/I10）；顺手把 `bridge_geom2.py:178` 的 `16` 改 `N_SPAN-1`（I14）。
9. `qa_bridge.derive/check_body` 加与框架同形的护栏（短序列/非数值 → 报告而非异常）（I11）；把 `CLOSURE_TOL=0.5`、`ARCH_RATIO_TARGET/TOL` 落进 `facts.py` 并登记 SOURCES，判据改读 facts（I12）。
10. 删 `assumptions.BRIDGE_ABUT_TARGET` 与 `bridge_geom2.py:31` 透传，manifest §5 同步"已裁决"（I13）；修 spec §9 断言使其按"标签+数值"配对而非裸子串（I15）。

## 9. 已申报的诚实边界——核对结论：如实记录，非隐瞒

| 申报项 | 我的核对 |
|---|---|
| 12 条 [工作值] 无公开测绘来源 → 冻结只能是 `CONDITIONAL_RECONSTRUCTION_FREEZE` | ✔ manifest §9 逐条列名、`test_freeze_state_matches_facts_reality` 双向锁、facts 实况一致 |
| 渲染像素级复现**不成立**（GPU 自适应采样非确定，arch 视图 5 渲 5 异）→ 只声明到配置锁定 | ✔ manifest §6/§7 明文"渲染对照不构成冻结判据"、seed 政策注明"只固定采样序列"；未把像素哈希当判据（这是加分的诚实） |
| L3 对 4 个扰动轴无判别力，逐条归因到该由哪层守 | ✔ 归因表在 `register_overlay.py:22-27` 与 FACTS §7；**但"缺孔由 L3 count+xc 硬判"这一条是空头承诺**（I3），其余三条归因成立 |
| 券洞表只跑渲染侧，抓"模型与 facts 不一致"而非照片基准；facts 错了会一致地错 | ✔ `commit 9a4282a` 与 §6.2-2 均已写明；本报告 I3 是其加强：连渲染侧这一票也还没接进判定 |
| 目视比对须过分辨率门槛（券石环 2.67px 不可分辨 → 撤回 M3 第 3 条） | ✔ `commit c02f412` 主动撤回臆断项，方向正确 |

## 10. 验证日志（全部可复现）

- `python3 -m pytest tests/ e30_shikongqiao_video/tests/ -q` → **1555 passed**, 4 warnings（无关的 Pydantic 弃用告警）
- `grep -rn "\b17\b" bridge3d/*.py` / `"\b53\b"` → **零命中**
- `grep -rn xfail tests/ e30_shikongqiao_video/tests/` → 仅剩注释，无 xfail 标记
- 破坏实验沙箱（仓库文件零改动）：
  - `/tmp/e30sab/clone` = `git archive HEAD | tar -x` → `import build_scene2` → `ModuleNotFoundError: No module named 'materials'`；克隆树内 pytest → 53 passed
  - `/tmp/e30sab/grade` = `facts.py`+`tests/test_facts.py` 沙箱 → 12 例等级/禁令破坏（§4.2）
  - `/tmp/e30sab/lit` = `bridge_geom2.py`+`test_no_literals.py` 沙箱 → int/float 注入 5 例（§4.3）
  - `/tmp/e30sab/fz` = 全量 `e30_shikongqiao_video`+`docs` 沙箱 → spec §9 SPRINGER 假通过实证
  - `/tmp/e30sab/exp1_asym.py` → 卢沟桥式不对称 11 孔 / 4 孔偶数桥 / 平桥 三构型交 `bridge3d.audit`
  - `/tmp/e30sab/exp2_tautology.py` → 恒真检测器三向探针（永不红 / 基线就红 / 聚合级死判据）
  - `/tmp/e30sab/exp4_l3.py` → 少一个券洞的 `overlay()` IoU=1.0000 + `VOID_XC_TOL` 消费点为 0
  - `/tmp/e30sab/exp6.py` → `qa_bridge.check_body` 对损坏 facts 崩溃 vs 框架 `run_l1` 报告
  - 真 Blender：`blender -b e30_bridge.blend --python qa_l2.py` → `QA_L2_OK`；两份 /tmp 改坏副本 → 零采样 `ok:true`、负控脱靶 `ok:true`
- manifest 哈希全表核对脚本：逐行解析 15 条 SHA256 与盘上比对 → 14 MATCH、1 DIFF（render_shot.py）、2 条对应文件未入库（materials/lions）

## 11. 未覆盖 / 存疑（诚实声明）

1. 未执行完整 T6/T8 冷重建链（需 Blender GUI/长渲染）；对 C1 的结论建立在"导入链在干净克隆中失败"这一确定性证据上，足以否定 §7 的可复现声明。
2. L2 负控的"正确形态"（带内翻 10 面 → 必 FAIL）我未重新跑一次正例（T5 报告已留档 10/494），只验证了脱靶时无人拒绝。
3. 报告未逐字核对 FACTS.md 全部 250+ 行引文与外部来源（属 M0/M2c 的既有审阅范围）；我只核了等级标注的自洽性与锁的可证伪性。
4. `e30_shikongqiao_video/design.md` 处于未提交的 `M` 状态（用户的并发改动），不在本补丁审查范围。
