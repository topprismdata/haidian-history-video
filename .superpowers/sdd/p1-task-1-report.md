# P1 Task 1 报告：ledger.py 数据模型与 id 纪律

- **状态：DONE**
- **Commit：`704b232`**（分支 `e30-bridge-body`，仓库根 `/Volumes/macstudio/video-projects/`）
  - 信息：`feat(e30): P1-T1 ledger数据模型(拓扑id+uuid+谱系+证据级+两缝分离)`
  - 2 files changed, 133 insertions：`e30_shikongqiao_video/3d/ledger.py`（新）、`e30_shikongqiao_video/tests/test_p1_ledger.py`（新）
- **测试输出末行：`4 passed in 0.02s`**（主树 `python3 -m pytest tests/test_p1_ledger.py -q`，Python 3.9.6 / pytest 8.4.2）

## TDD 五步执行记录
1. 隔离树 `/tmp/e30_p1/e30_shikongqiao_video/`（tests 全量 + 3d 仅 *.py，63 个；ledger.py 纯 stdlib 无需 refs）逐字写入 brief Step 1 测试。
2. 隔离树跑测试确认失败：`ModuleNotFoundError: No module named 'ledger'` ✓（与 brief 预期一致）。
3. 逐字写入 brief Step 3 实现（未改动任何一行逻辑）。
4. 隔离树跑测试：`4 passed in 0.01s` ✓。
5. 同步回主树（`cmp` 逐字节一致），主树重跑 `4 passed`，仓库根 commit。

## 自审发现
1. **brief 自身不一致（Interfaces 行 vs 逐字代码）**：Interfaces 写 `family_key(zone, role, course, block)`、`new_stone(zone, role, course, block, ...)`（4 拓扑参数），但 Step 1 测试与 Step 3 实现均为 5 参数 `(zone, face, role, course, block)`（face=EAST/WEST）。以逐字代码为准执行（测试即契约）；`_ID_RE` 含 `(EAST|WEST)` 段，与 5 参数签名自洽。**下游 task（T2 families / T3 masonry2）必须按 5 参数签名调用**。
2. **负控制已内建**（符合全局约束"新判据必须带负控制"）：`test_validate_rejects_coord_in_id_and_bad_evidence` 破坏 id（坐标混入 `C12.07x3.21`）与 evidence（`guess`），validate 分别报 `ID_COORD`/`EVIDENCE`——破坏能被抓住。
3. **Python 3.9.6 纪律合规**：全程 `Optional[X]` + type comments，无 `X | None`，无 `match`。
4. **几何冻结项零触碰**：仅新增两文件，未触碰 facts.py/砖谱 JSON/任何既有代码。
5. **roundtrip 语义确认**：`save_ledger`（sort_keys+indent=1）→ `load_ledger`，`None→null→None` 稳定，`clearance_manufacturing_mm is None` 过 JSON 后仍成立。

## 顾虑
- validate_ledger 的部分分支未被 brief 逐字测试覆盖：`ID_DUP`、`CLEARANCE_PREMATURE`、`SUPPORT_TYPE`、`SCHEMA`/`META_MISSING`，以及 `query` 无过滤路径。遵守"照抄执行"纪律未擅自扩测试；这些分支属逐字实现原文，建议后续 task（如 T5 printcheck 或治理套件扩充）按需补负控制覆盖。
- 本报告文件与 brief 文件均未入 commit（brief Step 5 仅指定两个代码文件）；是否入库由主控决定。

## 修复轮（T1 审查裁决落地）

- **Commit：`50e3662`**（分支 `e30-bridge-body`）`fix(e30): P1-T1审查修复(uuid主键+负控补全+fullmatch+原子写+鲁棒)`，2 files changed, 136 insertions(+), 15 deletions(-)。仅动 `3d/ledger.py` 与 `tests/test_p1_ledger.py`。
- **TDD**：先写 11 条新测试（红：`6 failed, 9 passed`——I2 各条对既有分支本就应过，红的是 I3/I4/M1/M4 六项：UUID_DUP、UUID_BAD、SUPPORT_EDGE_SHAPE(AttributeError 实测复现)、ID_MISSING、尾随换行 id、原子写截断），后改实现（绿）。
- **逐条落地**：
  1. **I2 负控补全**：ID_DUP / SUPPORT_TYPE / SCHEMA+META_MISSING / CLEARANCE_PREMATURE 各一条最小破坏用例（EVIDENCE 原已有）；另加正对照 `test_validate_positive_control_clean`（合规账目零错误，防新增 UUID 检查误伤 `new_stone` 产物）。
  2. **I3 uuid 主键**：validate 增 `UUID_DUP`（两石同 uuid）与 `UUID_BAD`（不可解析或非 v4，`_is_uuid4` 判 `UUID(s).version == 4`）；缺 uuid 键亦落 UUID_BAD。配 `test_neg_uuid_dup/_bad`。
  3. **I4 鲁棒**：support_edges 非 dict 元素 → `SUPPORT_EDGE_SHAPE` 不再抛 AttributeError；stone 缺 `id` 键 → `ID_MISSING uuid=…`（跳过 ID_COORD/ID_DUP 判定，空串不入 seen）；`query` 三过滤改 `.get`，缺 id 石不 KeyError。配 `test_neg_support_edge_shape_no_crash`、`test_stone_missing_id_validate_and_query_robust`。
  4. **M1**：`_ID_RE` 去 `^…$` 改 `fullmatch`（`$` 容忍尾随换行 → `'…B07\n'` 现被拒），配 `test_id_fullmatch_rejects_trailing_newline`。
  5. **M4**：`save_ledger` 原子写——同目录 `tempfile.mkstemp` 写入后 `os.replace`；异常路径 unlink 临时件后重抛。配 `test_save_ledger_atomic_survives_dump_failure`（monkeypatch `json.dump` 抛错，断言原文件逐字节未截断、无 `.tmp` 残留；旧实现此测试必红）。
  6. **M3**：测试文件删未用 `json` import；`pytest` 因新增用例使用 `pytest.raises` 而保留（`os/sys/uuid` 原已使用）。
- **回归**：单测文件 `15 passed in 0.01s`；全量 `cd /Volumes/macstudio/video-projects/e30_shikongqiao_video && python3 -m pytest tests/ -q` → 末行 `82 passed in 0.54s`（含既有治理套件与 T1/T2 测试，Python 3.9.6）。
- **兼容性自查**：`grep` 全仓仅 `tests/test_p1_ledger.py` import ledger，无其他消费方受错误消息/签名变化影响；错误码前缀（ID_DUP/SUPPORT_TYPE/…）保持不变，新码（UUID_*/SUPPORT_EDGE_SHAPE/ID_MISSING）为增量。
