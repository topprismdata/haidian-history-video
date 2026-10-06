# Task 1 报告: facts.py 本体节骨架 + 来源完备性测试

状态: DONE
Commit: `d413985` (branch `e30-bridge-body`) — `feat(e30): T1 facts骨架+assumptions假设层+来源完备性测试`, 恰好 3 个文件 / 173 行。

## 改了什么

1. **`e30_shikongqiao_video/3d/facts.py`**（新建）— 与简报代码块**逐字节一致**（用 difflib 对简报原文 diff 验证: `facts.py -> verbatim match`）。给定的代码不含注解/match，无需任何 3.9 兼容改动。含 19 个本体常量 + `SOURCES`(19 键) + `RESEARCH_DONE=False`。
2. **`e30_shikongqiao_video/3d/assumptions.py`**（新建）— 同样 verbatim match。5 个假设层参数（BODY_BOTTOM/MESH_TOL/CIRCLE_FIT_RTOL/NSEG_ARC/NSEG_X）。
3. **`e30_shikongqiao_video/tests/test_facts.py`**（新建，`tests/` 目录新建）— 简报只给了骨架；按任务书补全为 8 个测试，并修正简报骨架里的**旧等级集** `{"测绘","文献","实拍",...}` 为 G1 五级+待核 `{"测绘","档案","官方","图像推导","工作值","待核"}`（否则简报自己的测试会对 G1 的 facts 必 FAIL）。加载方式: `pathlib.Path(__file__).resolve().parents[1] / "3d"` 入 sys.path + `importlib.import_module`，无 `qa_facts_import` 之类。

### 8 个测试对任务书 6 条要求的覆盖

| 要求 | 测试 |
|---|---|
| 1. SOURCES 覆盖每个本体常量（漏一即 fail） | `test_every_constant_has_source`；另加 `test_sources_keys_are_live_names` 抓注册表里的死键（旧名 SPANS/HALF_SPANS 类残留） |
| 2. RESEARCH_DONE 初始 False；False 允许[待核]、True 禁[待核]/[工作值]，随旗标变化 | `test_research_done_initially_false` + `test_pending_gate_tracks_flag`（禁用等级集由旗标决定: True→(待核,工作值), False→()） |
| 3. SOURCES 值为 (等级,说明) 二元组、等级合法 | `test_sources_value_shape` |
| 4. SPAN_DISTINCT 9 元、对称展开自洽 | `test_span_distinct_shape_and_symmetric_closure`。算清后才写: sum(9值)=57.9，对称展开=2×57.9−8.5(中央孔只计一次)=**107.3**（=官方总水路），9×PIER_W=9×2.50=**22.5**，107.3+22.5=129.8。断言用 `pytest.approx(abs=1e-9)`。简报的 `sum(SPANS)+15*PIER_W+2*BRIDGE_ABUT` 全桥闭合判据未纳入（T2b 事务） |
| 5. assumptions 名字不得进 SOURCES（G1 分家） | `test_assumptions_not_in_sources` |
| 6. docstring 禁令可执行化 | `test_docstring_carries_bans`（锁 "ESRGAN" 与 "计量"） |

## 测试运行记录（TDD）

**先 FAIL（实现未写，红）：**
```
collected 0 items / 1 error
ERROR collecting e30_shikongqiao_video/tests/test_facts.py
e30_shikongqiao_video/tests/test_facts.py:19: in <module>
    facts = importlib.import_module("facts")
E   ModuleNotFoundError: No module named 'facts'
=============================== 1 error in 0.14s ===============================
```

**后 PASS（实现写入后，绿，= 验收命令原样重跑）：**
```
collected 8 items
test_facts.py::test_every_constant_has_source PASSED
test_facts.py::test_sources_keys_are_live_names PASSED
test_facts.py::test_sources_value_shape PASSED
test_facts.py::test_research_done_initially_false PASSED
test_facts.py::test_pending_gate_tracks_flag PASSED
test_facts.py::test_span_distinct_shape_and_symmetric_closure PASSED
test_facts.py::test_assumptions_not_in_sources PASSED
test_facts.py::test_docstring_carries_bans PASSED
============================== 8 passed in 0.02s ===============================
```

## 判据非恒真验证（负控，throwaway 脚本，未落盘）

4 项负控全部被抓（证明判据在测真东西）：
- SOURCES 删掉 SPRINGER → 核心判据报 `缺来源登记: ['SPRINGER']`
- RESEARCH_DONE 置 True 但保留工作值 → 闸门报 19 条禁用条目
- `MESH_TOL` 混入 SOURCES → G1 分家判据报错
- SPAN_DISTINCT 8.50→8.60 → 闭合断言报 `129.90000000000003 != 129.8`

## 遗留顾虑

1. **`.gitignore` 白名单不含 `e30_shikongqiao_video/3d/` 与其 `tests/`**，本次用 `git add -f` 入库（先例: `3d/refs/*.md` 也是被 ignore 目录下的强制入库文件）。后果: 后来者用普通 `git add` 加 3d/ 下文件会被静默忽略。是否给 `.gitignore` 开 `!e30_shikongqiao_video/3d/**/*.py` 洞由调度者定（本任务 3 文件限制，未动 .gitignore）。
2. 简报 Step 2 的测试骨架等级集是 G1 修订前的旧值（含"文献/实拍"、缺"档案/官方/图像推导"），已按任务书与 facts.py 实际等级集修正；若后续 Task 以简报骨架为"事实"请以本测试文件为准。
3. 简报 Step 4 的 commit 命令漏了 `assumptions.py`（G2/G3 修订后新增文件），已并入同一 commit。
4. 数值零改动：facts 内全部数值与简报逐字一致（含 `BRIDGE_ABUT=1.35` 待 T2b 裁决），未为测试变绿动任何数。
