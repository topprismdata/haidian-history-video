# P2-T5 报告: g3_check.py — G3 第一层(①支撑活跃) + snapshot 状态机

日期: 2026-10-07 | 分支基线: 0e3fe56 (T4 修复轮终态) | Python 3.9.6

## 1. 交付物

| 文件 | 内容 |
|---|---|
| `3d/g3_check.py` (新) | `Snapshot`/`snapshots()`/`check_dag()`/`check_dag_all()`/`holes_timeline()`/`derive_in_void()`/`double_model_scan()`/`run_g3()` |
| `tests/test_p2_g3_dag.py` (新, 17 测) | 正控 5 + 五负控(含 3b/5b 变体) + 机制闸 4 + 真账全链(存在性 skip) |
| `.superpowers/sdd/p2-task-4-report.md` | §6.6 加一行 superseded 注(W2 顺手项) |

Commit: `feat(e30): P2-T5 G3①支撑活跃+snapshot状态机(独立Σ交叉验证)`

## 2. 判据实现与语义决策(记录在案)

1. **独立 Σ 交叉验证**: `check_dag` 在置放与曲线结点处核 Σcapacity≥1,
   独立重写,**不 import sequencer**(含传递闭包, `test_g3_independent_no_
   sequencer_import` 以子进程钉死)——与 T4 的 `_check_capacity_invariant`
   构成两实现互证(T2 跨源钉哲学)。覆盖论证与 T4 同理但独立推导:
   capacity_curve 分段线性 ⇒ Σ 在相邻结点间线性 ⇒ **每个结点+每次置放**
   处核即覆盖连续全程。每个结点 x 都是独立核点(`dirty: {sid: [x,...]}`,
   同事件多结点逐一核, 端点全覆盖)。
2. **增量性能**: 每边结点入事件驱动小顶堆 `(x, sid, edge_idx)`, 推进到
   seq 时弹尽 `x<=seq` 并在该结点 x 处精确重估 —— 绝不每事件全扫
   (7.9M 点教训)。容量缓存 `capacity[(sid,i)]` 是"最近结点处份额"视图;
   精确插值一律现调 `L.edge_capacity`(荷载分担份额语义, 裁2 单源)。
3. **生命周期 as-of-x**: 立架/合龙/落架/拆架以 recorded seq 参与比对
   (`close is None or x < close`), 不受结点迟到影响; RING 三闸
   (合龙前 centering>0 / 合龙前自持=0 / 置放不先于立架)全部按 x 时点判定。
   立架锚 = 本孔首个 `HOLD_EVENT(stone_id=="CEN-"+hole)`(事件词表无
   ERECT 类的唯一合法形态, T4 交接 §6.5)。
4. **R6 独立重建(负控⑤)**: `holes_timeline` 从裸事件流重建 per-hole
   生命周期, 落架事件处自核前视 1 —— 每个既有邻孔须 ≥ 合龙持荷
   (`_supported_at`: close 已发生 ∧ (close,dstart) 窗内已有 HOLD 且其
   seq≤当前, 与 `derive_frontier` 的 CLOSED_SUPPORTED 语义同形但独立实现);
   禁相邻孔同落架。邻接域 = 事件孔 ∪ 石账孔排序表(空档孔参与判, 防
   "跳孔从空档漏过")。**不吃 sequencer 的 frontier_trace/derive_frontier**。
5. **幻影残留闸(双保险)**: in_void 单源复用 `build_scene2.classify_stones`
   (与 sequencer/_in_void_ids、excluded_ids.json 同一管线; 代理浅拷贝防
   clipped 标污染), 判红与拒收逻辑独立 —— 任何事件引用 in_void 石即
   `DAG_PHANTOM_IN_VOID`, 且 present **拒收**该石(集合不变量字面成立,
   即便上游漏滤也不扩散)。真账推导集与 `excluded_ids.json["in_void"]`
   2052 id **逐位相等**(常驻断言)。
