# P2-T2 完成报告 — centering.py 券架生成器

**日期:** 2026-10-07 · **执行:** P2T2Impl · **判据来源:** `.superpowers/sdd/p2-task-2-brief.md` Task 2 + 主控补充设计

## 交付

| 文件 | 内容 |
|---|---|
| `e30_shikongqiao_video/3d/centering.py` | 券架几何生成器, 纯 python 闭合六面体, blender-free |
| `e30_shikongqiao_video/tests/test_p2_centering.py` | 12 条测试(brief Step1 五判据 + 补充设计逐条对锚) |

Commit `45cff94` `feat(e30): P2-T2 券架生成器(排架/楞木/券胎板/卸架楔, 纯python闭合体)`(只含上述两文件, 453 行)

## 接口(承 brief)

`build_centering(arch_idx, span, ring_t, lift, springer_z, deck_z_fn) -> {"id":"CEN-ARCH08", "parts":[{kind, verts, faces, bbox}], "wedge_events":int, "footprint_polys":[[(x,z)…]]}`

- 坐标: 孔局部(xc=0 孔中, y=0 桥中线, z 绝对/常水位 0); `deck_z_fn(局部x)->桥面顶z`
- 便捷入口 `build_centering_for_arch(arch_idx, ring_t=None, lift=0.0)`: 跨径/RING_T/矢跨比/拱肩全从 facts 单源取;
  `arch_springer_z(i)` 由 DECK−spandrel−rise 反推, 中央孔恒等 `facts.SPRINGER=1.14`(断言过);
  `SPANS` = SPAN_DISTINCT 对称展开(与 bridge_geom2 同形态)。`bottom_z()` 暴露 assumptions.BODY_BOTTOM 单点。

## 几何模型(补充设计落地)

- 排架沿 y 两榀 @ ±(ring_t/2+0.1); 柱排数 = int(span/1.2)+1, 沿跨对称均布、首末贴拱脚; 柱底一律 BODY_BOTTOM=-2.20(端孔 springer 近水亦不改基准, 排数随跨自然减少)。
- 每柱头堆叠: 柱(0.2 方) → 卸架楔一对(下楔顶面斜/上楔底面同斜顶平, 各名义高 0.12, 斜面 1:8→高差 0.06) → 楞木(0.12) → 券胎板(rib, 0.03 厚, 24 段沿弧, 两行对位两榀)。
- 支撑面: 拱脚区(|x|>a−0.5)楞木顶贴 intrados 下方; 跨中工作面 = extrados+0.03; 券胎面 = extrados+0.03+lift → lift=0 时 rib 上缘恰 = extrados+0.06(brief 带宽上界)。
- 桥面拓扑夹持: 券胎面/支撑面 z ≤ deck_z_fn(x)(券架不高过桥面, 真实工况不触发: 中央 6.301<7.30, facts 口径端孔 2.66<2.73)。
- wedge_events = 柱头对数 = 柱数(每柱头一对上下楔); footprint_polys = rib 带 x-z 外轮廓, 与 rib 同一采样(sequencer 占位检查可逐点复算)。
- 全部构件 = 斜剪六面体 `_box(x0,x1,y0,y1,zb0,zb1,zt0,zt1)`: 底/顶 z 随 x 线性, 6 面均平面 quad、12 边各属 2 面。

## TDD 过程与证据

1. **红:** 先写 `test_p2_centering.py`(collection error: `import centering` 不存在)。
2. **实现踩坑(测试抓到):** `_box` 底面四角误用 zb0 丢弃 zb1 → 上楔/rib 底面被"压平"、bbox 与顶点失配、楔高均值判据 0.09≠0.12。3 条测试同时红, 修顶点后全绿。**证明闭合性/堆叠判据非恒真。**
3. **绿:** `python3 -m pytest tests/test_p2_centering.py -q` → **12 passed**(0.02s)。
4. **冒烟:** `build_centering_for_arch(0/8)`: 端孔 4 排/8 楔事件、中央 8 排、rib 顶 6.301, `sys.modules` 无 bpy。
5. **回归:** 全量 `python3 -m pytest tests/ -q` → **265 passed**(=基线 253 + 本任务 12, 零新增失败, 含 T1 并行落盘的 ledger 现版; 110s)。test_no_literals 扫描面只含 bridge_geom2/build_scene2, 新文件不入锁(P2 零触本体路径, facts/assumptions 未改)。

## 判据 → 测试映射

