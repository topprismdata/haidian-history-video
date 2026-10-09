## 修复轮 (P1T5Fix, 2026-10-06, commit d11b07f)

审查 BLOCK 四 Critical 假阴性 + W/S 项全部落地，只动 `3d/printcheck.py` 与 `tests/test_p1_printcheck.py`。
TDD：新套件先对旧实现跑红（34 failed；行为级取证：C1 apex=1e-7 ok=True / C2 NaN ok=True,vol=nan / C3 重合双壳 ok=True / C4 反绕 ok=True / FACE_INDEX 旧实现 IndexError / W3 index0 外包含漏报），修复后 35 passed；全量回归 `pytest tests/ -q` = **140 passed**。

每条新判据的负控/正控探针输出（pytest 之外独立取证）：

```
== C1 planarity
  neg wedge-std max_dev=1.388e-17 -> NON_PLANAR_FACE=False   (审查实测 1.39e-17, 阈 max(1e-12, 1e-9×尺度))
  neg slab/L/U  max_dev=0.000e+00 -> NON_PLANAR_FACE=False
  pos apex=-0.5  dev=4.082e-01 > 1.000e-09 -> 报; apex=-0.25 dev=3.313e-01 -> 报; apex=1e-07 dev=2.357e-01 -> 报
== C2 INVALID_COORD
  neg clean ok=True | pos nan ok=False codes=[INVALID_COORD] | pos inf ok=False codes=[INVALID_COORD]
== C3 MULTI_SHELL/DOUBLE_MATERIAL
  neg slab vol/bbox=1.0000 双码=False | neg wedge-std vol/bbox=0.9091 双码=False (审查实测 1.00/0.91)
  pos dup-shell codes=[MULTI_SHELL,DOUBLE_MATERIAL] | pos flush-x0.4 codes=[MULTI_SHELL,DOUBLE_MATERIAL]
  pos disjoint-x5 codes=[MULTI_SHELL] (分离双壳不误报 DOUBLE_MATERIAL)
== C4 NON_ORIENTABLE
  neg wedge/slab/L/U(全体内翻但一致)=False | pos 单面反绕 detail='4 directed edge(s) reused same direction'
== W1 THIN_WALL 方向无关代理
  pos 45° 斜置 0.03m 薄板: pair faces #0/#1 t=0.600mm < 1.200mm (bbox 全轴 ~14.6mm 沉默, 代理兜底)
  neg 轴对齐厚件 / 45° 厚件 / wedge / L / U 全 False
== W2 gap_check 旋转契约 (entry=6 元组 transform, 先旋转后 AABB)
  pos rz=90° 横穿长墙 -> PENETRATION | neg 同位移 rz=0 (未旋 AABB 漏判对照) -> ok=True | neg 旋转后真分离 -> ok=True
== W3 共面包含全顶点遍历
  pos 边界全共线、严格包含顶点不在 index0 -> SELF_INTERSECT=True | neg 叠置接触=False | neg 偏置接触=False
== W5/W6 闸门
  dup-idx/2-vert -> DEGENERATE_FACE | idx-99 -> FACE_INDEX_OUT_OF_RANGE (不再 IndexError) | empty -> EMPTY_MESH
== 决策1 域校验 + S1/S3
  scale=0.0/-1.0/50.0 -> ValueError; scale=1.0 合法 | issues 统一 {"code","detail"}; gap_check 返 {ok,issues}
  check_stone docstring 写死 post-inset 时序契约 (inset 再吃 2×clearance, 跑前检查=放行薄件)
```

实现要点：`_planarity_issues(V,faces,rel=1e-9,abs_eps=1e-12)`；面级 union-find 连通域（对齐 lions2.py assert_watertight 口径）+ `volume > bbox×1.000001` 体积上界不变量；有向边一致性（只保证一致，不强制朝外）；相邻面对自交精检与 shrink-by-epsilon 类方案未引入（按审查者"不建议"清单）；零新依赖，纯 numpy。
