# P2 遗留票（P2 整支终审 FIX-FIRST 轮开立, 2026-10-08）

来源: P2FinalReview 八系统面（终审 merge_ready 第 2 条"缺口升级为带判据的票"）。
主控裁决: 本轮只开票不扩轮; 每票带可执行验收判据, 禁散文式"记账"。

---

## 票1 FILL/肩背胞几何支承判据缺位（终审面1, 优先级最高）

**现状**: 入日程 3931 石的支撑边类型集 = {('stone',):3246 肩背胞,
('centering','stone'):193 券石, ('foundation',):492 墩肩}。non-RING 全部
是"单结点、值 1.0、结点 x=本石置放 seq"的**单点自持边** → Σ≥1 恒真,
①门结构上不可能对肩背/FILL 证伪（edge keys 仅 {type, capacity_curve},
无支撑对象引用字段）。终审实测: 把 ARCH05.FILL 最低 CORE(z=-2.200) 与
最顶 BACK(z=5.905) 置放时刻对调并同步移动曲线结点 → check_sequence
0 错、gate_dag 0 违例——**对调置放时刻全门无觉**。券石侧有牙
（摘 centering 边 → 8 违例点名）, 端到端负控已在测
（tests/test_p2_full.py::test_e2e_support_edge_removal_cli_blocks_delivery）。

**口径现状（已收口, 见 spec §5）**: "每石就位支撑已存在"=构造自证
（z 升序）+事件时序（R5A_PREREQ/R0_STONE_ONCE）, 非几何支承校验。

**验收判据（二选一, 写死）**:
1. 补 ① 的支承在位判据: 对调任意两置放时刻（同族或跨族, 含 FILL）→
   某门必红且点名两石 —— 注入负控入 tests/ 后方可宣称支承校验;
2. 或维持口径文档"已证范围"表述（构造自证+事件时序）, 并在本票关闭
   时复核 spec §5 / narration_beats 口径注记 / p2-progress 终态节三处
   无路线图原句的无条件引用。

**owner**: P3 开工前主控裁决取舍。

---

## 票2 R5b 填筑期荷载未评（终审面3, ④评窗缺口量化）

**现状**: ④门只评 R5a 锁固肩（1342 条）+ RING 顶载（Σ=1911.9 单位）;
R5b 填筑（CLEAR 后置放的 SPANDREL/BACK/CORE 胞）总重 **9163.9 单位
未评 = 已评顶载的 4.8 倍**（=R5a 带重 1137.6 的 8.1 倍）; 单孔最大
ARCH09=850.9, 而该孔邻墩典型 V≈250。填筑荷载经楔座/拱背传墩的路径
未建模, ④读数不含此项。

**验收判据**: ④门增 R5b 评窗（或出独立 ④b 填筑期门）: 逐 stage 填筑
增量荷载入墩静力账, 产出"填筑期 util 表"; 交付物=报告节 + 至少 1 条
变异负控（抽掉单孔最重填筑胞 → util 读数严格变化, 篡改可见）。
禁止: 只在报告文字里记"未评"而无读数表（=本票开立前的状态）。

**owner**: P3 前裁决（若 P3 叙事需要填筑期动画则升级为前置）。

---

## 票3 IMPOST 恒 0 重（终审面3, 潜在而非现错）

**现状**: 492 块 IMPOST（墩肩/拱座）params 无 'd' 断面键 → 计重口径
下体积 0; 族网格 |signed_volume| 合计 16.59。sequencer.stone_weight 与
g3_check._stone_weight 同式 → 双实现互证不报警。当前 ③④ 不消费
IMPOST 重（无现错）; fail-loud 哨兵已落
（g3_check._stone_weight 对无 w/h/d 石 raise; 测试钉
test_p2_g3_thrust.py::test_impost_never_in_load_integral_and_weight_fails_loud）。

**验收判据**: 给 IMPOST 计重口径（断面 d 实测或族体积单源接入）→
sequencer.stone_weight 与 g3_check._stone_weight 同轮改（保持同式互证）,
真账重跑全门绿; 同时退役"前提失效: IMPOST 已补 d 键"测试钉（同轮改）。
禁止: 只改一处实现（互证失效）。

**owner**: P3/P4 前任意轮, 与票2 联动（墩肩重入墩静力账时必须先解此票）。

---

## 票4 券架几何注册表消费细则（P3 交接, spec §6）

**现状（P2 已交付的最小落盘）**: event_ledger.json `meta.centerings`
17 副 [{id, zone, arch_idx, xc, family="wood-<zone>"}]（生成器单源取数,
纯度红线=只进事件簿 meta, 石账零触碰; 测试钉
test_p2_full.py::test_event_ledger_artifact_valid_and_idempotent）。
**几何本体（parts/footprint/wedge_events）仍不落盘** —— P3 若按 spec §6
"消费券架对象"需 import centering.build_centering_for_arch 现算
（run_g3 原 centerings 形参接口位已删, docstring 注"接口位→票4"）。

**验收判据**: P3 开工首周产出消费细则: (a) 显隐/动画用现算 or 落盘
bmesh, 二选一并写进 P3 交接; (b) 若落盘, 注册表从 5 字段扩到几何字段
时 sidecar+_SIDEAR_EXPECTED 钉同轮扩（BLK-1 纪律）; (c) centering 支承
在位判据（若做）归票1 不在本票。

**owner**: P3.
