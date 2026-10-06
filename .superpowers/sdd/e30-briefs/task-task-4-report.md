# Task 4 报告: bridge_geom2 从 facts 取数（消灭字面尺寸）

**Commit**: `78c3cc3`（e30-bridge-body 分支）— 3 files: `3d/bridge_geom2.py`、`3d/assumptions.py`、`tests/test_no_literals.py`

## 测试

`python3 -m pytest e30_shikongqiao_video/tests/ -v` → **37 passed**（原 35 条全绿一条不少 + 新增 2 条无字面测试）。

## Blender 冒烟

`blender -b --factory-startup --python build_scene2.py` → `SAVED v2`，`grep -cE "Error|Traceback"` = **0**。（仅既有 DeprecationWarning: World.use_nodes，与本次改动无关。）

## 几何未变证明（接线 = 换数据来源，必须逐点相同）

方法：改动前后各跑一次 dump（同一脚本，Blender 内 import bridge_geom2 构建两个 bmesh），对顶点坐标排序后 sha256，并比对计数/包围盒/关键标量。**三次比对（头部接线后、__main__ 修复后）`cmp` 均字节相同**：

| 特征 | 重建前（字面量版） | 重建后（facts 版） |
|---|---|---|
| 桥体 verts / faces | 964 / 960 | 964 / 960 |
| 桥体 bbox | x[-75,75] y[-7.3,7.3] z[-2.2,7.75] | 同左 |
| 桥体顶点 sha256(前16) | e8cd1cedf2146179 | e8cd1cedf2146179 |
| 挖除体 verts / faces | 1530 / 799 | 1530 / 799 |
| 挖除体顶点 sha256(前16) | 5721bfd7b6dee604 | 5721bfd7b6dee604 |
| PIER_X[0] / PIER_X[-1] | -74.325000 / 74.325000 (n=18) | 同左 |
| SPANS 求和 | 107.3000 (n=17) | 同左 |
| deck_z(±75/0) | 5.05 / 7.75 | 同左 |
| BRIDGE_ABUT / BRIDGE_ABUT_TARGET | 1.35 / 2.00 | 1.35 / 2.00 |

## 字面量处置清单

**进入 facts 的：无新增。** 所有本体尺寸（BRIDGE_LEN/N_SPAN/DECK_*/SPRINGER/ARCH_RATIO/RING_T/PIER_*/BRIDGE_ABUT/SPAN_DISTINCT/DECK_Z_AT_PIER）Task 1/2 已全部登记 facts，本任务纯消费；`facts.py` 零改动。

**改为推导（不进白名单的本体尺寸残余）：**
- `deck_z(75.0)`、`range(-75,76)`（自检）→ `half = BRIDGE_LEN / 2.0` 推导
- `150.0`、`75.001`（__main__ 闭合/端点自检）→ `BRIDGE_LEN` 推导。**这两处由负控制测试 `test_no_literal_equal_to_any_fact_value` 抓出**（报 `(150.0, ['BRIDGE_LEN'])`），证明该测试非恒真。

**留在白名单（实现参数，逐条注释在测试内）：**
- `0.01` 自检断言容差(1cm)；`0.001` 端点包围盒浮点余量(1mm) — 验证 epsilon
- `0.8` 券洞挖除体向下超出 BODY_BOTTOM 的贯通余量
- `0.05` 挖除体横向半宽余量（0.80 会切穿侧墙，"黑横杠"bug 已实测复现）
- `1.4` 挖除体 y 向拉伸宽度系数 `DECK_DOWN_W*1.40`（无量纲贯通系数）

## 偏离简报的一处（已按硬约束裁决）

`build_scene2.py:310` **活跃使用** `G.BRIDGE_ABUT_TARGET`（桥台加长"第4刀"），而简报替换块未含该名、facts 亦无此名、且 facts.py/build_scene2.py 均禁改。处置：值 `2.00` 落 `assumptions.py`（G1 分家的"建模假定"归处——它是 T2b 未裁决的 GPT v4 提案值，非文物事实，assumptions 头注"改动须记录"以行内注释履行），bridge_geom2 以 `BRIDGE_ABUT_TARGET = _A.BRIDGE_ABUT_TARGET` 同名透传。属性值不变 → 几何逐点相同已证。T2b 裁决后只改 assumptions（或迁 facts）一处。

## 删除的内容

头部字面常量区、"券形定论"注释块（出处已在 facts.py SOURCES + refs/FACTS.md L22 保留）、`HALF_SPANS`（更名 SPAN_DISTINCT，17 孔 = 9 值×2−1）、旧 `BRIDGE_ABUT = 1.35` 字面行、`BRIDGE_ABUT_TARGET = 2.00` 字面行。SPANS/PIER_X 递推与 `w = BRIDGE_ABUT if i in (0, N_SPAN) else PIER_W` 未动；docstring 改为"参数来自 facts.py（单一事实来源）"。
