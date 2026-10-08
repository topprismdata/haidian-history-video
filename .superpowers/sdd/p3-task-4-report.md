# P3 Task 4 报告：渲染侧参数单源 `film_geometry.py`

日期：2026-10-08 ｜ 执行：P3T4Geo ｜ Python 3.9.6 ｜ 计划：`docs/superpowers/plans/2026-10-08-p3-build-film.md` Task 4

## 0. 交付物

| 文件 | 性质 | 内容 |
|---|---|---|
| `e30_shikongqiao_video/3d/film/film_geometry.py` | 新建 | `WEDGE_DROP_M` / `yard_anchor` / `lift_anchor` / `home_position` / `SILHOUETTE_SLOTS` / `CAMERA_TRACKS`（纯函数+常量，blender-free） |
| `e30_shikongqiao_video/tests/test_p3_geometry.py` | 新建 | 计划原文三支 + 合同三支，6 tests |

TDD：先红（`ModuleNotFoundError: No module named 'film_geometry'`）后绿（6 passed）。commit：本文末 §8。

## 1. 接口落点（T5 消费面）

- `WEDGE_DROP_M = 0.04`（模型米）。[工程参数·敏感性] docstring 注明可调范围 **0.02–0.08**（下限以下落架段落感不足，上限以上相对缝宽失真，真缝实档见账 `joint_historical_mm`）；T5 按 `delta_z = -λ*WEDGE_DROP_M` 消费。
- `yard_anchor(stone_id) -> (x,y,z)`：堆场码位 = 行(zone)×列(family) 4 列网格，z=deck_z(x)+1。
- `lift_anchor(stone_id) -> (x,y,z)`：吊运过路点 = 就位位 (x,y) 原地，z=deck_z(就位 x)+2。
- `home_position(stone_id) -> (x,y,z)`：`out/ledger_sequenced.json` transform 前三分量**逐位**（不重算不取整）；未知 id `KeyError`（防静默零位）。
- `SILHOUETTE_SLOTS`：6 位（≤6 合同），pose 词表 `{lever, chisel, crowbar}` 三形制齐备，每位 `evidence` 含 `C:A4`（石作加工链：打荒→錾道→剁斧→扁光，`3d/refs/construction_history.md`）；坐标为 [设计选择]，证据字段如实分层（C:A4 只背工具形制不背站位）。
- `CAMERA_TRACKS`：键恰为 `film_state` phase 三段词表 `{"BUILD","DECENTER","DONE"}`（test 钉死）；BUILD=侧视正射（ortho_scale 165>150 留边）、DECENTER=45°鸟瞰（dy=dz=50 恰 45°）、DONE=侧视缓推（loc_start→loc_end 17m，T5 按 DONE 帧域 lerp）。

## 2. 锚点布局图（说明）

世界系：x 沿桥轴（桥长 150 m，±75），y 横桥向（桥轴 y=0，**北岸取 +y**），z 铅垂（常水位 0）。

```
 俯视（z 向下看，北在上）                        北岸堆场码位（列 y：9.0/11.2/13.4/15.6）
                                                impost slab  ring  wedge
        +y 北岸                                     ↓     ↓     ↓     ↓
   ─────────────────────────────────────        ARCH01 ●────●────●────●        x=-71.03
   │ CHAR01 ●────●────●────●（堆场 4 列/孔）       ARCH02 ●────●────●────●        x=-66.11
   │   ...   17 行随孔展开，x=arch_center_x        ⋮      ⋮                   （行距随孔宽）
   │ ARCH17 ●────●────●────●        x=+71.03     ARCH09 ●────●────●────●        x≈0
   ─────────────────────────────────────        ⋮
   ═══════ 桥体 |y|≤7.3（收分 14.6→6.56）═════    ARCH17 ●────●────●────●        x=+71.03
   ─────────────────────────────────────
        -y 南侧：BUILD 侧视正射机位 y=-85；
                 DONE 缓推 y=-55→-38；DECENTER 鸟瞰 (0,-50,54)
```

- **行**：`x = geom_math.arch_center_x(zone)` —— 石料码在其目标孔旁，吊运动线最短。
- **列**：`col = _FAM_COL[family]`，四族按 **crc32 散列定序**后依次占列 0..3：`impost-step→9.0`、`slab→11.2`、`ring-wedge→13.4`、`wedge-std→15.6`（实测落位）。
- **吊运路径**：yard(x_yard, y_yard, deck+1) → lift(就位 x,y 原地, deck+2) → home(账本 transform)。
- 剪影 6 位：4 位桥面（x=-60/-30/0/+30，z=deck_z(x) 行走面）+ 2 位北岸堆场（y=11，z=0），pose 覆盖 chisel/crowbar/lever。

## 3. 净空检查通过证据（全量数值扫描，非抽样）

判据（合同）：yard/lift 锚点须满足 **|y| ≥ hw(x,z)+0.5m** 或 **z ≥ deck_z(x)+2m**；hw=geom_math.width_at（facts 收分单源）、deck_z=geom_math.deck_z，测试独立 import 反查。

