# E30 修复批次 2 报告（I8–I15，不含 ★ 条目）

- 执行：FixBatch2（并行批次，负责与 ★ agent 文件不重叠的 8 条）
- 分支：`e30-bridge-body`；commit：`f908065` `090b86a` `e29cb62` `15d2afd` `ad02a2b` `21b269c`
- 测试：`e30_shikongqiao_video/tests` → **63 passed, 1 failed**；唯一 fail 是 `test_frozen_file_hashes_match_disk` 对 **VisualPolish 正在改的 3 个文件**（build_scene2.py / materials.py / ortho.py，盘上哈希尚未回填 manifest）——不在本批授权范围，其所有者需在 landing 时同步 manifest §2。本批 4 个冻结文件（facts/assumptions/bridge_geom2/qa_bridge）哈希已同步，对应不一致已清零。

## I14 几何 SHA 验证（实测值）

Blender 5.2.2 LTS（同 build hash d13f752e3b9c）冷重建 A/B（改动前 / 改动后各跑一遍 `build_scene2.py` + `freeze_hash.py`）：

| 对象 | sha_sorted（前后逐位一致） | 顶点/面 |
|---|---|---|
| bridge_body | `861d8836b1704067d537ab7e7945f4a247043d9856743ab99e45cc40cea150f2` | 4409/2260 |
| voussoir | `b4421770a9e7951965968341c8a3174433377fe3c326abc1c7a4ca5cc4db047f` | 1656/1242 |
| impost | `5154f49e49d7af1e52ba3b5cb710b9ada7c8a437295b86c99397e850e6aa0c0a` | 136/34 |

- 三个值与 manifest §7 冻结候选**逐位一致**；盘上 e30_bridge.blend 现值亦为 `861d8836…`（三方互证）。
- bridge_geom2 `__main__` 自检实跑：`闭合校验 150.00 (须 150.00)` + `GEOM2_OK`。
- ⚠ **任务书给的锚值 `6194d02d5557cc91` 与三方（manifest §7 / 冷重建 / 盘上 blend）全都不符**。已按"不变性"口径完成验证（前后逐位一致）；该锚值来源不明，建议主控核实是否旧口径（本批未采信、未凑数）。

## 逐条对照（修复前实测症状 → 修复后同款破坏）

| 条 | 修复前实测 | 修复后同款破坏 |
|---|---|---|
| **I13** | `assumptions.py:10` `BRIDGE_ABUT_TARGET=2.00`+「未裁决」注释、`bridge_geom2.py:31` 死透传谎称 build_scene2 依赖（grep 全仓：唯一代码消费者就是透传自身；build_scene2:275 仅注释提及，实消费 `G.BRIDGE_ABUT`） | 两处删除；manifest §5 尾行标记 C6 裁决已落地（唯一生效值 1.35）。几何 SHA 见上表 |
| **I14** | `bridge_geom2.py:178` `16*PIER_W`（-2.50m 假闭合差数字形状：`107.3+15×2.5+2×1.35=147.5`） | 改 `(N_SPAN-1)*PIER_W`；`GEOM2_OK`；几何 SHA 三对象逐位不变 |
| **I12** | `bridge3d.audit(facts)` 实测 `skip MET_CLOSURE`（无闭合容差依据）、`skip MET_ARCH_RATIO`（缺 TARGET/TOL）；0.5 与 0.50±0.05 硬写在 qa_bridge 源码 | 三参数进 facts（[工作值]+依据）并登记 SOURCES；判据改消费；实测：收紧 `CLOSURE_TOL=0.1` 后同一 +0.2m 桥台扰动由放行转红、`ARCH_RATIO_TOL=0.01` 抓住 0.53、删阈值→skip（不静默放行）；audit 双 skip 变执行 |
| **I11** | 实测崩溃：短 `SPAN_DISTINCT=[4.5,4.9]` → `IndexError`；`DECK_Z_TOP="7.75"` → `TypeError` | 前置类型/形状校验 → `IMP_TYPES` fail；derive 截断递推 → `INV_SPANS_LEN` fail。**破坏均报 fail 不降级 skip**；基线与既有 test_l1_body 20 例全绿 |
| **I9** | 沙箱注入 `=17`（==facts.N_SPAN）→ 2 测全绿；build_scene2 不在扫描范围 | 扫描收 int+float（int/float 数值同键），范围加 build_scene2.py；注入 int17/6.56/build_scene2 int150、8.0 全部红；`int 3`（无 facts 等值）保持绿（无误伤） |
| **I10** | 沙箱把 0.50 放回白名单+注入 0.50 字面量 → 2 测全绿（死锁证实） | 删 `and f not in ALLOW`；同款构造 → 红；基线绿 |
| **I8** | 沙箱：inline `[工作值]→[测绘]`（抬级）与 `[官方]→[工作值]`（降级）两方向 → 15 测全绿 | 新增双向交叉核对测试；两方向沙箱构造均红；现库逐条一致 → 绿 |
| **I15** | 实测 `"2.5" in sec9 == True` 且 §9 无 SPRINGER/起拱线字样（标题 M2.5 子串假通过） | 结构化匹配（锚+推导值同行；表格条目限 `\|`-行，防 §9.3 栏板预置行同含 DECK_UP_W/2 与 3.28 的数值巧合假配对）；恒假 SPRINGER 行删除（§9 本无此契约条目，不补造）；负控：逐条删锚行/改值必红（7/7 条实测） |

