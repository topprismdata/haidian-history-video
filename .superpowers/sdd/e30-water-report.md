# E30 WaterFix 报告：水面/岸坡观感修复（侦察建议 1–5）

- 日期: 2026-10-05 · agent: WaterFix · 分支: e30-bridge-body（未 commit，按多 agent 并发约束）
- 改动文件: `3d/materials.py`（仅 `water_material`/`earth_material` 内部，**函数签名零改动**；stone/marble/qingshi/fog 未动）、新增 `3d/ab_water_split.py`（A/B 渲染）、`3d/ab_water/measure_ab.py`（量化）。零新几何，本体三对象未触。
- 登记: `3d/refs/body_changelog.md` WaterFix 节；`3d/refs/freeze_manifest.md` §2 materials 行已同步 `873c0a6dede8f49b7f9b4df516918d041f692976ff39c9826b7cb29279f3a03a`。

## 1. 参数落点（对任务清单）

| # | 清单 | 落点 |
|---|---|---|
| 1 | bump .20→.30–.35；第三频权 .18→.28 或加第四频 scale≈30 | strength **0.32**；权 **0.28** 且加第四频 `_noise(30.0, 2.0, 0.14)`（h34 链） |
| 2 | Mapping (0.6,2.0,1.0)→(2.0,0.6,1.0) | 已改，风纹转 90°（旧方向沿桥纵深 → hero 里抹成竖条） |
| 3 | rough 底 .04→.02、斑块 .05→.09 | 已改（0.02 + noise×0.09） |
| 4 | earth base×0.8、亮斑倍率 1.55→1.8 | 干基 ×0.8；亮斑 **(1.80, 1.55, 1.30) 作用于原 palette**。⚠ 对字面读法的偏离及依据：若把 1.8 乘在 ×0.8 后的 base 上，净对比 0.8×1.8=1.44 < 旧 1.55，雾占比反升，hero 实测左岸 sat **反降**（S1=18.94 / S2=20.02，均 < A=20.73）；按治#4 可观测目标做 S1–S5 变体扫描，S4 (1.80,1.55,1.30) 胜出（sat 23.38，G 1.55 保 G>R>B 橄榄序）。扫描脚本 /tmp/wfix_sweep.py（一次性），结果记于 changelog |
| 5 | earth 水线湿带 z∈[0,0.5] 复用 stone waterline 节点式 | SeparateXYZ→SUBTRACT 0.5→DIVIDE −0.5→Clamp→MixRGB（与 stone_material L143-155 同构），z=0.5 干→z=0 全湿渐变压暗至干基 ×(0.38,0.42,0.34)，水下保持湿色 |

## 2. A/B 设计与有效性

- 开 `3d/e30_bridge.blend`，**单进程单相机**背靠背渲 A、B → 差异只来自水/岸材质，免疫并行 rebuild/渲染竞争。相机逐条复刻 shot_auto2 hero：`Nv*0.90+Bv*0.42+(0,0,0.06)`、dist×1.02、`camera_to_view_selected`×14、z=3+size.z×0.06、50mm、clip_end 20000；res 800×450、32spp、seed=20261004、use_animated_seed=False、denoise on、METAL GPU。带坐标按 1600×900 侦察值等比 ÷2。
- 对象定位：先打印 blend 对象名单（任务要求），水=`water`、岸=`shore_bank`（各 1 对象 1 槽），换材质后自证 swap 成功。
- **事故**：任务中途 blend 被并行集成批（M7 接线）rebuild，把当时盘上**中间态**材质烧进 blend，"blend 原样=A"失效。A 侧改为 `git show HEAD:…materials.py`（92f95fa，C2 落地态=改前状态）落盘 `/tmp/materials_old.py` 后由 `ab_water_split.py` argv[2] 重建 water/earth。渲染前探针自证 A≠B：water bump **0.20/0.32**、earth 节点 **7/12**。（首版探针曾在 swap 后读槽位、读到新材质打假自己——已修为渲染前抓快照，探针保留为常驻护栏。）
- **遗留给主控**：现 blend 内 earth 仍为 v1 中间态（water 已是终版），下次接线 rebuild 以终版 materials.py 为准即可。

## 3. 量化 A vs B（官方对：`ab_hero_A_old.png` / `ab_hero_B_waterfix.png`）

