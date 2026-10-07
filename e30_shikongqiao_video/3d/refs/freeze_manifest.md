# E30 M2.5 本体冻结包 manifest

- 日期: 2026-10-04（T8）；2026-10-06 M18 砌筑 + M19 冬照重标定后全量重采（哈希/等级分布/§9 清单/spec §9 契约同步，判据本体随 facts 重整）
- **冻结状态: `CONDITIONAL_RECONSTRUCTION_FREEZE`（候选）——未锁定，待用户裁决**（§9）
- 冻结范围: **本体**三对象 `bridge_body` / `voussoir` / `impost`（含布尔进 body 的 17 券洞、16 墩、双桥台）
- **不在**冻结范围: `deck_rail` / `lions` / `beasts` / `pier_plinth` / `deck_cornice` / `abutment_ground` / `water`（M3 附属构件 / M5 环境预置件，受 spec §9 接口契约约束但不受本冻结保护）
- 判据语义: 只有 `fail` 阻塞；`skip`=未执行不算通过；每条判据必须有故意破坏用例且破坏被抓
- 配套工具: `3d/freeze_hash.py`（核心几何哈希的唯一定义点，冷重建对照用它跑）
- `.blend` 不入库（gitignore，设计决策）：真相源 = facts/assumptions + 生成器脚本；`.blend` 是可从零重建的产物

## 1. 事实/假设层快照

| 文件 | SHA256 | 说明 |
|---|---|---|
| `3d/facts.py` | `af260eab4f78a666c9c301d9face053140cb20ade8a5e2e47c61dbc4439dd7b6` | 31 条本体条目（M19 冬照重标定 2026-10-06：DECK_Z_TOP/DECK_Z_END/SPANDREL_C/SPANDREL_E/RISE_E 改标 [图像推导]，新增 RISE_C/CROWN_BLUNT_K/CROWN_BLUNT_CAP/SPRINGER_WATER_MIN 登记）；等级分布见 §9 |
| `3d/assumptions.py` | `94e428e48b8a05ed1f1d016e59e1b15ed6c336f582e440e4a142dcedd0102dec` | 假设层，不进冻结，改动须记录（终审 I13 删 `BRIDGE_ABUT_TARGET`、I9/I12 外置 `VOID_CUT_MARGIN`；2026-10-06 外置 `VOID_CUT_WIDTH_K` 贯通系数，SPANDREL_C 等值锁正规出路） |

等级分布（facts.SOURCES 31 条）: **官方 6**（BRIDGE_LEN / N_SPAN / DECK_UP_W / DECK_DOWN_W / PUBLISHED_GENERAL_WIDTH / PUBLISHED_BRIDGE_HEIGHT）、**图像推导 7**（ARCH_RATIO + M19 冬照重标定 DECK_Z_TOP / DECK_Z_END / SPANDREL_C / SPANDREL_E / RISE_C / RISE_E）、**工作值 18**（14 条本体尺寸/形状锚 + 4 条判据阈值参数 CLOSURE_TOL / ARCH_RATIO_TARGET / ARCH_RATIO_TOL / SPRINGER_WATER_MIN，清单见 §9）。**测绘 0 / 档案 0** —— 故本体只能走条件冻结（§9）。

## 2. 生成器与判据（管线 commit 与文件哈希）

管线 HEAD: `35e0ccf`（"docs(e30): T6 Step0 标记完成(T5已修C6与法线工序)…"，冻结包提交前的最后管线 commit）。冻结包自身的 commit 哈希在用户批准后回填 `3d/refs/body_changelog.md`。

