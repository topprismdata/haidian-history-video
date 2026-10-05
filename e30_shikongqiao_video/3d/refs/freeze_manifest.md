# E30 M2.5 本体冻结包 manifest

- 日期: 2026-10-04（T8）
- **冻结状态: `CONDITIONAL_RECONSTRUCTION_FREEZE`（候选）——未锁定，待用户裁决**（§9）
- 冻结范围: **本体**三对象 `bridge_body` / `voussoir` / `impost`（含布尔进 body 的 17 券洞、16 墩、双桥台）
- **不在**冻结范围: `deck_rail` / `lions` / `beasts` / `pier_plinth` / `deck_cornice` / `abutment_ground` / `water`（M3 附属构件 / M5 环境预置件，受 spec §9 接口契约约束但不受本冻结保护）
- 判据语义: 只有 `fail` 阻塞；`skip`=未执行不算通过；每条判据必须有故意破坏用例且破坏被抓
- 配套工具: `3d/freeze_hash.py`（核心几何哈希的唯一定义点，冷重建对照用它跑）
- `.blend` 不入库（gitignore，设计决策）：真相源 = facts/assumptions + 生成器脚本；`.blend` 是可从零重建的产物

## 1. 事实/假设层快照

| 文件 | SHA256 | 说明 |
|---|---|---|
| `3d/facts.py` | `f74f8312415647f8e1bf88c848ddca45829b77ae6960c25cdad6b7726db52012` | 22 条本体条目（终审 I12 新增 3 条判据阈值参数）；等级分布见 §9 |
| `3d/assumptions.py` | `eaf0493868ea6f0c7b80e70ca08e6c8e37cfbfc74e610cbcd5157f35286e5be8` | 假设层，不进冻结，改动须记录（终审 I13 删 `BRIDGE_ABUT_TARGET`、I9/I12 外置 `VOID_CUT_MARGIN`） |

等级分布（facts.SOURCES 22 条）: **官方 6**（BRIDGE_LEN / N_SPAN / DECK_UP_W / DECK_DOWN_W / PUBLISHED_GENERAL_WIDTH / PUBLISHED_BRIDGE_HEIGHT）、**图像推导 1**（ARCH_RATIO）、**工作值 15**（12 条本体尺寸 + 3 条判据阈值参数 CLOSURE_TOL / ARCH_RATIO_TARGET / ARCH_RATIO_TOL，清单见 §9）。**测绘 0 / 档案 0** —— 故本体只能走条件冻结（§9）。

## 2. 生成器与判据（管线 commit 与文件哈希）

管线 HEAD: `35e0ccf`（"docs(e30): T6 Step0 标记完成(T5已修C6与法线工序)…"，冻结包提交前的最后管线 commit）。冻结包自身的 commit 哈希在用户批准后回填 `3d/refs/body_changelog.md`。

