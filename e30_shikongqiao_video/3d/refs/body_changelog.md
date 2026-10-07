## M7 (2026-10-05 主控集成批)
- C2 接线: build_scene2 m_body/m_ring 改 qingshi_material(青石 albedo); **M4 暖白基色勘误作废**——
  分档复采 ref_elevation.jpg 全档偏冷(亮-6.2/中-18.3/暗-31.1), M4 采样点误采; 暖属光照不属 albedo。
- build_scene2:344 无源注释「常见做法30-45°」删除, 改引 abutment_design.md 与卫星负读数。
- FACTS.md 补登 C7/C9 补充 + W1(WING_L 矛盾) + 术语约束。
- 冻结影响: 纯 shader+注释+文档, 本体三对象几何零触(freeze_hash 验)。

# 本体变更记录

> 规则（facts.py docstring / spec §7）: M2.5 用户批准后 facts 本体节锁死；此后改锁死条目必须先在本文件登记，再改，再重跑本体判据（L1+L2 正检+负控，判据全绿才算完成）。

## 2026-10-05 WaterFix 水面/岸坡观感修复（建议 1–5）—— 纯材质参数/节点，零几何

**改动文件**: `materials.py`（仅 `water_material`/`earth_material` 内部，**函数签名零改动**，stone/marble/qingshi/fog 未动）、新增 `3d/ab_water_split.py` + `3d/ab_water/measure_ab.py`（A/B 证据）。本体 `bridge_body`/`voussoir`/`impost` 顶点未动（freeze_hash 三对象 sha_sorted 与冻结值逐位一致：861d8836… / b4421770… / 5154f49e…，nv 4409/1656/136 不变）。

**1. water（治#1 倒影竖抹柱 / #2 前景死水）**: bump strength .20→.32；风纹权 .18→.28 + 新增第四频 scale30(权 .14，近机位 sparkle)；Mapping scale (0.6,2.0,1.0)→(2.0,0.6,1.0) 风纹转 90°（旧方向沿桥纵深，hero 里把拱倒影抹成竖条）；粗糙度底 .04→.02、斑块 .05→.09（底更镜、斑块更碎）。

**2. earth（治#4 左岸被雾洗灰 / #3 岸水交界湿带）**: 干基 ×0.8 压暗；亮斑倍率 (1.55,1.42,1.30)→(1.80,1.55,1.30)，**作用于原 palette 而非缩放后 base**——若乘在 ×0.8 后的 base 上净对比 0.8×1.8=1.44<旧 1.55，雾占比反升，A/B 实测左岸 sat 反降（18.94 vs 20.73）；G 用 1.55 保 G>R>B 橄榄序。增水线湿带：复用 stone_material waterline 节点式（SeparateXYZ→SUBTRACT 0.5→DIVIDE −0.5→Clamp→MixRGB），z∈[0,0.5] 渐变压暗至干基 ×(0.38,0.42,0.34)，水下保持湿色。

**3. A/B 证据（`3d/ab_water/`，res 800×450、32spp、seed=20261004、denoise on、METAL GPU、hero 机位逐条复刻 shot_auto2：50mm/clip_end 20000/z=3+size.z×0.06）**。A=git HEAD（92f95fa）materials.py 重建 water/earth，B=盘上终版，单进程单相机背靠背；渲染前探针自证 A≠B（water bump 0.20/0.32，earth 节点 7/12）。带坐标按 1600×900 侦察值等比缩放：

| 带(1600×900 口径) | 指标 | A | B | Δ | 判读 |
|---|---|---|---|---|---|
| 前景水 y650-900 全宽 | 高频能量(laplacian 均值) | 2.1672 | 2.6448 | **+22.0%** | 治#2 ✓ |
| 倒影带 x340-1520,y460-610 | 水平/竖直梯度比 Gx/Gy | 0.9923 | 0.9518 | −4.1% | 治#1 ✓（方向对，量级温和；并排图横向波痕肉眼可辨） |
| 水线带 y445-465 全宽 | 相邻行均亮最大跳变 | 21.2821 | 21.3153 | ≈0 | **该线主体是 mesh 剪影，shader 不可达**（分条：桥基/水 30.93→30.96、右端桥台 27.24→27.81 不变） |
| 水线带同上 | 带内亮度方差 | 33.2769 | 33.3367 | +0.06 | 湿带方向 ✓ 量级弱（同因：带内被几何边主导） |
| 左岸 x0-135,y420-485 | HSV 饱和度 | 20.7393 | 23.3806 | **+12.7%** | 治#4 ✓（V 124.0→116.4 同时变暗，橄榄序 G>R>B 保持） |

岸侧湿带单独量化：接触线上缘 119.2→106.7（湿暗 rim 形成）、岸面带 y228-238 均亮 115.8→113.5。变体扫描（/tmp/wfix_sweep.py，S1–S5）记录：字面读法"1.8 乘缩放后 base"（S1/S2）sat 18.94/20.02 均不达标，S4 (1.80,1.55,1.30) 达标胜出。

**4. 判据重跑（全绿）**: freeze_hash 三对象逐位一致；qa_l2 正检 ok=true（fail/warn/skip 0/0/0，sampled 494）、负控 CAUGHT（翻 10 面全被抓）；register_overlay **VERDICT PASS**（重渲 ortho_side 2200px，水/shore_bank 在 ortho 隐藏名单实测不受影响：SILHOUETTE_IOU=0.8089 与冻结基线 0.8070 差 0.0019 属渲染非确定带 §8-11；VOID n=17，max|Δxc|=0.0181 不变）；pytest 见本节末（唯一红=manifest materials 行待本节同步，落盘后复跑转绿）。

**5. 事故与护栏记录**: ①本任务进行中 `e30_bridge.blend` 被并行 rebuild 重写，把当时盘上**中间态**材质（water 新版+earth v1）烧了进去，首轮"blend 原样=A"失效——A 侧改为 git HEAD 模块重建（`ab_water_split.py` argv[2]），与 blend 内容解耦；**现 blend 内 earth 仍为 v1 中间态，主控接线 rebuild 时以终版 materials.py 为准**。②首版 A/B 探针在 swap 后读槽位，读到新材质打假自己（old=0.32）——已改为渲染前抓快照；探针保留为常驻护栏。

**6. 未治项（几何/表现层类，不在本任务）**: #5 引道白色浮板（几何问题，任务原文排除）；#6 右端缺岸（远岸出画）；#7 无水平线分离；#8 远端翼墙暗块（树冠带任务）；另 #3 的"y452-458 全宽硬线"主体为桥体石作（frozen stone_material，本任务禁改）与远岸 mesh 剪影，earth 湿带只覆盖岸侧，该线全宽消除需另立任务。

---



## 2026-10-05 C2 材质分工来源核实 + 青石材质预备（MaterialSplit agent）—— 本体零改动，接线待主控

**改动文件**: `materials.py`（**纯追加** `qingshi_material`，既有函数签名/行为零改动）、新增独立脚本 `3d/ab_qingshi_split.py` + `3d/ab_qingshi/`（A/B 证据）。`build_scene2.py` 未动（材质赋值接线由主控执行）。

**1. 来源核实（C2 由疑转实）**。两处原文直接抓取全文核对：京报网 2025-12-09 07:14《十七孔桥的金光穿洞，你知道它的来龙去脉吗？》(来源：北京青年报) https://news.bjd.com.cn/2025/12/09/11451647.shtml 与中新网同文转发 https://www.chinanews.com.cn/cul/2025/12-09/10529704.shtml，逐字：**「……特在南湖岛与东堤之间仿照北京卢沟桥，兼收苏州宝带桥特点，以青石筑成桥体，以汉白玉为栏杆，因有17个拱券，故名十七孔桥……」**。京报网 2025-12-24《数字密码》(https://news.bjd.com.cn/2025/12/24/11482771.shtml ，快照级)同句互证。注意：原文只定**石材种类**分工；M4 节"基色暖白"是实拍光照结果，两者不矛盾——基色数值裁决见 A/B，接线决定权在主控。

**2. qingshi_material（追加）**。`base_rgb=(0.305,0.342,0.381)` 线性（≈sRGB 149,157,165 冷灰蓝，青石新出面工作值），复用 `stone_material` 节点栈：joint=0.010 / course_h=0.60 / weather=0.32 / block_var=0.12 / bump 0.30 / rough 0.84（比现 stone_body 接法略强调砌缝块差）。券圈建议略亮变体 `(0.350,0.382,0.418)` 保持券圈可读层次（同现 m_ring>m_body 的相对步进）。

**3. A/B 证据（同 blend 同相机同 seed=20261004，res 800 samples 32）**：`3d/ab_qingshi/ab_hero_A_warm.png` vs `ab_hero_B_qingshi.png`（并排 `ab_hero_AB_side.png`）。材质生效区（两图逐像素差>8 掩膜，占画面 17.7%）实测：A 暖白桥体 mask-mean RGB **(146.0,147.8,148.4)** R−B=−2.3 lum=147.5 → B 青石 **(126.9,132.1,136.8)** **R−B=−10.0** lum=131.3 —— 亮度 −16.2、冷移 −7.7，方向正确量级温和；掩膜外最大差仅 8/255（天空区 ≤1、近水区 ≤2，属去噪/采样抖动级，非结构变化；=0 占 75.9%）。目视：B 桥体青灰、栏杆白线保留、无伪影。

**4. 判据重跑（全绿）**：freeze_hash 三对象 sha_sorted 与冻结值逐位一致（861d8836… / b4421770… / 5154f49e…，顶点数 4409/1656/136 不变）——纯 shader 追加零触几何；L1 `test_l1_body.py + test_checks_l1.py` **207 passed**；L2 正检 **exit 0 / ok=True 零 fail 零 skip**；L2 负控 **exit 0**（护栏按预期抓到扰动）。materials.py 新盘上哈希 `52c68ce3bcaf…` 已同步 manifest §2。

---

## 2026-10-05 M4b 雾岸修补（FogAndBank agent）：天空雾硬边 + 岸坡生硬感 —— 本体零改动

