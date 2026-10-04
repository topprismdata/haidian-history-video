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
| `3d/facts.py` | `10a32dc629766e9c481dad34279918aa2b03284cab7caac4ce16055035999171` | 19 条本体条目；等级分布见 §9 |
| `3d/assumptions.py` | `3a2eb2ed1f47446d0b9e278f792d8e12aa7fb435dbcf9a0d712fa96cf7201fec` | 假设层，不进冻结，改动须记录 |

等级分布（facts.SOURCES 19 条）: **官方 6**（BRIDGE_LEN / N_SPAN / DECK_UP_W / DECK_DOWN_W / PUBLISHED_GENERAL_WIDTH / PUBLISHED_BRIDGE_HEIGHT）、**图像推导 1**（ARCH_RATIO）、**工作值 12**（清单见 §9）。**测绘 0 / 档案 0** —— 故本体只能走条件冻结（§9）。

## 2. 生成器与判据（管线 commit 与文件哈希）

管线 HEAD: `35e0ccf`（"docs(e30): T6 Step0 标记完成(T5已修C6与法线工序)…"，冻结包提交前的最后管线 commit）。冻结包自身的 commit 哈希在用户批准后回填 `3d/refs/body_changelog.md`。

| 文件 | SHA256 | 角色 |
|---|---|---|
| `3d/bridge_geom2.py` | `8990d5e80d856c5788365e136a4820a125b1b6574ee2f2d55d179820dc727296` | 纯几何（消费 facts，零字面尺寸） |
| `3d/build_scene2.py` | `ffb53006bd860149b34d9332fc471c6f13ff8d0d24911fa10199c46220e1edad` | 场景构建（C6 后消费 facts.BRIDGE_ABUT=1.35） |
| `3d/qa_bridge.py` | `e8e6684bb5a7016e700bb8485a78959aa0f95e3224ddc0df4967311bacb4f64e` | L1 判据（纯数据） |
| `3d/qa_l2.py` | `315898346b895a07bb887a3c036fe90edac4d43c6c4d61e0cccc66228aebd34e` | L2 判据（开 blend 查 evaluated mesh） |
| `3d/materials.py` | `590c528508637a25e330d9fb67c1bb0bf2cc3554f1383cf28589f2357b99b35b` | 程序化材质（无 random，节点内置噪声同版本确定） |
| `3d/lions.py` | `aa4c3b3e3f0314da3594a4c070aee4722660ee581a88b5122f5db5406610d627` | 狮母题（自带 LCG，seed 显式入参，确定） |
| `3d/ortho.py` | `2fe76ce0baedd79773e4aef43ae9321cf4fac9f1c325352a05bde841b4ee4879` | 正交出图（seed 显式） |
| `3d/render_shot.py` | `957322629203d449aebe660e7912c0c113f3206bb55f120abf2f75b0d9e5a247` | 机位渲染（seed 显式） |
| `3d/shot_auto2.py` | `1a46bcec6997df0f6e45c3a7e623051cf1b900c1ff826a58b094e2e0f59c63e2` | 自动取景渲染（**seed 未显式**，见 §6 偏差 7） |
| `3d/freeze_hash.py` | （随冻结包提交，以提交版为准） | 核心几何哈希工具 |

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
| MET_CLOSURE | 0.5 m | qa_bridge.py | T2b 闭合口径（N_SPAN−1 个内墩）；阈值承计划稿 |
| WALL_NORMAL θ | 6° | qa_l2.py | 离散弦面理论半扇形角 π/NSEG_ARC/2≈2.25°，G2 取 6° |
| WALL_NORMAL 采样带 | \|y\|<7.0；z>SPRINGER+0.02；\|n_y\|<0.5；\|r−a\|≤0.15 | qa_l2.py | T5 实测修订：剔除 26 个洞缘倾斜 n-gon（§8-1）；负控翻"采样带内前 10 面"（R3） |
| IMPOST_ANCHOR | 0.5 m（xz 平面距离） | qa_l2.py | T5 修订：起拱线石是 x×z 纵剖面陈述，3D 距离版假红 34/34 |
| VOUSSOIR_IN_VOID | r < a − MESH_TOL | qa_l2.py | 2026-10-04 修订：券石内缘=拱腹，须加径向条件否则全孔误杀 |
| L3/T7 阈值 | **待回填** | register_overlay.py（T7 交付） | Brumana 2019（精度须与目标挂钩）+ Lague 2013（裸距离阈值须配置信区间）；**若无判别力须如实报告** |

