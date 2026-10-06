# E30 终审 ★ 项修复报告（I1★–I5★）

- 修复人：FixStarred（主控委派 worker）
- 日期：2026-10-05
- 分支：`e30-bridge-body`
- Commits：`4798aae`(I1) → `c4dd3bd`(I2) → `4ae4b51`(I3+I4) → `fd1c407`(I5)

## 测试结果

| 环境 | 结果 |
|---|---|
| 主工作树（HEAD + 并发 sibling 未提交改动） | **1699 passed, 2 failed** —— 2 个失败全部来自 sibling 正在进行的未提交编辑（assumptions/bridge_geom2/build_scene2/facts/materials/ortho/qa_bridge 七个冻结文件被改、manifest §9 未同步），正是 I2 新闸门**按设计**抓住的形状；非本补丁引入 |
| 干净 worktree（`git worktree` checkout 我方 HEAD `fd1c407`） | **1694 passed, 7 failed** —— 7 个全部是 `tests/test_viewport_math.py`（chemistry-video 视口组件文件被 gitignore，干净 checkout 里不存在；主工作树实测 14 passed，属预先存在的环境性失败，与本补丁无关）。bridge3d + e30 全部测试在隔离 HEAD 上全绿，冻结闸门在真实 git worktree 下通过 |

原 1555 条一条未删；仅两类测试按新契约重写（见各节"测试变更"）。基线 1555 → 现 1701 条（+I1 十三条、I3 五条、I5 约百条参数化点名审计，及并发 sibling 已落地 commit 的合法新增）。

---

## I1★ 对称性契约放宽（用户已批准）— `4798aae`

**改了什么**
1. `bridge3d/derive.spans(f)`：`len(SPAN_DISTINCT) == N_SPAN` → **全长表直接用作跨序**（不对称桥/偶数孔桥/等跨桥均可表达）；否则保留 `D + reversed(D[:-1])` 镜像展开作对称奇数孔便利路径。`N_SPAN` 成为展开前置事实（缺失 → MissingFactError → 判据层 skip）。
2. `bridge3d/checks_l1.py`：删除 `inv_spans_sym`（出 INV_CHECKS）——对称不再是 INV 普适律，降级为项目 `facts.RELATIONS` 自声明（走现成 `imp_relations` 机制）。展开规则的回文属性下沉到 `test_derive` 单测锁。
3. `met_deck_camber`：`top > end` → `top >= end`（与 MET_TAPER 同款教训：平桥是合法构型，只禁倒拱 `end > top`）。此为 I16 的平桥半边，属 I1 四构型基线的必要前提；`checks=` 透传等其余 I16 内容未动。
4. E30 `3d/facts.py` 增 `RELATIONS`（半侧严格递增 + 半侧表形态声明 2n−1==N_SPAN）——E30 自声明对称，其对称检查不丢且可证伪（乱序 SPAN_DISTINCT 实测触发 `REL_half_side_rises_to_center` fail）。
5. `tests/bridge3d/facts_synth.py` 增四个合法替代构型：`make_asym11`（卢沟桥式不对称奇数孔，全长表，东端跨≠西端跨）、`make_even6`（对称偶数孔，全长回文表+回文关系）、`make_flat3`（平桥 顶=端）、`make_equal4`（等宽桥 顶=底）。全部精确闭合。
6. `docs/bridge3d.md` 第 29 行改写（不再写"半侧→对称展开"为唯一契约）；schema/derive/checks_l1/__init__ docstring 同步。

**测试变更**：`test_patched_derive_kills_sym_guard` → `test_patched_derive_kills_spans_len_guard`（SYM 判据已删，检测器级护栏目标改为 INV_SPANS_LEN）；`test_no_always_true_in_l1` 移除 SYM 断言。二者断言的是被删除的框架行为。

**怎么验的（实测输出）**
```
make_asym11 N_SPAN= 11 len(SD)= 11 fails= [] skips= []
make_even6  N_SPAN= 6  len(SD)= 6  fails= [] skips= []
make_flat3  N_SPAN= 3  len(SD)= 3  fails= [] skips= []
make_equal4 N_SPAN= 4  len(SD)= 4  fails= [] skips= []
```
（即 `bridge3d.audit` 对不对称桥与偶数孔桥基线全绿零 skip。）破坏侧：偶数孔桥全长表打破坏文 → `REL_spans_palindrome` 红（框架 INV 层保持沉默）；倒拱 `end>top` → `MET_DECK_DIR` 仍红。

