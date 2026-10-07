# P1 Task 4 报告: masonry2.py 背衬层 + core cells

**Commit:** `d095eee` `feat(e30): P1-T4 背衬层+core cells(证据级core_reconstruction, 隐缝2mm)`
**Files:** 修改 `e30_shikongqiao_video/3d/masonry2.py`(+152)、`e30_shikongqiao_video/tests/test_p1_masonry2.py`(+61, 7 新测试)
**Branch:** e30-bridge-body(主树直接 commit, 未走隔离树回写——本任务与 T5 printcheck 并行, T5 已先行落主树 2ca3434)

## TDD 五步
1. **失败测试**: brief 逐字 2 条 verbatim + 5 条自加(理由见下)追加到 `tests/test_p1_masonry2.py`。
2. **失败确认**: `7 failed, 8 passed` —— 全部 `AttributeError: module 'masonry2' has no attribute 'backing_stones'/'core_cells'`(红灯=接口缺失, 非断言误写)。
3. **实现**: `backing_stones(spec, arch_idx, side, hw_fn, course_h=None, seed=0)` + `core_cells(arch_idx, hw_fn, z_lo, z_hi, seed=0, x_lo=None, x_hi=None)` + 辅助 `_face_idx`。
4. **通过**: `tests/test_p1_masonry2.py` 15 passed; 主树全量回归 **114 passed**(基线 107, 含 T5 已落的 printcheck 套件; ≥96 达标)。
5. **Commit**: 见上, 仅含 2 个文件(报告/brief 照 T1-T3 惯例不入库)。

## 实现要点
### 背衬层 role=BACK, evidence=ashlar_truth
- **同口径层高/块位(硬契约)**: 直接调 `face_stones(...)` 拿面石账目, 背衬逐块对齐面石(course/block/x 宽/z 带/层高全部继承, 层高即 `_course_heights` 推导链)——不另算一遍层高, 契约由测试 `test_backing_reuses_course_heights_contract`(UNEQUAL_SPEC 下背衬 h 与 zm 序列逐位==面石)钉死。
- **隐缝 2mm 真几何**: 退让线 = 该块 z 向"可及"丁石内缘(取自面石账目实值, 非参数复算)的最小值再退 `BACKING_GAP=0.002`。可及判定逐丁石: `|zm差| < max(DEFAULT_COURSE_H, 0.5*(两石层高))` —— 前者覆盖薄层相邻(brief 测试窗口 0.55), 后者覆盖厚层贴触(两层 0.641 时半跨和 0.641>0.55, 窗口不够会漏真穿透)。可及集为空(全顺层)回退全部面石内缘最小值。
- **transform 语义与面石一致**: `transform[1]=背衬外缘 y`, 内缘=`|y|-d`(wedge-std 局部 y∈[proud-d, proud], proud=0); 测试的 `y_in = |transform[1]| - params.d` 读到的就是真实内缘, 非算术假过。真砖谱 269 石冒烟全查穿透=0(见验证记录)。
- **深度伪随机**: `random.Random(seed)` 固定遍历序(course-major)逐块抽 `0.8+0.4*random()`; 同 seed 逐位可复现, 东西同 seed 即镜像对称(测试钉死三条: 同 seed 相等/异 seed 相异/镜像对称)。
- **2mm 记 params["gap_mm"]**: 最初写进 `clearance_manufacturing_mm`, 被 `validate_ledger` 抓 `CLEARANCE_PREMATURE`(ledger I1: 制造间隙挂 T6 allow_clearance 时序才准置值)——负控制由既有校验器当场抓到, 改记 params.gap_mm(几何事实), clearance 字段保持 None 与面石同纪律。
- family `wedge-std`(hw_b=hw_t 平脸, proud=0), material `maoshi`(毛石), `print.watertight=True`(直盒天然水密, T5 printcheck 复核)。

### core cells role=CORE, evidence=core_reconstruction
- **网格**: x 分 `CORE_COLS=3` 列 × z 每 `CORE_CELL_H=0.6` 一层 × 前后合并单 cell(贯穿东西两墙, y∈[-hw, +hw], hw 取该列心/层中处 `hw_fn`)。z 界只从 z_lo/z_hi 推导(末层短胞兜到 z_hi), 无硬编; 1.0→6.0 产 9 层×3 列=27 cells。
- **bbox 入 params**: `{x0,x1,y0,y1,z0,z1}`, 并满足恒等式 `z1 == z0 + params.h`、`x1-x0 == w`、`y1-y0 == d`(测试逐条钉死)。
- **浮点纪律**: 层高用 `h=min(CORE_CELL_H, z_hi-z0)` 截断量, 不用 `z1-z0` 回减(回减得 0.6000000000000001, brief verbatim 断言 `h<=0.6` 即红, 曾抓出 1 次)。
- family `slab`(直盒), material `maoshi`, `print.watertight=True`; id 形如 `ARCH09.EAST.CORE.C03.B01`(前后合并胞不区分面向, face 词元按 id 词法归 EAST 常规位)。
- **x 界口径(声明)**: 缺省以 `hw_fn(0, 层中)`(拱心线处墙面半宽)近似孔净半跨——hw_fn 是本模块唯一几何注入口(T3 DI 契约, 不 import 冻结 facts); T8 接真实拱线时用 `x_lo/x_hi` 精化, 签名已留口。

