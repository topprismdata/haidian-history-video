# P1 Task 3 报告: masonry2.py 面石层生成器

**Commit:** `dee62a6` `feat(e30): P1-T3 面石层生成器(砖谱->ledger, 顺丁相间, 两缝分离)`
**Files:** 新增 `e30_shikongqiao_video/3d/masonry2.py`(56 行)、`e30_shikongqiao_video/tests/test_p1_masonry2.py`(4 测试)
**Diff:** `.superpowers/sdd/p1-task-3-diff.txt`

## TDD 五步
1. **失败测试**: 按 brief 逐字写入 2 条 verbatim 测试, 另加 2 条(理由见下); 运行 `ModuleNotFoundError: masonry2` 红灯确认。
2. **失败确认**: 同上(collection error 即红)。
3. **实现**: `face_stones(spec, arch_idx, side, hw_fn, course_h=0.55)` + `build_face_layer(stones_dir, hw_fn, arches)`。
4. **通过**: P1 套件 26 passed(隔离树); 主树全量回归 **90 passed**(基线 86 + 4 新增, ≥88 达标)。
5. **Commit**: 见上, 仅含 2 个新文件(任务报告/brief 照 T1/T2 惯例不入库)。

## 与 brief Step-3 实现代码的两处偏差(均为核对后修正, 测试为准)
1. **zone 改 1 基**: `zone = "ARCH%02d" % (arch_idx + 1)`。brief 代码 `"ARCH%02d" % arch_idx` 会使其**自己的** verbatim 测试失败(face_stones(SPEC, 8, …) 断言 `ARCH09.EAST…`, snippet 产出 `ARCH08`)。依据: 设计 spec 明文「孔=ARCH01..17(西→东)」, 且砖谱 `stones_p0.json` 自带 `"arch": 0`(0 基)——文件索引与 zone 显示号差 1。
2. **块界归一 `_pairs`**: 真实砖谱 `courses[].blocks` 是沿 x 的界边表(如 `[-42.196, -41.596, …]`), 非测试合成 spec 的 `{x0,x1}` 字典。`_pairs` 对字典直通、对边表取相邻对, 使 `face_stones` 两种格式通吃(Interfaces 声明 Consumes `stones/stones_pX.json`, 不归一则该声明为空话)。

新增的 2 条测试即守上述两处: `test_face_stones_accepts_edge_list_blocks`(边表→w 值)、`test_build_face_layer_aggregates_sides`(两面聚合+1 基 zone)。修正过程自曝 1 次: 聚合测试最初把 ids[1] 误写为 `C01.B00`(实为 `C00.B01`, course-major 序, brief verbatim 测试 ids[3]=C01.B01 可证), 改测试不改实现。

## 契约遵守(T2 审查确立)
- 5 拓扑参含 face 调 `L.new_stone(zone, face, "SPANDREL", ci, bi, …)`, material `qingshi`。
- **深度差进 params["d"]**: 顺石 1.2 / 丁石 2.4(顺丁规则 `(ci+bi)%2==0`→顺); verbatim 断言 `abs(d0-d1)>0.3` 读的正是 params 实值, 全链可查。
- params 带 `w/h/d/proud/back/hw_b/hw_t` 供 T6/T7 材料化(`families._wedge_std` 以 d 为权威深度, hw_b/hw_t 在块上下沿取值); transform=[xm, ±(hw(xm,zm)+PROUD), zm, 0,0,0], 西面 y 取负。
- 两缝分离: `joint_historical_mm=10.0`(new_stone 默认), `clearance_manufacturing_mm=None`。
- Python 3.9.6(注释式类型注解, 无 match/无 `X | None`); 测试不依赖 blender(hw_fn 注入)。

## 验证记录
- 主树全量回归: `python3 -m pytest tests/ -q` → **90 passed**(e30_shikongqiao_video/, 含治理套件 test_no_literals/test_freeze_manifest, 确认新文件不在其扫描/冻结清单)。
- 真实砖谱冒烟(throwaway, 未落盘): `build_face_layer(3d/stones, hw, [4])` → 134 石(stones_p4, 11 层×东西), id 100% 过 `ledger._ID_RE` fullmatch, depths={1.2, 2.4}, 边表块 w 值正确(首块 w=0.60)。
- 隔离树 `/tmp/e30_p1/` 先同步主树 T1/T2 修复版 ledger/families 再开发; 试跑后回写主树。隔离树内 `test_facts/test_register` 收集错误为该局部副本缺依赖的存量问题, 与本任务无关(主树同两文件正常)。

## 移交下游(T4+)
- `build_face_layer` 现以 `course_h=0.55` 默认值跑真实砖谱(接口签名无该参); 真实砖谱每层高不同(冒烟 z0 序列 0.15/0.85/1.455/2.073…间距 0.55~0.7), T4/T6 接真实数据时需决定逐层高度来源(砖谱 courses 内或 hw_fn 配套), 本任务未擅动签名。
- 背衬/core cells(T4)可复用 `_pairs` 与 STRETCHER_D/HEADER_D/PROUD/BACK 常量。

