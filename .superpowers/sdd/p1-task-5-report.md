# P1 Task 5 报告: printcheck.py 验证器

- **状态**: 完成
- **Commit**: `2ca3434` `feat(e30): P1-T5 printcheck(流形/自交/壁厚@scale/穿透)`（branch `e30-bridge-body`，仅含 3d/printcheck.py + tests/test_p1_printcheck.py 两新文件，426 行）
- **测试末行**: `107 passed in 0.57s`（`cd e30_shikongqiao_video && python3 -m pytest tests/ -q`；基线 90+ 兄弟 task 并行新增，本 task 贡献 13 条全绿，隔离树 /tmp/e30_p1 同为 13/13）

## 交付内容
- `3d/printcheck.py`：`check_stone(verts, faces, scale, min_wall_mm) -> {ok, issues, volume_m3}`；`gap_check(entry_a, entry_b, tol_mm, scale) -> [str]`；`volume()` 辅助。判据：流形=面拓扑每边恰 2 面（不依赖法向，遵 T2 审查裁决）；THIN_WALL=任一 bbox 维×scale×1000 < min_wall_mm（brief 公式，严格小于）；自交=逐面 AABB 粗筛 + numpy 手写精检（共面对按多边形边界横穿/严格包含判，非共面对按严格跨越+交线段相交判）；PENETRATION=AABB 重叠深（模型 mm）> tol_mm。纯 numpy，无第三方几何库，Python 3.9.6（type comment 风格，无 `X | None`/match）。
- 测试 13 条：brief 逐字 4 条 + 自交正例（针穿盒、共面交叉、共面包含）+ 负控制 4 条（共面叠置接触不报、偏置 T 形部分接触不报、壁厚恰在 1.2mm 阈值不报、贴合/分离/容差内不报 PENETRATION）+ 体积。

## 自审（要点）
- **单位语义经 brief 测试钉死**：tol_mm 是模型毫米（0.999 间距=重叠 1mm 模型 > 0.5mm 必报）；若按打印毫米解释该测试不可能通过。scale 仅用于消息中打印当量换算。
- **自交语义边界（关键设计决定）**：共面接触（叠置/共边/偏置 T 形交界）一律不报——零体积重叠即接触。扇形三角化的对角线是伪边不参与共面判（否则叠置两石因对角线交叉必误报，已由负控制抓住并修复）。面级判据无法区分「接触」与「轴向齐平实体互穿」（二者共面对 2D 构型全同），后者归 gap_check 的 AABB 判据（test_penetration 的 0.999 偏置即此构型，能抓住）。
- **负控制齐备**（全局约束）：NON_MANIFOLD/THIN_WALL/SELF_INTERSECT/PENETRATION 四判据均有「干净输入不放行」与「坏输入必报」双向钉死；阈值边界（=1.2mm 不报）验证严格不等号。
- 隔离树 TDD 全程：RED（ModuleNotFoundError）→ GREEN → 主树全量回归 107 绿。

## 顾虑（不阻塞）
1. `check_stone` 按凸平面面片假定设计（族库满足）；非凸面片的共面路径可能漏检/误判，当前 ledger 生成链不会产生。
2. O(n²) AABB 粗筛契约限逐石（数百面）；勿直接喂整桥合并网格（docstring 已注明规模契约）。
3. `volume()` 取绝对值（族库绕向朝内），不作绕向判据；若未来需要绕向检查需另行立判据+负控制。

## 复审收口

- **状态**: M1(CRITICAL)/M2(HIGH)/M3(HIGH) 三点全关闭
- **Commit**: `aad7779` `fix(e30): P1-T5复审收口(gap闸门NaN/平面阈1e-5导出安全/薄壁代理绕向自适应)`（仅 3d/printcheck.py + tests/test_p1_printcheck.py）
- **测试末行**: `147 passed in 0.74s`（`cd e30_shikongqiao_video && python3 -m pytest tests/ -q`；基线 140 → +7 新测试；本文件 35→42 全绿，既有 35 条零删改语义）。TDD 全程：新增 7 条先跑红（NaN-entry/nan-transform 红在 `ok=True` 静默放行、empty-entry 红在 `ValueError: shapes (0,) (3,)` 崩、M2 两条红在假报 `dev=8.575e-08 > 9.900e-10`、M3 两条红在薄板 0 报 + 空腔假报 `#5/#7 t=1.000mm`），实现后全绿。