## 自加 5 条测试的理由
| 测试 | 守什么 |
|---|---|
| `test_backing_evidence_depth_and_clearance` | brief Step1 口头判据落码: role/evidence/深 0.8-1.2/gap_mm=2.0/clearance 保持 None(时序纪律) |
| `test_backing_depth_is_pseudorandom_deterministic` | 伪随机三性: 同 seed 逐位同、异 seed 异、东西镜像 |
| `test_backing_penetration_negative_control` | **判据负控制**(全局约束): 抵消退让量再推 1cm, 穿透必须被抓住(判据非恒真, 违规量>0 断言) |
| `test_backing_reuses_course_heights_contract` | T3 审查硬契约: 背衬层高必须与面石同口径 |
| `test_core_cells_bbox_watertight_and_coverage` | bbox 三恒等式 + y=2*hw 口径 + 水密标记 + z 覆盖无缝无叠(首=1.0 尾=6.0 层界相接) |

## 验证记录
- 主树全量回归: `python3 -m pytest tests/ -q` → **114 passed**(基线 107 + 7 新增; Python 3.9.6 实机, 无 match/无 `X | None`, 注释式类型注解; 测试零 blender 依赖)。
- 真实砖谱冒烟(throwaway, 未落盘): `stones_p8.json` → face 121 + back 121 + core 27 = 269 石, `validate_ledger` **0 错误**(id 全过 `_ID_RE`, 无 CLEARANCE_PREMATURE/UUID_DUP); 真砖谱穿透全查(面石丁石×背衬, brief 同判据不限合成)= **0 穿透**。
- 浮点缺陷自曝 1 次: 层高回减 `2.2-1.6=0.6000000000000001` 被 brief verbatim `h<=0.6` 断言当场抓红 → 改截断式 `h=min(0.6, z_hi-z0)`; 修 params 后自加测试里同型回减(`bb.z1-bb.z0==h`)又红一次 → 改钉构造恒等式 `z1==z0+h`(更强且无浮点敏感)。

## 移交下游(T5/T6/T8)
- 背衬/core cells 均带 `print.watertight=True`; T5 printcheck 流形/自交复核直盒时应全过, 若报错即网格生成端问题(families.slab/wedge-std), 不是账目端。
- `clearance_manufacturing_mm` 全线仍 None: T6 挂 `allow_clearance` 时序时, 背衬隐缝实值读 `params["gap_mm"]=2.0`(面石丁石间隐缝同源, 面石侧 T3 未记, T6 若需可由 HEADER_D/STRETCHER_D 差推)。
- T8 取 ARCH09 全量时: core cells 用 `core_cells(8, hw_fn, z_lo=<起拱线>, z_hi=<冠内缘>, x_lo/x_hi=<拱线净跨>)`, z_lo/z_hi 请从面石/背衬几何算(契约: 不硬编); 现缺省 x 界是墙面半宽近似, 真实拱线务必显式传。
- 镜像对称: 东西两面同 seed 产出镜像背衬(core 无面向之分只出一份)。

## 修复轮 (2026-10-06, commit 3780306)

审查 BLOCK 三 Critical 全修 + W1-W7 + suggestion 1; 只动 `3d/masonry2.py` 与 `tests/test_p1_masonry2.py`。TDD: 先加 10 个失败测试(red 实证)再实现; 全量回归 `python3 -m pytest tests/ -q` = **118 passed**(原 114, +6 新增 −2 替换删除)。