| 文件 | SHA256 | 角色 |
|---|---|---|
| `3d/bridge_geom2.py` | `e985dc72fdc0382d3d8d221ed58e89327036803564e8ee8230aa31f6eeecb4c7` | 纯几何（消费 facts，零字面尺寸；终审 I13 删 BRIDGE_ABUT_TARGET 死透传、I14 闭合自检改 (N_SPAN−1) 口径、I9/I12 券洞余量改引用 assumptions.VOID_CUT_MARGIN —— 几何 SHA 不变，冷重建 A/B 实测 bridge_body sha_sorted 与冻结候选逐位一致） |
| `3d/build_scene2.py` | `c4d0e9e1b3e9f5f78f914dd10b4c5b20d3b8b10fda2b2a8d75c633d6b54c9b12` | 场景构建（C6 后消费 facts.BRIDGE_ABUT=1.35；2026-10-04 补入 abutment_ground 桥轴旋转，核心三对象几何 SHA 未变；2026-10-05 M4 表现层：abutment_ground 改燕翅型桥台(前墙+八字燕翅墙)、新增 shore_bank/fog_volume 环境件——本体 bridge_body/voussoir/impost 顶点未动，qa_l2 正检 QA_L2_OK、register VERDICT PASS(IoU 0.8070 与冻结基线一致、void max\|Δxc\|=0.0181 不变)，见 body_changelog.md M4 节；2026-10-05 M6 蹲狮重雕：import 换 lions2(母模 EXACT 布尔并+SIMPLE 细分, 单 mesh 连通域=1)，build_lions_bm 合并版改 place_lions linked duplicates(256 对象/2 unique mesh)，build_scene2 其余零改动——freeze_hash 三对象逐位一致(861d8836…/b4421770…/5154f49e…)，hero A/B 同机位逐像素差 0.123% 且全部落于 y∈[359,461] 狮带，见 body_changelog.md M6 节；2026-10-05 M4b 雾岸修补：shore_bank 网格 24x40→72x120+横向随 u 收窄(±30→±46m, 埋翼墙/引道切面)+两档高频正弦岸线（本体零改动，freeze_hash 三对象逐位一致），见 body_changelog.md M4b 节） |
| `3d/qa_bridge.py` | `22edb160edaacdff8316fb51ac41accf7b20e03f92456a050c14ff1a2603a530` | L1 判据（纯数据；终审 I11 损坏 facts 报告不崩溃、I12 阈值消费 facts.CLOSURE_TOL/ARCH_RATIO_TARGET/ARCH_RATIO_TOL） |
| `3d/qa_l2.py` | `4457508cee6e53d5b5c6f0e03b932ab3ff7e6088115db614b6923bab8fa5beb2` | L2 判据（开 blend 查 evaluated mesh；2026-10-05 终审 I4/I6：零采样记 skip 且 ok=false，负控脱靶/未抓到一律 exit 1） |
| `3d/materials.py` | `a0d0e34cd86123579194b7f3c884456dcb09e39b7081710efb8292fbdfd003a1` | 程序化材质（无 random，节点内置噪声同版本确定；2026-10-05 M4 表现层：stone 增逐块色差+bump 砌缝凹槽、water 三频波纹+粗糙度斑块、新增 earth/fog 材质——纯 shader 层，不触 mesh；2026-10-05 C2 纯追加 qingshi_material（青石桥体，来源逐字核实见 body_changelog.md C2 节），既有函数零改动，freeze_hash 三对象 sha 逐位不变；2026-10-05 WaterFix water/earth 调参（水 bump .20→.32+第四频 scale30+风纹 Mapping 转 90°+rough .02/.09；earth 干基 ×0.8+亮斑 (1.80,1.55,1.30) 作用原 palette+水线湿带 z∈[0,0.5]）——纯参数/节点零几何，函数签名不变，hero A/B 量化见 3d/ab_water/，见 body_changelog.md WaterFix 节） |
| `3d/lions.py` | `aa4c3b3e3f0314da3594a4c070aee4722660ee581a88b5122f5db5406610d627` | 狮母题（自带 LCG，seed 显式入参，确定） |
| `3d/ortho.py` | `603140be8d42e0cd30992a092ab8b07a6bae55f33557c02c8d57fcda14a763d6` | 正交出图（T6 当日演进：新增 top/arch 机位，首采哈希 2fe76ce0… 已被取代；2026-10-05 终审 I2 回填——`4ce8475` M3-1 加水线 sidecar 后未同步 manifest；2026-10-05 M4 隐藏名单补 shore_bank/fog_volume 环境件，正交立面只认本体轮廓，IoU 0.8070 不变；M4b 相机 clip_end=20000——默认 1000m 截断雾盒出射面的根因修复同步到此，正交视图环境件仍隐藏，重渲后 VERDICT PASS 不变） |
| `3d/render_shot.py` | `bef2368ccecb732aff765930aed3c7165e813d691eb849c0741b73630c647275` | 机位渲染（seed 显式；2026-10-05 终审 I2 回填实际盘上哈希——原记录 `95732262…` 是 `cf11ac3` 改文件前的旧值） |
| `3d/shot_auto2.py` | `4d2dc0877081f8816cc6c179030e301804fd500e9a7454b8f3fa04ac51ebfde9` | 自动取景渲染（主控 2026-10-04 补 seed 显式化，已提交；2026-10-05 M4b 修天空硬边：相机 clip_end 1000→20000——默认 1000m 截断雾盒(侧壁 2600m/顶 123m)出射面, >1000m 出射的天空射线体积栈为空致雾效 binary 消失(实测硬边在仰角 6.9°=y173 处 Δ7.68, 修复后 0.79), seed=20261004 不变） |
| `3d/freeze_hash.py` | `120e8e40be6d0992410809dbf5cd8b8347176f8308a61716884d45e154c4f370` | 核心几何哈希唯一定义点（随冻结包 commit `6d8a838`） |
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
| MET_ARCH_RATIO | 0.50±0.05 | facts.py `ARCH_RATIO_TARGET`/`ARCH_RATIO_TOL`（终审 I12 落地，qa_bridge 消费） | 券形设计意图半圆，与 ARCH_RATIO 同源（图像推导比例假设）；容差承现脚本判据 |
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

