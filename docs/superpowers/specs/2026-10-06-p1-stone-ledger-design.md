# Spec#1（P1）：砌体实体引擎 stone-ledger
状态：**v2**（自审×3 → GPT 评审 8.8/10 → 主控裁决：6 项全采纳，见文内 GPT 修正版标记）。上游：M22 路线图 `2026-10-06-m22-stone-by-stone-roadmap.md`。

## 1. 目标与非目标
**目标**：把"合并网格+程序贴面"的桥体，转为**每石一条账目、每石一个可打印流形实体**的砌体数据系统。
**非目标**：建造顺序（P2）、动画（P3）、打印排版（P4）、几何曲线变更（P0/M19-M21 管辖）。P1 期间 P0 曲线若再变，ledger 重新生成即可（数据与代码分离是本 spec 的核心红利）。

## 2. 砌体构造模型（历史真实 + 打印可行的合题）
中国官式石桥剖面 = **三面分层**（待 C 线史料印证，若史料给出更具体名目以史料为准）：
1. **面石层**（可见）：现有 _wedge 贴面块，全深化——深度从 6~30mm 改为**顺丁相间**：顺石深 1.0~1.5m、丁石深入至背衬层（墩基处墙厚达 6m，双面丁石互穿不得，透层职责由背衬乱纹砌承担）
2. **背衬层**（半可见，剖面镜头可用）：粗料石乱纹背砌，深 0.8~1.2m
3. **核心**（不可见）= **truth volume 三层制**（GPT 评审采纳，A 线证据仅证"餬灰"砌缝、未证整芯灌砌）：
   - `ashlar_truth`：券石/面石/丁石/impost 等**可考石件**——一石一 ID，真逐石
   - `core_reconstruction`：内部填芯 = seeded procedural rubble packing（视觉逐石），ledger 全标 **[推断重建]**，不暗示具体石块位置有史据
   - `core_print_cell`：打印**不做整长 core**——按孔/墩/施工层切成 100-300mm(模型尺) 水密 cell，剖开仍见片石面，装配可控
   公开表述纪律：剖面镜头出现 core 时字幕标"[推断填芯]"；"全深真砌体"一词仅指 ashlar_truth 层。
⇒ 块数账：青石面石 ~2800 + 背衬 ~1500 + 券石全深化 193 ≈ **4500-5000**；汉白玉系(栏板/望柱/狮/兽/桥面石)另账 ~600-900；**全账 ≈ 5100-5900 实体**（远低于"全深每石"的 1-2 万，因核心不碎化）。D1 提案（待用户拍板）：采「面石全深+背衬+核心灌砌单实体」——依据=真实官式做法（核心本是片石灌浆非逐块砌），非偷懒；若 C 线史料给出更细内部砌法，按史料改。

## 3. 数据模型
### 3.1 `3d/ledger/ledger.json`（主索引，仓库内，随 curve_hash 版本化）
```
{ "meta": {bridge_rev, curve_hash, seed, scale_params},
  "stones": [ {
    "id": "ARCH09.EAST.RING.C12.B07",  // 纯拓扑语义键: 孔.面.角色.层.块——坐标变化不改 id
                       // 孔=ARCH01..17(西→东), 面=EAST/WEST, 角色=RING/SPANDREL/PIER/
                       // IMPOST/BACK/PAVING/RAIL/POST/CARVE/CORE, 另附 immutable uuid
    "uuid": "7c3f...",   // 永久主键; 谱系字段: parent_id/replaces(拆分合并时维护)
    "evidence": "ashlar_truth|core_reconstruction|measured",
    "family": "wedge-std-09",    // 参数化族(共享网格), 异形块(贴拱切块)族=unique
    "params": {...},             // 族参数: 宽/高/深/切弧/相位
    "transform": [x,y,z,rx,ry,rz],
    "material": "qingshi|marble|mortar",
    "role_struct": "voussoir| facing| backing| impost| paving| rail| carve| core",
    "support_edges": [ {"target":"ARCH09.EAST.RING.C12.B06", "type":"stone",
                        "active_from":null, "active_to":null, "contact":"+X"},
                      {"target":"CENTERING.A08", "type":"centering",
                        "active_from":0, "active_to":"closure+7d"} ],
    // 支撑是**带时间窗的边**(GPT: 支撑会出现和撤除, 静态数组不够):
    // type=stone|centering|fill|foundation|temporary; 券架=一等实体(P2 建, P1 留 schema)
    // P1 只填几何静态边(type=stone/foundation, 时窗空), 动态边由 P2 序列器补
    "stage_hint": "arch_ring|spandrel|pier|deck|rail|carve",  // 施工阶段粗类(P2 细化)
    "print": {"batch": 12, "faces_up": "+Z", "min_feature_ok": true}
  } ] }
```
### 3.2 网格生成
- **id 稳定性规则（GPT 修正版）**：id=纯拓扑语义键（孔/面/角色/层/块），**世界坐标永不参与 ID**（M19 刚发生 1.3m 基准重标定即为反证）；坐标永远是属性；uuid 主键 + parent_id/replaces 谱系处理块拆分合并
- 族库 `families/`：每族一个 bmesh 生成函数（确定性，seed 入 meta）；实例=transform 引用
- 异形块（券石楔、贴拱切块、impost 阶、兽/狮雕刻）族=unique，直接烘焙网格入 `3d/ledger_cache/<id>.obj`（gitignore，curve_hash 变更失效）
- **历史缝 vs 制造间隙（GPT 修正版，两量永不混同）**：
   - `joint_historical_mm`：明缝 10 / 隐缝 2~3——几何模型永久保真值，**1:50 下不放大**（放大 0.05→0.2 会累计漂移拱跨/券石角/墩位/合龙石，毁掉 G1 封版几何）
   - `clearance_manufacturing_mm`：只在 export profile 对**接触面做局部 inset/缩块**（公差吃进石头，不撑大桥）；FIT_TIGHT/NORMAL/LOOSE 三档按块尺寸分派；正式试印前先打**券石接缝 coupon 组**（不同间隙楔形接头实测插配窗口），树脂/FDM/SLA 各一值
   - 模型内接触对不共面不重叠（穿透容差 0.5mm）

