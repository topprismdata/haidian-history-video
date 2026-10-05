# E30 望柱蹲狮重雕（M6）交付报告

- **任务**：按验收判据重做望柱石狮几何，使近景（0.8-1.2m）可辨识为石狮；交付形态为 linked duplicates（主控 2026-10-05 中途定版）。
- **分支**：`e30-bridge-body`　**commit**：`123f74f`
- **参考**：`3d/refs/lugou_lion/`（卢沟桥望柱狮，Wikimedia Commons CC/GFDL，仅造型参照不入成片素材）。取官式蹲狮解剖：大头≈40%H、双层眉弓、凸眼、宽上翘吻+口裂、髭须卷、卷云鬃、阔胸垂饰、并拢前肢+趾、低臀、卷尾、雄抱绣球/雌伴幼狮。

## 怎么做的

1. **新模块 `3d/lions2.py`**（旧 `lions.py` 留盘不动，仍是 freeze manifest 记录文件）：
   - 每变体只建一次**母模**：~48 个闭合体块（颅/颧/双层眉弓/凸眼/宽吻/上翘鼻/下颌留缝=口裂/髭须卷×4/卷云鬃×9+额顶双卷/颈圈垂饰/胸/并拢前肢+爪+趾/臀座/折后腿/卷尾/配件）→ **EXACT 布尔并**成单一水密实体 → **SUBSURF(SIMPLE) 细分**补密度 → 归一化到单位高。缓存为 2 个 bpy mesh。
   - **坑（实测）**：Blender 5.2.2 LTS 的 `bmesh.ops.subdivide_edges` 对任意输入静默无操作（`cuts=1` 亦然，cube 复现）——改走 SUBSURF 修改器 + `new_from_object`（与布尔并同一条管道），实测有效且确定。
   - `place_lions(spots, material)`：**linked duplicates**——256 个对象共享 2 个 mesh datablock，每对象仅 transform（scale=H、微yaw ±2.6°），零几何拷贝。
2. **`build_scene2.py` 改动**（3 处，均记录于 changelog/manifest）：`import lions2 as LIONS`；`bm_to_obj(build_lions_bm(...), "lions", ...)` → `LIONS.place_lions(spots, m_rail)`；旋转名单中 `"lions"` 移出、256 个狮对象逐一叠加桥轴 −112°。`build_lions_bm` 合并版删除。

## 验收实测（判据→数字）

| 判据 | 要求 | 实测 | 结论 |
|---|---|---|---|
| 近景可辨识 | 头(含吻)/鬃毛/前肢/蹲姿 | `lion_closeup_front.png`、`lion_closeup_threeq.png`（距狮 1.1-1.3m，35mm 全栈含望柱）：正面可见颅+双层眉弓+凸眼+宽吻+口裂+髭须卷+卷云鬃+耳；3/4 侧可见昂首/厚胸/并拢前肢+爪趾/低臀/足下绣球/幼狮，及沿栏一线群狮 | **通过**（渲染纪律同 shot_auto2：seed=20261004、METAL GPU、denoise、64spp） |
| 单只面数 | ≥4000 | 主狮 mesh **10632** 面、幼狮 mesh **11026** 面 | **通过** |
| 水密性/连通域 | 单 mesh 连通域=1（新口径，替代"全对象=狮只数"） | 两 mesh **连通域均=1**；unique mesh=**2**；对象数=**256**（主128+幼128） | **通过** |
| 就位 | 狮坐于望柱顶 | 抽 16 只：底垫中心到 deck_rail 最近面距离 <3cm 且法线 +Z（底垫沉入柱顶 2cm=1.20−1.18 口径差）**16/16**（`tools/lion_seat_check.py`） | **通过** |
| hero 不退化 | 轮廓/孔数/栏杆连续性不差于现状 | 同机位同 seed A/B（仅狮几何不同）：1600×900 逐像素差 **0.123%**（1773px，容差>8），**全部落于 y∈[359,461] 狮带**；栏杆顶缘线逐列一致（二阶趋势去除后残差 std=0、列间跳变 max=0，新旧相同）。孔数/桥体由本体保证：freeze_hash 三对象 sha_sorted 与改前**逐位一致**（`861d8836…`/`b4421770…`/`5154f49e…`） | **通过** |
| 测试 | 全绿 | `pytest e30_shikongqiao_video/tests tests/bridge3d -q` → **376 passed**；`qa_l2` 正检 `QA_L2_OK` exit=0，负控 `NEG_CAUGHT`(10/494 翻转面全被抓) exit=0 | **通过** |
| 数量/尺寸登记 | 写入 FACTS.md 或 changelog 并注等级 | changelog **M6 节** + FACTS.md §已知差距两条更新：256 只实体（linked duplicates），主狮高 **0.30m**、幼狮 **0.17m**，**[工作值]**（沿用旧 LOD 口径，无文献数值）；"544 只"仍为三套并存二手口径不作计量事实 | **完成** |

## 证据文件（绝对路径）

- 近景正面：`/Volumes/macstudio/video-projects/e30_shikongqiao_video/3d/lion_closeup_front.png`
- 近景 3/4 侧：`/Volumes/macstudio/video-projects/e30_shikongqiao_video/3d/lion_closeup_threeq.png`
- hero A/B：A(旧狮)=`/Volumes/macstudio/video-projects/e30_shikongqiao_video/3d/refs/hero_AB_old_lions_samecam.png`，B(新狮)=`/Volumes/macstudio/video-projects/e30_shikongqiao_video/3d/shot_hero.png`（另存改前原渲染 `/Volumes/macstudio/video-projects/e30_shikongqiao_video/3d/refs/hero_ab_old_lions.png`）
- 本体哈希对照：`refs/regression/lion_m6_core_hash_{oldlions,newlions}.json`；QA：`refs/regression/lion_m6_qa_l2{,_neg}.json`
- 复现工具：`3d/tools/lion_closeup.py`、`3d/tools/lion_seat_check.py`