## I2★ 冻结哈希闸门 8/15 → 全量 — `c4dd3bd`

**改了什么**：`test_freeze_manifest.py` 的 `_LOCKED_FILES` 手写 8 项清单删除，闸门改为解析 manifest §1/§2/§4 三个文件哈希节的**全部记录**（15 条）逐条比对盘上哈希；§6 IDAT 像素哈希按 manifest 自身声明（存档快照、非判据）显式排除并有防混入断言。新增：
- `test_manifest_recorded_files_are_git_tracked`：**凡 manifest 记哈希的文件必须被 git 跟踪**（C1 回归闸门）；
- `test_manifest_records_full_file_hash_table`：核心 8 文件不得从 manifest 缩水 + IDAT 不混入；
- 篡改负控测试改在 15 条全量映射上进行。

**漂移修复**：`render_shot.py` 按盘上哈希回填（`bef2368c…`）；新闸门随即**自己抓出第二处漂移** `ortho.py`（`4ce8475` M3-1 改后未同步，旧 8 项清单覆盖不到），同样回填（`1a44bcd3…`）。

**怎么验的**：
- 负控演练 1：把 render_shot 记录值改回旧值 `9573226…` → 闸门立刻报 `render_shot.py (盘上 bef2368ccecb != 记录 957322629203)`；
- 负控演练 2：`3d/report.py` 未入库（git ls-files 无）而 `materials.py` 在库——若有人给未入库文件记哈希，tracked 闸门必红；
- 干净 worktree（HEAD）下 `test_freeze_manifest.py` 12 条全绿。

## I3★ L3 券洞硬判真实现 — `4ae4b51`（前半）

**改了什么**：`register_overlay.py` 新增 `expected_void_table(facts)`（由 facts 经 **bridge3d.derive** 推导期望券洞表——与 bridge_geom2/qa_l2 挖孔同口径，无第二套几何）与 `void_verdict(render_mask, facts)`（孔数 == facts.N_SPAN 且逐孔 |Δxc| ≤ VOID_XC_TOL=0.02；Δw 仍只报告不硬判——诚实边界不变）。`__main__` 的 `VERDICT` 改为 `IoU 达标 **且** void_verdict 通过`。manifest §2/§11 哈希同步。

**修复前实测症状（同一破坏用例）**：
```
缺 1 孔渲染 vs 完整渲染  IoU=1.0000
修复前 VERDICT: PASS (VOID_XC_TOL=0.02 全仓 0 处消费, void_table 仅打印)
```
**修复后同一破坏**：
```
AFTER-fix missing-1: False ['孔数 16 != facts.N_SPAN 17 (render=[...] exp=[...] )']
→ VERDICT FAIL
```
**合法基线该绿**：17 孔合成带 `void_verdict` ok=True 零故障；真冻结渲染 `ortho_side.png`：
```
SILHOUETTE_IOU 0.8070 (min 0.76)
VOID_VERDICT PASS (n=17, max|Δxc|=0.0181 <= 0.02)
VERDICT PASS
```
测试：`test_register.py` 新增 4 条（合法基线绿 / 缺 1 孔红 / 大间距注入 facts 上 xc 轴独立红——E30 真桥孔间距小于 2×TOL，大位移会粘连塌缩为 count 破坏，注释写明 / 期望表与 facts 递推闭式一致）。

## I4★ L2 判据未执行不得报通过（含 I6 负控脱靶护栏）— `4ae4b51`（后半）

**改了什么**：`qa_l2.py`：①采样零命中从 warn 改为记入 `skip`，`ok = 零 fail 且零 skip`，JSON 显式区分 fail/warn/skip 并新增 `sampled` 字段；②`--negative` 翻转零命中 → `QA_L2_NEG_MISS` exit 1；翻转后仍全绿 → `QA_L2_NEG_NOT_CAUGHT` exit 1；抓到 → `QA_L2_NEG_CAUGHT` exit 0（负控流程成功的语义，docstring 写明退出码约定）。

**修复前实测症状（真 blend + 零采样破坏副本）**：
```
QA_L2_OK   / {"fail":[],"warn":[L2_SAMPLE 未采到拱腹面],"ok":true}   / exit 0
```
**修复后同一破坏**：
```
QA_L2_FAIL 0 fail, 1 skip / {"fail":[],"warn":[],"skip":[L2_SAMPLE skip≠通过],"ok":false,"sampled":0} / exit 1
```
**正检无回归 + 负控真实有效（真 blend）**：
```
正检:   QA_L2_OK, sampled=494, skip=[], exit 0
负控:   翻转 10 面 → QA_L2_NEG_CAUGHT (10/494 坏面全部被抓), exit 0
脱靶:   零采样副本负控 → QA_L2_NEG_MISS 拒绝静默通过, exit 1
```