## 4. 模块与文件
| 模块 | 职责 | 新/改 |
|---|---|---|
| `ledger.py` | schema/读写/校验/查询(按孔/材质/角色) | 新 |
| `masonry2.py` | 生成器：消费 P0 几何+砖谱 → 产出 ledger+族实例；三面分层+顺丁排法。输入优先级：stones_pX.json 砖谱 > M18 程序兜底布局（G1 前全走兜底，G1 后逐孔切换） | 新(从 masonry.py 渐进迁移，旧路保留出 proxy mesh 供 L2) |
| `printcheck.py` | 逐石流形/自交/最小壁厚/体积/间隙穿透检查；报告=JSON | 新 |
| `export_print.py` | **canonical = 族网格+ledger/manifest**（STL 不承载单位/材质/ID，降为派生格式）；按 ledger 逐块临时实例化→inset→导出 STL/3MF→销毁；`assembly_manifest.json`（材质分组/分批/装配图数据每孔一张） | 新 |
| `build_scene2.py` | 场景改为按 ledger 装配(collection 分区分族), proxy 模式开关 `--proxy`(旧合并网格, 供既有 checks) | 改 |

## 5. 场景架构（GPT 修正版：ledger 是主数据，Blender 是渲染器）
- **不让 5900 个 Object 进 master scene**：石=Geometry Nodes 实例（point=石，attribute=id/family/transform/stage/material），族网格共享；`stage<=current` 控制显隐（P3 动画即改一个整数）；Cycles 特写只 realize 镜头邻域几十块；远景不 realize
- collection 分区：`SPAN01..SPAN17 + ABUT_E/W + TEMP_WORKS`（券架等临时结构独立区）
- 导出走"逐块临时实例化→bake→销毁"脚本路径，主场景恒轻
- 三角形预算 ≤60 万（现基线待实测）；ledger 读写 <2s

## 6. 验证与测试
- 单测（合成小场景，不渲桥）：schema 校验/确定性(双跑 hash 等)/穿透检查抓人造重叠/间隙检查抓人造共面/族库参数边界(最小壁厚 1:50 下 <1.2mm 报 fail)
- 集成：桥全量生成 → printcheck 全石 pass → 导出 100 石试包(G2 门) → L2/32 断言/312 测试在 proxy 模式零回归
- 视觉：正交剖面渲染一张（三面分层可读）+ 任意孔装配爆炸图一张

## 7. 对下游接口承诺
- P2 消费：`supports` 字段 + `stage_hint`(施工阶段粗分类) + 券架对象注册表(P2 新增, 不入打印账)
- P3 消费：`transform` 序列插值起点终点；`id` 稳定命名贯穿
- P4 消费：`scale_params`（缝宽夸张系数/最小特征放大）+ `print.batch` 分批 + 材质分组
- 接口冻结：ledger.json schema v1 随 G2 门封版；改字段=minor 版本+迁移脚本

## 8. 风险
- 丁石穿透对面的排法与券环/墩轮廓相交 → 生成器需布尔裁切(精确 CSG 慢)：应对=丁石深度按列预计算墙厚函数, 不做实时布尔
- 兽/狮雕刻网格非流形史 → printcheck 首当其冲, 预留雕刻修复轮
- P0 曲线未封版(M19 在跑) → P1 开发用当前曲线跑通管线, G1 后一键重生成
- 雕刻件 1:50 细节损失：狮 40cm→8mm、兽鬃/火焰瓣薄边 <1.2mm 打印必断 → 属 P4 决策（简化铸造版 or 雕刻件改 1:25 放大单出），P1 只做 printcheck 标记不定方案