## 已知不足（不粉饰）

1. **逐只差异消失**：共享 mesh 后每只狮几何完全相同，仅 transform 微差（±2.6°yaw）。旧实现有 seed 抖动。官式狮本以程式化重复为常态，且同柱双狮不邻接（主狮/幼狮各一），近景单机位内不可见重复；但若未来需要"每只不同"，需回到多 mesh（违背 ≤2 mesh 口径）或 Geometry Nodes 变形。
2. **近景平直棱面可见**：~10mm 级平直面片在 1m 近景可辨（凿石风格化）。未做平滑着色/法线贴图——属表现层后续工作，不影响辨识判据。
3. **底垫沉入柱顶 2cm**：沿旧口径（柱高 1.20 与狮位 z+1.18 的差），非新引入。
4. **544 只文献口径仍以 256 实体表现**（每柱 1 主狮+1 幼狮，其余以柱头狮群轮廓表示）——沿旧降级决策，本次未扩量。
5. **造型是卢沟桥解剖 + 程序化纹样从简**，非十七孔桥某只具体狮的复刻（参考照片分辨率不足以支撑逐像素复刻，验收口径即为"可辨识"）。
6. **`bmesh.ops.subdivide_edges` 在本 Blender 版本静默无操作**已写进代码注释与 changelog——后续任何依赖该算子的脚本需警惕。
7. 合并版 `build_lions_bm` 删除后，旧分析脚本（`section.py`/`silhouette.py`/`ab_texture_test.py`，均未跟踪的临时工具）按名查 `"lions"` 单对象会 KeyError——它们面向旧单 mesh 设计，如需再用须改为遍历 `lion_*` 对象。

## 返工轮（M6.1，2026-10-05，主控复核后）

主控复核判定：剪影级判据通过；①面部平板化（吻=矩形板+穿透黑槽="信箱口"）②折面感（纸工艺）不达标。返工**只动 `lions2.py`**，其余冻结不动，未 commit（主控统一提交）。

**改了什么**：
1. 布尔链重构 `pos → neg → final`：正体并 → 减法浅凹（口裂/鼻孔/眼窝，均不穿透）→ 眼球最后并入。
2. 口裂：穿透缝 → 7 球抛物弧内凹线槽（深≈0.013 单位≈4mm 实物，两端上挑），刻在颌前面、吻底悬垂阴影下。
3. 鼻：方盒 → 楔形鼻梁（后宽前窄上扬）+ 椭球上翘鼻头；鼻孔=鼻梁顶面两个椭圆浅凹。
4. 眼：眉弓改双层椭圆棱 + 眼窝浅碗（减法）+ 眼球凸块凸出碗缘 14mm。
5. 髭须改贴面浅浮雕三连卷；胸垂饰矩形板改上宽下窄绶带棱台；吻部方盒改圆垫椭球（矩形板上凹槽必继承矩形轮廓——根因之一）。
6. **平滑着色**：全 face smooth + 二面角>40° sharp 边（auto-smooth 等价）——消纸感、保凿棱。

**返工中抓到的三个连通域杀手（均实测复现并修复）**：
- `_frustum` tilt 语义错 → ±0.06 扭曲棱台毒化整条 EXACT 链（pos_only comps=5，四肢 severed+体内残壳）→ tilt 改绝对外缘偏移后 comps=1；
- 眼球不越过眼窝碗缘 → 悬空成岛（comps=3）→ 眼球 r 加大穿越碗缘；
- 鼻孔刀在鼻头球上切落两端月牙帽（comps=3）→ 移到鼻梁顶面小椭圆刀。

**面数前后**：主狮 10632 → **15692**；幼狮 11026 → **16054**（≤25k 预算内）；连通域均=1；smooth 着色 sharp 边 4545/4653。

**量化对照（返工后重验）**：
- 对象 256 / unique mesh 2 / 坐实 16/16（<3cm +Z）不变；
- freeze_hash 三对象逐位一致（861d8836…/b4421770…/5154f49e…）；
- qa_l2 正检 QA_L2_OK、负控 NEG_CAUGHT，exit 均 0；
- pytest **376 passed**（含 freeze 闸门）；
- hero A/B（同机位同 seed）：天空 0.00% 差、桥/栏/狮带 46.6%、水区 44.3% 且随距离 91%→0.5% 衰减。**归因警示**：A=927f940~1 旧 build_scene2（旧狮+旧材质接线），B=现 build_scene2（新狮+主控 M7 接线勘误+水岸调整），26.9% 为【新狮反射+M7 材质差异】叠加，非全为狮几何；狮几何无涉的硬证据：栏杆顶缘线逐列一致（残差 std=0、跳变 0）、天空 0 差、freeze_hash 三对象逐位一致。
- 证据（覆盖原路径）：`lion_closeup_front.png`、`lion_closeup_threeq.png`（应为 `lion_closeup_threeq.png`）、`shot_hero.png`、`refs/hero_AB_old_lions_samecam.png`。

## commit

- `feat(e30): M6 望柱蹲狮重雕——lions2 母模布尔并+linked duplicates(256对象/2mesh/单mesh连通域=1/近景可辨识); 本体三对象sha逐位不变; hero A/B像素差0.123%限狮带; 376 tests pass`