## I5★ 恒真检测改双向 — `fd1c407`

**改了什么**：
1. `assert_no_always_true(..., require_baseline_green=True)`：默认断言合法基线零 fail——"基线即红"的过度约束判据（MET_TAPER 原病 / I1 同款机制）直接报错；`require_baseline_green=False` 为显式可见豁免。
2. 新增 `assert_criterion_alive(check, f, codes, ...)` 逐判据入口：codes 必须显式给出该判据声明的**全部** fail 代码，死判据（无破坏可触发）必须报错；`codes=None` 聚合级会被活判据杀伤记录掩盖——此限制在 docstring 写明为文档化限制，点名入口为强制出口。已导出 `bridge3d.assert_criterion_alive`。
3. `default_corruptions` 增破坏轴：`scale8` 高倍率（高净空桥 SPRINGER 类）、`type:N_SPAN_float/bool`、`shape:{SOURCES,RESEARCH_DONE,RELATIONS}_non_dict/nonbool`、`shape:{可选条目}_nonnum`、逐条关系独立恒假破坏。
4. `imp_sources_cover / imp_grades_legal / imp_assumptions_isolated` 对形状非法 SOURCES 降级 skip（不得崩溃，形状由 IMP_REGS_SHAPE 报告）。
5. 测试：六构型 × 16 条 L1 判据 + imp_relations 动态代码的**逐条显式点名审计**（`test_each_criterion_alive_on_every_morphology`，约 96 例）；事实层 10 校验器 × 显式点名；工具层新测试（基线即红拦截 / 豁免可见 / MET_TAPER 原病复刻在等宽桥基线被拦 / 死代码点名报错 / 新破坏轴存在且类型安全）。`test_no_project_literals` 白名单增 `8`（scale8 倍率，逐条注释）。

**修复前症状 vs 修复后（同一破坏用例，实测）**——"只许半侧表对称奇数孔"的 I1 原形判据：
```
修复前(等价 require_baseline_green=False): 放行, kills = ['ODD_ONLY']      ← I1 就是这样过审的
修复后在 even6(对称偶数孔) 基线拦截: AssertionError: 基线即红: 判据在合法事实上就 fail
修复后在 asym11(不对称)   基线拦截: AssertionError: 基线即红: ...
修复后在 flat3(平桥)      基线拦截: AssertionError: 基线即红: ...
```
死判据（仅 N_SPAN==999999 时红）：
```
聚合级 codes=None: 仍放行(文档化限制) → 逐判据显式点名: 恒真嫌疑: ['DEAD'] 无破坏可触发
```
**真项目端到端**：E30 facts 过双向审计（21 个 fail 代码全部可杀、基线绿）；`imp_relations` 两条自声明关系逐条点名通过。

---

## 顾虑

1. **并发 sibling 与冻结闸门**：另一 worker 正在改 7 个冻结文件（assumptions/bridge_geom2/build_scene2/facts/materials/ortho/qa_bridge，全部 `M` 未提交）且 manifest §9 未同步——主工作树当前 2 个失败全是它造成的。这不是坏事：正是 I2 新闸门在按设计逼它落盘时同步哈希。**主控集成验证应在 sibling 落地并回填 manifest 后跑**；我方四个 commit 在隔离 HEAD worktree 上全绿（除 7 条与本工作无关的 chemistry-video gitignore 环境性失败，主工作树通过）。
2. **`l2_baseline.json` 快照**仍是 I4 改动前的旧形状（fail/warn/ok 三键）。无测试消费它、manifest 未记它哈希，属 T6 历史快照；若 M4 要复用它作对照需按新形状重采。
3. **I3 真渲染端孔余量偏薄**：真渲染 max|Δxc|=0.0181 vs TOL=0.02（端孔受剪影 bbox 端部效应 + 桥台≠墩宽口径差 ~0.0019 影响）。当前 PASS，但若 M3 改端部几何需留意该余量；T7 标定的"可接受 max 0.0000"实际未把渲染自身端孔偏移计入——已在测试 docstring 注明口径。
4. **met_deck_camber 放宽（顶≥端合法）**是 I16 的平桥半边，为 I1 平桥基线所必需；I16 的 `audit(checks=)` 透传与 REQUIRED 拱桥专用字段问题仍在非★清单，未动。