**状态: 几何硬门已通过（2026-10-04 实测执行）**。流程: ①删除前重采候选态（blend/核心哈希/L2 正检+负控/渲染 IDAT 存档）→ ②删除 `e30_bridge.blend`+`e30_bridge.blend1`（渲染产物按主控并发约束暂不动，`ortho_side.png` 留给 T7）→ ③干净状态 T4 `blender -b --python build_scene2.py` → T5 L2 正检+负控 → ④几何对照（硬门）。hero/arch 已重渲为新基线快照（非判据）；`ortho_side.png` 待 T7 释放后重渲记录新基线。

| 项 | 冻结候选 | 冷重建 | 一致? |
|---|---|---|---|
| `bridge_body` sha_sorted | `861d8836b1704067d537ab7e7945f4a247043d9856743ab99e45cc40cea150f2` | 同左 | **MATCH** |
| `bridge_body` sha_order | `5a5c923275057a127fec2138a53b5b4a02bc66750639fb82978601e82b113674` | 同左 | **MATCH** |
| `voussoir` sha_sorted | `b4421770a9e7951965968341c8a3174433377fe3c326abc1c7a4ca5cc4db047f` | 同左 | **MATCH** |
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
| 6 | C3 高 7.0 测点未注明 | DECK_Z_TOP=7.75 工作值；PUBLISHED_BRIDGE_HEIGHT 禁止映射 | FACTS.md C3 |
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
| 1 | DECK_Z_TOP | 7.75 m | 桥面顶标高（官方"高7米"测点未注明，C3 禁止映射） |
| 2 | DECK_Z_END | 5.05 m | 桥端标高 |
| 3 | SPRINGER | 2.50 m | 起拱线高度 |
| 4 | RING_T | 0.40 m | 券圈径向厚 |
| 5 | SPAN_DISTINCT | [4.50,4.90,5.40,5.90,6.40,6.90,7.40,8.00,8.50] | 9 个完整净跨（无逐孔测绘值） |
| 6 | PIER_W | 2.50 m | 内墩厚 |
| 7 | PIER_MAIN_W | 2.80 m | 主墩束宽 |
| 8 | PIER_FOUND_W | 3.10 m | 主墩基础宽 |
| 9 | PIER_MAIN_W_C | 2.90 m | 中央孔墩束宽 |
| 10 | PIER_FOUND_W_C | 3.20 m | 中央孔墩基础宽 |
| 11 | BRIDGE_ABUT | 1.35 m | 桥台长（T2b 闭合唯一解，非测绘值） |
| 12 | DECK_Z_AT_PIER | [5.30,5.53,5.82,6.11,6.40,6.69,6.97,7.29,7.55] | 纵坡控制点 |
| 13 | CLOSURE_TOL | 0.5 m | MET_CLOSURE 闭合容差（判据阈值参数，终审 I12 落地；现脚本判据值承 T2b 计划稿，无文献） |
| 14 | ARCH_RATIO_TARGET | 0.50 | MET_ARCH_RATIO 券形设计意图 f/l=半圆（判据阈值参数，终审 I12 落地；与 ARCH_RATIO 同源） |
| 15 | ARCH_RATIO_TOL | 0.05 | MET_ARCH_RATIO 容差带宽（判据阈值参数，终审 I12 落地；现脚本判据值，无文献） |
| 附 | ARCH_RATIO | 0.50 | [图像推导]，非米制来源，同列依赖非测绘证据 |

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
