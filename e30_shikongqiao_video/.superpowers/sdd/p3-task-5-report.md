# P3-T5 报告: Blender 无头渲染驱动(film_render.py) + 3 帧冒烟

日期: 2026-10-08 · 执行: P3T5Render · commit: `feat(e30): P3-T5 无头渲染驱动(GN阈值显隐+选择记录JSONL)`

## 交付物

| 文件 | 内容 |
|---|---|
| `3d/film/film_render.py` | 无头驱动: CLI `--frames a-b --out DIR`(另有 --blend/--pace/--seq/--work/--samples) |
| `3d/film/film_layout_build.py` | **T5b** 点云扩容 builder: 5935 全量 → out/film/layout_film.blend(--verify-only 取证) |
| `3d/film/_probe_scene.py` | 场景结构探针(blender -b <blend> -P, 只读, JSON 到 stdout) |
| `tests/test_p3_render_smoke.py` | 3 测试(blender 门控 skipif): 冒烟 + 两负控 + 四层一线 |
| `tests/test_p3_film_layout.py` | **T5b** 结构负控 5 支(裁判在测试, builder 只 dump 事实) |
| `tests/conftest.py` | session 夹具: film blend 缺失/陈旧自动重建 + 输入 sha 钉 |

## 一、场景结构探针(先探后写, 计划 Task 5 前置指令)

探针: `blender -b <blend> -P 3d/film/_probe_scene.py`(两个 blend 各跑一遍, 结论):

**3d/e30_bridge.blend**(P1 proxy 默认路径产物, sha `edbac0b6…8baa`):
- 561 物体(560 MESH + 1 LIGHT), 全是成桥合并网格(lions/beasts/bridge_body/voussoir…)
- **无 GN 修改器/无 GN 节点组/无相机/无 CEN-ARCHxx/无楔石物体** —— 石级几何不存在

**3d/out/e30_layout.blend**(build_scene2 `--layout` 产物, sha `6fd0dc24…83dd`):
- Scene Collection → 20 个 collection(SPAN01-17/ABUT_E/ABUT_W/CORE), 每个 1 个 `points_XXX`
  点云对象, 挂 GN 修改器 `gn` → 共享树 **`P1_LAYOUT_INSTANCES`**(8 节点:
  GroupInput → DeleteGeometry(in_void) → CollectionInfo(PickInstance, SeparateChildren,
  库链 COL_FAMILIES) → InstanceOnPoints(fam_idx 定实例, rot 定朝向) → GroupOutput)
- 点云域属性: `sid`(STRING, 石 id)/`fam`/`fam_idx`(INT)/`rot`/`in_void`(BOOL); 共 5250 点
- **无相机/无灯/无 world/无券架/无楔石物体**; 引擎已 BLENDER_EEVEE 1920×1080

### 计划偏差 1: 消费对象 e30_bridge.blend → e30_layout.blend
计划写"Consumes e30_bridge.blend(build_scene2 产物)", 但探针证明该文件是 proxy 合并
网格场景, **无法表达逐石显隐**; GN 实例装配场景(计划自己的接口语言"GN 域属性写入
实例集"只能落在这里)是 `out/e30_layout.blend`——与 context 场景结构注记一致(石=GN
实例装配, Object 禁入 master scene 是 P1 结论)。驱动消费后者; 测试对**两个原料都断言
sha 不变**(只读打开纪律), 实测前后逐位同(上表 sha 即今日钉值)。

### 计划偏差 2: 券架/楔石/灯由驱动生成执行脚手架
layout blend 无 CEN-ARCHxx/WEDGE 物体(计划假设其存在), 驱动在建 work 副本时生成
`[设计选择·执行脚手架]`: `COL_CENTERING/COL_WEDGES` 两 collection, CEN-ARCHxx=起拱线
下支箱(宽 0.76×孔距), WEDGE-ARCHxx=起拱线下楔块(1.2×1.0×0.3m), 几何锚只取 geom_math
单源(arch_center_x/arch_springer_z)。**非考古复原**, T8 灯光/材质轮再细化。另补 SUN+
天光 world(P1 blend 无灯, 无灯渲染全黑)与相机 CAM_P3_FILM(clip_end=20000, 大场景
远裁剪面教训沿用)。

## 二、驱动机制(薄执行, 不内嵌判据)