## VOID_CUT_MARGIN 专节（应主控要求单列）

- **是什么**：bridge_geom2 既有裸字面量 `0.05`（券洞挖除体横向半宽余量，布尔施工余量），非新参数、值未改。
- **为何外置**：I10 把「等于任一 facts 常量的字面量」改为绝对禁止后，I12 的 `ARCH_RATIO_TOL=0.05` 与生成器里语义无关的余量 `0.05` 数值撞车，基线必红。消除数值同一性的唯一不动几何的办法是命名外置（改值会动布尔体→动冻结几何）。
- **依据**：沿用原白名单条目的历史标定说明——给到 0.80 会把两侧墙整块切穿（"每个券洞被黑横杠腰斩"已实测复现）；非文物尺寸、非桥体几何。
- **治理**：assumptions.py 本身在冻结清单（c4dd3bd 闸门守哈希）；`test_assumptions_not_in_sources` 防其进台账洗白等级；同时 bridge_geom2 的 float 白名单收窄一条（0.05 移出）。

## 反事实值锁的数值巧合误伤（应主控要求单列）

I10 的「字面量等于任一 facts 常量即禁」是用**数值同一性代理语义同一性**，固有代价是巧合误伤：本批实测一例——施工余量 0.05（bridge_geom2）× 判据容差 ARCH_RATIO_TOL=0.05（facts），语义完全无关却互相绊倒。解法：**外置命名**（VOID_CUT_MARGIN 范例），让两个 0.05 各归各位、可分别审计。已写进 `tests/test_no_literals.py` docstring：撞红时 ⛔禁止改值避开（=动几何=破坏冻结）、⛔禁止加白名单（=I10 刚堵的逃逸）；✔正确做法是命名外置。下一个项目大概率再撞，按此注释处置。

## build_scene2.py 扫描取舍（I9 注）

该文件属表现层（材质/LOD/机位）且不在本批授权文件清单。其存量 5 个与 facts 数值巧合的字面量（0.05 采样余量 ×10 处、0.4 异兽腿位、0.5 异兽宽/起拱石高、1.35 异兽体长、7 立方体角点索引 ×25 处）无法在本批清零 → `SCENE2_BASELINE` 逐条豁免并留档（核对过行内语境）；豁免表外新增 facts 等值字面量照红（实测 build_scene2 注入 int150/8.0 均被抓）。bridge_geom2 零豁免。

## 其他连带（防并发回归）

- manifest 同步：§1/§2 四文件哈希、§1 条目数 19→22/工作值 12→15、§5 MET_CLOSURE/MET_ARCH_RATIO 定义点改 facts.py 并新增 ARCH_RATIO 行、§5 尾行 BRIDGE_ABUT_TARGET 删除标记+VOID_CUT_MARGIN 入册、§9 工作值清单补 13–15 三行（否则 `test_work_values_listed_one_by_one` 因 want−listed 红）。
- 未触碰：materials.py / ortho.py / build_scene2.py / qa_l2.py / register_overlay.py / bridge3d/ / design.md / spec §9（结构化匹配不需要改 spec）。
- 本体几何零变化（无 body_changelog 义务）；facts 只增不改锁死条目。
- 并发提示：facts.py 在本批中途被并行方加入 `RELATIONS` 块（I1 配套），本批编辑已避开该块、互不覆盖。

## 顾虑

1. `6194d02d5557cc91` 锚值来源不明（三方都不符），需主控核实。
2. 唯一遗留红是 VisualPolish 三个文件的 manifest 哈希——其 landing 时必须同步 §2，否则主验证红（新 I2 闸门会抓，已验证抓得住）。
3. `SCENE2_BASELINE` 豁免表是数值级豁免：build_scene2 将来若新增**同值**字面量不会被抓（行号级豁免更严但随编辑漂移，未采用）；建议 build_scene2 后续迭代时把该表收敛为命名引用。