| 文件 | SHA256 | 角色 |
|---|---|---|
| `3d/bridge_geom2.py` | `70e0771f5d83bf184316027d41b8093301ac0d123aa0666dc9890cd156e9f9a9` | 纯几何（消费 facts，零字面尺寸；终审 I13/I14/I9/I12 沿革见前版记录；2026-10-05 M18 逐块砌筑消费 masonry 同一 facts 函数族；2026-10-06 M19 纵剖重标定：逐孔 spandrel/arch_springer_z 剖面、DECK_Z 7.30/2.20、RISE_E 0.32；贯通系数 1.40 外置 assumptions.VOID_CUT_WIDTH_K——M19 新增 facts.SPANDREL_C=1.40 后等值锁正规出路，几何语义零变化；2026-10-07 P2-T2 修复轮 D3：deck_z/arch_crown_z/arch_springer_z/arch_rise/PIER_X/收分 width_at 公式单源提取至 geom_math.py，本文件一行委托+收分消费转发，**重建实测 core_hash 三对象逐位不变** CORE_HASH_IDENTICAL=True） |
| `3d/geom_math.py` | `f7656316c4b4da9cb458e96f941da4e0346b9a0b0a9f0fb587c57879be268c4c` | 纵剖/收分纯数学单源（P2-T2 修复轮 D3 新建，零 bmesh：deck_z/arch_crown_z/arch_springer_z/width_at 公式自 bridge_geom2 原样搬移，常数读 facts/assumptions；centering(P2)/sequencer(T4) 消费；跨源钉=石账 RING 龙门石 transform z 逐孔 ±1e-9（tests/test_p2_geom_math.py，实测 17 孔 Δ=0 逐位等）） |
| `3d/build_scene2.py` | `63bef392dfba3f0ee7ad8e01956f89c561d82865b7293d62c1b615a6c18305c6` | 场景构建（2026-10-07 P1-T8b: cap_to_deck wedge 截顶同步重算 transform[1] 前脸锚(A1, 审查恒等式 pen+BACKING_GAP≡-(|ty|-(hw+proud)) 全链 2290 对余量<1e-6mm, pen>0 116→0)——仅 ledger 链, proxy 本体三对象零变化；2026-10-07 P1-T7 审查修复轮：cap_to_deck 按族分派锚语义(slab 最小角锚 transform[2] 不动+桥面采样改块心 bbox 中点——旧版把 slab 当中心锚截顶, 全 role 越顶 29→0)+超底弃石 skipped_below_deck 计数/ids 记 meta 并打日志+classify_stones 给 clip 石打 params.clipped 标(materialize 缺烘焙网格即 raise, W4)+守护导入 bpy 可用而本体模块缺失显式 ImportError(S1)+LAYOUT_MAX_OBJECTS 60→50(W1)——全部 ledger/layout 链改动, 默认 proxy 路径零改动、本体三对象几何 SHA 零变化；历史: C6 后消费 facts.BRIDGE_ABUT=1.35；2026-10-04 补入 abutment_ground 桥轴旋转，核心三对象几何 SHA 未变；2026-10-05 M4 表现层：abutment_ground 改燕翅型桥台(前墙+八字燕翅墙)、新增 shore_bank/fog_volume 环境件——本体 bridge_body/voussoir/impost 顶点未动，qa_l2 正检 QA_L2_OK、register VERDICT PASS(IoU 0.8070 与冻结基线一致、void max\|Δxc\|=0.0181 不变)，见 body_changelog.md M4 节；2026-10-05 M6 蹲狮重雕：import 换 lions2(母模 EXACT 布尔并+SIMPLE 细分, 单 mesh 连通域=1)，build_lions_bm 合并版改 place_lions linked duplicates(256 对象/2 unique mesh)，build_scene2 其余零改动——freeze_hash 三对象逐位一致(861d8836…/b4421770…/5154f49e…)，hero A/B 同机位逐像素差 0.123% 且全部落于 y∈[359,461] 狮带，见 body_changelog.md M6 节；2026-10-05 M4b 雾岸修补：shore_bank 网格 24x40→72x120+横向随 u 收窄(±30→±46m, 埋翼墙/引道切面)+两档高频正弦岸线（本体零改动，freeze_hash 三对象逐位一致），见 body_changelog.md M4b 节；2026-10-06 M18 砌筑贴面 + M19 纵剖重标定：桥头-岸系 6 常数随端标高 -1.4、座石 impost 3 阶线脚、百叶贴收分（详见 body_changelog.md M18/M19 节））;2026-10-06 P1-T7 场景三模式: 头部 blender 依赖改守护导入(无 bpy 可导入, blender 路径逐位不变), 尾部新增 blender-free 纯逻辑段(全桥账目链/void 裁剪/族清点/GN 放置数学)与 --emit-lib/--layout 模式, 默认 proxy 路径零改动——本体三对象 freeze_hash 逐位一致、qa_l2 正检 OK+负控 10/10、_check_abutment ALL PASS 实测见 body_changelog.md T7 节 |
| `3d/qa_bridge.py` | `f370d8bad49d4a4b812af74576f1ccd4725c5e29b3aa3d61367c0985b94db285` | L1 判据（纯数据；终审 I11 损坏 facts 报告不崩溃、I12 阈值消费 facts.CLOSURE_TOL/ARCH_RATIO_TARGET/ARCH_RATIO_TOL；2026-10-06 M19 判据重整：MET_ARCH_FAMILY 冠高期望扣钝化 s·ln2（facts.blunt_s 单一来源，钝化=七审P1-1 已登记设计特征）、MET_SPRINGER 增水上硬下限（facts.SPRINGER_WATER_MIN，全局 Z 漂移唯一绝对判据）与 SPRINGER 声明=导出恒等校验） |
| `3d/qa_l2.py` | `7cf5e2da2203322efa28f0c831292a8185689ab19ad89ffc421939ecc95c4ad3` | L2 判据（开 blend 查 evaluated mesh；2026-10-05 终审 I4/I6：零采样记 skip 且 ok=false，负控脱靶/未抓到一律 exit 1；哈希为 M18/M19 后盘上重采） |
| `3d/materials.py` | `539445c6f3de06cef0658ba3e4d75f4d4fc9ca662ce8afe48c46f3da7bcce2f5` | 程序化材质（无 random，节点内置噪声同版本确定；2026-10-05 M4 表现层：stone 增逐块色差+bump 砌缝凹槽、water 三频波纹+粗糙度斑块、新增 earth/fog 材质——纯 shader 层，不触 mesh；2026-10-05 C2 纯追加 qingshi_material（青石桥体，来源逐字核实见 body_changelog.md C2 节），既有函数零改动，freeze_hash 三对象 sha 逐位不变；2026-10-05 WaterFix water/earth 调参（水 bump .20→.32+第四频 scale30+风纹 Mapping 转 90°+rough .02/.09；earth 干基 ×0.8+亮斑 (1.80,1.55,1.30) 作用原 palette+水线湿带 z∈[0,0.5]）——纯参数/节点零几何，函数签名不变，hero A/B 量化见 3d/ab_water/，见 body_changelog.md WaterFix 节） |
| `3d/lions.py` | `aa4c3b3e3f0314da3594a4c070aee4722660ee581a88b5122f5db5406610d627` | 狮母题（自带 LCG，seed 显式入参，确定） |
| `3d/ortho.py` | `603140be8d42e0cd30992a092ab8b07a6bae55f33557c02c8d57fcda14a763d6` | 正交出图（T6 当日演进：新增 top/arch 机位，首采哈希 2fe76ce0… 已被取代；2026-10-05 终审 I2 回填——`4ce8475` M3-1 加水线 sidecar 后未同步 manifest；2026-10-05 M4 隐藏名单补 shore_bank/fog_volume 环境件，正交立面只认本体轮廓，IoU 0.8070 不变；M4b 相机 clip_end=20000——默认 1000m 截断雾盒出射面的根因修复同步到此，正交视图环境件仍隐藏，重渲后 VERDICT PASS 不变） |
| `3d/render_shot.py` | `bef2368ccecb732aff765930aed3c7165e813d691eb849c0741b73630c647275` | 机位渲染（seed 显式；2026-10-05 终审 I2 回填实际盘上哈希——原记录 `95732262…` 是 `cf11ac3` 改文件前的旧值） |
| `3d/shot_auto2.py` | `be0e96c8154b410920fca747122d489b42d1e2ac9cb5d8f6946680b965b39801` | 自动取景渲染（主控 2026-10-04 补 seed 显式化，已提交；2026-10-05 M4b 修天空硬边：相机 clip_end 1000→20000——默认 1000m 截断雾盒(侧壁 2600m/顶 123m)出射面, >1000m 出射的天空射线体积栈为空致雾效 binary 消失(实测硬边在仰角 6.9°=y173 处 Δ7.68, 修复后 0.79), seed=20261004 不变） |
| `3d/freeze_hash.py` | `9bdb35407bd1ba2687c89358b4db05b2c5b080a26da8fd402bedcc9e2f2c7677` | 核心几何哈希唯一定义点（随冻结包 commit `6d8a838`；2026-10-06 M19 拓扑跟随：第三核心对象 impost→coursing，impost 单 mesh 已废并入 coursing，见 §7） |
| `3d/register_overlay.py` | `d3da15cd9f09ce5c4bddd14084f5e59d4ad2133c7d0f40b0b8dfc74009eb7530`（T7 `d30502f` 定版阈值；2026-10-05 终审 I3 增补券洞表硬判 void_verdict） | T7 L3 配准判据（OVERLAY_IOU_MIN=0.76 / VOID_XC_TOL=0.02；T8 只引用不运行） |