| brief Step1 判据 | 测试 |
|---|---|
| 中央孔 span 8.5 → 柱排数 8 | `test_central_post_rows`(排数=int(8.5/1.2)+1=8, 两柱/排, 首末±a) |
| 每 part 闭合六面体(8 顶点 6 quad 12 边各属 2 面) | `test_all_parts_are_closed_hexahedra`(含面共面 + bbox≡verts 校验, 中央+端孔全构件) |
| rib 上缘 ∈[extrados+0.03−tol, +0.06] | `test_rib_verts_in_extrados_band`(逐顶点带检) + `test_lift_raises_centering_surface`(lift 抬升) |
| wedge_events==柱头对数>0 | `test_wedge_events_equal_post_heads`(=柱数; 楔高 0.12/斜面 1:8 实测) + `test_waling_sits_on_wedge_pairs`(柱顶+0.24=楞木底, 逐层相接) |
| footprint 覆盖孔跨×环带区 面积>0 | `test_footprint_covers_span_and_ring_band` |
| 端孔柱高 ≤ crown+ring_t+0.1; 排数<中央 | `test_end_arch_fewer_rows_and_height_cap`(端冠 2.23 锚过) |
| 补充设计: 两榀±(ring_t/2+0.1)/拱脚贴 intrados/跨中 extrados+0.03 | `test_two_bents_y_layout` / `test_springing_and_arc_support_targets` |

## 备注(留主控)

- brief 文字"柱排数=⌈8.5/1.2⌉+1=8"数学上=9, 与结果值 8 自相矛盾; 按结果值实现 floor(span/1.2)+1(=⌈⌉仅在整除时同), 中央 8、端 4 均符。
- 端孔 brief 锚 crown 2.23(springer 0.79)与 `arch_springer_z(0)`=0.26(冬照端 deck 2.20 口径)不同源; 生成器不选边——build_centering 收显式 springer_z, 测试用 brief 锚, wrapper 用 facts 推导, 两路都过。sequencer(T3)接线时主控定口径。
- 工作面置于拱背(extrados)+30mm 系 brief/补充设计两处明文, 按文实现; 若 T4 占位冲突检查中券胎带与券石环显重叠, 属该设计的预期后果, 再议改 intrados 口径。

## 修复轮（2026-10-07 · P2T2Fix · 审查 BLOCK 2C+4H+变异盲区 → 主控裁决 D1-D7）

**交付**: `3d/geom_math.py`(新) / `3d/bridge_geom2.py`(D3 委托) / `3d/centering.py`(D1/D2解耦/D4/D5/D6/D7 重写) / `3d/facts.py`(D2 停车线 STALE 注记) / `3d/masonry.py`(D2 分叉指针) / `tests/test_p2_geom_math.py`(新 9 条) / `tests/test_p2_centering.py`(重写 20 条) / `refs/freeze_manifest.md`(哈希重锚×3 + §2 geom_math 建行 + §9 STALE) / `refs/body_changelog.md`(D3 条 + D1-D7 条)。

### D2 停车线响应记录（主控裁决 2026-10-07 收口）

按 D2 指令把 facts.RING_T 对齐账目真值 0.54 后，`qa_bridge.check_body(facts)` 实测 **MET_RING_FIT fail ×2**：孔1/孔17 拱背 2.77 > 桥面 2.73（余量 −0.040m）。未动容差、未动 SPANDREL_E，停车报主控。主控裁决回退 0.40 并留 STALE 债务注记。

**数学根源（判据等价式，M20b 标定 ring_t(i) 的起点）**：MET_RING_FIT 的 fail 条件
  `crown_i + RING_T > deck_z(xc) + 1e-9`，代入 `crown_i = deck_z(xc) − spandrel(i)` 后桥面项**逐位消去**，等价于
  **`RING_T > spandrel(i) + 1e-9`** —— 桥面绝对标高与全局 Z 平移完全无关（这正是 M19 把全局漂移判据让位给 SPRINGER_WATER_MIN 的同一构造）。
spandrel 剖面 = 1.40(中央, SPANDREL_C) 线性过渡到 0.50(端孔, SPANDREL_E)：RING_T=0.54 时 `1.40−0.90u < 0.54 ⟺ u > 0.9556 ⟺ |i−8| > 7.644 ⟺ i ∈ {0,16}` —— **恰端两孔必红，红差恒等于 RING_T − SPANDREL_E = 0.04**。任何容差/平移自救都改写不了这个等价式；M20b 要消红，唯一正路是逐孔标定 ring_t(i)（端孔 ring_t ≤ spandrel ≈ 0.50）或重标 SPANDREL_E。

