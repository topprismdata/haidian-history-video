# Spec#3（P3）：逐石建造动画 build-film（Blender 渲染 + Remotion 合成）

状态：**草案 v1.1（三轮自审毕：r1 补旁白-画面同步铁律与 P2 代码边界；r2 落地；r3 核真账数字 5935→3931 入画口径）→ 待用户签字 → writing-plans**。上游：P2 已关账（G3 三门全绿，474 测试）。

## 0. 已定决策（用户拍板 2026-10-08）

- **D3 = Blender 渲画面 + Remotion 合成**：EEVEE 渲 3D 建造镜头，Remotion 挂 TTS 克隆音色旁白/字幕/题卡；E 系列基建（mlx TTS、subtitles、QA 哲学）全复用。
- **D4 = 匠人剪影点缀**：低细节平面剪影（billboard），只出现在堆场/冰道/吊运位；**剪影只考工具形制不考衣纹**（轮廓即全部信息量，规避服饰考据负担）。
- **渲染节奏 = spec+计划先行，渲染等绿灯**：全部逻辑验收绿之前，不开夜跑。

## 1. 目标与非目标

**目标**
1. 1080p30、变速叙事 3-6 分钟的逐石建造动画：**3931 入日程石**按 sequence.json 408 stages 逐序就位（5935 石账中 2004 块 in_void 幻影**永不入画**——void-cut 裁片，此口径与终态回归判据同源），17 副券架立/卸可视化，落架波（λ 四档同波）为高潮段。
2. **状态一致性可机验**：任意抽帧的"在场石集合"必须逐位等于 sequence 推导集合——这是 P3 的第一判据（qa_v2 哲学：石级读回，不是观感）。
3. 旁白素材从 narration_beats.md 生成，成片文案过 narration_lint（四铁律+禁词）。
4. 匠人剪影与工具形制挂证据（C:A2/C:A4/样式雷平格），无出处者 [比较证据]/[推断] 标注，禁臆造。

**非目标**
- 不改 P2 工件（sequence/event_ledger/ledger_sequenced/g3_report/beats 只读）。
- 不做水纹/天光大场面（桥系列既有镜头语言之外）。
- v1 无音效设计（打击声无史据；BGM 走既有管线）。
- 不做 Cycles 全片（仅 4-6 个特写镜头）。

## 2. 输入契约（P2 交付物，消费不改）

| 工件 | 用途 | 锁 |
|---|---|---|
| `out/sequence.json` | 4118 事件/408 stages：显隐真源 | sidecar 1cefc071 |
| `out/event_ledger.json` `meta.centerings` | 17 副券架注册（id/zone/arch_idx/xc/family） | sidecar a908f60d |
| `out/ledger_sequenced.json` | 5935 石几何/族/transform | sidecar f7e26c2f |
| `out/narration_beats.md` | 408 行 stage→规则→G0→素材；四铁律 | sidecar d19d037d |
| `out/g3_report.json` | 三门读数（题卡数据源，引用即锁） | content_sha 7188388d |
| `3d/centering.py` | 券架杆件几何（rib 贴拱腹/柱头/楔石 λ 档） | 代码 |
| `3d/narration.py::narration_lint` | 成片文案验收 | 代码 |

## 3. 架构

### 3.1 帧→状态机（核心，纯 python 可测）
`film_state.py`：`state_at_frame(f, pace, sequence) -> {visible_stones, centering_parts, wedge_lambda_by_arch, silhouette_slots}`。
- `pace.json`（新建，**单一节奏源**）：stage→[start_frame, end_frame] 变速映射表——首孔全细、中孔蒙太奇、合龙/落架拍留白。**渲染器与验收器都从 pace.json 派生帧号，禁止第二套**（E8 页边界不同源累积 288 帧事故的前置防线）。
- **旁白-画面同步铁律（E8 页边界事故前置防线）**：Remotion 是 pace.json 的**第三消费者**——旁白拍点全挂在 pace 的 stage 边界上；TTS 实测时长只能经 `pace_writeback.py`（音频→padding 字段，唯一写入通道）回写，渲染器/验收器/Remotion 三方只读。禁 Remotion 侧自算时间轴。
- 石在场判定：`placement_event(stone) ≤ event_cursor(stage)`；券架件按 CENTER_ERECT/CLEAR 事件；楔石按 WEDGE_RELEASE 的 λ 档下沉量 `z_offset = λ·wedge_drop`（**wedge_drop 属渲染侧新参数，入 P3 自有 `film_geometry.py` 标 [工程参数·敏感性]；centering.py/sequencer.py/g3_check.py 等 P2 代码零修改，只 import 消费**）。
- 飞入路径（渲染层表现，不入场次真源）：每石三段贝塞尔 堆场锚点→吊运锚点→就位位；堆场布局=[设计选择]（分区按族/孔，参考漕运旱船通例）；吊具形制=杩+绞盘 [比较证据·则例附图/清会通图类]，无本桥直接出处即标 [推断]。**路径只影响中途帧，不改"在场集合"语义**（验收在 stage 末帧取态，避飞入中段）。