## 3. Blender 版本

```
Blender 5.2.2 LTS
build date: 2026-09-15 01:49:19
build commit date: 2026-09-14 15:14
build hash: d13f752e3b9c
build branch: blender-v5.2-release
build platform: Darwin (arm64)  build type: Release
```

冷重建判据：**同 build hash**。跨 build hash 的浮点/布尔求解器差异不在本冻结的复现承诺内。

## 4. 参考资产哈希（T3.5 冻结，先于查看任何重建结果；FACTS.md §6）

| 文件 | SHA256 | 备注 |
|---|---|---|
| `3d/refs/ref_elevation.jpg` | `c1e491f3a39b1f7ab053dfcdd75d0aa55990d62193255675eb02aa693d61f970` | 1920×879 原字节，EXIF Canon EOS 400D |
| `3d/refs/ref_mask.png` | `aec338605d7f1177ebc0187ae7c2e08864c9de30875a5da63534586770a207c8` | 人工掩膜（L 模式，白=桥体带）；**参考侧禁止重跑自动 RGB 阈值** |

与 FACTS.md §6.1 登记的前 16 位哈希（`c1e491f3a39b1f7a` / `aec338605d7f1177`）一致。

## 5. 容差配置（判据阈值及其依据）

| 阈值 | 值 | 定义点 | 依据 |
|---|---|---|---|
| MESH_TOL | 0.005 m | assumptions.py | 券石入净空 epsilon（网格数值容差，G1 分家设定） |
| CIRCLE_FIT_RTOL | 0.01 | assumptions.py | G2: f/l 只是必要条件，圆拟合残差/半径 ≤1% 证明"是圆" |
| MET_CLOSURE | 0.5 m | facts.py `CLOSURE_TOL`（终审 I12 落地，qa_bridge 消费） | T2b 闭合口径（N_SPAN−1 个内墩）；阈值承计划稿 |
| MET_ARCH_RATIO | 0.56±0.02 | facts.py `ARCH_RATIO_TARGET`/`ARCH_RATIO_TOL`（终审 I12 落地，qa_bridge 消费；M14 起比对 facts.rise_ratio 剖面中心） | 券形设计意图尖拱 0.56（六审标定，0.61 哥特味收 0.56）；M19 冬照隐含 0.53±0.08 覆盖 0.56 故冻结 |
| WALL_NORMAL θ | 6° | qa_l2.py | 离散弦面理论半扇形角 π/NSEG_ARC/2≈2.25°，G2 取 6° |
| WALL_NORMAL 采样带 | \|y\|<7.0；z>SPRINGER+0.02；\|n_y\|<0.5；\|r−a\|≤0.15 | qa_l2.py | T5 实测修订：剔除 26 个洞缘倾斜 n-gon（§8-1）；负控翻"采样带内前 10 面"（R3） |
| IMPOST_ANCHOR | 0.5 m（xz 平面距离） | qa_l2.py | T5 修订：起拱线石是 x×z 纵剖面陈述，3D 距离版假红 34/34 |
| VOUSSOIR_IN_VOID | r < a − MESH_TOL | qa_l2.py | 2026-10-04 修订：券石内缘=拱腹，须加径向条件否则全孔误杀 |
| L3/T7 阈值 | OVERLAY_IOU_MIN=0.76；VOID_XC_TOL=0.02 | register_overlay.py | 扰动标定（E2 可接受/不可接受分布中点，Brumana 精度-目标挂钩）；复现 `refs/calibrate_iou.py` |