实现参数（非文物事实，不冻结）: NSEG_ARC=40, NSEG_X=240, SEG=40；建模假定: BODY_BOTTOM=−2.20, BRIDGE_ABUT_TARGET=2.00（GPT v4 未裁决提案，仅属性透传）。

## 6. 渲染图哈希 + seed

seed 政策: `ortho.py` / `render_shot.py` 显式 `cycles.seed=20261004`、`use_animated_seed=False`；Cycles 自适应采样 + OpenImageDenoise 同机同版本确定。**同机同 build 承诺可逐字节复现；跨机/跨 GPU 不承诺。**

冻结候选（2026-10-04 采集，T6 出图期间快照；冷重建后以重建值为准）:

| 文件 | SHA256 | seed |
|---|---|---|
| `ortho_side.png` | `0c29503b5afc1669173daffbf262382cb1b941fd8f0c731e0e054e9500af36fc` | 20261004 |
| `ortho_front.png` | `41a1525825e65467cebf18a1d702aa278e43b7dbbe6c5469a3e6b643731d3a9c` | 20261004 |
| `ortho_top.png` | `38d483a5b461f2d0128a5ac6aa76c5224974b12e840633d35d832e49caac27fc` | 20261004 |
| `ortho_arch.png` | `20f24fde030298e4124a9f9b9de5fceb76a53ebcc304ae6023f92223445da84f` | 20261004 |
| `shot_hero.png` | `e037dcfd23d664a7db1d3d047ee2279cb921a4bccd9ac32883c6df0b10eb0061` | 未显式（§8-7） |
| `shot_arch.png` | `54649219c37eeeef89ce0e127d6d2dd4f6295089fac726c59d61d885a588c1b4` | 未显式（§8-7） |
| `shot_side.png` | `cbb4bfc1d21db6f67422bf6d7ed93e88d6c0ceaa90d4d6a0877a75adc126cd12` | 未显式（§8-7） |

M2.5 冻结包机位口径（简报 G3）: ortho side 2200px + hero/arch 1600px/96spp；**rail/lion 特写属 M3 附属件，不在本体冻结包**。

## 7. 冷启动重建验证（G3 硬门）

**状态: 待执行**（等主控确认并发隔离窗口后删除产物重建；本节结构先行，对照表回填）。

流程: ①记录候选（本 manifest §1-§6 + 下表候选列）→ ②删除 `e30_bridge.blend` 与全部渲染产物 → ③干净状态依次 T4 构建（`blender -b --python build_scene2.py`）→ T5 L2（正检+负控）→ T6 渲染 → T7 标定 → ④对照。

| 项 | 冻结候选 | 冷重建 | 一致? |
|---|---|---|---|
| `bridge_body` sha_sorted | `861d8836b1704067d537ab7e7945f4a247043d9856743ab99e45cc40cea150f2` | 待回填 | 待回填 |
| `bridge_body` sha_order | `5a5c923275057a127fec2138a53b5b4a02bc66750639fb82978601e82b113674` | 待回填 | 待回填 |
| `voussoir` sha_sorted | `b4421770a9e7951965968341c8a3174433377fe3c326abc1c7a4ca5cc4db047f` | 待回填 | 待回填 |
| `voussoir` sha_order | `1c7ded704ed262389bcab794dcc733396f76703ef8aa825ee36c04a0c8173a49` | 待回填 | 待回填 |
| `impost` sha_sorted | `5154f49e49d7af1e52ba3b5cb710b9ada7c8a437295b86c99397e850e6aa0c0a` | 待回填 | 待回填 |
| `impost` sha_order | `13743527ae240699e76fc6365ab37b72537614eb76e9f37c905f4b987a30adf9` | 待回填 | 待回填 |
| `bridge_body` 顶点/面数 | 4409 / 2260 | 待回填 | 待回填 |
| `voussoir` 顶点/面数 | 1656 / 1242 | 待回填 | 待回填 |
| `impost` 顶点/面数 | 136 / 34 | 待回填 | 待回填 |
| `bridge_body` 世界 bbox | x[−34.864,34.864] y[−72.273,72.273] z[−2.2,7.75] | 待回填 | 待回填 |
| L1 fail 数 | 0 | 待回填 | 待回填 |
| L2 正检 | ok=true, warn=0 | 待回填 | 待回填 |
| L2 负控 | 翻 10 面 → FAIL(被抓) | 待回填 | 待回填 |
| pytest | 37 passed | 待回填 | 待回填 |
| `ortho_side.png` SHA | §6 | 待回填 | 待回填 |
| `shot_hero.png` / `shot_arch.png` SHA | §6 | 待回填 | 待回填 |

