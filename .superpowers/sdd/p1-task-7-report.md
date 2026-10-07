# P1 Task 7 报告: build_scene2 三模式（--emit-lib / --layout GN 实例 / --proxy 回归）+ materialize

日期: 2026-10-06 · commit `1b5f9df` · 隔离树 `/tmp/e30_p1/work`（git archive HEAD=6900449 + 独立 git init，基线复现 173 passed）→ 绿后同步主树。Python 3.9.6（无 `X | None`、无 match）/ Blender 5.2.2 LTS。

## 交付

**`3d/masonry2.py`（仅新增放置算子节）**
- `anchor_offset(family, params, transform)`：族锚点→平移偏移。**wedge-std**：transform 的 x/z=块中心、y=前脸位置（`off=[tx−w/2, ty−proud, tz−h/2]`，U2 context 公式逐位实现）；**slab**：transform=最小角（core_cells 与 params.bbox 同式直写）→`off=[tx,ty,tz]`。未知族 raise（负控：对 slab 误用 wedge 公式则世界 bbox ≠ params.bbox，测试钉死）。
- `_euler_xyz_matrix` + `materialize(stone, verts=None, faces=None)`：`world = 块中心 + R(rx,ry,rz)·(local − 块中心)`；无旋转走 `local+off` 逐位直加（不经矩阵）。块中心取**完整族网格** bbox 中点（裁剪 unique 网格仍按整块语义定位）。纯 python、不改写输入。实测：wedge 世界 y 最大面 == transform[1]（前脸账目语义 ✓）、slab 世界 bbox == params.bbox（逐轴 ==）、旋转后顶点重心不动、GN 实例组合 `placement_point + R·centered_verts` 与 materialize 逐点恒等（±1e-12）。

**`3d/build_scene2.py`（三模式 + blender-free 纯逻辑段）**
- 头部 blender 依赖（bpy/bmesh/bridge_geom2/materials/lions2/beasts2/mathutils）改**守护导入**：无 bpy 环境置 None，pytest 可直接 import；blender 模式行为逐位不变（proxy 全门实测，见下）。
- 尾部纯逻辑段（只用 facts/assumptions/masonry2/families/ledger/export_print）：
  - 桥几何 facts 侧推导（deck_z_at/hw_wall/piers_and_spans/arch_band），blender 模式跑 `_check_geom_parity` 对 G.PIER_X/G.SPANS/arch_springer_z 逐一断言零漂移（实测抓出过 spans 镜像写反的 bug）。
  - `bridge_ledger()`：全桥账目链 = 17 孔 × 东西面石（谱 p0..p8，9..16 镜像复用）+ 背衬（seed=孔号，东西同 seed 镜像对称）+ core（z 带=水线下底..拱心线桥面，端孔带外扩到桥端）。`cap_to_deck()`：谱末层平线高于桥面弧线（端孔一孔内落差可达 0.5m）的块按块心桥面标高截顶（h/zm/hw_t/bbox 同步），整块高于桥面的不留——实测全账 0 块超顶，z∈[−2.2, 7.30]。
  - `clip_footprint`/`_kept_pieces`：跨净空石足印 → **保留片**（净空以外，逐片凸多边形）。拱腹线取与 build_void_bm **同一 NSEG_ARC 弦折线**（石块边内插到同一弦）——layout 的离散净空与 proxy 布尔切割逐弦一致，不引入第二种离散化；曾实测 x-等分采样在起拱段（斜率~9）弦误差 0.33m 吃进洞内，改 chord 对齐后归零。
  - `classify_stones`（out/inside/clip 三分类）+ `census`/`family_identity`（clip 石逐石 `uniq:`，其余按 (family, params-json) 去重）+ `family_obj_name`（排序序号前缀，sorted(名)==census 序，≤63 字节）。
  - `emit_lib()`：全账校验 → 每族一个**材料化前局部网格**（居中）对象入 COL_FAMILIES → `out/families.blend` + `out/ledger_bridge.json`；打印 `FAMILIES_EMIT n=…`。
  - `layout_scene()`：空场景 `wm.link` families.blend 的 COL_FAMILIES（摘掉自动 instance empty，族库不进 view layer）→ 每分区一片点云（顶点=placement_point；属性 sid/fam/fam_idx/stage/mat/xyz/rot/in_void，STRING 属性按 5.x bytes 口径写）→ 共享 GN 树（Delete[in_void] → Instance on Points[Collection Info separate + Pick Instance，Index=fam_idx，Rotation=rot]）→ SPAN01..17/ABUT_E/ABUT_W/CORE 分区（ABUT 为占位：桥台砌体未入账前无石可落）→ `out/e30_layout.blend`；`LAYOUT_OBJECTS` 硬门 <60（实测 **20**）。