实现参数（非文物事实，不冻结）: NSEG_ARC=40, NSEG_X=240, SEG=40, VOID_CUT_MARGIN=0.05（券洞挖除体布尔施工余量，"黑横杠"bug 标定值；2026-10-05 终审 I13/I9/I12 外置命名）；建模假定: BODY_BOTTOM=−2.20。~~BRIDGE_ABUT_TARGET=2.00~~ 已随 C6 裁决删除（桥台唯一生效值 = facts.BRIDGE_ABUT=1.35，150.0 精确闭合唯一解）。

## 6. 渲染图哈希 + seed

seed 政策: `ortho.py` / `render_shot.py` / `shot_auto2.py`（主控 2026-10-04 修正显式化）均 `cycles.seed=20261004`、`use_animated_seed=False`。⚠ seed 只固定采样序列；自适应采样调度仍非确定（见下），"同机同版本确定"仅对**采样序列**成立。

**对照口径（主控 2026-10-04 提出，T8 复测后修订）**: 渲染对照**禁用 PNG 文件哈希**（文件差异含 `tEXt` 元数据 `Date`/`RenderTime`）。像素级（IDAT 拼流 SHA256）对照经 T8 冷重建复测**被证伪为不可用判据**：
- 主控独占条件实验（旧 blend、arch 视图）：seed 固定后两渲像素逐位相同、IDAT 一致——当时据此采纳 IDAT 口径；
- **T8 复测（重建 blend、arch 视图）：5 渲 5 异**（IDAT 全不同，含 GPU 空闲条件下背靠背两渲仍异）；hero 视图 2 渲一致（单视图偶证）。
- **归因**: `use_adaptive_sampling=True` + Metal 后端下，自适应采样调度存在运行间非确定（seed 只固定采样序列，不固定逐步收敛判定）；与 GPU 并发无关（空闲条件复现）。
- **结论**: 渲染层可复现性当前只能声明到**配置锁定**（seed/samples/分辨率/脚本哈希），**逐位像素复现不成立**；IDAT/文件哈希均不构成冻结判据。逐位复现需 M4 关闭自适应采样（`use_adaptive_sampling=False`）后独占 GPU 另测（§8-11）。

冻结候选（2026-10-04 冷重建删除前重采，**仅作存档快照，非对照判据**）:

| 文件 | IDAT 像素 SHA256 | seed |
|---|---|---|
| `ortho_side.png` | 候选 `58db0658ed3757d2…e5a9`（T6 23:18 版，**T7 标定所用文件**）；T8 重渲基线 `86fe24ec09e97d…62f2`（mtime 1791127424，ortho.py 桥轴 112° 版） | 20261004 |
| `ortho_front.png` | `85ec08dbf8cc8a62523f9b25ab94b7b520615e3e37ad82e7d2b1cb08a249d49d` | 20261004 |
| `ortho_top.png` | `6a8b0ded5e00b83156fec5fc7cb0421753fa8e696a0f40249b1db3d66f106242` | 20261004 |
| `ortho_arch.png` | `729b41bebf9f15c830b9ac6452d4ecddb84a56f92f0b94ce080b909e604946d6` | 20261004 |
| `shot_hero.png` | `2e9a6d31768651442b0aacb410e04f15c2bfe9c5330fcd775c06cab49514b0d4`（**候选为 seed 修正前渲染，与重渲不可比**） | 20261004（修正后） |
| `shot_arch.png` | `425d5c9ba4b336ac4d50306f44a05d5cc5155844c7f4f47920bcbb79936ec0a6`（主控实验渲染；重渲 DIFF 已归因 §8-11 渲染层非确定，非 blend 差异） | 20261004 |
| `shot_side.png` | `ce7b997339d2894404eb257346ac3e9a54be00b7782be52d3c2000b13aec6d0e` | 20261004 |