判读规则: `sha_sorted` 不一致 = **不可复现，冻结失败**（如发生：逐项归因浮点非确定 vs 隐藏状态如 seed，如实记录，不"差不多"放行）；`sha_order` 不一致而 `sha_sorted` 一致 = 布尔求解器顶点顺序非确定，记 §8 豁免。渲染 PNG 哈希不一致但几何与判据一致 = 渲染层非确定（去噪/采样），单列归因不算冻结失败。

## 8. 已知偏差豁免表

| # | 偏差 | 处置 | 依据 |
|---|---|---|---|
| 1 | 26 个洞缘倾斜 n-gon（\|n_y\|≈0.878，与朝心夹角 63–69°，9–15 边）——carve 在洞缘并出的缘饰刻面，**无判据覆盖** | WALL_NORMAL 采样带以 \|n_y\|<0.5 过滤不测它；缘饰刻面列 M3 前表现层待办，不由本体判据承担 | task-task-5-report |
| 2 | 参考掩膜桥带仅 843×44px（62px 高） | L3 只能声明"构图与轮廓一致性"，**禁止**声称逐拱轮廓校核 | FACTS.md §6.2/6.4 |
| 3 | 正交投影消掉尺度-深度可解性 | 照片只能约束平面内轮廓；**测不到**拱圈矢高/桥身纵坡/券石厚度等面外形变 | FACTS.md §4c.3 |
| 4 | 渲染 vs 单张照片无学术定量范式 | 像素层判据只能声明"结构与照片不矛盾"，**不能**声明准确性 | FACTS.md §4c.3 |
| 5 | C2 桥宽双官方口径（6.56 vs 8.0） | DECK_UP_W=6.56 采用；8.0 并存登记禁止覆盖 | FACTS.md C2 |
| 6 | C3 高 7.0 测点未注明 | DECK_Z_TOP=7.75 工作值；PUBLISHED_BRIDGE_HEIGHT 禁止映射 | FACTS.md C3 |
| 7 | `shot_auto2.py` 未显式设 seed（继承场景默认 0，`use_animated_seed=False`） | 复现依赖 Cycles 默认值不变；M4 渲染契约锁定时显式写入（不回改 T6 当前工具） | 本 manifest §6 |
| 8 | C4 走向三值并存（90/112/135） | BRIDGE_AXIS_AZ=112 建模值，**不冻结为事实**；M5 日照判据裁决前不得锁死方位 | FACTS.md C4 |
| 9 | `.blend`/渲染产物不入库 | 设计决策：可从零重建，真相源=脚本+数据 | 本 manifest 头部 |
| 10 | T7 标定结果 | 占位，T7 交付后回填（含阈值标定与"无判别力"如实报告义务） | §5 L3 行 |

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
| 附 | ARCH_RATIO | 0.50 | [图像推导]，非米制来源，同列依赖非测绘证据 |

升级路径: 梁雪《颐和园测绘笔记》、孔庆普《中国古桥结构考察》、严雨 2022 论文（均需线下获取，FACTS.md §5-3）。获批前 `facts.py` 锁定规则按其 docstring: 非工作值条目锁死；改动走 `3d/refs/body_changelog.md` 并重跑本体判据。

### `FACTUAL_FREEZE`：不适用（本项目不满足，如实声明）

## 10. 附属构件接口契约

见 spec `docs/superpowers/specs/2026-10-04-e30-bridge-facts-design.md` §9（由冻结 facts 推导，全部为公式与公式值，无新数字）。M3 附属构件（栏板/望柱/狮/异兽/地形）不得反改本冻结本体。

## 11. T7 配准标定（占位）

- 工具: `3d/register_overlay.py`（T7 交付后回填路径与用法）
- 阈值标定: 待回填（扰动标定要求 + 无可分性时如实报告义务）
- 对叠图路径: 待回填