### 3.2 场景实现（Blender 侧）
- 复用 build_scene2 GN 实例装配（P1 结论：5900 Object 禁入 master scene）。显隐驱动=每帧把 `visible_count` 写入实例域选择属性（python driver，无逐石关键帧）；飞入=GN Set Position 按域属性插值。
- 剪影：平面贴图对象（每镜 ≤5 个），EEVEE 混浊背景前纯黑/深褐；贴图=矢量 SVG 光栅（形制注记入文件头）。
- 机位：侧视正射（建造主力）+ 45° 鸟瞰（波次段）+ 特写机位组；相机轨迹关键帧由 pace 段驱动。
- Cycles 特写 4-6 镜：合龙龙门石/楔石卸落 λ 档/**压力线叠加可视化**（g3 §8.3 逐孔 H 窗与压力线折线单源，[现代分析] 题卡）/餬灰缝（C:A5）/桥成暮色。

### 3.3 合成与旁白（Remotion 侧）
- 帧序列 + pace.json + beats 选材 → `src/e30film/`（E 系列 SlotPage 模式）；TTS=mlx 克隆音色既有管线；题卡数据引 g3_report（引用即锁）。
- 成片文案先过 `narration_lint`（CI 化：文案文件纳入测试），红即拒渲染。

### 3.4 验收（P3 门 = G4）
1. **状态一致性**：抽帧集合 == sequence 推导（全 stage 末帧必查 408 帧 + 随机 100 中间帧）；负控：删/加一石→必红；挪 pace 边界→必红。
2. **节奏同源**：frame→stage 双实现（film_state vs 独立 validator，互不 import）逐帧对拍。
3. **终态回归**：末帧在场集 == 3931 入日程集 == 建成桥场景可见集 == P1 出图（石账零漂移旁证；幻影 2004 三处同为缺席）。
4. **文案 lint**：旁白稿+题卡全过；四铁律在成片文案中逐条可指认。
5. **视觉抽检**：人眼逐拍（E 系列 SOP）+ 剪影不遮关键石位（遮挡率判据）。
6. 渲染绿灯门：1-5 全绿 + 30 帧试渲实测分钟/帧 → 预算表签字后才夜跑。

## 4. 已知难点与预案

| 难点 | 预案 |
|---|---|
| 万帧级渲染时长 | 变速表把 408 stages 压进 3-6 min（≈5400-10800 帧）；EEVEE Metal 实测后定；分段夜跑+断点续渲 |
| GN 实例逐帧驱动性能 | 域属性写入 O(n)/帧可接受；若爆，退化为按 stage 渲（408 关键帧+补间由相机运动承担，石无中途飞行）——[设计降级项，需拍板] |
| 飞入路径穿模（石撞架/撞邻石） | 路径只走空域（堆场在岸侧、吊运沿桥轴上方）；碰撞抽检=对在场盒做 AABB 抽查，违例即调锚点 |
| 剪影考据不足 | 只画工具轮廓+杵/杠杆动作；每个剪影文件头注证据号；查不到即删（宁缺毋臆） |
| 压力线可视化误导 | 只画 §8.3 出货口径 Hmin 读数+题卡条件性文案（viol_uniform_hmax=1 同屏），禁"证明稳"字样 |

## 5. 待定项（自审/签字时拍板）

- E1 成片时长目标（3/4/6 min 档）→ 影响 pace 表密度
- E2 GN 逐帧驱动 vs 按 stage 渲降级：先试渲 30 帧再定
- E3 特写镜头清单终版（4-6 个选题）
- E4 堆场布局图是否入片（一张平面题卡 vs 直接画面交代）
- E5 与 P4 打印工程的素材复用（族模具渲染图可否同场景出）

## 6. 下游接口

- P4：print-pack 分批清单消费同一 ledger（无冲突）；E5 若复用场景，P3 负责 collection 命名规范。
- QA：G4 验收器落 `tests/test_p3_*.py` + 抽帧脚本，纳入全量 pytest（blender-free 部分）；渲染帧比对为独立 CLI（夜跑后跑）。
- 交片产物：`out/film/frames/`、`out/film/e30_film.mp4`、Remotion 工程 `src/e30film/`、`pace.json` 入 sidecar。