M2.5 冻结包机位口径（简报 G3）: ortho side 2200px + hero/arch 1600px/96spp；**rail/lion 特写属 M3 附属件，不在本体冻结包**。

## 7. 冷启动重建验证（G3 硬门）

**状态: 几何硬门已通过（2026-10-04 实测执行；2026-10-06 M18/M19 几何变更后按同门重采, 见下方新基线表）**。流程: ①删除前重采候选态（blend/核心哈希/L2 正检+负控/渲染 IDAT 存档）→ ②删除 `e30_bridge.blend`+`e30_bridge.blend1`（渲染产物按主控并发约束暂不动，`ortho_side.png` 留给 T7）→ ③干净状态 T4 `blender -b --python build_scene2.py` → T5 L2 正检+负控 → ④几何对照（硬门）。hero/arch 已重渲为新基线快照（非判据）；`ortho_side.png` 待 T7 释放后重渲记录新基线。

**〔存档〕2026-10-04 T8 冷重建对照（M19 前几何；`impost` 行为末次独立记录）**:

| 项 | 冻结候选 | 冷重建 | 一致? |
|---|---|---|---|
| `bridge_body` sha_sorted | `cdba970973a4e711c767385c52f4967e0db5af893ca0efc70622fad72945ea7b` | 同左 | **MATCH** |
| `bridge_body` sha_order | `5a5c923275057a127fec2138a53b5b4a02bc66750639fb82978601e82b113674` | 同左 | **MATCH** |
| `voussoir` sha_sorted | `ba2e09516e1e5d3a256b02c9277861fd811343a49d0aaebac39cc6cd06993694` | 同左 | **MATCH** |
| `voussoir` sha_order | `1c7ded704ed262389bcab794dcc733396f76703ef8aa825ee36c04a0c8173a49` | 同左 | **MATCH** |
| `impost` sha_sorted | `5154f49e49d7af1e52ba3b5cb710b9ada7c8a437295b86c99397e850e6aa0c0a` | 同左 | **MATCH** |
| `impost` sha_order | `13743527ae240699e76fc6365ab37b72537614eb76e9f37c905f4b987a30adf9` | 同左 | **MATCH** |
| `bridge_body` 顶点/面数 | 4409 / 2260 | 4409 / 2260 | **MATCH** |
| `voussoir` 顶点/面数 | 1656 / 1242 | 1656 / 1242 | **MATCH** |
| `impost` 顶点/面数 | 136 / 34 | 136 / 34 | **MATCH** |
| `bridge_body` 世界 bbox | x[−34.864,34.864] y[−72.273,72.273] z[−2.2,7.75] | 同左 | **MATCH** |
| L1 fail 数 | 0 | 0 | **MATCH** |
| L2 正检 | ok=true, warn=0 | ok=true, warn=0 | **MATCH** |
| L2 负控 | 翻 10 面 → FAIL(被抓) | 翻 10 面 → FAIL(被抓) | **MATCH** |
| pytest | 37 passed（候选时点） | 47 passed（含 T8 冻结包 10 条） | 绿（测试只增未红） |
| （信息项）`e30_bridge.blend` 文件 SHA | `10b750218354822e…` | `a3dcfcaa956b077b…` | 非判据（.blend 内含渲染时刻等元数据，字节级不同属预期；真相源=脚本+数据） |

**〔现行基线〕2026-10-06 M18 砌筑 + M19 冬照重标定后重采**（同 build d13f752e3b9c；重建命令 `blender -b --python build_scene2.py` 零错 SAVED v2，endzone=52 pier=878 bay=1312 impost=204 grand=2639；随后 `blender -b e30_bridge.blend --python qa_l2.py` → QA_L2_OK、`--negative` → NEG_CAUGHT 10/10、`_check_abutment.py` → ALL PASS C1-C11、`pytest tests/bridge3d -q` → 312 passed、`e30_shikongqiao_video/tests -q` → 64 passed）:

| 项 | 值（2026-10-06 重采） |
|---|---|
| `bridge_body` sha_sorted | `cdba970973a4e711c767385c52f4967e0db5af893ca0efc70622fad72945ea7b` |
| `bridge_body` sha_order | `6442839341c987281d6b4bdf6c3234a6887045c77310a1c611d0b7ef61d41eac` |
| `voussoir` sha_sorted | `ba2e09516e1e5d3a256b02c9277861fd811343a49d0aaebac39cc6cd06993694` |
| `voussoir` sha_order | `bb2defc9c0595a61422e1be3c94c08302086dbe82cf811e98129275413840c96` |
| `coursing` sha_sorted（第三核心, M19 拓扑: 原 impost 并入贴面系统） | `f2968f4c70fd92943478c0b28b34d8233ef50077049982a63ffad24274b03f77` |
| `impost` sha_sorted（末次独立记录, 对象已废除） | `5154f49e49d7af1e52ba3b5cb710b9ada7c8a437295b86c99397e850e6aa0c0a`（M2.5 候选） |
| `bridge_body` 顶点/面数 | 2648 / 1520 |
| `voussoir` 顶点/面数 | 2316 / 1544 |
| `coursing` 顶点/面数 | 59716 / 34878 |
| `bridge_body` 世界 bbox | x[−34.864,34.864] y[−72.273,72.273] z[−2.2,**7.3**]（M19 DECK_Z_TOP 同步） |
| L1 fail 数 | 0（qa_bridge M19 判据重整后基线绿） |
| L2 正检 / 负控 | ok=true, warn=0 / 翻 10 面 → NEG_CAUGHT 10/10 |