- `__main__` 移至文件尾：`-- --emit-lib` / `-- --layout` / 默认 proxy（现行合并网格路径零改动）。

**`3d/export_print.py`（仅 mesh_fn 默认）**
- `export_ledger(mesh_fn=None)` 默认走 `_materialize_to_bed`（materialize → 三轴 min 归零回床）。与显式 `family_mesh` 路径**平移等价**（逐顶点常向量差，dev<1e-3 打印毫米浮点容差；体积/范围相同——同一块砖同一几何）。显式路径零改动，T6 套件原样绿。

**`tests/test_p1_scene.py`（新，15 条，全部 blender-free、不渲桥）**
- materialize：wedge 前脸 y==transform y（验收指定一致性测试）、slab bbox==params.bbox、旋转绕块中心、纯度、未知族 raise。
- GN 组合恒等 == materialize（rot 0 与带旋转双 case）。
- void 分类：内外分诊、跨拱脚保留片面积==足印−净空交（细采样交叉核对 ±5%）、顶点不入洞（≤ARC_STEP 折线残隙豁免）+ 洞心深点必红负控；跨洞面石裁剪网格水密（有向边一一配对）+ 体积为正。
- 净空内必有可剔除石（in_void 判据非恒假）。
- 族清点/身份去重、对象名序稳定；全桥链结构（17 区/三角色/东西共 x 足印/跨孔镜像/顶不越桥面）+ **独立实现链族数互证**（测试自带 hw/deck/镜像装配链，与 BS.bridge_ledger 族数相等）。
- export 默认路径平移等价 + 等价判据对真差异必红负控。

## 验收门实测（主树）

| 门 | 结果 |
|---|---|
| `python3 -m pytest tests/ -q` | **188 passed**（基线 173 + 新 15） |
| `python3 -m pytest tests/bridge3d -q` | **312 passed** |
| `blender -b --python build_scene2.py`（默认 proxy） | 零错 SAVED v2；本体三对象 **freeze_hash 逐位一致**（sha_sorted/sha_order 全同） |
| qa_l2 正检 / 负控 | **QA_L2_OK**（fail/warn/skip 0/0/0）/ **NEG_CAUGHT 翻 10 面全被抓（10/10）** |
| `_check_abutment.py` | **ABUTMENT_CHECK ALL PASS** |
| `-- --emit-lib` | families.blend(1.2MB) + ledger_bridge.json；**FAMILIES_EMIT n=3327 == 纯 python census n=3327**（测试独立链同值互证） |
| `-- --layout` | e30_layout.blend；**LAYOUT_OBJECTS n=20 < 60**；LAYOUT_STONES 5250（SPAN01..17 各 56..488 + CORE 670 + ABUT 0） |
| layout vs proxy 剪影 | **SILHOUETTE_IOU=0.9326（>0.9）** 且像素非全等（RGBA maxdiff=1.0，掩膜 XOR=1852px）→ VERDICT PASS |

## 剪影对照口径（gate 6 的两个裁决，留档）