- **在场判定单源**: 只 import film_state; 每帧 `state_at_frame` → 四项机械执行:
  1. **GN 阈值显隐**: 初始化时逐点写持久域属性 `vis_rank`(int)= 该石 PLACE_STONE
     事件全局秩; GN 树手术加输入 socket `vis_idx` + `vis_rank >= vis_idx` 删除支
     (接在 P1 原 in_void 剔点支之后, fail-closed 默认 0=全删)。每帧只写一次
     `vis_idx = len(visible)`。
  2. **楔石位移**: `WEDGE-ARCHxx.location.z = base_z - λ·WEDGE_DROP_M`(λ 直读
     wedge_lambda, 系数单源 film_geometry)。
  3. **券架显隐**: `hide_render/hide_viewport = (CEN-ARCHxx ∉ centering_up)`。
  4. **相机**: 位姿/投影 = `CAMERA_TRACKS[phase]`; DONE 段内 loc_start→loc_end 线性。
- **落盘**: 每帧 `selection.jsonl` 行 `{"frame","selected"(sorted),"wedge_lambda",
  "phase","driver":"film_render"}`(计划原文 schema, T8 对拍信任面) + `probe.jsonl`
  行(场景**回读**: 楔石物体 z/券架可见布尔/相机实参——负控取证源, 不只看记录) +
  `timing.json`(每帧耗时)。
- **原料只读**: open → 手术 → `save_as out/film/work.blend`, 原件永不回写。
- **Blender 5.2 API 备注**(5.2.2 LTS 实测): NodesModifier **不支持 ID properties**
  (`m["Socket_2"]=x` 报 TypeError), 输入值走 `m.properties.inputs["Socket_2"]["value"]`;
  STRING 域属性读出为 bytes。

## 三、测试与负控证据(全绿, `4 passed in ~18s`, 含夹具重建)

| 测试 | 断言 | 结果 |
|---|---|---|
| test_layout_structure(T5b) | 五支结构负控(见 §五表) | ✅ |
| test_render_3frames_smoke | 帧 0/71/7199 真跑 rc==0; PNG 存在; **选择记录==状态机**(逐帧 selected/phase/wedge_lambda); **末帧四层一线**(selected/probe.vis_idx/probe.scene_instances==3931); work.blend 落盘; film blend+全部只读输入 sha 不变; 相机接线(BUILD=ORTHO/165, DONE 末帧=loc_end PERSP) | ✅ |
| test_wedge_drop_negative_control | **读场景物体位置**(probe.jsonl 回读): λ=0 帧 vs λ=1 帧 17 孔楔石 z 差 == −WEDGE_DROP_M(1e-6); λ=0 帧停基准位 | ✅ |
| test_centering_visibility_negative_control | CEN-ARCHxx: 帧 71(centering_up={CEN-ARCH01})回读可见集合**逐孔==状态机**; 帧 0 与 7199 全隐藏 | ✅ |

选帧: 0(BUILD/10 石/λ=0)、71(首个券架在场帧, stage 起点扫描)、7199(DONE/3931/λ 全 1)。

## 四、每帧耗时实测(T8 预算表输入)

EEVEE, 1920×1080, taa_render_samples=16, 本机(macstudio, 前台),
**T5b 扩容 blend(5935 点)**:

| 帧 | vis_idx | 耗时 s |
|---|---|---|
| 0 | 10 | 0.92 |
| 71 | 26 | 1.25 |
| 3600 | 1695 | 1.05 |
| 7199 | 3931 | 1.56 |

- 扩容前(5250 点)对照: 0.71/0.74/0.79/0.97 s —— +685 实例满帧 +0.6s;
  表内 71 帧高于 3600 帧为冷进程 shader 编译噪声, 趋势以 vis_idx 单调为准
- 单次进程 init(GN 手术+5935 点秩写+脚手架+work 另存)≈0.5s/帧段启动一次
- **外推: 7200 帧 ≈ 1.8–2.5h 墙钟**(0.9–1.6 s/帧 + init×段数), 仍低于
  6h 夜跑切点; T8 30 帧试渲预计 <1min(不含启动)
- 注意: timing.json 语义=单次调用的逐帧耗时(多次调用覆盖); 汇总以上表为准

## 五、跨链缺口(已裁决关闭 → T5b 点云扩容)