**证据分层（主控收尾要求，两类不可混为一谈）**:

- **几何可复现性证据（硬门）——已通过**: 核心三对象 sha_sorted/sha_order/顶点面数/bbox 逐位一致；L1/L2 正检负检同判；EXACT 布尔求解器同 build 完全确定，无浮点非确定、无隐藏状态。主控已独立复核（其法线修复工序后实测值与本重建一致）。
- **渲染可复现性证据（加分项）——如实结论: 不成立**: 见 §6——arch 视图 5 渲 5 异（含 GPU 空闲背靠背仍异），归因自适应采样调度非确定；hero 2 渲一致仅单视图偶证。**渲染对照不构成冻结判据**，冻结渲染证据=配置锁定（seed/samples/分辨率/脚本哈希，§2/§6）+ 几何硬门。

渲染产物处置（主控裁决：无需等 T7，T7 标定写新文件不回写 ortho_side）: 冷重建后 `shot_hero.png`/`shot_arch.png`/`ortho_side.png` 已重渲（配置同锁定值；ortho.py 为桥轴 112° 修正版）作为**新基线快照**；均**不作对照判据**（§6/§8-11）。

**⚠️ 坐标系警告（2026-10-04 主控实测，本表已因此误判过一次"几何漂移"）**：
项目里存在**两把不同的几何尺**，值不可互相比较：

| 尺 | 来源 | 坐标 | `bridge_body` 值 |
|---|---|---|---|
| **官方工具**（本表用） | `3d/freeze_hash.py:35` 取 `matrix_world @ v.co` | **世界坐标**（含 −112° 桥轴旋转） | `861d8836b1704067…` |
| 临时手算（勿用于比对） | 一次性 `bpy` 表达式取 `v.co` | **局部坐标**（未旋转） | `6194d02d5557cc91…` |

两者**都正确**，只是量的对象不同。**跨尺比对必然"不符"，那不是几何漂移。**
本 manifest 与冷重建验证一律以 `freeze_hash.py` 为准；任何临时脚本要参与冻结判定，必须先声明坐标系并与此表对齐。
（`voussoir` 世界=`b4421770a9e79519`、`impost` 世界=`5154f49e49d7af1e`，同表可查。）

判读规则: `sha_sorted` 不一致 = **不可复现，冻结失败**（逐项归因浮点非确定 vs 隐藏状态，如实记录，不"差不多"放行）；`sha_order` 不一致而 `sha_sorted` 一致 = 布尔求解器顶点顺序非确定，记 §8 豁免；渲染层不作复现判据（§6 结论：像素/文件哈希均无判别力），PNG 差异不触发冻结失败。

## 8. 已知偏差豁免表