## 修复轮(T3 审查裁决: course_h 定高导致层间纵向插穿)
**Commit:** `6974723` `fix(e30): P1-T3审查修复(course_h从spec层距推导, 消纵向插穿)`
**Files:** 只动 `3d/masonry2.py`(+52/-12)、`tests/test_p1_masonry2.py`(+67, 4 新测试)
**Diff:** `.superpowers/sdd/p1-task-3-fix-diff.txt`

### 缺陷与修法
审查实测: `face_stones`/`build_face_layer` 用定高 `course_h=0.55` 建层, 而真实砖谱层间距不等
→ 矮层砖顶越过上层起算线 = **纵向插穿**。修法按裁决: **层高从 spec 自身推导**
`h_i = z0_{i+1} - z0_i`(相邻层起算线差), 末层(无下一条起算线)用显式传入的 `course_h` 兜底。
- 新增 `_course_heights(courses, course_h)`; `face_stones(..., course_h=None)` —— `None`=从砖谱推导,
  未传时末层回退 `DEFAULT_COURSE_H = 0.55`(保留旧默认数值, 命名常量而非裸字面量)。
- `build_face_layer(..., course_h=None)` 透传该末层兜底值; 逐孔读各自砖谱层距。
- `params["h"]`、`zm = z0 + h/2`、`hw_t = hw_fn(xm, z0 + h)` 三处随之全部改用本层实高(裁决点名的 z 中点/上沿口径)。
- 顺带(审查 Minor): `_pairs` docstring 补「边表相邻成块、首尾两边为该列左右界, n 条界边产 n-1 块,
  故奇数长度边表不是缺块」。

### TDD
1. 先写 4 条测试 → 红灯确认 `4 failed, 4 passed`(旧实现全层返回 0.55; `DEFAULT_COURSE_H` 不存在)。
2. 实现后 `8 passed`; 主树全量回归 `python3 -m pytest tests/ -q` → **94 passed**(基线 90 + 4 新增, 无新增失败, 无收集错误)。
3. 既有 4 测试**未改动**即保持绿: 合成 SPEC 层间隔恰为 0.55(等距), 推导值==旧默认值; 显式 `course_h=0.55` 路径行为不变。
4. 新测试内容: 推导序列 `== [0.290-0.146, 0.850-0.290, DEFAULT]`、显式参只兜末层、
   **真实 `3d/stones/stones_p8.json` 逐层断言 `z0_i + h_i <= z0_{i+1} + 1e-9`**(即块顶≤上层块底)且 h 序列==相邻 z0 差序列、
   `build_face_layer` 默认走推导+透传兜底值。

### 插穿前后对比(throwaway 探针, 全 10 孔真实砖谱)
| 砖谱 | 层数 | 层间隔 | 插穿(旧 0.55) | 插穿(修复后) | minGap | maxGap |
|---|---|---|---|---|---|---|
| stones_p0 | 5 | 4 | 0 | 0 | 0.555 | 0.700 |
| stones_p1 | 7 | 6 | 2 | 0 | 0.356 | 0.776 |
| stones_p2 | 8 | 7 | 4 | 0 | 0.412 | 0.706 |
| stones_p3 | 10 | 9 | 5 | 0 | 0.455 | 0.709 |
| stones_p4 | 11 | 10 | 5 | 0 | 0.420 | 0.738 |
| stones_p5 | 13 | 12 | 4 | 0 | 0.144 | 0.641 |
| stones_p6 | 15 | 14 | 6 | 0 | 0.144 | 0.641 |
| stones_p7 | 16 | 15 | 7 | 0 | 0.144 | 0.641 |
| **stones_p8** | 16 | 15 | **7** | **0** | 0.144 | 0.641 |
| stones_p9 | 16 | 15 | 7 | 0 | 0.144 | 0.641 |
| 合计 | — | 107 | **47** | **0** | — | — |

- p8 与审查裁决逐条吻合: 15 个层间隔中 7 个插穿, 最差 **0.406m**(C0 实高 0.144 却按 0.55 建),
  顶层带 0.22~0.33m 连环穿(C10~C14 间距 0.236/0.236/0.26/0.32/0.33)。
- 修复后 10 个砖谱 107 个层间隔插穿 **47 → 0**; 最差插穿深度 **0.406m → 0**。

### 下游口径变化(取代上方「移交下游」第 1 条)
`build_face_layer` 不再需要下游决定层高来源——层高已随砖谱走; `course_h` 语义降级为
**仅末层兜底值**(旧"每层定高"语义废除)。T4 背衬/core cells 若按层铺筑, 应复用
`_course_heights(courses, course_h)` 取同一序列, 勿另立层高口径, 否则背衬会重犯同类插穿。