### M1 gap_check 闸门（CRITICAL）
`_xform` 之前/之后、min-max 之前加三道结构化闸门：空顶点表 → EMPTY_MESH（先于 xform，否则零尺寸数组广播崩）；ledger transform 6 元组整体 `isfinite` → INVALID_COORD（先于三角变换，免 `np.cos(Inf)` RuntimeWarning）；旋后顶点 `not np.isfinite(Va).all() or not np.isfinite(Vb).all()` → INVALID_COORD（detail 带非有限计数）。旧路径真伤：NaN 重叠比较 `(nan>0)=False` → `not all` → **静默 ok=True**，真实 0.2m 穿透被放行。留证输出行：
```
M1 nan-entry:     {'ok': False, 'issues': [{'code': 'INVALID_COORD', 'detail': '1 non-finite coord(s) (NaN/Inf) post-transform, A=0 B=1'}]}
M1 empty-entry:   {'ok': False, 'issues': [{'code': 'EMPTY_MESH', 'detail': 'A: 8 verts/6 faces; B: 0 verts/0 faces'}]}
M1 nan-transform: {'ok': False, 'issues': [{'code': 'INVALID_COORD', 'detail': '1 non-finite transform value(s) (NaN/Inf) in ledger 6-tuples'}]}
```
配测 3 条：`test_gap_check_nan_entry_rejected`（NaN 顶点+真实重叠 0.2m → INVALID_COORD 非 ok=True 且不到 PENETRATION 分支）、`test_gap_check_empty_entry_does_not_crash`、`test_gap_check_nan_transform_rejected`（rz=NaN 被 6 元组整体 isfinite 抓到）。

### M2 平面性绝对阈（HIGH，复审者方案①）
`_ABS_PLANAR` 1e-12 → **1e-5**（0.01mm 模型当量）：导出侧坐标量化（%.6f 截断/float32 回读）在斜置面上产生 ~1e-8 量级非平面偏差，旧阈必假报 NON_PLANAR_FACE；新阈放行量化噪声、保留真折叠检出。回读留证输出行（wedge-std 绕 Y 45°）：
```
M2 round6:  dev=8.575e-08 -> NON_PLANAR=False ok=True
M2 float32: dev=5.111e-09 -> NON_PLANAR=False ok=True
M2 apex=-0.5   dev=4.082e-01 reported=True | 1 face(s), e.g. #1 dev=4.082e-01 > 1.000e-05
M2 apex=-0.25  dev=3.313e-01 reported=True | 1 face(s), e.g. #1 dev=3.313e-01 > 1.000e-05
M2 apex=1e-07  dev=2.357e-01 reported=True | 1 face(s), e.g. #1 dev=2.357e-01 > 1.000e-05
```
折叠三档 dev=0.235~0.408m 仍必报（既有 `test_non_planar_folded_box_reported` 原样保留为回归锚）。配测 2 条：`test_planarity_export_round6_readback_negative`、`test_planarity_export_float32_readback_negative`。

### M3 薄壁代理绕向自适应（HIGH）
新增 `_signed_volume`（`_volume = abs(其)`）；check_stone 在调用代理前判：`NON_MANIFOLD`/`MULTI_SHELL` 均未报（流形+单域，带符号体积才代表整网格绕向）且 `_signed_volume > 0`（外翻）→ `_thin_wall_proxy_issues(..., outward=True)` 对法线统一取反，复用内翻语义；否则维持现行为（开放网面/多壳符号无全局意义）。修复的双向失效：外翻时真薄壁「互相朝向」全落空（假阴性）、空腔对壁反被当薄壁（假阳性）。外翻负控留证输出行：
```
M3 outward-thin-slab: ['pair faces #0/#1 t=0.600mm < 1.200mm @scale 1/50 (proxy)']
M3 outward-5cm-slot:  THIN_WALL=False issues=[]
```
（修复前同一输入分别为 `[]` 与 `pair faces #5/#7 t=1.000mm` 假阳。）配测 2 条：`test_thin_wall_proxy_outward_winding_still_reported`（整体反绕 45° 薄板仍报 THIN_WALL 且走 pair 代理）、`test_thin_wall_proxy_outward_winding_cavity_not_flagged`（5cm 缝厚件内翻/外翻双向均不报空腔对壁）。

### 契约影响
- 族库/棱柱全体内翻（实测 slab=-0.5、wedge=-0.4、prism=-2.4 带符号体积）→ outward=False → T4/T6 现依赖路径行为逐字节不变；全量回归 147 绿即证。
- 模块 docstring 同步更新（C1 阈值语义、M1 闸门、M3 绕向自适应各一段）；无新依赖、Python 3.9.6 纯 numpy。