| # | 偏差 | 处置 | 依据 |
|---|---|---|---|
| 1 | 26 个洞缘倾斜 n-gon（\|n_y\|≈0.878，与朝心夹角 63–69°，9–15 边）——carve 在洞缘并出的缘饰刻面，**无判据覆盖** | WALL_NORMAL 采样带以 \|n_y\|<0.5 过滤不测它；缘饰刻面列 M3 前表现层待办，不由本体判据承担 | task-task-5-report |
| 2 | 参考掩膜桥带仅 843×44px（62px 高） | L3 只能声明"构图与轮廓一致性"，**禁止**声称逐拱轮廓校核 | FACTS.md §6.2/6.4 |
| 3 | 正交投影消掉尺度-深度可解性 | 照片只能约束平面内轮廓；**测不到**拱圈矢高/桥身纵坡/券石厚度等面外形变 | FACTS.md §4c.3 |
| 4 | 渲染 vs 单张照片无学术定量范式 | 像素层判据只能声明"结构与照片不矛盾"，**不能**声明准确性 | FACTS.md §4c.3 |
| 5 | C2 桥宽双官方口径（6.56 vs 8.0） | DECK_UP_W=6.56 采用；8.0 并存登记禁止覆盖 | FACTS.md C2 |
| 6 | C3 高 7.0 测点未注明 | ~~DECK_Z_TOP=7.75 工作值~~ M19 起改标 [图像推导]=7.30（冬照直读）；PUBLISHED_BRIDGE_HEIGHT 禁止映射不变 | FACTS.md C3 / body_changelog.md M19 |
| 7 | ~~`shot_auto2.py` 未显式设 seed~~ **已修复（主控 2026-10-04）**: 显式 `cycles.seed=20261004` + 关闭 animated seed，固定了**采样序列**；其"渲染像素级可复现"后续被 §8-11 复测证伪（自适应调度非确定），本条只保留**配置锁定**效力 | 关闭（限配置锁定语义） | 本 manifest §6 |
| 8 | C4 走向三值并存（90/112/135） | BRIDGE_AXIS_AZ=112 建模值，**不冻结为事实**；M5 日照判据裁决前不得锁死方位 | FACTS.md C4 |
| 9 | `.blend`/渲染产物不入库 | 设计决策：可从零重建，真相源=脚本+数据 | 本 manifest 头部 |
| 10 | ~~T7 标定结果占位~~ **已闭环（T7 `d30502f`）**: OVERLAY_IOU_MIN=0.76 / VOID_XC_TOL=0.02 扰动标定回填，基线 0.8070 PASS 余量 0.047；重渲前后基线 4 位小数不变 | 关闭；细目见 §11 | §5 L3 行 / §11 |
| 11 | **Cycles(Metal) 自适应采样运行间非确定**：arch 视图 5 渲 5 异（GPU 空闲背靠背两渲仍异）；hero 2 渲一致属偶证。seed 只固定采样序列，不固定自适应收敛判定 | 渲染像素/文件哈希**均不作冻结判据**（§6/§7）；M4 渲染契约建议 `use_adaptive_sampling=False` 后独占 GPU 复测逐位复现，再决定是否恢复像素级判据 | T8 冷重建复测（2026-10-04） |
| 12 | **竖向比例偏高 27%**（长高比模型 13.61 vs 参考 18.76）：根因是出图裁切口径——`BODY_BOTTOM=−2.20` 水下不可见基座计入渲染高（9.95m），参考照片桥带只到水线；**非本体几何错** | 不阻塞 M2.5 冻结（用户"90% 进下一步"）；列 M3 迭代清单；T7 掩膜 IoU 判据应能抓，待其真实图标定跑通后回归 | body_changelog.md M3 首轮迭代 |
| 13 | 栏杆望柱锯齿起伏：初判为缺陷，**经与原图对照后推翻**——原图即密排小方块纹理 | 非缺陷；仅高度略高且不匀，列 M3 微调清单 | body_changelog.md M3 首轮迭代 |
| 14 | ~~券洞内壁纯黑、券石不可见~~ **主张已撤回（commit `c02f412`）**：券圈 0.40m 在参考图单拱 30px 下仅 **2.67px**，不可分辨——"原图可见券石环"是从不可分辨信号读出结论（与判据恒真同类错误） | 券石环核验须换高分辨近正面照或正交特写，不得从 `ref_elevation.jpg` 得出；教训：目视比对同样须过分辨率门槛 | body_changelog.md M3 首轮迭代 / `c02f412` |
| 15 | **石狮仅 256 只实体，非 544 只**：`build_scene2.py:136-138` 自陈"544 只全做高模不现实 → 每柱 1 只 LOD-M + 柱侧 1 只小狮，合计 2×64×2 = **256 只实体**，其余以柱头狮群轮廓表示（远景不可分辨）"。实测 `lions` 对象 nv=230912 / face=183040（≈256 只 × 902 面）与该描述一致 | **交付文案禁止写"544 只石狮"**，应写"望柱柱头狮群（远景轮廓化表现）"或明示 LOD 策略；544 只本身是 [二手文献] 口径（另有 540余/500余 并存，FACTS.md 史料节），不作计量事实 | 本 manifest 主控复核（2026-10-04）+ `build_scene2.py:136` |
| 16 | **桥头异兽仅 4 只低模**：`beasts` 对象 nv=384 / face=288 = 4 只 × 96 面，尺寸为主控工作值（高 1.05–1.20m，`build_scene2.py:166`），无文献支撑 | 列 [工作值]；异兽形态属表现层，M4 若做细节需另找依据（实拍近景或文保图档） | 本 manifest 主控复核（2026-10-04） |

## 9. 冻结状态声明（二选一，如实）

### `CONDITIONAL_RECONSTRUCTION_FREEZE`（本项目实况；候选，待用户批准）

判据（spec §1）: `FACTUAL_FREEZE` 要求本体全部关键尺寸有 `[测绘]`/`[档案]` 级来源——**本项目一条都没有**（测绘 0 / 档案 0），宏观尺寸最高只到 `[官方]` 公开口径，构件尺寸依赖 `[工作值]`。故走条件冻结，依赖工作值的条目**逐条列出**：