**诚实记录（主控裁决#5）**：MET_RING_FIT 在 RING_T=0.40 下测的是虚构几何 —— 端孔 extrados（按账目真值 0.54）真实穿出桥面 4-11cm，判据对此恒绿灯。这次统一尝试的价值就是把这个"绿灯测的是假人"坐实成可复现的数字（等价式 + 端孔 0.04 红差），债务显式挂进 facts 行尾注记 + manifest §9 + M20b 票。

### 逐项落地

| 项 | 实现 | 测试 |
|---|---|---|
| D1 | 工作面=拱腹：rib 顶 z=arch_z(x)−0.005(RIB_GAP)−lift，楞木/柱顶级联下移；SPRINGER_ZONE/WORK_CLEAR 分叉删失；楔副 0.06m 行程=合龙后压缩沉落（非脱环），lift∈[0,WEDGE_TRAVEL] 越界 raise | rib 顶点双侧带界(含 RIB_T)/全线贴面/沉落方向+行程闸/hasattr 负证 |
| D2 | 对齐尝试红 → 停车线回退：facts.RING_T 维持 0.40+STALE 注记；qa_bridge 零改动；masonry.RING_T=0.54 加分叉指针；**centering 解耦**：stone_ring_t(i) 从石账 params.ring_t 现算（按孔缓存，账目缺失响亮 raise），不引 facts.RING_T | AST 扫描无消费节点 + wrapper 缺省==0.54 + facts 仍 0.40 + 缺账本 raise |
| D3 | geom_math 单源提取（deck_z/arch_crown_z/arch_springer_z/width_at+PIER_X/SPANS+两自检随迁）；bridge_geom2 一行委托；centering 消费（旧线性内插第二套纵剖公式废除）；**跨源钉**：geom_math vs 石账 RING 龙门石 transform z 逐孔 ±1e-9（实测 17 孔 Δ=0 逐位等，f32 量化重放，带 ring_t+1cm 负控） | test_p2_geom_math 8 条 |
| D4 | id="CEN-ARCH%02d"%(idx+1)；返回体加 zone/arch_idx/xc(geom_math 孔心表) | 钉 CEN-ARCH09 + 17 孔 CEN 集合==石账 zone 集合（fail-on-skip） |
| D5 | 桥面夹持 min()→DECK_CLASH raise（附 x/余量），rib 顶纳入，排位+rib 采样双覆盖 | 压低 deck_z_fn 必红（断言消息含 x=/余量/−0.01）+ 17 孔零误伤 |
| D6 | footprint=[{poly,y0,y1,kind}]×2 榀 + 全局 xc；docstring"占位体积取 parts[].bbox 全局系，footprint 仅 rib 带轮廓"；旧键删失 | footprint≡rib 采样逐点等（独立重算 50 点） |
| D7 | "端孔柱高"=柱顶标高，docstring+测试注释写明 | 端冠 2.23 锚 + 柱顶<3.0m 与柱长>4m 两量级可分 |
| 变异补测 | M06 rib 两榀计数=48；M07 楞木跨两柱头；M08 夹持 raise；M11 RIB_T 双侧带界；M12 footprint≡采样；恒真 stations 换独立字面钉（中央 8/端 4，排数断言收敛一处） | 见 test_p2_centering |

### 验收（全程实测）

- TDD：test_p2_geom_math 先红（ModuleNotFoundError）→ 绿；test_p2_centering 重写先红 → 绿。
- **冻结硬门**：`blender -b --python build_scene2.py` 零错 SAVED v2 ×3 次（D3 后/D2 对齐后/回退后），freeze_hash 三对象 sha_sorted/sha_order/nverts/nfaces/bbox **逐位不变 CORE_HASH_IDENTICAL=True ×3**。
- L2：正检 QA_L2_OK + 负控 NEG_CAUGHT 10/10。
- 冻结面：freeze_manifest 哈希重锚（bridge_geom2/geom_math/facts），test_freeze_manifest 15 条绿（含 C1 git-tracked 闸 + 篡改负控）。
- 全量 pytest：修复轮起点全量 341 条（含 T1/T3 并行落盘版）→ 收口 **348 绿 0 红**（唯一次红灯是 geom_math 未入库时的 C1 git-tracked 闸，随 commit da89080 自愈）；本轮净增 16 条（test_p2_geom_math 9 + test_p2_centering 12→20），其余增量来自 T1/T3 并行任务。
- Python 3.9.6 兼容（无 match/新语法；typing 注释风格沿用）。