### C2 方案B: 楔形背衬平行退让
- `backing_stones(faces, hw_fn, seed=0)`(W5): 单一真相收 faces 账目, 不再内部重跑 face_stones; zone/face/side 从 `faces[0].id` 派生。
- 背衬改楔形: `proud=0`, `hw_b/hw_t = hw_fn(xm, z0)/(z0+h)`(墙面收分参考, 只载斜率); 外缘面 = 墙面平行平面 `hw_fn(xm,z)+front_c`, 与同带丁石内缘面(`hw_fn(xm_h,z)+PROUD-d_h`, 同斜率)**平行**, 沿 z∧x 真相交带整体退 `BACKING_GAP`; 偏移记 `params["front_c"]`(消 params-几何错配陷阱), `transform[1]` = 层中处外缘 y。
- reachability 改**严格 z 带真相交**(`0.5*(h+h_h)` 带正长度重叠, 端点贴合不算)∧x 带真相交; 删 DEFAULT_COURSE_H 项(W3)。自身块位恒真相交 → 可及集永不为空, 废旧"全顺层回退全局面石最小值"。
- 沿相交带**两端**比斜面(hw 沿 z 线性 → 两端即全域): `c = min_z∈band[hw(xm_s,z)-hw(xm,z)] + PROUD - d_s - BACKING_GAP`。
- 实证: 真实 p8 + 真实收分(测试内独立线性 hw 近似, 斜率 -0.4232/m 与审查同值, 不依赖 blender) → 0 穿透 ∧ 全部缝 = 2.0mm(旧: 11 块穿透 +24.1mm, 其余空腔 181~403mm)。

### C1 强判据 + 边界标定负控(W4)
- 新判据 `_hdr_violations`: 对每块背衬取 z∧x 带真相交丁石, 沿相交带两端比斜面 `y_out(z) <= hw(xm_h,z)+PROUD-d_h-BACKING_GAP`; 替换被背衬自身深度吞掉的 `y_in<=y_h_in-0.002` 标量判据(旧判据对 0.8m 穿透免疫)。
- 负控制打在容差边界: `MIN_CLEARANCE = 0.5*BACKING_GAP`(名义缝 2mm 允缩到 1mm)。实测: **+1mm 位移(缝 1mm)不抓 ✓; +3mm(真穿 1mm)必抓 ✓**(替换旧 +0.81~1.21m 假负控)。
- 补 UNEQUAL_SPEC 薄层(0.144)与厚层(0.641→wedge 测试)贴触用例: `test_backing_is_wall_parallel_wedge` 逐石断言 proud=0 / hw_b>hw_t(收分楔形非平盒) / transform[1]=hw_fn(xm,zm)+front_c。

### 突变自证(新判据下必须被抓; 突变后复原 diff 干净)
| 突变 | 结果 | 抓获者(实测 fail 明细) |
|---|---|---|
| M2: `BACKING_GAP 0.002→0` | 1 failed | `test_backing_c1_judgement_boundary_calibration`(clearance=-0.001, 即缝塌到 0 < 1mm 边界) |
| M10: 外缘 +500mm | 4 failed | `c1_strong_criterion_synthetic`(-0.498) + `boundary_calibration`(-0.499) + `wall_parallel_wedge` + `real_p8 穿透/缝不足: -0.498` |
| M-flat: 平盒回归(hw_b=hw_t=层中) | 1 failed | `test_backing_is_wall_parallel_wedge`(hw_b≠_hw(xm,z0)) |
| C3 缺省 x 界路径(修复前 red) | TypeError 缺失 → fail | `test_core_cells_x_bounds_are_required` |

### C3 + 其余
- `core_cells(arch_idx, hw_fn, z_lo, z_hi, x_lo, x_hi, seed=0)`: x 界**必填**(删 ±hw_fn(0,·) 缺省推导路径); `z_hi<=z_lo → ValueError`(采纳 suggestion, 废静默空表); 合成测试显式传 x_lo=-4/x_hi=4。
- W1: 模块头+backing docstring 两处改为"记 params.gap_mm; clearance 保持 None 至 T6"。
- W2: `"gap_mm": BACKING_GAP*1000.0` 绑定常量。
- W6: core params 记 `"y_extent": "full_wall(overlaps ashlar)"`; "总体积按 evidence 分层不相加"写进 core docstring。
- W7: 模块头 T4 节/背衬/core 三处 docstring 与实现逐条同步(含退让公式、可及集定义、print 纪律)。
- suggestion 1: 删 `st["print"]["watertight"]=True` 两处赋值+文档一处自证表述; 真实测由 T5 printcheck 产出(全仓无消费者断言已随测试删除)。

### 移交契约变化(下游注意)
- **签名 breaking**: `backing_stones(spec, arch_idx, side, hw_fn, course_h, seed)` → `backing_stones(faces, hw_fn, seed)`(T8 调用方必须先跑 `face_stones`); `core_cells` x_lo/x_hi 由可选变必填位置参(seed 前)。
- 背衬 params 新增 `front_c`(外缘面相对墙面参考面的 y 偏移)与 `front_c` 语义见 docstring; hw_b/hw_t 只载斜率。
- 未动 UNEQUAL_SPEC/REAL_P8 既有面石测试; 未触碰 T5 并行工作的 printcheck 文件(回归无收集冲突)。