1. **对照范围**：layout 只含砌体，故 proxy 侧只渲染结构砌体 `bridge_body + voussoir + pier_plinth`（deck/栏/狮/兽/水/岸/雾/桥台引道双侧一致排除）。**coursing（拱肩/墩区贴面层）单独排除**：实测该层拱肩块在侧视投影里二次覆盖券洞净空（中央孔净空带内**质心入洞 4872 三角面**，带内采样 7306/全层 121960——可复现口径：`rev_dump_tris.py` 导出 coursing 三角面后逐面取 x-z 质心、`build_scene2.point_in_void` 判定；2026-10-07 修复轮在 HEAD blend 重算与审查者复测数逐位一致，留档 /tmp/e30_p1/rev_tris_fix1.json。原"348 面"为不可复现的口数，作废。masonry.py 资产既有性状，不在本任务可改范围），而 layout 的面石账目在语义上正是它的替代物；若计入则 openings 被贴面盖死，IoU 物理上限 ~0.66。机位为桥局坐标（proxy 四对象临时归零 −112° 桥轴旋转）正交侧视，1200×120px（1px=0.1375m）、24spp、Cycles GPU、film_transparent、alpha≥0.5 掩膜。
2. **帧内残差 1852px**： pier_plinth 出挑带/桥端条带（layout 无对应账目石）、AA 边缘抖动、券石环出挑的次像素差——量级与渲染非确定带一致。

## 流程记录

- 隔离树先行（/tmp/e30_p1/work，独立 git）；主树落盘前核实与 archive 基线零漂移（三文件 HEAD 哈希一致）后一次同步。
- freeze_manifest `3d/build_scene2.py` 哈希按规程更新（dec29901…→1bac2519…）+ body_changelog.md T7 节登记；本体判据四门（freeze_hash/qa_l2 正检+负控/abutment）重跑全绿后才更新。
- **stones_p0..p6 砖谱入库**（git add -f，目录在 .gitignore 内）：全桥账目链的必需输入此前未跟踪，干净克隆 `--emit-lib` 必 ModuleNotFoundError/FileNotFoundError（C1 同族事故预防；p7/p8/p9 已有入库先例）。stones_deck.json 本链不消费，维持原状。
- commit：`1b5f9df feat(e30): P1-T7 场景三模式(emit-lib/layout GN实例/proxy回归)`（工作树净）。

## 已知边界（非缺陷，留档）

- layout 场景为**桥局坐标**（X=桥轴），未带 −112° 桥轴方位旋转——方位属表现层装配，GN 实例文件保持账目坐标系。
- ABUT_E/W 为分区占位（空 collection 合法）：桥台砌体尚未入 ledger（后续任务范围）。
- 面石账目不含 RING/IMPOST 角色的独立石（券环贴面由谱内块+scene 层 voussoir 表达）；P4 雕件角色不在砌体账目。
- `--layout` 依赖先跑 `--emit-lib`（link families.blend），脚本缺文件时显式 raise。

## 修复轮（2026-10-07）：审查 FAIL 单点 H1 + W1/W3/W4/S1/S4

隔离树 `/tmp/e30_p1/fix1`（git archive HEAD=29a5fa4 + 独立 git，基线 188 passed）→ TDD 先红（6 失败：5 新增 + 扩断言 1）→ 修复 → 193 passed → blender 全门绿 → 一次同步主树。Python 3.9.6 / Blender 5.2.2 LTS。

### H1 cap_to_deck 按族分派锚语义（HIGH，唯一 FAIL 单点）

- **病灶**：旧版对全体石用块中心锚公式截顶。对 slab（core cells，最小角锚）意味着 z0=tz−h/2 半高虚低 + 桥面采样误用最小角 x0（顺坡偏差）→ 截顶线系统性偏高，CORE 胞顶穿桥面弧线。
- **越顶数前后（全 role，世界顶 vs 采样点桥面，容差 1e-9）**：
  - 旧断言口径（采样 transform[0]）：修复前 **29 块**越顶（全部 CORE）→ 修复后按新口径（采样块心 bbox 中点）**0 块**；
  - 块心口径：修复前 18 块 → 修复后 0 块。