**改动文件**: `shot_auto2.py` / `shot.py` / `shot_auto.py` / `ortho.py`（相机 clip_end）、`build_scene2.py`（仅 shore_bank 环境段）。本体 `bridge_body`/`voussoir`/`impost` 顶点一字未动（freeze_hash 三对象 sha_sorted 与冻结值逐位一致：861d8836… / b4421770… / 5154f49e…）。

**1. 天空水平硬边（主控量化：逐行亮度 y=173 处 Δ=7.68）——根因不是雾盒，是相机 clip_end**。
排查过程：隐藏/改变雾盒顶高（123→60→30）做对照渲染，发现雾效在仰角 >6.9° 的天空整段存在、其下**精确为零**；6.9° = atan((盒顶123−相机2)/1000)，1000 恰是 Blender 新建相机默认 `clip_end`。机制：出射距离 >clip_end 的射线永不注册体积边界穿越，Cycles 体积栈为空 → 该段雾效 binary 消失，在仰角 6.9° 处形成有雾/无雾硬边（此前 M4"盒顶加高消除 1.3° 硬边"实为把硬边推高到 6.9°，未触根因）。**修复 = 出图脚本相机 `clip_end=20000`**（shot_auto2/shot/shot_auto/ortho 四处），雾盒本身零改动。复验：逐行亮度最大跳变 7.680 → **0.794**（阈值 <1.5），全程无雾/有雾对照光滑；seed=20261004 + use_animated_seed=False 不变。
副产物：天空整段进入大气散射（近地平线 τ≈6.5、画面顶 τ≈1.1，光滑过渡），远端拱洞被雾提亮（暗部 +27），远景层次与实拍 haze 口径一致。

**2. 岸坡"生硬立方体"（主控量化：岸缘水平梯度 max=81.7）——shore_bank 网格重塑**。
24x40(4m 刻面/直岸线) → **72x120**，横向宽度随 u 收窄（近桥端 ±30m 埋住翼墙/引道端部垂直切面，向外展至 ±46m 再收），加两档高频正弦（确定性、无随机）让岸线自然弯曲。迭代中实测修掉一个自伤：首版 ±20m 起步把翼墙端部切面露成直边（对照渲染复现后回调到 ±30m）。**量化边界**：暗块区最大水平梯度 107.3 → 98.7——残差属 `abutment_ground` 翼墙（桥体投影内的阴影面，M4 设计的石砌挡墙剪影），非岸坡；且参考照片自身岸线/树线剪影梯度 217–231（`ref_elevation.jpg` 实测），剪影级 per-pixel 梯度天然高，"生硬感"来源（平顶直崖+折线岸线）已消除（两端目视复验：近端圆缓土丘埋住桥基、远端暗块缩为翼墙本体）。岸坡颜色零改动（遵守主控指令）。