6. **W1 不判红**: rbo 占位石单自持边 Σ=1.0 合规(真账测逐石逐结点核
   Σ==1.0), gate_dag 对它们零输出; 只进 `double_model_placeholders`
   清单(id+吞没率)供 P3 视觉隐藏。

## 3. 性能(真账 5935 石 / 4070 事件 / 4076 边)

| 量 | 实测 |
|---|---|
| `check_dag_all` 全程(含 in_void 推导) | **2.63s** (<10s 闸 ✓) |
| 其中 snapshot 流 + check(纯增量路径) | 0.06s |
| in_void 推导(classify_stones, 5935 石) | ~2.5s(可传 `in_void=` 复用) |
| 石级复核点 | **6,199**(=3883 置放 + 2,316 置放后曲线结点; 另 4,076 个迟到/同步结点由置放步精确插值覆盖, 不另设核点) —— **勘误(W-3)**: 原载"10,543(=3883+~6,660)"不可复现(全账曲线上不同结点总数仅 6,392), 系迟到结点内联实现更新前的观测残留, 以本行落盘 `stats.n_stone_checks` 为准(T5 修复轮实测 6,199, `n_tail_checks=0` —— 真账结点皆真实事件 seq, 流尾排空零开销) |
| 微账 103 事件 | 0.026s |

> **数字纪律(T5 审查 W-3 后增补)**: 本报告及后续任务报告的一切计数一律
> 从代码 stats 落盘字段取(`n_stone_checks`/`n_snapshots`/`final_present`
> 等), 会话内观测值不得直接入文; 报告即交付物, 数字须与落盘代码对账。

## 4. 五负控(全部恰红, 微账 ARCH01-03)

| # | 注入 | 实测违例码(计数) |
|---|---|---|
| ① | 删 RING 石 centering 边 | `DAG_UNSUPPORTED`×5 + `DAG_NO_ACTIVE_SUPPORT`×2 + `DAG_RING_NO_CENTERING`×1, 全部点名该石 |
| ② | RING PLACE 排到立架前 | `DAG_RING_BEFORE_ERECT`×1(点名石+erect 未发生) + 左钳连锁 UNSUPPORTED/NO_ACTIVE/NO_CENTERING |
| ③ | 自持 stone 边提前衰减 | `DAG_UNSUPPORTED`×5, **Σ=0.75/0.5/0.25/0.0 逐档可见**(恰在 WEDGE/CLEAR 结点) |
| ③b | 自持边合龙前置 1.0 | `DAG_RING_SELFHOLD_EARLY`×1(环未合成不得自持) |
| ④ | in_void 石混入事件流 | `DAG_PHANTOM_IN_VOID`×1 且 present 拒收(终态集不含该石) |
| ⑤ | ARCH03 落架块插到 ARCH02 合龙前 | `DAG_R6_JUMP_DECENTER`×2(孔+邻孔+seq 点名; g3 自建 R6, 非 sequencer 判) |
| ⑤b | ARCH02 落架块插进 ARCH01 落架窗 | `DAG_R6_ADJ_DECENTERING`×1 |

另: 错序流防御 —— 事件 seq 非严格递增直接 `ValueError`(g3 不猜错序流);
全浮动石(边全 0)双码同出(`DAG_UNSUPPORTED`+`DAG_NO_ACTIVE_SUPPORT`)。

## 5. 真账全链结果

- `check_dag == []` —— **4070 事件全 snapshot 零违例**(W1 清单石本就不判红)。
- 终态 present = 3883 入日程石(=T4 meta.n_stones)。
- `holes_timeline` 与 `sequence.json frontier_trace` 逐孔同值
  (RING_CLOSED/DECENTERING/CLEARED at_seq 全等, 常驻断言)。