- **layout 掩膜越桥面像素**（同机位正交侧视，掩膜 px 高于 deck 曲线 +0.5px AA 豁免）：181 → **28**（−85%；余量=楔石角点亚像素+AA 边带）。
- **slab 负控**（合成 cells + 平桥面 monkeypatch）：截顶后 `transform[2]==bbox.z0` 不变式成立、世界 z 跨度==bbox 跨度（1e-12）、截后顶==块心桥面（1e-9）；wedge 中心锚分支逐位保持（zm=z0+h2/2 回归钉）。
- **超底弃石归账**：`bridge_ledger` 记 `meta.skipped_below_deck(_ids)` + stdout `SKIPPED_BELOW_DECK n=52`（修复前静默弃；含审查点名 ARCH11.EAST.CORE.C15.B02 / ARCH14.EAST.CORE.C12.B02，两块修复前因病灶锚位虚低而**错误在账**，修复后弃且记名）。
- **意外收获（buggy 截顶误弃救回）**：修复让端孔外扩带 2 块胞（ARCH01.EAST.CORE.C08.B01 / ARCH03.EAST.CORE.C11.B01）从"被病灶错误丢弃"回到账面——净账面 5250→5250（弃 2 救 2），角色构成不变（SPANDREL 2290/BACK 2290/CORE 670）。
- **FAMILIES_EMIT 3327→3327 不变**（简报预期"会变"实测不成立：CORE 胞族身份由 bbox x 界决定，截顶只改 h/bbox.z1 不改族数；纯 python census 互证相等）。

### W1 / W3 / W4 / S1 / S4

- **W1**：`LAYOUT_MAX_OBJECTS` 60→50；实测 LAYOUT_OBJECTS n=20 ≤ 50。
- **W3**：报告"348 面"改可复现口径（见上方剪影对照口径 §1 的改写）——质心入洞 4872 三角面，修复轮在 HEAD blend 重算与审查者复测数逐位一致。
- **W4**：`classify_stones` 给 clip 石打 `params["clipped"]=True`；`masonry2.materialize` 对 verts=None 的带标石 raise（"clip 石导出必须传烘焙网格"）——前向陷阱响亮化；未裁剪石不打标、默认路径不变（测试钉）。
- **S1**：守护导入分组：bpy 组缺失→静默 None（pytest 路径不变）；**bpy 可用而本体模块（G/MAT/LIONS/BEASTS）缺失→显式 ImportError**。测试用 sys.modules[名]=None 模拟缺文件（reload 负控）。
- **S4**：`.gitignore` 反豁免。⚠ 审查给的单行 `!e30_shikongqiao_video/3d/stones/*.json` **不可达**——gitignore 语义下父目录被 `*` 排除时文件级 `!` 规则无效（check-ignore 实测复现），故补目录级 `!e30_shikongqiao_video/3d/stones/` 共两条；`stones_p10.json` 假想件实测从被吞变为 `??` 可见；stones_deck.json 只可见不入库（git add 仍需显式）。

### 全门回归（隔离树 fix1 实测，主树六文件逐字节同步）

| 门 | 修复前(T7) | 修复后 |
|---|---|---|
| `pytest tests/ -q` | 188 | **193**（+5 新增/扩 1） |
| `pytest tests/bridge3d -q` | 312 | **312** |
| blender proxy 重建 | 零错 | **零错 SAVED v2**（proxy 路径零改动） |
| freeze_hash 三对象 | cdba9709…/ba2e0951…/f2968f4c… | **逐位一致** |
| qa_l2 正检 / 负控 | OK / 10-10 | **QA_L2_OK / NEG_CAUGHT 10/10** |
| `_check_abutment` | ALL PASS | **ALL PASS** |
| `--emit-lib` | 3327 | **3327**（+SKIPPED_BELOW_DECK n=52） |
| `--layout` | 20 < 60 | **20 ≤ 50**（LAYOUT_STONES 5250） |
| SILHOUETTE_IOU | 0.9326（XOR 1852px） | **0.9393（XOR 1657px）VERDICT PASS** |

对照产物：/tmp/e30_p1/fix1/cmp_proxy.png、cmp_layout.png、cmp_mask_*.png；修复轮越桥面量化探针（before_layout.png 为主树 T7 版 layout blend 同机位重渲）留档 /tmp/e30_p1/。

### 流程记录

- freeze_manifest `3d/build_scene2.py` 哈希按规程更新（1bac2519…→c4cf0110…）+ body_changelog.md 修复轮节登记；masonry2.py 不在 manifest 冻结清单（核实过），改动由本报告与 changelog 记录。
- commit：`fix(e30): P1-T7审查修复(cap_to_deck slab锚+越顶全role断言+clip响亮化+门常数50+gitignore反豁免)`。