| 带(1600×900 口径) | 指标 | A | B | Δ | 方向 | 判读 |
|---|---|---|---|---|---|---|
| 前景水 y650-900 全宽 | 高频能量（laplacian \|mean\|） | 2.1672 | 2.6448 | **+22.0%** | B>A ✓ | 治#2：前景死水出现波纹（并排图下半段肉眼可辨） |
| 倒影带 x340-1520,y460-610 | 水平/竖直梯度比 Gx/Gy | 0.9923 | 0.9518 | −4.1% | B<A ✓ | 治#1：竖抹柱消退、横向波痕出现；量级温和（32spp 去噪后残留镜面平滑） |
| 水线带 y445-465 全宽 | 相邻行均亮最大跳变 | 21.2821 | 21.3153 | ≈0(+0.03) | B<A ✗ | **该线主体是 mesh 剪影，shader 不可达**（分条实测：桥基/水 30.93→30.96、右端桥台 27.24→27.81、左条 0.40→0.49——全宽硬线由桥体石作与远岸几何边构成） |
| 水线带同上 | 带内亮度方差 | 33.2769 | 33.3367 | +0.06 | B>A ✓ | 湿带结构方向 ✓，量级弱（同因：带内被几何边主导） |
| 左岸 x0-135,y420-485 | HSV 饱和度 | 20.7393 | 23.3806 | **+12.7%** | B>A ✓ | 治#4：橄榄色回饱和（V 124.0→116.4 同时变暗，色序 G>R>B 保持） |

岸侧湿带单独量化（任务外补充，证明 #5 落地生效）：左岸楔接触线上缘 **119.2→106.7**（湿暗 rim 形成）、岸面带 y228-238 均亮 115.8→113.5、接触线区出现明确暗 rim（A 该区无可见边 jump 1.70，B 10.12@y239）。

## 4. 图路径（png 不入库，测量脚本入库）

- A/B 单图：`3d/ab_water/ab_hero_A_old.png`、`3d/ab_water/ab_hero_B_waterfix.png`
- 并排：`3d/ab_water/ab_hero_AB_side.png`（左 A 右 B）
- 量化 JSON：`3d/ab_water/measure.json`；复算：`python3 3d/ab_water/measure_ab.py <A> <B>`
- 复渲命令：`blender -b e30_bridge.blend --python ab_water_split.py -- 800 32 <旧materials.py路径>`

## 5. 判据重跑（全绿）

| 判据 | 结果 |
|---|---|
| freeze_hash 三核心对象 | **逐位一致**（bridge_body 861d8836… / voussoir b4421770… / impost 5154f49e…，nv 4409/1656/136）——纯 shader 零触几何 |
| qa_l2 正检 | **ok=true**，fail/warn/skip = 0/0/0，sampled=494，exit 0 |
| qa_l2 负控 | **CAUGHT**（翻 10 面全被 WALL_NORMAL 抓到，10/494），exit 0 |
| register_overlay | **VERDICT PASS**：重渲 ortho_side 2200px 后 SILHOUETTE_IOU=**0.8089**（min 0.76；冻结基线 0.8070，差 0.0019 属 §8-11 渲染非确定带）；VOID_VERDICT n=17，max\|Δxc\|=**0.0181** ≤ 0.02 不变——水/shore_bank 在 ortho 隐藏名单，实测不受影响 |
| pytest（`tests/ e30_shikongqiao_video/tests/`） | **1706 passed, 0 failed**（唯一红曾为 manifest materials 行待同步，落盘后复跑转绿；无 build_scene2 在途漂移残留） |

## 6. 未治项声明（几何/表现层类，不在本任务）

- **#5 引道白色浮板**（x135-330,y425-452）：几何问题，任务原文排除，未动。
- **#6 右端缺岸**（x1540-1600）：远岸出画/桥端截断，几何构图类。
- **#7 无水平线分离**（y450-560 水/低空同调）：需表现层另案（水面远区色调/雾分层）。
- **#8 远端翼墙暗块剪影**：scout 已划给树冠带任务。
- **#3 残留**：y452-458"全宽硬线"的主体（桥体石作入水线=冻结 stone_material 禁改 + 远岸 mesh 剪影）shader 不可达；本任务的 earth 湿带只覆盖岸侧并已量化生效。该线全宽消除需另立任务（涉冻结文件，须主控裁决）。