§五初版上报的"735 无实例 + 50 内藏"缺口, 主控两轮裁决(2026-10-08)定性:
P1 几何链(spec/layout 5250)与 P2 账(5935=5250+685)并存是**设计使然**
(两表征并存, 685=impost-step 492 + ring-wedge 193 是 P2 打印表征扩账);
film 需要全量实例表征 → **T5b 点云扩容**(组级映射路线因 layout blend 无
coursing/voussoir 可切被探针证伪作废):

- 新增 `3d/film/film_layout_build.py`: 消费 ledger_sequenced 5935 全量 +
  build_scene2 单源函数(identity/census/placement_point/layout_group,
  blender-free 段), 产 `out/film/layout_film.blend`(20 分区点云, 0.5s)。
- 网格来源层级(裁决钉死): **A**(5250 spec 石)= families.blend 2824 族
  对象, 随 GN 树 append 从 P1 layout blend 拖带(link), 名字序号零重排;
  **B**(685 RING/IMPOST)= ledger_sequenced `params.bake` 同源还原
  (p1a_slice 逐石重放 masonry 单一真相图元提取, 顶点多重集互证), 经
  families.family_mesh 确定性还原 —— 无 proxy 网格, 停报条件未触发
  (4 族 dispatch 齐备)。
- fam_idx 序: A=P1 emit 序号(嵌名), B=2824+rank 续排; sorted(名)==序号
  (PickInstance 序双保险, 同 P1)。
- GN 树: P1_LAYOUT_INSTANCES **append 复用**(单一真相, 零重实现);
  5.2 实证 append 拖带 link 版 COL_FAMILIES(本体只读), 另建本地
  COL_FAMILIES_FILM 装 A+B 并回接 Collection Info 指针。
- **显隐语义升级(四层一线)**: in_void = id ∉ PLACE_STONE 日程(excluded
  2004, GN 首支剔除); 排程 3931 全部获得实例(50 颗"已排程几何内藏"
  异常随点云重建消解 —— 排程石不再标 in_void)。**末帧场景可见实例
  3931 == 选择记录 == 状态机 == 账面日程**。驱动 write_vis_ranks 升级为
  硬双射断言(缺失/重复/账外非 void 一律 raise)。
- P1 工件(e30_layout.blend / e30_bridge.blend / families.blend)全程只读
  不动, sha 测试钉。

### T5b 负控(tests/test_p3_film_layout.py, 裁判在测试, builder 只取证)

| 负控 | 断言 | 结果 |
|---|---|---|
| 点数 | blend 点数 == 账面 5935 | ✅ |
| in_void | == excluded 2004; 非 void 集 == 排程集(3931) | ✅ |
| 分区守恒 | 20 zone 逐区计数 == 单源重算 | ✅ |
| 族结构 | 3509 族对象(2824 A+685 B); GN 树 8 节点; CI 指针接本地族 | ✅ |
| 100 石对账 | sid→xyz/rot(float32 容差 1e-5)/fam_idx(精确) == 单源重算 | ✅ |

## 六、T8 终态回归口径(裁决定稿, 供 TRIAL_BUDGET 引用)

**四层一线**: 末帧场景实例集 == 3931 == 选择记录 == 状态机(scene 层由
驱动硬双射断言 + T5b 负控背书); 在此之上, 末帧渲染 PNG 与 P1 建成桥出图
(cmp_side 同机位重渲)做非空气区 RMS —— 视觉层末帧含 GN 3931 实例全量
(5250 spec 表征 + 685 RING/IMPOST 打印表征首获实例), 与 P1 出图的几何
人口一致(spec 5250 = GN 3196 可见 + 内藏; 差异仅剩渲染口径, T8 实测定阈)。
spec §3.2 口径: RING/IMPOST 不再走场景合并网格组级动画(该路线已证伪),
以点云扩容全量逐石表征替代。

## 七、T8 注意事项

- 冒烟图低对比(白石近白天光): 灯光/world/ToneMapping(AgX)建议 T8 试渲轮调, 不影响
  本任务验收口径
- samples=16 冒烟档; T8 预算表如提采样需按倍数重测每帧耗时
- 断点续跑"逐字节同"验证(T8 计划项): selection/probe 为 append 模式, 重跑同帧会
  追加重复行, T8 对拍前按 frame 去重或整段清目录重渲
- 楔石/券架为占位脚手架, T8 灯光轮可替换形体(接口不变: 物体名+base_z 自定义属性)