### 留主控

- M20b 起点：判据等价式 `fail ⟺ RING_T > spandrel(i)` + 端孔红差恒 = RING_T−SPANDREL_E；石账 params.ring_t 读取器 `centering.stone_ring_t(i)` 已就位，ring_t(i) 标定后券架 y 位自动跟随。
- spec `2026-10-07-p2-build-sequencer-design.md` 与 plans 文中 centering 行仍是 pre-ruling 文（extrados+30mm 工作面/footprint_polys 旧形），主控口径同步时请一并改。
- wrapper 依赖石账文件（缺账本响亮 raise）；sequencer(T4) 若需账本无关构建，显式传 ring_t 即可。

## 补丁轮（2026-10-07 · P2T2Patch · 复审抓 M11 假完成+3 存活变异+§7 历史计数 → commit `e32753a`）

| 项 | 实现（全在 tests 层，centering.py 零改动） | 变异注入证红（注入→定向跑→`git checkout` 还原） |
|---|---|---|
| M11 真钉 | `test_family_constants_literal_pinned`：`C.RIB_T==0.03`/`C.RIB_GAP==0.005`/`C.WEDGE_H==0.12` 字面直钉，不经派生带 | RIB_T→0.015、RIB_GAP→0.05、WEDGE_H→0.10 各自使 **literal_pinned 单条红**（assert 0.015==0.03 / 0.05==0.005 / 0.1==0.12），而同跑的 `test_rib_verts_in_intrados_band_double_sided`/`test_support_line_uniformly_below_intrados`/`test_wedge_events_equal_post_heads`/`test_wedge_travel_is_six_centimeters` 全绿 —— 坐实旧带界测试用 C.* 复算带界、翻常量带跟翻的假完成盲区 |
| AST 堵 import-from | `test_centering_does_not_consume_facts_ring_t` 扩展：新增 `ast.ImportFrom(module=='facts')` 且 alias 名 `RING_T` 或 `*` 即红 | centering 注 `from facts import RING_T as _RT` → 扩展后测试红（AssertionError 解耦被回退）；同一变异跑旧检查逻辑 `OLD-CHECK-CAUGHT: False`（存活实证，扩展必要性） |
| wrapper 桥面主张补牙（建议级） | `test_clamp_reads_pointwise_deck_not_constant`：端孔 idx0（xc=−71.03, crown 工作面 2.2206）传真桥面 `λx→GM.deck_z(xc+x)`（crown 处 2.7256）正常建成；传常数桥面 `λx→2.20`（DECK_Z_END）必 DECK_CLASH 且报错 x∈crown 区（\|x\|<0.5，实测首炸样点 −0.188） | 注 `d = deck_z_fn(x)`→`d = _F.DECK_Z_TOP`（常数桥面近似回潮）→ **新测试红**（DID NOT RAISE），`test_deck_clash_raises…` 同红（双重把守） |
| §7 历史计数 | freeze_manifest §7 `coursing 顶点/面数` 59716/34878 → **66964/39466**（`blender -b e30_bridge.blend --python freeze_hash.py` 2026-10-07 实测），同行注记 f5d2dcc 重锚漏更计数行、M20b/T2 复审发现；`sha_sorted f2968f4c…` 实测逐位未动 = 计数行陈旧非几何漂移（`git log -L137` 证实该行由 f5d2dcc 新增即带旧数）；只改这一行，§7 sha 行零触碰 | —（文档行，无测试依赖：`grep 59716\|coursing tests/` 空） |
| 石账无孔 ValueError（次要项） | `test_stone_ledger_missing_arch_valueerror`：tmp_path 假账本（仅 ARCH01.RING）→ 账内孔 0.54 现算正常、孔 6（0 基 5）响亮 `ValueError 石账无孔6`；finally 还原 _LEDGER_PATH+清缓存 | 注 `raise ValueError("石账无孔…")`→`return _F.RING_T`（静默兜底 STALE）→ 新测试红（DID NOT RAISE） |

**回归**：补丁轮起点全量 348 绿 → 收口 **351 passed 0 红**（净增 4 条 = test_p2_centering 19→23；起点与基线计数的 ±1 漂移是并行任务瞬时未跟踪测试文件，工作树 `git diff` 仅本票两文件、HEAD `71ecd56` 未动，非新增红）。冻结面/几何零触碰（centering.py 零改动，无需重跑 core_hash 门）。