| # | 常量 | 值 | 无公开来源的量 |
|---|---|---|---|
| 1 | RING_T | 0.40 m | 券圈径向厚 |
| 2 | SPAN_DISTINCT | [4.50,4.90,5.40,5.90,6.40,6.90,7.40,8.00,8.50] | 9 个完整净跨（无逐孔测绘值） |
| 3 | SPRINGER | 1.14 m | 中央孔起拱线（M19 导出值=DECK_Z_TOP−SPANDREL_C−rise·8.50，非独立事实；MET_SPRINGER 恒等校验） |
| 4 | SPRINGER_WATER_MIN | 0.15 m | 起拱线水上硬下限（M19 冬照"springer≥0.15"约束升格判据阈值，无文献） |
| 5 | PIER_W | 2.50 m | 内墩厚（六审后为剖面均值锚，16 墩和恒等式锚） |
| 6 | PIER_W_C | 2.17 m | 中央内墩宽(i=8,9)（七审P0-2 整改值，无文献） |
| 7 | PIER_W_E | 2.83 m | 端内墩宽（与 PIER_W_C 成对，守恒对 C+E=2·PIER_W） |
| 8 | PIER_W_INT | [2.830,…,2.170,…,2.830] | i=1..16 逐墩线性内插表（轴对称，facts 导入断言守护） |
| 9 | PIER_MAIN_W | 2.80 m | 主墩束宽 |
| 10 | PIER_FOUND_W | 3.10 m | 主墩基础宽 |
| 11 | PIER_MAIN_W_C | 2.90 m | 中央孔墩束宽 |
| 12 | PIER_FOUND_W_C | 3.20 m | 中央孔墩基础宽 |
| 13 | BRIDGE_ABUT | 1.35 m | 桥台长（T2b 闭合唯一解，非测绘值） |
| 14 | CROWN_BLUNT_K | 0.40 | 冠钝化强度 s=K·e（七审P1-1 标定，无文献） |
| 15 | CROWN_BLUNT_CAP | 0.020 | 钝化带宽封顶 s≤CAP·a（七审"冠顶最后 3-5% 弧长"，无文献） |
| 16 | CLOSURE_TOL | 0.5 m | MET_CLOSURE 闭合容差（判据阈值参数，终审 I12 落地；现脚本判据值承 T2b 计划稿，无文献） |
| 17 | ARCH_RATIO_TARGET | 0.56 | MET_ARCH_RATIO 券形设计意图 f/l（判据阈值参数，六审标定 0.56；qa_bridge 比对 rise_ratio 剖面中心） |
| 18 | ARCH_RATIO_TOL | 0.02 | MET_ARCH_RATIO 容差带宽（判据阈值参数，终审 I12 落地；现脚本判据值，无文献） |
| 附 | ARCH_RATIO | 0.50 | [图像推导]，非米制来源，同列依赖非测绘证据 |

**2026-10-06 M19 冬照重标定后的等级变动**（台账事实，测试锁"工作值逐条列出"）: `DECK_Z_TOP`（7.75→7.30）、`DECK_Z_END`（5.05/3.60→2.20）改标 **[图像推导]**（冬照 winter_20201221160537 直读，枯湖基准证伪，见 body_changelog.md M19），移出本工作值清单；`SPANDREL_C/SPANDREL_E/RISE_C/RISE_E` 同批登记为 [图像推导]。原第 12 行 `DECK_Z_AT_PIER` 纵坡控制点表已随 M19 抛物线 deck_z 单一公式废除，常量不复存在。

升级路径: 梁雪《颐和园测绘笔记》、孔庆普《中国古桥结构考察》、严雨 2022 论文（均需线下获取，FACTS.md §5-3）。获批前 `facts.py` 锁定规则按其 docstring: 非工作值条目锁死；改动走 `3d/refs/body_changelog.md` 并重跑本体判据。

### `FACTUAL_FREEZE`：不适用（本项目不满足，如实声明）

## 10. 附属构件接口契约

见 spec `docs/superpowers/specs/2026-10-04-e30-bridge-facts-design.md` §9（由冻结 facts 推导，全部为公式与公式值，无新数字）。M3 附属构件（栏板/望柱/狮/异兽/地形）不得反改本冻结本体。

## 11. T7 配准标定（已回填，T7 commit `d30502f`）

- 判据工具: `3d/register_overlay.py`（SHA256 `7092146c922d9a3637d1714623bc3ebe6d1ebef5c494271c94c122a48249b134`；T8 只引用不运行；2026-10-05 终审 I3 在判定路径增补券洞表硬判 `void_verdict`——渲染侧孔数须 == facts.N_SPAN 且逐孔 \|Δxc\|≤VOID_XC_TOL，此前该判只存在于文档）
- 阈值（扰动标定，依据见常量注释块）: **OVERLAY_IOU_MIN = 0.76**（E2 可分: 可接受[0.8046,0.8373] vs 不可接受[0.0030,0.7216] 取中点；基线实测 **0.8070 PASS，余量 0.047**）；**VOID_XC_TOL = 0.02**（券洞表 xc 轴: 可接受 max 0.0000 vs 缺孔信号 min 0.0442 中点）
- 复现: `3d/refs/calibrate_iou.py`（SEED 20261004，复现命令见文件 docstring）
- 对叠图: `3d/refs/overlay_M2.png`；T7 报告: `.superpowers/sdd/e30-briefs/task-task-7-report.md`
- 渲染对照（加分项）结论: **无判别力**（§6/§8-11），已从判据中移除；T7 实测重渲前后 E2 基线 4 位小数不变（0.8070）——渲染噪声与桥轴 112° 修正对判据无影响（已由 T7 写入 FACTS.md §7）

| `3d/tools/cert_gates.json` | `dd8f7bbfaa650bea89456e250163208ced843d45533ae3fc550ae4fa80ddc667` | M11-D 事前冻结门(八审后补 hash 证据; 冻结于反演跑前, commit f62ea63) |