**3. 大气透视可测性复验（无雾对照渲染归因）**：按亮度分类采样（避开边缘），雾致对比度压缩近端 11.0 → 桥中 29.7 → 远端 36.3，随距离单调 ✓；亮部雾差 −8.0（近）/−9.3（远），暗部雾差 −3.0（近）/**+27.0（远）**——远端拱洞被雾明显提亮，两端差异可测且方向正确。

**4. 判据重跑（全绿）**：qa_l2 **QA_L2_OK**；register_overlay **VERDICT PASS**（SILHOUETTE_IOU=0.8070 与冻结基线一致；VOID n=17，max|Δxc|=0.0181 不变；ortho 隐藏名单含 shore_bank/fog_volume，重渲后无污染）。pytest `tests/ e30_shikongqiao_video/tests/`：1703 过 / 3 红，红项全部落在本任务外的 `facts.py`（他人并行改等级注释中，见 git status）+ 由其引发的 manifest facts 行漂移，与本次改动文件零交集。

---

## 2026-10-05 M4 表现层改版（VisualPolish agent）：燕翅桥台/岸坡/雾 + 材质感 —— 本体零改动

**改动文件**: `materials.py`、`build_scene2.py`（仅环境/材质段）、`ortho.py`（隐藏名单）。本体 `bridge_body`/`voussoir`/`impost` 的生成路径与顶点**一字未动**。

**1. 桥台改燕翅型（接岸）**。文献依据：茅以升基金会《中国古代石拱桥——古桥各部名称》——桥台三型（带燕翅/凹字/一字），前墙=金刚墙，八字挡墙=燕翅墙。原 `abutment_ground` 楔形块垂直插水（"桥漂着"根因）。现环境段重做为：引道缓坡（根部断面与本体端墙收分齐平、battered 裙板——垂直裙曾留 V 形黑三角缝，实测复现后修复）＋两侧 35° 八字燕翅墙（展开角/翼长 24m/墙厚 1.4m/岸坡顶 2.1m 均为[工作值]，常见做法 30–45°）＋两端 `shore_bank` 岸坡地形（确定性正弦起伏，非随机位移）。

**2. 材质（纯 shader，不触 mesh）**。桥体基色按主控实测订正为暖白 (0.79,0.765,0.70)——「青石筑桥体」是石材种类，实拍亮部 RGB(252,245,227) R−B=+25 偏暖，文献字面≠渲染颜色；stone 增逐块色差（块编号采样噪声）＋bump（砌缝凹槽+石面颗粒）；water 三频波纹 bump＋粗糙度斑块（去"完美镜面"）；新增 earth（岸坡植被）/fog（体积散射）。

**3. 大气透视**。`fog_volume` 均匀体积散射盒（密度 0.0018/m 工作值；0.003 实测过浓全画面发灰弃用）＋sky 气溶胶 0.45。盒顶加高消除 1.3° 侧壁出射硬边带。

**4. 判据重跑（全绿）**：qa_l2 正检 **QA_L2_OK**（494 拱腹面，fail 0）；register_overlay **VERDICT PASS**（SILHOUETTE_IOU=0.8070 与冻结基线一致；VOID_VERDICT n=17，max|Δxc|=0.0181≤0.02 余量不变——桥台/岸坡改动未移动任何券洞）。无雾对照渲染证明雾效应可测且方向正确（远端中间调 +1.3% vs 近端 +0.6%，亮部向雾色收敛）。

**5. 渲染观感复核（read 目视）**：桥两端接入岸坡不再悬空；望柱/狮/靠山兽近景确认构件在位、比例合理（主视角可见性差是对比度问题，未改尺寸——无文献依据）；水面倒影柔碎有波纹；石材暖白有砌缝与块差。遗留：靠山兽/狮为低模（manifest §8-15/16 已豁免，LOD 策略）；大气透视效应偏弱（密度受"不发灰"约束）。

---


## 2026-10-04 M3-3 复核：券洞内壁"纯黑"也是误判，撤回

**实测**（采样洞内 vs 白石亮度）：

| | 洞内:白石亮度比 | 洞内亮度范围 |
|---|---|---|
| 参考照片 `ref_elevation.jpg` | **0.17** | — |
| 当前模型 `shot_hero.png` | **0.12** | 17.7 ~ 187.3（mean 99.1） |

模型洞内**有完整层次**（拱顶阴影 + 透过洞看到的亮背景），差异仅 30%，且部分是拍摄条件所致：参考是远拍（大气散射提亮暗部），模型是近拍无雾。**"纯黑"不成立。**

**但由此得出一个真实可改进项：模型缺大气透视。** 参考照片里桥的两端（离相机距离差约 60m）应有可测的亮度/对比度差异，我们的全桥对比度一致——这是"塑料感"的一个来源，不只是材质问题。已交 VisualPolish agent 处理（验收标准：两端白石亮度应有可测差异）。

**连续三条目视误判的教训（M3-2 栏杆、M3-3 券石环、M3-3 洞内黑）**：
三条都是**从渲染图上"看出"了问题，量化后都不成立**。共同机制：人眼对高对比边缘（望柱凸起、暗部）会脑补成"缺陷"。
**纪律：目视比对只能用来"提出假设"，结论必须由量化采样决定。** 已把这条写进 M3 工作方法。

---

## 2026-10-04 M3-2 复核：栏杆"高度不匀"是主控误判，撤回

**实测**（`ortho_side.png` 逐列取顶缘，去桥面二次拱度后）：
- 残差 std = **0.116 m**，max 0.375 m
- 仅 4.3% 的列有 >2px 跳变

**结论**：那些跳变就是**望柱凸起**（柱头高于栏板扶手是正常的，0.375m 量级合理）。栏杆顶缘本身是平的。目视觉得"锯齿参差"是把正常望柱阵列误读成缺陷——**与 M3-3 券石环同族错误：从视觉上读出构造里没有/不该有的东西**。

**附带核实的自洽性**（`build_scene2.py:136`）：模型取 **64 根/侧 = 128 望柱**，狮数分配 `16 根×5 狮 + 48 根×4 狮 = 272/侧 → 544 总`。
- 该组合**自洽**（544 ÷ 128 不整除，但按 5 狮柱/4 狮柱分配后整除）
- 若改用吴齐正的 124 根，544 无法这样分配 → 模型选 128 有内部一致性依据
- 但望柱数仍是 [二手文献] 口径冲突（128 / 124 / 62对=124），**属附属构件（M3 范围），不在本体冻结内**，维持"不作计量事实"标注

---

## 2026-10-04 M3 首轮迭代：出图 vs 实拍目视比对（用户要求"90% 进下一步"）

**方法**：把 `ortho_side.png` 与 `refs/ref_elevation.jpg` 摆在一起看，并做量化（不靠印象）。

**几何正确**：
- 17 孔透明段实测序列 `[509, 96,90,97,105,112,105,97,90,96, 509]` —— 对称、中央最宽（96→112），**标准半圆券特征成立**
- 长高比模型 13.61 vs 参考 18.76

**发现真差异（列入 M3 待办，不在 M2.5 本体冻结内）**：
1. **竖向比例偏高 27%**。根因：`BODY_BOTTOM = -2.20`（水下基座，不可见）把渲染高撑到 9.95m，而参考照片桥带只到水线。**这不是几何错，是出图裁切口径问题**——T7 的掩膜 IoU 判据本该抓，但它尚未在真实图上跑。
2. **栏杆望柱锯齿起伏**。初判为缺陷，**经与原图对照后推翻**：原图正是密排小方块纹理，此项基本对上，仅高度略高且不匀。
3. ~~**券洞内壁纯黑、券石不可见**（原图洞内可见浅色券石环）~~ —— **主控复核后撤回此条**。
   计算：券圈厚 0.40m ÷ 净跨 4.5m × 参考照片单拱 30px = **2.67 px**。券石环在参考图上不足 3 像素，**无法分辨**。"原图可见券石环"是把 3 像素以下的纹理当成了证据，属主观臆断。
   **教训**：目视比对同样要过分辨率门槛——**与判据恒真是同一类错误**（从不可分辨的信号里读出结论）。若要核券石环，必须有近正面高分辨率照片或正交特写，不可从 `ref_elevation.jpg` 得出。

**处置**：按用户"不要一次性追求完美，90% 进下一步"的要求，M2.5 冻结**不因这两条阻塞**；两条进 M3 迭代清单。
- 第 1 条（竖向比例偏高 27%）根因是出图裁切口径（水下不可见基座计入桥高），非本体几何错
- 第 2 条（栏杆望柱锯齿）经与原图对照**已推翻**，不是缺陷
- 券石环可见性因分辨率不足**不可验证**，需换参考图或改用正交特写才能核

---

## 2026-10-04 环境构件桥轴旋转补正（T6 反馈）

- **问题**：T6 出图时发现 `abutment_ground` 旋转 0°，而本体与其余 8 个构件均为 −112°（`BRIDGE_AXIS_AZ`）。引道块孤悬水中并遮挡正交侧立面。T6 出图时用 `hide_render` 规避——那是绕过不是修复。
- **根因**：`build_scene2.py` 的批量旋转用内联元组枚举构件名，`abutment_ground` 漏在名单外。它与本体同父级 `m_body`，本就该一起转。
- **改动**：`build_scene2.py` 旋转名单补入 `abutment_ground`，并把枚举提为具名清单加注释说明为什么它在册。
- **是否触及冻结本体**：**否**。`abutment_ground` 属环境构件（`pier_plinth`/`deck_cornice` 同类），不在 M2.5 冻结的本体三对象内。
- **重跑判据（全绿才算完成）**：
  - 核心三对象几何 SHA **完全不变**：`bridge_body` nv=4409 sha=`6194d02d5557cc91`（与修复前一致）、`voussoir` sha=`da5441c7628a3215`、`impost` sha=`3db908a3a628646f`
  - L1 `fail=0`
  - L2 正检 `ok=True fail=[] exit=0`
  - L2 负控 `拱腹法线偏离朝心超容差 10/494 面 exit=1`（仍能抓）
  - 旋转核对：9 个桥体构件全部 −112.00°；`water` 0°（水平面，正确）
  - `pytest` 47 passed（改 manifest 哈希后）
- **冷重建硬门**：不受影响（几何哈希未变），T8 的对照结论继续有效。

## 2026-10-04 M2.5 冻结前基线

- commit: <待填——冻结包 commit 哈希，用户批准后回填>
- 状态: 待用户目验（冻结包为**候选**，未锁定；见 `3d/refs/freeze_manifest.md`）
- 冻结状态候选: `CONDITIONAL_RECONSTRUCTION_FREEZE`（依赖 12 条工作值 + 1 条图像推导，清单见 manifest §9）

## 2026-10-05 M6 望柱蹲狮重雕（近景可辨识 + linked duplicates）

- **触发**：用户判据「近景 0.8-1.2m 下石狮必须可辨识（头/吻/鬃毛/前肢/蹲姿）」；现状 `lions.py` 球块堆叠在近景为无定形白块（`lion_single.png` 存档），且 256 只并成单 mesh 后连通域 7168（每狮碎成 ~28 片）。
- **造型依据**：`refs/lugou_lion/`（Wikimedia Commons，CC/GFDL，仅造型参照不入成片素材）。十七孔桥与卢沟桥同属明清官式蹲狮谱系，取解剖正确性（大头≈40%H、双层眉弓、凸眼、宽上翘吻、口裂、髭须卷、卷云鬃、阔胸垂饰、并拢前肢+趾、低臀、卷尾），纹样从简。
- **实现**（新模块 `3d/lions2.py`，旧 `lions.py` 留盘不动——freeze manifest 记录文件）：
  - 每变体一次"母模"：~48 个闭合体块 → EXACT 布尔并成单一水密实体 → SUBSURF(SIMPLE) 细分补密度（5.2.2 LTS 实测 `bmesh.ops.subdivide_edges` 对任意输入静默无操作，cube 复现，故走修改器管道）→ 归一化单位高。
  - 场景接入改 **linked duplicates**（主控 2026-10-05 口径）：`place_lions(spots)` 建 256 对象共享 2 个 mesh datablock（主狮变体0 / 幼狮变体1），每对象 scale=H、微yaw ±2.6°；`build_scene2.py` 仅改 import、调用与旋转名单（build_lions_bm 合并版删除）。
- **实测**（`blender -b e30_bridge.blend`）：
  - unique mesh = 2（`_lion2_master_0` 10632 面 / `_lion2_master_1` 11026 面，均 ≥4000），**单 mesh 连通域 = 1（水密）**
  - 对象数 256（主 128 + 幼 128）；主狮高 0.30m、幼狮高 0.17m【工作值，沿用旧 LOD 口径】；实际雕体总高=H（母模归一）
  - **坐实**：抽 16 只主狮，底垫中心到 deck_rail 最近表面距离 <3cm 且法线 +Z（=底垫沉入柱顶 2cm，1.20−1.18）16/16 通过
  - **本体零改动**：freeze_hash 三对象 sha_sorted 与改前逐位一致（bridge_body `861d8836…`、voussoir `b4421770…`、impost `5154f49e…`；注意 changelog 旧记 `6194d02d…` 是 manifest 标注"勿用于比对"的手算口径）
- **hero A/B**（同机位同 seed=20261004，仅狮几何不同）：逐像素差 0.123%（1773px，容差>8），全部落于 y∈[359,461] 狮带；栏杆顶缘线新旧逐列一致（残差 std=0、列间跳变 0）。A=`refs/hero_AB_old_lions_samecam.png`，B=`shot_hero.png`。
- **近景证据**：`lion_closeup_front.png` / `lion_closeup_threeq.png`（距狮头 1.1-1.3m，35mm，渲染纪律同 shot_auto2）。
- **是否触及冻结本体**：**否**（lions 不在 M2.5 冻结范围；三对象哈希逐位实测一致）。
- **已知限制**：①共享 mesh 后逐只几何差异消失（仅 transform 微差）——官式程式化本就以重复为常态，远景不可辨，近景同柱双狮不邻接；②狮底垫沉入柱顶 2cm（1.20 与 1.18 口径差，沿旧口径）；③ 544 只文献口径仍以 256 实体 + 柱头群轮廓表现（不变）；④近景平直面片 ~10mm 可见（凿石风格化，非缺陷）。

### M6.1 返工轮（2026-10-05，主控复核后；只动 lions2.py）

- **触发**：主控复核近景图，判定剪影级判据通过，但①面部平板化（吻=矩形板+穿透黑槽读作"信箱口"）②折面感（大平 facet 纸工艺观感）两项不达标。
- **改动（全部在 `lions2.py`）**：
  - **布尔链重构** `_boolean_chain(pos, neg, final)`：正体并 → 减法浅凹 → 眼球最后并。
  - **口裂**：废除穿透缝，改为 7 球抛物弧**内凹线槽**（宽 0.024/深≈0.013 单位，两端上挑 0.022），刻在颌前面、吻底悬垂阴影下——不穿透。
  - **鼻**：方盒改 `_frustum` 楔形鼻梁（后宽 0.092→前窄 0.052，顶面渐升）+ 椭球鼻头上翘；鼻孔为鼻梁顶面两个椭圆浅凹（0.010×0.012）。
  - **眼**：眉弓改双层椭圆棱；眉弓下眼窝浅碗（r 0.030 减法）+ 眼球凸块（r 0.032，r 须越过碗缘否则悬空成岛——实测踩坑）。
  - **髭须**：吻侧三连卷改贴面浅浮雕（rx 0.012-0.014，凸出≈0.02）。
  - **胸垂饰**：矩形板改上宽下窄绶带棱台（0.104→0.058），微倾贴胸。
  - **吻部**：方盒改圆垫椭球（0.055, 0.075, 0.047）——矩形板上任何凹槽都会继承矩形轮廓，圆垫让口裂读作弧线。
  - **平滑着色** `_mark_smooth`：全 face smooth + 二面角 >40° 标 sharp（auto-smooth 等价），保留部件交界凿棱、消大平 facet 纸感。
  - **微调**：前爪加大（0.165×0.110×0.095）、颈背鬃加厚填喉凹、鬃卷 r+0.006。
- **踩坑记录**：①`_frustum` tilt 语义错（比例≠绝对偏移）曾产生 ±0.06 扭曲棱台，毒化整条 EXACT 布尔链（四肢 severed、体内残壳，pos_only comps=5）——tilt 改绝对外缘偏移 -0.008 后 comps=1；②眼球若不越过眼窝碗缘会成悬空岛（comps=3）；③鼻孔刀在鼻头球上会切落两端月牙帽（comps=3）——移到鼻梁顶面用小椭圆刀解决。
- **实测（重雕后）**：主狮 mesh **15692 面** / 幼狮 **16054 面**（≤25k 预算内，≥4000 达标），**连通域均=1**，unique mesh=2，对象 256，平滑着色 sharp 边 4545/4653（凿棱保留）；坐实 16/16（<3cm +Z）；freeze_hash 三对象逐位一致（`861d8836…`/`b4421770…`/`5154f49e…`）。
- **QA/测试**：qa_l2 正检 `QA_L2_OK` exit=0，负控 `NEG_CAUGHT` exit=0；pytest **376 passed**。
- **hero A/B（同机位同 seed）**：差 26.9%——分解：天空 0.00%、桥/栏/狮带 46.6%、水区 44.3% 且随距离 91%→0.5% 衰减。**归因警示**：A 用 927f940~1 旧 build_scene2（旧狮 + M6 期材质接线），B 用现 build_scene2（新狮 + 主控 M7 接线勘误青石冷色/WaterFix 水岸），故该差值=【新狮反射 + M7 材质接线差异】叠加，**不能全记狮几何**；狮几何无涉的硬证据是：栏杆顶缘线逐列一致（二阶去趋势残差 std=0、列间跳变 0）、天空 0 差、freeze_hash 三对象逐位一致。纯狮变量 A/B 需待 M7 接线落定后用同脚本换狮重渲。
- **证据（覆盖原路径）**：`lion_closeup_front.png`、`lion_closeup_threeq.png`、`shot_hero.png`、`refs/hero_AB_old_lions_samecam.png`。
- **未 commit**（主控统一提交）。


## M8 (2026-10-05) ChatGPT 二审缺陷清零批（常规模式 Python 解包逐图审查, 综合 6.9/10 → 修复批）

二审裁决原文: `3d/refs/gpt_review_round2.md`。本批只动表现层/附属构件/判据口径, 不动 facts 本体条目。

- **M8-1 券洞切刀根因修复（bridge_geom2.py）**: 旧归因"余量 0.80 致黑横杠"证伪——真根因是 `build_void_bm` 轮廓自相交（起拱线处两次横穿直径生成水平残面）。轮廓改简单闭合法（底左→底右→右起拱→弧→左起拱）；`VOID_CUT_MARGIN` 0.05→0.60（assumptions.py, 射线实测 0.05 时背墙残留命中 dist=33.6m, 0.60 全高贯通 water/sky）。布尔后新增残片清理（桥身顶点不得超自身收分轮廓 hw+2cm, 实测清除 13 悬空顶点, 原残片悬在券脸前 0.5~0.9m 遮挡题额区）。
- **M8-2 544 石狮体系（lions2.py）**: 撤回"256 只"口径。128 望柱×1 主狮 + 32 柱×4 幼狮 + 96 柱×3 幼狮 = 128+416 = **544**（官方口径）。4 主狮姿态母模 + 4 幼狮母模（8 套水密 mesh, linked duplicates）；幼狮偏移改沿桥轴坐标系贴柱头四角（旧版加在世界 X/Y 致悬空, 二审广角图实证）。主狮 0.32m 回归柱头比例。
- **M8-3 栏板透空形制（build_scene2.py）**: 实心白板墙改官式四段: 地栿 0.18 + 下华板 0.22 + 双孔透空区 0.22（含中梃荷叶墩, 两真实镂孔）+ 寻杖 0.14, 依老照片 11/14_ref 实测形制。桥面改三带错缝大石板。
- **M8-4 靠山兽返雕（beasts2.py）**: 废铜麒麟细颈卧态, 改老照片 11 实证蹲坐式: 直立粗壮前肢+宽爪按地、雄挺前胸、巨大阔吻头颅、卷云鬃环颈、背顺接桥台抱鼓（废多层展陈须弥座）。双变体水密 12.5k 面。
- **M8-5 材质块级化（materials.py）**: 青石 course_h 0.60→0.46、joint 0.010→0.024、block_var 0.12→0.36、bump 0.30→0.68（大条石横分层+纵错缝+块级灰差）；汉白玉基色改暖象牙古玉白 (0.865,0.840,0.795) + weather 0.40 消 CGI 纯白；水线湿带叠加低频噪声扰动 Z（±0.11m 起伏, 废机械直横线）。
- **M8-6 判据口径更正（register_overlay.py）**: 切刀贯通后券洞为开敞湾, 旧 enclosed-hole 检测恒 0（假阴性）。void_table 改"触底不触顶背景连通域=湾"并保留 enclosed 并集；solidify 增 seal_bottom（crop 后封底 1px）维持参考侧"拱洞计白区"IoU 口径。负控制: 实心掩膜→[]、缺孔→16（docstring 声明, test_register 覆盖）。
- **判据复跑**: L1 qa_bridge exit=0；L2 `QA_L2_OK`；L3 IoU **0.8176**（≥0.76）+ VOID n=17 max|Δxc|=**0.0096**（≤0.02, 优于修复前 0.0181）VERDICT PASS。
- **新增交付证据**: `delivery/render_arch_see_through.png`（中央孔低水位对穿, 射线全高 water/sky 命中）、`delivery/arch_registration.csv`（17 孔逐孔 xc/span/rise/rise_ratio/墩位）、`delivery/08_render_registration_overlay_with_voids.png`、`delivery/05/06_render_plaque_*.png`（南北题额 3D 刻字特写, 《日下旧闻考》卷84）。
- **manifest**: §1 assumptions、§2 bridge_geom2/build_scene2/materials/register_overlay 哈希回填本批。


## M9 (2026-10-05) 三审修复批（8.2 → 目标终验）

三审裁决原文见会话；本批落实三审四条最小修复指令 + 审计瑕疵纠正。

- **M9-1 狮/兽位置桥轴旋转根因修复（build_scene2.py）**: 旧代码对 lion_objs/beast_objs 只加朝向旋转不加位置旋转 -> 全桥 544 狮群与 4 兽悬空错位（二审"浮狮"、三审 21 号图集群漂在开间的真因）。现位置与朝向一并绕 BRIDGE_AXIS_AZ 旋转（Rz @ location）。
- **M9-2 靠山兽 v4（beasts2.py）**: 焊缝清理(remove_doubles 1e-4+法线一致化)消黑缝; 吻前伸+上颌唇缘/下颌分层+口裂负刀加宽半凸; 球串鬃改 300° 环颈双层片状定向鬃(rot_x 定向扁盒); 双变体水密 10.9k/11.4k 面。
- **M9-3 题额可读性双根因（render_plaques.py）**: ①字对象位置赋值行在编辑手术中丢失致字埋桥身中线; ②GPU+Cycles 全场景 FONT 偶发不渲染(二分: CPU 全场景 17k 红px / GPU 全场景 0 / GPU 仅字 34 万)。修复: 补位置行 + 题额机位强制 CPU + 字色加深(0.16,0.015,0.012)/光比压低(120W) + 正视/掠光双机位 × 南北 = 4 图, 红字像素自验 7.8万-13.7万。
- **M9-4 细部举证新机位（tools/render_details.py）**: 19 券脸环带近景 / 20 桥面三带错缝低机位 / 21 狮+栏板对照(18 号构图) / 22 靠山兽对照(17 号构图)。
- **M9-5 审计纠正**: arch_registration.csv 列名 pier_*_x → opening_*_x(孔口边界语义); _beast_preview 分辨率 1280×960 → 1600×900(三审 07 尺寸误标根因); INDEX v4 全表重标 03/04 描述。
- **判据复跑**: L1 exit 0; L2 QA_L2_OK; L3 IoU 0.8142(≥0.76) + 17 湾 max|Δxc| 0.0096 VERDICT PASS; pytest 376(哈希回填后)。
- **manifest**: §2 build_scene2.py 哈希回填本批。


## M9b 补充 (2026-10-05) 雕塑终批集成
- lions2 v4 (LionSculptFinal agent): 成年狮瘦身去萌化+层片鬃领+三趾分缝, 幼狮四态分化; 8 母模水密 ≤13802 面。
- beasts2 v5 (BeastSculptFinal agent): 两层头颅/楔刀口裂/分层下颌/獠牙含珠/三层瓦鬃/S尾带; 双变体水密 ≤15390 面; 平衡树并集+sliver 清除。已知残留: 体侧一处黑色细缝(threeq)、颅偏方盔感——登记待五审前修。
- build_scene2: 靠山兽坐栏端抱鼓位(M9b)哈希回填本节。


## M10.1 (2026-10-05) 四审修复批（8.5 → 终验冲刺）
- **兽 v5.1**: 补洞硬工序(boundary edges 80→0, 四审 22 号黑缝根因=并集开边界洞); 头颅椭球语言重做(废棱台面盔/矩形耳/悬浮唇); 口裂楔刀加深+上唇棱; voxel remesh 0.016 兜底闭流形(70k 面); 预览机位距离放大适配 v5 体量(07 取景不合格根因)。
- **桥面缝三连根因**: ①共面条带无缝→189 实体石板; ②掠射自遮挡(抬阶 5cm 反藏缝)→顶面齐平+深色砂浆缝带; ③**deck_cornice 全宽盖层压住全桥面**(20 号纯白片真因)→改两侧 0.43m 边缘仰天石带。终图 20 号横缝/纵带/错缝一眼可辨。
- **19/20/21/22 机位重定**: 19 券脸环带+拱腹满幅; 20 贴地 24mm; 21 狮栏对照; 22 兽正面外侧对照 17 号构图。
- **CSV 重生成**: 孔口=孔贴桥台布局(旧表 xc 偏半墩), 增 pier_width_m 列(2.5), 闭合 107.3+16×2.5+2×1.35=150 复算通过。
- **审计统一**: IoU 口径 0.8136(overlay 终渲复算), INDEX v4 图数 23/描述纠正。
- 判据: L3 IoU 0.8136-0.8138 + 17 湾 Δxc 0.0096 PASS(石板/仰天石改动后复跑); pytest 376; manifest §2 build_scene2 哈希回填。


## M10.2 (2026-10-05) 风化/水面批 + 实拍接近度协议
- materials.py: stone_material 增风化三件套(pointiness 腔隙积垢/棱缘磨亮/Z拉伸雨痕) + 逐块粗糙度±0.08; water 增米级破碎频 h6(scale 0.9, w 0.38, 远距反射 breakup) + 高频 h5 + rough 底 0.015。纯 shader 零网格。
- tools/photo_similarity.py 新增: 实拍接近度三协议(A 冬至实拍开口检测/ A2 历史扫描开敞湾检测+1D单应 rectify / B 轮廓IoU / C 天空基准桥面驼峰相关) + 并排对照图 24/25 + 报告 23。
- 校准结论(如实): 黄昏逆光+霾使 A/C 自动检测证据不足(A 9/17, C pearson 0.53); 历史扫描为 mid-gray 天空照片, 全局阈值不成立(B 0.375 为协议失效非模型误差); 可靠四项结构匹配率 99.76%; 像素面积口径以 L3 冻结掩膜 0.8136 为准。
- CSV 末行 pier_width_m=NA(四审 H 项); manifest §2 materials.py 哈希回填。

## M10.3 (2026-10-05) 证据图重渲批（六审补证）
- 六审点名 v6 07 号与 v5 像素零差异。根因: ①v6 渲染批(14:55)早于 materials.py M10.2 保存(14:57), 全批证据图用旧材质; ②`_beast_preview.py` 自建平 Principled 绕过 materials.py, 07 永远不反映风化。
- 修: ①15:19 全量重渲(hero/side/arch/top/狮×2/兽/透视/细部19-22/匾额×4); ②`_beast_preview.py` 改挂 `MAT.marble_material`。重渲后 07 vs v5 mean|d|=5.54, 31.5% 像素 >3 级。
- overlay 正参复跑(ortho_side.png): VOID PASS n=17 max|Δxc|=0.0096, IoU 0.8136 不变(几何冻结)。
- 承认 v6「全构件风化已复验」措辞不成立; v6.1 起成立。

## M11-protocol (2026-10-05) 实拍相机注册审计协议(六审§8 工程实现)
- tools/cam_register.py: EXIF-K(Canon 400D 85mm) + 暗拱腔连通域半自动 landmark(近面 silhouette 边) + look-at 参数化多初值 LM(控制点共面, 弃常规 PnP) + shift RMSE 扫描 + 裁切主点/水位 nuisance 先验。
- tools/cam_clay_compare.py: 同机位 clay 渲染(白名单物件, fog_volume/water 隐藏) + Blender 自投影控制点侧车 affine + 近面开口投影 void 掩膜; 分项: body IoU / void IoU / Chamfer / 驼峰 pearson+RMSE。
- 结果(delivery/26, 图 27/28): similarity_landmarks 0.9718 但残差结构化; void 0.378 / body 0.254 / 驼峰 0.46 → **>=95% 照片几何相似不认证**; 误差源 = 拱形/跨距工作值(模型拱窄高 vs 实拍), 列 M11 反演候选。
- 协议自身修复链(留证): PnP 平面歧义→look-at 先验; 相机 up 列反号; 拱筒非通透→开口投影掩膜; 0/1 掩膜 resize/warp 阈值病×3; Blender 内参约定→控制点侧车 affine; dtf 天空列污染×2; samp 全/半分辨率单位。

## v6.4.1 (2026-10-05) 九审第1-5项审计工具链收口
- 九审发现 v6.4.zip 装陈旧副本(K_bl 15.6%各向异性/k1±0.05/manifest无hash/certify单图/SVD非边缘化)。本批从实时文件重建并逐文件 md5 校验入包。
- cam_clay_compare resolution 前置→26 K_bl fx=fy ratio=1.000000; cam_register k1±0.02; manifest 加 cert_gates sha256; certify.py 升级多照片+holdout ALL-AND(缺clay门判fail不默认通过); svd_analysis 改 Schur 补边缘化相机+列归一+active-bound, 措辞修正为"可辨识秩不足"; 30 status 降级 OPTIMIZATION_CONVERGED_DIAGNOSTIC_ONLY。

## M12 (2026-10-05) 视觉几何重建启动(九审撤回"视觉封卷"后)
- 触发: 用户肉眼+我复测确认桥面弧度 Critical。同估计器+同注册相机(斜视偏差抵消): 照片17拱冠矢跨比 0.034, 模型仅 0.017 → 太平约2倍。
- 根因: ①deck_z 抛物线矢高仅2.7m; ②拱冠不跟桥面(springer恒定2.5m, 冠高只随span微变)。真桥冠线随桥面隆起(恒定拱肩)。
- cmp10 悬空横条 = impost 起拱石(恒定z, 洞口边缘外凸), 且 impost/pier_plinth/voussoir 均未过 void 布尔。
- 反演工具 tools/m12_geom_invert.py: 8参自由联合反演**证实退化**(eig最小=0, 全参顶界, ovf对齐崩) → 印证八九审"侧视不能同时定span/pier/camber/rise"。改受约束定标: span保持工作值, 冠随桥面, 只解 camber 幅度 → 桥面矢高≈5.4m(0.034×142/0.897)。
- 并行子agent: BeastRebuild(整模)/LionRebuild(换母模)/RailMeasure(一开间测绘)。
## M13 (2026-10-05) 逐块砌筑 + 尖拱 + 端头/机位/构件修正
- 用户方法论转折: "先做每块石板再数" → masonry.py 真块石(放射券石环+错缝砧石), 总 2068 块, 统计入 masonry_stats.json。光滑体+噪声假纹判弃。
- 两圆心尖拱(ogee): bridge_geom2 新增 arch_e/arch_z/arch_dzdx 单一来源, void+券石+qa_l2 三处同步(644采样面 0 fail)。
- **矢跨比空改事故**: M12 比例回调把 replace 打在 masonry.py(字符串不存在→静默无操作), 真源头在 bridge_geom2:47。M13-B2 才落地: 0.70-0.20u -> 0.61-0.15u, 中央 e/a 0.48->0.24(近真桥缓ogee, 侧视对照 winter 确认)。
- 券石块数改按照片目标表 VOUSSOIR_TARGET=[17,15,13,13,11,11,9,9,7](对称): 统一面宽数学上给不出端7/心17(半弧长比2.19≠块数比2.43)——真桥端孔块更宽。
- arch 机位重写: 原机位退到桥端轴向被岸坡挡+auto-frame把全桥拉回(近景变全景); 改水面侧斜对第3孔、z按 bridge_body 世界bbox映射、不auto-frame。
- **靠山兽姿态假设推翻**: 设计注释"伏卧前探+卷云顶1.23高过头"读错证据——真拍(3627588283)为蹲坐昂首、背火焰云多层顺脊、最高≈头高。BeastPoseFix 重做中。
- 石狮官方近证 off_13: 蹲坐昂首、鬃为顺披火焰长棱(非圆球堆)、望柱柱台偏矮(我柱台≈狮高1.5x, 真≈1x)。并入 BeastPoseFix。
## M14 (2026-10-06) 六审四刀落地(并行子代理+隔离副本+主控三方合并)
- 刀1 拱: ratio 0.61->0.56-0.10u(中央 cusp 25°->13°)。soft-min 冠钝化试验**当日废除**: e=0 端孔两弧全等时 soft-min 恒沉 s*ln2(整弧均匀缩水非圆角)。教训: 角点圆化必须角点局部, 均匀偏移=改形。
- 刀1b 六审E: 券石全深筒券化(贯通墙厚+内弧伸入0.03+放射缝0.025), 透洞内壁从光滑内筒变阶梯环石。派生修复: qa_l2 侵入判据从竖直z比较改有符号径向距离 arch_signed_r(肩段斜率~9 处 0.03 横移被放大成 0.2m 假侵入——判据错非几何错)。
- 刀2 墩: facts.PIER_W_INT 剖面表(中央2.27/-9.2% 端2.73/+9.2%), 对称恒等式 w[i]+w[17-i]=2*PIER_W 证总宽40.0/闭合150.0 精确守恒; qa_bridge 同表消费。
- 刀3 桥台: 引道24m缓坡2.54%/末孔外墩座总厚4.35m/燕翅+29%底-2.8插水底/岸坡走廊限高。**关键发现**: Blender 5.2 EXACT UNION 在合并体底面非共面时静默失败(单侧成功双侧失败随参数漂移)——旧 abutments UNION 路线废除, 免布尔并入, 附带清掉 bridge_body 29 条非流形边。
- 刀4 兽: 圆泡脊->7片火焰瓣(内收腰+后掠尖锋+瓦叠凹口), 身姿前探(长高比1.56->1.81)。回归自修: 口裂楔刀切穿瘦吻/眼珠悬空孤岛。
- 狮: 0.85x+胸削11%+头群0.94收紧+幼狮4槽内收成团+承托石0.31->0.16薄板。assert_watertight 升级(boundary edges==0)抓到既有简并边3条(cub kind1 鬃环布尔残留)。
- 砌缝三级层级: qingshi_material 参数化, 券石100%/砧石m_course~40%/本体去斑驳(几何全保留只调权重)。
- 判据卫生: MET_ARCH_FAMILY 恒真闸门(合成半圆点拟合圆残差恒0)改测真实剖面不变量; MET_RING_FIT/SPRINGER 随 M12 逐孔语义(旧红6条系判据问错问题); 拱数学归一 facts 单一来源。
- 新证据机位 deep(低角斜看中央孔, 六审尾注)。重冻结 core_hash/l2_baseline。
- 流程: 4子代理并行, 隔离协议=/tmp副本干活+互斥文件集写回+共享文件(build_scene2)留副本主控区段拼接; 一次跨文件时序冲突(PierWidth 副本早于筒券提交)靠 rebase 警告避免吞改动。
## M15 (2026-10-06) 七审六刀全落地 -> 八审 8.8, 桥身主参数封卷
- 六刀: 桥头体系重做(实腹台体42m坡道连续栏杆抱鼓石; 燕翅墙三轮修补失败后删除, 八审裁决"删得对")/券脸0.54+墩剖面v2/冠钝化v2(∝e+封顶)/筒券深度衰减/材质100-28-15/兽雕刻化v8。
- 潜伏bug修: b<a 端孔两圆心公式静默退化 rise=a 半圆(全链一致地错), 改单心平拱分支; 八审裁"轮廓可信度8.5->9.2, 禁回抬"。
- 八审冻结令: 矢跨0.56/冠圆化/券脸0.54/中央墩2.17/端孔算法/砌缝三级 锁死。九轮只碰: 兽解剖重塑 + 桥头massing收口 + 材质光学。
## M16 (2026-10-06) 九轮两刀 -> 八审8.8->九审9.0, 几何封卷
- 刀1 兽解剖 v9: 躯干+17%/腹线0.13/肩胛前移12°前倾力线/吻越石座/四肢92°折线/冠焰比0.823。九审: 一级形体冻结, 二级(头颈负形/关节去球感/焰瓣厚根打碎)留雕刻轮。
- 刀2 桥头 massing: 台体楔退6.50->4.55/坡道幂曲线t^0.65肩宽递减石颊1.35->0.75/顶铺侧台同步外展; 自抓石颊露出方向反+岸丘吞头墙两真缺陷。九审: 桥头冻结, 再碰形体=为迭代而迭代。
- 材质第一轮: 缝黑线->浅灰侵蚀/基色提亮去蓝/暖灰污染/砧石贴平; 棋盘斑块残留->材质灯光轮议题(九审确认最低板8.4)。
- 子代理纪律事故: BeastAnatomy 误覆盖 beast_pose_report.md(20标题->1), git show 恢复拼回; 教训入记忆: 报告类共享文件 append-only, 子代理 brief 必须写"先读现有内容再追加"。
## M19 (2026-10-06) 桥面纵剖冬照重标定(破九审冻结·依据=标定基准证伪) + 三缺陷修复
- 破封依据: 七审 M12 桥面/拱线用 side_elev_6794(枯湖水位, 干湖床当水线)标定 → 全纵剖
  系统偏高。冬照 winter_20201221160537(结冰=常水位, D810 38mm)实测: 端部桥面 2.1-2.3 /
  中央冠 5.9 / 中央桥面 7.3 / camber 4.8-5.1; 外部水深(昆明湖均深 1.5m/最深 3m,
  beijing.gov.cn 2020-12-08)独立互证枯湖-常水位差 Δ≈1.5±0.3。
- Δz 扫描(0/-1.0/-1.4/-1.8/-1.2/-1.5, 桥动水不动)证伪纯平移: camber 残差 0.80 为
  Δ 不变量, ±0.35 门任意 Δ 不可满足(montage /tmp/e30_m19_zshift/m19_dz_scan.png)。
- 重标定: DECK_Z_TOP 7.75->7.30 / DECK_Z_END 3.60->2.20 / SPANDREL 恒1.0->逐孔
  1.4->0.5(facts.spandrel 单一来源, bridge_geom2+qa_bridge 同消费) / RISE_E 0.46->0.32
  (旧值端起拱=冠-2.07 数学上必没水, 违 springer>=0.15 硬约束)。
  RISE_C 0.56/SPAN_DISTINCT/PIER_W/尖拱 a-b/端孔算法/砌缝三级 不动(冬照冠/起拱隐含
  0.53±0.08 覆盖 0.56)。
- 桥头-岸系 6 常数随端标高整体 -1.4(ABUT_TOP_Z 3.56->2.16/RAMP_Z0 3.55->2.15/
  Z_TIP 2.45->1.05/PAD_Z 2.42->1.02/BANK_Z 2.1->0.70/LOW_Z 1.05->0.30 重定),
  坡度 2.62% 不变; _check_abutment C1/C2/C6 同步; stones_p8.json z 锚点重推(x 布局不动)。
- 三缺陷: ①座石悬空 -> 新增 masonry.build_impost 3 阶出挑线脚(高0.35/挑0.30,
  顶=spz-GAP 承压面, 逐孔随 springer, 没水阶不建, 204 块); ②端区百叶 -> _wedge->_stone
  逐顶点贴收分(布局/层高冻结); ③impost 为 M19 brief 新增项, 同①。
- 贴面块桥面削坡薄片 >=0.02 即落(旧 min_h 整块弃): 露体带 109899 -> 45124 格
  ≈ M18 基线 44938(存量债务, 本轮无恶化)。
- 验收: build 零错 / QA_L2_OK(负控 10/10) / ABUTMENT_CHECK ALL PASS /
  pytest tests/bridge3d 312 过 / e30_shikongqiao_video/tests 15 fail = M18 存量零新增 /
  平色消融同机位 1200s 对比无新暗块(见 .superpowers/sdd/m19-brief.md M19 报告)。

## M19b (2026-10-06) 治理层随 M19 重整(govfix: 15 红→0, 判据本体不许放松)
- 背景: M18/M19 落地后 e30_shikongqiao_video/tests 15 条治理测试红(全部为台账/
  契约/判据期望未跟随几何重标定, 无一为几何错误; 逐条归因见 .superpowers/sdd/govfix-report.md)。
- facts.py: inline [等级] 注释与 SOURCES 双向对齐(M19 七常量: DECK_Z_TOP/DECK_Z_END/
  SPANDREL_C/SPANDREL_E/RISE_E 改标[图像推导], SPRINGER 归位[工作值]+沿用锚说明);
  新登记 RISE_C[图像推导] / CROWN_BLUNT_K / CROWN_BLUNT_CAP / SPRINGER_WATER_MIN=0.15[工作值]
  —— 0.15 即 M19 RISE_E 重标定依据的"springer≥0.15 硬约束"升格为判据阈值。
- qa_bridge.py(MET 重整, 阈值/精度零放松):
  ①MET_ARCH_FAMILY 冠高期望 spz+矢 → spz+矢−s·ln2(s=facts.blunt_s, 七审P1-1 已登记
    的冠钝化设计特征; 删钝化/放大越界同判据即红);
  ②MET_SPRINGER 新增水上硬下限(z=0 常水位为 M19 唯一绝对基准; deck 相对判据按构造
    平移不变, 全局 Z 漂移唯一绝对判据, 抓 M12 枯湖基准事故重演);
  ③MET_SPRINGER 新增 SPRINGER"声明=导出"恒等校验(facts 值域, 容差=声明粒度半字 0.005)。
- freeze_hash.py: CORE 第三对象 impost→coursing(M19 起 impost 线脚 204 块并入 coursing,
  单 mesh 对象废除; 末次独立记录 5154f49e… 见 manifest §7)。
- freeze_manifest.md: §1/§2 全量重哈希(含 M18/M19 已改未同步的 materials/qa_l2/shot_auto2);
  §5 MET_ARCH_RATIO 0.56±0.02; §8-6 DECK_Z_TOP 改标注; §9 工作值清单重建(18 条,
  补 PIER_W_C/E/INT + CROWN_BLUNT_K/CAP + SPRINGER_WATER_MIN, DECK_Z_AT_PIER 废除行删除);
  §7 追加 M19 后重采基线表(bridge_body cdba9709…/voussoir ba2e0951…/coursing 0bd11e71…,
  bbox z max 7.3)。
- spec §9: 契约标高推导值同步 7.30/2.20(三处 7.75/5.05), 加 M19 同步注。
- tests: 负控打击面跟随判据数据通路更新(M14 后 ARCH_RATIO 退出通路→RISE_C 活通路 +
  monkeypatch 模块全局; 全局 Z 漂移负控 MET_RING_FIT→MET_SPRINGER; MET_CLOSURE 负控
  PIER_W→PIER_W_INT 表; 新增 PIER_W 均值锚特异性正判据)。测试期望更新均有几何/机制
  依据, 判据阈值与精度零放松。
- 验收(隔离副本实测): tests 64 passed / tests/bridge3d 312 passed / blender 重建零错
  SAVED v2 / QA_L2_OK / NEG_CAUGHT 10/10 / ABUTMENT_CHECK ALL PASS。

## 2026-10-06 P1-T7 场景三模式(emit-lib/layout GN 实例/proxy 回归) —— 本体零几何

**改动文件**: `build_scene2.py`(头部导入守护化 + 尾部纯逻辑段/三模式; 默认 proxy 路径零改动)、`masonry2.py`(新增 materialize/anchor_offset/_euler_xyz_matrix, U2 全局唯一放置算子)、`export_print.py`(export_ledger mesh_fn=None 默认走 materialize 回床; 显式路径逐位不变)、新增 `tests/test_p1_scene.py`(15 条 blender-free 单测)。

**冻结影响**: 本体 bridge_body/voussoir/coursing freeze_hash 三对象 sha_sorted/sha_order 逐位一致(隔离树实测 CORE_HASH_IDENTICAL: True); qa_l2 正检 QA_L2_OK(fail/warn/skip 0/0/0)、负控 NEG_CAUGHT 10/10、_check_abutment ALL PASS。`--emit-lib` 出 out/families.blend(FAMILIES_EMIT 与纯 python 族清点互证相等)、`--layout` 出 out/e30_layout.blend(场景 Object 20 < 60; GN 点云 5250 石 × Pick Instance)。layout vs proxy 结构砌体正交侧视剪影(1200px/24spp) SILHOUETTE_IOU=0.9326(>0.9) 且像素非全等(对照口径与残差见 .superpowers/sdd/p1-task-7-report.md)。

## 2026-10-07 P1-T7 审查修复轮(H1/W1/W3/W4/S1/S4) —— 本体零几何

**改动文件**: `build_scene2.py`(cap_to_deck 按族分派锚语义+超底弃石归账; classify_stones clip 打标; 守护导入响亮化; LAYOUT_MAX_OBJECTS 60→50)、`masonry2.py`(materialize 对无烘焙网格的 clipped 石显式 raise)、`tests/test_p1_scene.py`(+6 条/扩 1 条)、`.gitignore`(stones/*.json 反豁免, S4)。

- **H1**: cap_to_deck 旧版把 slab(core cells, 最小角锚)当块中心锚截顶: z0=tz−h/2 半高虚低+桥面采样误用最小角 x0 → 截顶线系统性偏高, CORE 顶穿桥面(全 role 旧断言口径实测 29 块越顶)。修复: 锚语义按 masonry2._ANCHOR_MIN_CORNER 分派——slab z0=transform[2] 不动、只改 params.h/bbox.z1(不变式 bbox.z0==transform[2])、桥面采样 x=bbox 中点; wedge 分支逐位保持。整块超底弃石不再静默: bridge_ledger 记 meta.skipped_below_deck(_ids) 并打 SKIPPED_BELOW_DECK 日志(含审查点名的 ARCH11.EAST.CORE.C15.B02/ARCH14.EAST.CORE.C12.B02)。越顶断言从"只扫 SPANDREL"扩到全 role(世界顶 ≤ 块心桥面, 1e-9)。
- **W1**: LAYOUT_MAX_OBJECTS 60→50(对齐简报; 实测 20 仍过)。
- **W4**: 跨洞裁剪石由 classify_stones 打 params.clipped=True; materialize 对 verts=None 的带标石 raise("clip 石导出必须传烘焙网格")——"整块族网格静默顶替裁剪片"的前向陷阱变响亮错误。
- **S1**: 守护导入分两组: bpy 组缺失→静默 None(pytest 路径不变); bpy 可用而本体模块(G/MAT/LIONS/BEASTS)缺失→显式 ImportError, 不再吞成 bpy=None 静默降级。
- **S4**: .gitignore 反豁免 `!e30_shikongqiao_video/3d/stones/` + `!e30_shikongqiao_video/3d/stones/*.json`(父目录被 `*` 排除时文件级 ! 规则不可达, 须两条; stones_deck.json 只可见不入库)。
- **W3**(仅报告口径): coursing 层"洞内 348 面"改可复现口径(质心入洞三角面数, 探针 rev_iou2.py 口径), 见 p1-task-7-report.md 修复轮节。
- **验收**(隔离树 /tmp/e30_p1/fix1 实测): 本体三对象 freeze_hash 逐位一致(cdba9709…/ba2e0951…/f2968f4c…, proxy 路径零改动, blender 重建零错 SAVED v2); FAMILIES_EMIT 3327→3327 不变(CORE 胞族身份由 bbox x 界决定, 截顶改 h/bbox.z1 不改族数; 纯链 census 互证相等); LAYOUT_STONES 5250→5250(弃审查点名超底 2 块, 救回 buggy 截顶误弃的端带 2 块 ARCH01.EAST.CORE.C08.B01/ARCH03.EAST.CORE.C11.B01); LAYOUT_OBJECTS 20 ≤ 50; SILHOUETTE_IOU 0.9326→0.9393(掩膜 XOR 1852→1657px); layout 掩膜越桥面像素 181→28; W3 复算 coursing 质心入洞 4872 三角面(带内 7306/全层 121960)与审查数逐位一致; tests 193 passed / qa_l2 正检 QA_L2_OK + 负控 NEG_CAUGHT 10/10 / _check_abutment ALL PASS。

## 2026-10-07 P1-T8b G2 收口修复轮(A1/B2/B3/B4/D6/D7/E8, 审查 BLOCK 收口) —— 本体零几何

**改动文件**: `build_scene2.py`(cap_to_deck wedge 截顶重算 transform[1] 前脸锚, 仅此一处)、`p1a_slice.py`(B2 包含型 gap 判/B3 RING 真剪影栅格面积判据/B4 ring↔链 volume 处置宇宙+final_scope_check/覆盖率审计/D6 excluded_ids 旁挂/D7 spandrel-back 全量带界/E8 体积口径/2A 红门纪律)、`export_print.py`(装箱允许 90°/45° 旋转, fit_diagonal 非独占批)、`tests/test_p1_slice.py`(+12)、`tests/test_p1_scene.py`(+2)、`tests/test_p1_export.py`(+2)、`.gitignore`(excluded_ids.json 白名单)、`3d/refs/freeze_manifest.md`(build_scene2 哈希)。

- **A1**(审查 T9 处方更正): cap_to_deck 截顶改 h/transform[2] 时同步重算 transform[1]=side*(hw(xm,z0+h2/2)+proud) —— 旧值锚原层中, 截顶石内错撞进同位背衬退让线。验收恒等式(审查给出): pen+BACKING_GAP ≡ −(|ty|−(hw+proud)), 全链 2290 对余量<1e-6mm, pen>0 修复前 116 对→0; G2 assembly_fit 实体相交 30 对→0。
- **B2**: gap_check_pair 第三级包含判(顶点入体⇒PENETRATION, 射线奇偶), 负控: 吞没盒必抓/共面贴合不抓/反向对称。
- **B3**: ring_band_overlap 判据 point-in-bbox→面积法(RING 烘焙网格逐三角 x-z 投影真剪影栅格 2cm, 分母=链石自身剪影格数), 完全吞没石必排除(单测)。面积 ratio 只记账, 处置由 B4 裁决。
- **B4**(审查三裁+主控 1b/2A): ring↔{SPANDREL,BACK,CORE} pre-inset dedup 宇宙(bbox 预筛+面级精判), PENETRATION 不进缝 fail; 处置按 unique_vol=V(stone)−V(stone∩RING∪) 同栅格度量: case_A(≤1%·V 且 ≤50cm³ 且顶点包含复证)subsume 出集; case_B 按 masonry._hole_cut_polyline 单一真相折线 print-view 裁剪(承压带保座石 z<spz-GAP, 加环 lift 包络), 同位 partner 对称传播(缝一致性); final_scope_check 独立 3D 复测不从桶成员推导。负控 4 条(关 subsume 破不变式/吞没盒 case_A/咬角 case_B/post-inset 拒绝)。
- **D6**: out/print/excluded_ids.json 桶→ids 全表(入库白名单)。**D7**: spandrel-back 全量(不抽样), 实体相交 depth>5mm 或 AABB 交叠>100cm³ 计 fail, 界内豁免全量记账, >50 打 WARN。
- **E8**: 体积口径声明(耳切对角约定 6.2e-3 实测复现/129h 实心体上界/CORE 非加和)、装箱旋转(fit_diagonal)、SLICE_NOTES 重写。
- **红门现状**(主控 2A 预授权 FAIL 交付): verdict=FAIL —— check_stone 106(全部为带裁片 SELF_INTERSECT 1-2 面对级, 耳切在折线密采样+抽稀后的薄片三角伪交叉, 属本轮新裁片网格质量)、gap 216(全部 spandrel-back-bounds, 与 SELF_INTERSECT 石同 id 集合——被自交片污染的面级判)、ring↔链残留 87/903。归因: 裁片耳切网格化质量, T9 范围输入; 判据/桶/阈值零放宽(主控禁令)。
- **冻结影响**: build_scene2 仅 cap_to_deck ledger 链改动, 本体 bridge_body/voussoir/coursing 三对象几何零变化(freeze_hash 实测见 p1-task-8-report 修复轮节); p1a_slice/export_print 不在冻结清单。

## 2026-10-07 P2-T2 修复轮 D3 geom_math 纵剖/收分纯数学单源提取 —— 本体零几何

**主控裁决**: D3(审查 BLOCK 修复, 与 D1/D2/D4-D7 同轮; 本条只记 D3 本体侧)。

**改动文件**: `geom_math.py`(新建, 零 bmesh: deck_z/arch_crown_z/arch_springer_z/arch_rise/arch_center_x/width_at + PIER_X/SPANS 表, 公式自 bridge_geom2 **原样搬移**, 常数读 facts/assumptions, 桥面反向自检与桥长闭合断言随公式迁入)、`bridge_geom2.py`(一行委托+收分消费转发: deck_z/arch_crown_z/arch_springer_z/arch_rise 转发, PIER_X/SPANS 引 geom_math 表, 删本地 `_width_at`(build_body_bm/build_void_bm.hw_at 改消费 geom_math.width_at 同式))、`centering.py`(D3 消费侧: SPANS/arch_springer_z 委托 geom_math, 旧"DECK 线性内插"第二套纵剖公式废除; wrapper 桥面改真抛物线 _GM.deck_z(孔心全局 x+局部 x))、`tests/test_p2_geom_math.py`(新建 8 条: 单元独立锚/委托逐位断言/零 bmesh 子进程证/石账跨源钉)、`refs/freeze_manifest.md`(§2 bridge_geom2 哈希重锚 + geom_math 建行)。

**跨源钉(D3 主控要求)**: geom_math vs 石账(out/ledger_full.json) RING 龙门石 transform z 逐孔 ±1e-9 —— 纯 python 重放账本 params(孔心/ stations/环厚/预抬)×geom_math(springer=arch_springer_z(i), a=SPANS[i]/2, b=arch_rise(i))×masonry 缝宽常量, bmesh float32 顶点量化后取包围盒中心; **实测 17 孔 Δ=0 逐位相等**, 且带 ring_t+1cm 扰动负控(钉非恒真)。

**冻结影响**: blender 重建零错 SAVED v2, freeze_hash 三对象(bridge_body/voussoir/coursing) sha_sorted/sha_order/nverts/nfaces/bbox **逐位不变(CORE_HASH_IDENTICAL: True)**; qa_l2 正检 QA_L2_OK、负控 NEG_CAUGHT 10/10。几何值逐位未动 —— 委托只改公式住址, 不改数值。

## 2026-10-07 P2-T2 审查修复轮 D1/D2/D4/D5/D6/D7 + 变异盲区补测 —— centering 语义重锚, 本体几何零变化

**主控裁决**: 审查 BLOCK(2C+4H+变异盲区)七项 D1-D7(见 p2-task-2-report.md 修复轮节); D3 本体侧另条记录。

**改动文件**: `centering.py`(D1 工作面重锚+D2 RING_T 解耦+D4 id/zone/arch_idx/xc+D5 DECK_CLASH+D6 footprint 结构+D7 语义注记; 删 SPRINGER_ZONE/WORK_CLEAR 分叉)、`facts.py`(D2 停车线: RING_T 维持 0.40 + 行尾 STALE 注记 + SOURCES 溯源更新)、`masonry.py`(D2: RING_T=0.54 加分叉指针注记, 数值不变→几何逐位不变)、`tests/test_p2_centering.py`(重写 20 条, 含变异补测与解耦钉)、`refs/freeze_manifest.md`(§1 facts 哈希重锚+§9 RING_T 行 STALE 注记)。

- **D1**: 工作面基准 = 拱腹 intrados: rib 板顶 z = arch_z(x) − RIB_GAP(0.005 施工隙), 楞木/柱顶随之下移(rib→楞木→楔对→柱堆叠不变); "拱脚区贴 intrados/跨中 extrados+30mm"分叉删除(SPRINGER_ZONE/WORK_CLEAR 常量删失, 测试含 hasattr 负证); 楔副 1:8 行程 0.06m 语义 = **合龙后压缩沉落**(非脱环预抬), lift 参数 = 沉落状态模拟量 ∈[0, WEDGE_TRAVEL], 越行程/负值 raise。
- **D2 停车线响应记录**(主控裁决 2026-10-07): 对齐尝试(临时把 facts.RING_T 改账目真值 0.54)实测 **MET_RING_FIT fail ×2** —— 孔1/孔17: 拱背 2.77 高于桥面 2.73(余量 −0.040m)。**数学根源(判据等价式, M20b 起点)**: 该判据 fail ⟺ `RING_T > spandrel(i)`(crown=deck−spandrel 代入后桥面项消去, 平移不变), spandrel 剖面 1.40(中央)→0.50(端孔), RING_T=0.54 时端孔必红恰 0.04, 与 Z 平移/容差无关 —— **0.40 的旧绿灯测的是虚构几何**(本次统一尝试的价值所在)。按主控裁决收口: facts.RING_T **维持 0.40 原值**, 行尾加 STALE 注记(端孔 extrados 穿桥面 4-11cm 属真缺陷, 债务票 M20b 标定 ring_t(i) 后统一); qa_bridge/MET_RING_FIT 零改动; masonry.RING_T=0.54(券石几何冻结侧, core_hash 门)加分叉指针注记防"善意对齐"。
- **D1 红利(主控裁决#2 确认)**: 工作面改 intrados 后 centering **不再消费 facts.RING_T** —— 新增 `stone_ring_t(arch_idx)` 从石账 params.ring_t 现算(按孔缓存, 账目缺失响亮 raise 不静默兜底), wrapper 缺省环厚走它; 解耦可执行钉: AST 扫描 centering 代码无 `_F.RING_T/facts.RING_T` 消费节点 + wrapper 缺省值 == 0.54(账目真值) + facts.RING_T 仍 0.40。M20b 标定 ring_t(i) 后券架自动跟随。
- **D4**: id = "CEN-ARCH%02d" % (arch_idx+1)(1 基, 与石账 zone/事件账 CEN-ARCH09 同形); 返回体加 zone="ARCH%02d"/arch_idx/xc(geom_math.arch_center_x 孔心表); 测试钉 CEN-ARCH09 + 17 孔 CEN 集合 == 石账 zone 集合(跨源, fail-on-skip)。
- **D5**: 桥面夹持 min() → **DECK_CLASH raise**(消息附 x 位置与余量), rib 顶(全链最高点)纳入夹持, 排位点+rib 采样双重覆盖; 测试: 压低 deck_z_fn 必红(断言消息含 x=/余量/−0.01) + 17 孔真实工况零误伤。
- **D6**: footprint 改 `[{"poly": [(x,z)...], "y0", "y1", "kind": "rib"}, ...]` 按榀(两行)返回 + 全局 xc 平移字段; docstring 改"占位体积取 parts[].bbox 加 xc 平移(全局系), footprint 仅 rib 带轮廓"; footprint_polys 旧键删失(干净切换); 测试: footprint ≡ rib 采样逐点等(独立重算 25+25 点)。
- **D7**: "端孔柱高"语义 = **柱顶标高**(非柱长), docstring+测试注释写明(柱顶 <3.0m vs 柱长 >4m 两量级可分)。
- **变异盲区补测**(审查 M06/M07/M08/M11/M12 存活项): rib 两榀计数恰 2×RIB_SEG_N=48; 楞木 y 向跨两柱头(同排两柱心均在楞木 y 域内); 夹持 raise(见 D5); RIB_T 带界改**含 rib 厚的双侧界** [拱腹−0.005−lift−RIB_T, 拱腹−0.005−lift] 逐顶点; 恒真 stations 测试换独立期望值(中央 8 排/端 4 排字面钉, 排数断言收敛到 test_post_station_counts_pinned_to_literals 一处)。
- **冻结影响**: blender 重建零错 SAVED v2, freeze_hash 三对象逐位不变(本修复轮二次实测, CORE_HASH_IDENTICAL True×2); qa_l2 正检 QA_L2_OK + 负控 NEG_CAUGHT 10/10; 本体 build 链不消费 RING_T, masonry 数值不变, 几何零变化。

## 2026-10-07 M20b 冠部带解剖标定轮 —— ring_t(i) 逐孔化否证, 端孔拱肩未达改数门槛, 本体数值零变化

**改动文件**: `facts.py`（仅 RING_T 注记块 + SOURCES["RING_T"] 台账更新, **数值零变化**）、`refs/freeze_manifest.md`（§3 facts.py 哈希重锚）。`qa_bridge.py`/`masonry.py`/build 链零改动。隔离树 `/tmp/e30_m20b/`。

**测量（方法: intrados 锚定差分 + 锚点对齐堆叠边缘剖面 + 整线扫描, 基准无关/datum-free; 报告 `.superpowers/sdd/m20b-report.md`, 工件 `3d/m20_ctrl/m20b_*`）**:
- 位姿验证: CCTV f000150(m20B_pose_f150) 逐孔洞顶底通扫描 a0-a6 实测 Δz=+0.002..+0.043m —— 模型冠点独立验证 ±0.04; 冬照 16:05(m20C_pose_winter) 沿用(M20C rms 5.29px)。
- **① ring_t(i) 逐孔化否证**: 环带特征逐孔恒定 —— 冬照 a15/a14: 内缘倒角线 0.33-0.35 / 外缘脊 0.59-0.67(106/95 px/m); CCTV a0/a8: 内缘倒角线 0.40-0.43 / 外缘脊 0.62-0.65(50/89 px/m)。端孔与中央孔同带同值(±0.03), 假设(b) "端孔细环 0.35-0.40" 在全部剖面无兑现。统一值维持 masonry.RING_T=0.54。
- **② 端孔拱肩未达 ±0.05 改数门槛**: 檐口整线扫描 deckΔ: a16 +0.265(fwhm 0.25) / a15 +0.326(fwhm 0.70) / a14 +0.322 / a13 +0.196 / a12 +0.087(fwhm 0.12) —— 多特征混锁(檐口底线/檐口顶线/女儿墙底), D_true(a16)∈[0.50,0.80]。假设(a) "spandrel_E 实为 0.65-0.8" 与 (d) "穿面为真桥特征" 均不裁决。
- **审计发现**: M20C 冬照 c16 冠点(5893,2610)与模型投影差 <1px —— 系 ±12px 模型引导窗内"暗→亮"探针锁定, 该处实际为墙面/檐口带(物理拱 16 开孔被桥头垛石/蹬道遮挡), 其 "E3 拱16冠 Δz=-0.008" 为循环标记, 不作独立证据引用。

**裁决**: 债务票 "M20b 标定 ring_t(i) 后统一" 收口 —— 逐孔化否证后, 统一(→0.54)被端孔 deck ±0.05 裁决阻塞(非 ring 问题), 债务转型为 **端孔拱肩高分辨裁决**(候选源: w1222 12-22 冬照位姿拟合(端孔清晰可见)/实地测绘); 运行值维持 facts.RING_T=0.40(D2 先例, 0.40 绿灯=虚构几何性质不变)。

**冻结影响**: blender 重建零错 SAVED v2; freeze_hash 三对象 sha_sorted(cdba97…/ba2e09…/f2968f…) 与冻结清单**逐位一致(零漂移)**; qa_l2 正检 ok=true + 负控 NEG_CAUGHT 10/10; L1 复跑 0 fail 0 skip。

## 2026-10-07 P2-T4 修复轮(幻影石过滤+Σ≥1曲线语义+体积单源+窗口收紧) —— 本体零几何, ledger 曲线语义定稿

**改动文件**: `3d/sequencer.py`/`tests/test_p2_sequencer.py`(围栏内) + `3d/ledger.py`/`tests/test_p2_ledger_v2.py`(主控授权扩围)。**教训一句**: T1 审查轮把「剩余能力」语义的单调律写成无 type 分型的普适闸, T4 换「荷载分担份额」语义时相撞(Σ≥1 数学强制 stone 自持边递增, 递减编码不存在) —— 验证器编码的语义前提必须与数据语义同生共死, 换语义先盘点以旧语义为真值条件的闸门; 单调律现按边类型分型: 退化型(centering/foundation/fill/temporary)单调不增(CURVE_MONOTONIC), stone 型只增不减(STONE_CURVE_REGRESSION), 正反闸成对。工件重生成: events 6122→4070(in_void 2052 幻影石不入日程, 滤除集与 excluded_ids.json 逐位相等), R5a 3187→1307(1880 幻影+余量全为真实环带裁片/墙肩), 支撑边 9315→4076, R3 偶数前缀最大失衡 0.0367→0.002147(F5 体积单源 families.family_mesh+export_print.signed_volume)。全量 pytest 392 绿(基线 379+13 负控/不变量钉)。

## 2026-10-07 P2-T6b 砌筑相位桥轴镜像协变（ARCH07 手性伪影治本 + 账目链重锚）

**改动文件**: `3d/masonry2.py`(face_stones 顺丁奇偶东半孔倒序 + backing_stones 消费序镜像) / `3d/build_scene2.py`(背衬种子跨孔镜像锚 + clip_footprint 保留片上穿出界支补 z1 折返闭合) / `3d/g3_check.py`(CORE 肩载质心锚 + 冠载侧归属 EPS 一致)。**根因链**(Arch07Diag 诊断 + P2T6Fix 三层定位): masonry2 顺丁深度奇偶按孔西缘计数, 跨孔镜像不翻转 → 145/214 镜像位深度反相 → ARCH07 左右半环推力窗错开 ~3%·h_ref 无交。**治本三层**: ①相位协变(只动相位锚, 砖谱 x/z 块界/石型多重集零触碰, stones_pX.json 字节不变); ②in_void 手性修复(48 块跨缘真石出狱, 2052→2004, 两半桥 176/176); ③压力线荷载锚语义修正(slab min-corner→质心, 同 H1 分派表; 冠载侧归属 EPS_X 一致)。**冻结影响**: ledger/print 链全重锚(freeze_manifest §7 T6b 表); 核心三对象参数化路径不消费账目相位, core_hash 逐位不变(本体零漂移直接证据); blend 重建 SAVED v2。**验收**: ARCH07 acceptance 转可行 [33.479,39.106](治本达成); A08-11 转不可行(冠列核心荷载 13.5-15.4 锚修正后作用臂移向冠点 ~1.1m 的物理后果, 停车线维持待主控裁决冠列荷载分摊方式); A07 相位敏感: 反相(旧 102 石集)vs 同相窗差 0.44 = 1.3%·h_ref(上界)。**教训**: 生成器序号(孔西缘起数/行主序)在镜像对称结构上系统性产生手性伪影 —— 凡按序数取值(奇偶/伪随机/锚点)的自由量, 必须以结构对称轴为锚或显式镜像消费; "逐位一致"类断言必须写明坐标系(打印精度同 ≠ 逐位同)。