- 幻影负控(真账): 追加一枚 in_void 石事件 → 恰红。
- in_void 推导 == `excluded_ids.json["in_void"]`(2052, 逐位)。

## 6. W1 双建模债清单(T4 交接 → P3)

扫描口径: rbo 桶(`excluded_ids.json["ring_band_overlap"]`, 182 块)逐石
量 `V(stone∩RING∪)/V(stone)`, **P1 体素单源**(`p1a_slice._voxel_unique_vol`,
2cm 栅格, bbox 预筛, pre-inset), 阈值 ≥0.99, 耗时 ~26s。

**本扫描复现 = 25 块**(24 块吞没率 1.0000 + 1 块 0.9979), 按组展开
(括号内为组内块数, 合计 25; **勘误(S-3)**: 原列表重复计入
ARCH07/11.EAST.{BACK,SPANDREL}.C12.B03 且漏 ARCH07.WEST.BACK.C12.B03,
去重后仅 24≠25):

ARCH07/11.EAST.{BACK,SPANDREL}.C06.{B00,B08}(8),
ARCH07-11.{EAST.BACK,EAST.SPANDREL,WEST.BACK}.C12.B03(15),
ARCH07/11.WEST.BACK.C06.B00(2; ARCH07=0.9979, 余 1.0000)
(完整 id+率以 `run_g3` 报告 `double_model_placeholders` 落盘为准, 幂等可复现)

**与主控口径 28 块的差异说明**: T4 修复轮的 28 系会话内实测未落盘, 不可
逐位复算。本口径在阈值敏感带内的分布: 0.99→25 块, 0.985→28 块(恰差
ARCH06.WEST.BACK.C10.B04=0.9891 / ARCH07.WEST.BACK.C06.B08=0.9870 /
ARCH12.WEST.BACK.C10.B03=0.9860 三块), 0.85→55 块。差异量级与体素栅格
离散化一致(薄片石 h=0.05m, 单格翻转 ≈0.3-0.5%)。**未为凑 28 放宽阈值**
—— 判据先行、数字后置; P3 隐藏处置建议以本扫描落盘清单为准(可复现),
如主控坚持 28 口径, 将阈值参数定为 0.985 即可重现, 无需改代码。

## 7. 给 T6/T7 的扩展点

- **快照面**: `snapshots(events, ledger)` 逐事件产出 `Snapshot`
  (seq/present/capacity/by_hole/holes); 单对象复用, 留存用 `snap.copy()`
  (深拷贝集合, 共享只读边表)。③压力线/④推力包络在目标 seq 处
  `copy()` 即得该时刻全部已砌石与支撑份额。
- **报告串接**: `run_g3` 返回 dict, `gate_dag` 节已就位; T6 加
  `gate_stress`、T7 加 `gate_thrust` 同形节即可(键即扩展点, 无需改
  既有节)。`holes_timeline`/`stone_edges`/`derive_in_void` 均为可独立
  调用的纯函数。
- **石重**: ①层无需; T6 需要时走 `sequencer.stone_weight` 同源路径
  (`export_print.signed_volume`×密度), 禁第二套。
- **阈值**: 吞没阈值 `SWALLOW_THRESHOLD=0.99` 与 R6/Σ 容差 `TOL=1e-9`
  均为模块常量, 敏感性可在报告层扫描。

## 8. 回归与遗留

- 全量 `python3 -m pytest tests -q`: 基线 392 绿 + 本任务 17 = **409 passed**
  (真账全链 skip 语义保持: 工件不在盘上时 fail-on-skip)。
- 已知边界: 迟到结点(x<置放)只改容量缓存, 核点仍=置放 seq —— 石只在
  present 后受核; 非事件 seq 的结点由堆在下一事件弹出并按结点 x 精确核。
- 遗留(主控裁决项): W1 口径 25(≥0.99) vs 28(≥0.985) 取哪个作为 P3 处置
  清单的正式口径(两口径都可复现, 见 §6)。