| 项 | 扫描域 | 结论 | 最小余量 |
|---|---|---|---|
| yard y 判 | 全部 17×4=68 网格单元（每 zone×family 抽首块） | **全过**（y 判真过；z=deck+1 构造上不满足兜底判，双断言防兜底掩目标） | |y|−hw(x,z)−0.5 = **+5.220 m** |
| lift z 判 | 全账 **5935** 石逐一反查 | **全过** | z−deck_z(x) = **1.999999999999999 m**（deck+2 精确值，浮点 1 ulp；判据 ε=1e-9） |
| home 逐位 | 随机 100 石（seed=7） | **0 错位**（== tuple(transform[:3]) 逐位） | — |
| 码位不叠 | 任一 zone 内四族码位 | **4 互异**（test 钉） | — |
| 跨进程确定性 | `PYTHONHASHSEED=0` vs `12345` 对照实测 | 锚点逐位同（crc32 纯函数；**禁内建 hash()**——按进程加盐） | — |

净空物理量：yard 列起点 9.0 m > 桥体半宽极值 7.3 m（DECK_DOWN_W/2）+0.5 m 合同余量，码位高度处 hw=3.28 m（收分顶宽），实际横向净距 5.7 m；lift 在桥体正上方走 z 判（y 不避让是设计意图——过路点就是就位位上方）。

## 4. 实现决定与偏差

1. **"facts 的 hw 函数"口径**：facts.py 只有常数，几何纯函数单源在 **`geom_math.py`**（D3 主控裁决层，`deck_z`/`width_at` 自 bridge_geom2 原样搬移、常数全读 facts）。本模块与测试均 `import geom_math`（P2 只读），零几何公式复制。hw ≡ `geom_math.width_at`。
2. **散列叠码消解（实现轮发现）**：族→列用朴素 `crc32 % 4` 会把 `ring-wedge`/`impost-step` 散到同列（同 zone 两族码位**完全重合**成叠码、另两列恒空，首跑实测）。改为**散列定序双射**：族全域按 crc32 排序后依次占列 0..3——仍由散列驱动、跨进程确定，且四族恰占四列。族全域外 KeyError 早爆（网格须随账重排，拒绝静默并列）。
3. **yard family 读账本**：族字段只在账（id 内不含 family），与 `home_position` 共用同一惰性账本索引（单源，不抄 id→族第二套映射）。
4. 测试文件按上下文取独立 `tests/test_p3_geometry.py`（未追加进 test_p3_state.py，更清晰）。

## 5. 全量 pytest 分片明细（沿 T3 口径）

**分母以 --collect-only 实测为准：`pytest tests/ --collect-only -q --ignore=tests/test_p4_section.py` → 498 collected**（= T3 基线 492 + 本任务 6；全收含 P4 section 为 503，P4 线冻结后由主控复核）。范围只取 `tests/`（3d/ 下 `ab_texture_test.py` 为 bpy 直跑脚本，非 pytest 件，不入分母——历轮同口径）。

| 片 | 文件 | 结果 | 耗时 | 通道 |
|---|---|---|---|---|
| 1 | facts / freeze_manifest / l1_body / no_literals / p1_export / p1_families / p1_ledger / p1_masonry2 / p1_printcheck / register | 178 passed | 0.86s | 前台 |
| 2 | p1_scene / p1_slice | 65 passed | 107.2s | 后台（当日通道实测全速，≈T3 的 109.2s） |
| 3 | p2_centering / p2_events / p2_geom_math / p2_ledger_v2 / p2_sequencer | 160 passed | 72.0s | 后台（≈T3 的 74.5s） |
| 4 | p2_full / p2_g3_dag / p2_g3_imbalance / p2_g3_thrust | 71 passed | 121.2s | 后台（≈T3 的 123.6s） |
| 5 | p3_pace / p3_state(8) / p3_verify(4) / **p3_geometry(6)** / p4_scale | 24 passed | 2.94s | 前台 |

**合计 498 passed / 0 红**（= T3 末基线 492 + 本任务 6，口径自洽）。P4 红窗沿先例 `--ignore=tests/test_p4_section.py`。

## 6. 给 T5 的交接注记

- 楔石位移：`delta_z = -state["wedge_lambda"][hole] * WEDGE_DROP_M`（λ∈[0,1]）。
- 相机取位：`CAMERA_TRACKS[state["phase"]]`；DONE 段 `loc = lerp(loc_start, loc_end, 帧进度)`，target 恒定。BUILD 正射注意 Blender 相机 `clip_end` 默认 1000 够用（机位最远 y=-85）。
- 显隐/对拍一律走 `film_state.state_at_frame`（单源），本模块只供坐标/常量；`home_position` 未知 id KeyError 是**预期硬错**（幻影 2004 块有账本位、无日程位，yard/lift 对其仍可调用——如 T5 需要区分，请用 `film_state` visible 集判定，勿在本模块加日程语义）。
- `SILHOUETTE_SLOTS` 的 pos 的 z 分量已按 deck_z(x) 就地取值（import 时计算，确定性同函数）。

## 8. Commit

`feat(e30): P3-T4 渲染侧参数单源(锚点/λ下沉/机位/剪影位)` —— 仅含上表两文件（P4 线并行，未触碰他线文件；报告本身不入库，沿 T1–T3 先例）。
