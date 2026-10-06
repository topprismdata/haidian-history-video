# 角度 D：国外平台与官方技术资料 — Blender 做古建筑遗产复原的方法论与硬边界

> 环境：Blender **5.2 LTS**（docs.blender.org 当前 `latest` 即 5.2 LTS Manual，与本项目版本一致）。
> 所有引文均来自**亲自抓取并读到正文**的页面；未读到正文的明确标「未获全文」。

## 0. 一句话结论

Blender 5.2 LTS 对本项目（单座桥、十万~百万面级、headless 脚本化、几何节点参数化）**没有性能或精度上的硬边界**，官方文档反而明确背书「修改器栈非破坏性 + 几何节点参数化」；真正的硬边界在**「无 BIM 语义」「.blend 二进制无法合并协作」「缺少测绘级精度契约」**三处。社区对「什么场景别用 Blender」有明确共识：**要出图、要参数化、要表达假说 = 用 Blender；要出测量成果、要施工图、要可制造 = 不用**。

## 1. 《伦敦宪章》英文原文的准确出处

| 项 | 内容 |
|---|---|
| 标题 | *The London Charter for the Computer-based Visualisation of Cultural Heritage* |
| 版本 | **Version 2.1, 7 February 2009**（文件抬头另印 "DRAFT 2.1"） |
| 英文 PDF | `https://www.london-charter.org/media/files/london_charter_2_1_en.pdf`（13 页，已读全文） |
| 索引页 | `https://www.london-charter.org/downloads.html`（含**中文版** `london_charter_2_1_cn.pdf`） |
| 编者 | **Hugh Denard, King's College London**（载于宪章末页） |
| 旧版 | Version 1.1, June 2006 |
| 官方导言 | `https://www.london-charter.org/introduction.html`（源自 *Paradata and Transparency in Virtual Heritage*, Ashgate 2012, pp. 57–71） |

### ⚠️ 归属陷阱（极易写错，本次最重要纠错点）

核对 ICOMOS 官方教义文本总目录 `https://www.icomos.org/charters-and-doctrinal-texts/`（已读全文）：**《伦敦宪章》不在其中。ICOMOS 大会通过的教义文本里没有它。**

准确说法：起草于 **ICOMOS 旗下 CIPA（Committee for Documentation of Cultural Heritage，1968 年与 ISPRS 联合创立）** 的框架下——宪章自身 Preamble 只提 CIPA，未提 ICOMOS 大会。宪章导言称其已获 "adoption as an official guideline by the Italian Ministry of Culture"，但**截至 2012 年仍在寻求** UNESCO 与 ISO 正式采纳——**至今未获**。

> **不要写成「ICOMOS 2008/2009 大会通过」或「ICOMOS 宪章」。**
> 建议表述：「CIPA（ICOMOS/ISPRS 文化遗产记录委员会）框架下起草的 2009 年 2 月 2.1 版非约束性行业宪章」。

### 可直接支撑本项目方法论的条款（逐字摘自英文原文）

- **Principle 2.1**：*"It should not be assumed that computer-based visualisation is the most appropriate means of addressing all cultural heritage research or communication aims."*
- **Principle 2.2**：*"A systematic, documented evaluation of the suitability of each method to each aim should be carried out..."* → **「摄影测量 vs 参数化」必须写成书面评估的宪章依据。**
- **Principle 4.4**：*"It should be made clear to users what a computer-based visualisation seeks to represent, for example the existing state, an evidence-based restoration or an hypothetical reconstruction … and the extent and nature of any factual uncertainty."* → **重建模型必须自标「假说」身份，是宪章硬要求。**
- **Principle 4.10 + 术语表 Dependency relationship**：*"A dependent relationship between the properties of elements within digital models, such that a change in one property will necessitate change in the dependent properties."* → **参数化建模方法论本身的合法性来源。**

## 2. Blender 官方技术文档（5.2 LTS，已逐页读原文）

### 2.1 精度：float32 对本项目绰绰有余

`.../advanced/limits.html` 原文：*"values within -5,000/+5,000 are typically reliable … **Internally single precision** floating-point calculations are used."*

| 坐标量级 | 可用精度 |
|---|---|
| 100 | 1/131,072 |
| 1,000 | ≈ **0.061 mm** |
| 10,000 | ≈ 0.98 mm |
| 100,000 | ≈ 7.8 mm |

**判读**：桥全长约 150 m，坐标跨度 ±100，单位内精度约 **±0.06 mm**，比照片比对判据（厘米级）精细三个数量级。**float32 不是限制项。** 唯一真陷阱是**直接套用 GIS/UTM 或经纬度绝对坐标**（北京约 39.9°N/116.3°E，量级 1e2~1e6），精度掉到米级——解法是「导入前先减锚点偏移、偏移量存元数据」。

### 2.2 修改器栈：evaluated vs base mesh（官方陷阱）

Python API 官方原文：
> "This is an original object. **Its data does not have any modifiers applied.**"
> "For mesh objects the object.data will be a mesh with all modifiers applied. **This means that in access to vertices or faces after modifier stack happens via fields of object_eval.**"

`to_mesh()` 官方说明：用 original = **不算修改器**；用 evaluated = 算。且 *"The result mesh must be treated as temporary… use `new_from_object()` instead"*。

→ **任何「导出网格/量取尺寸/比对」必须先 `evaluated_get(depsgraph)`；`obj.data` 永远是 base mesh。**（T5 已据此修复）

属性页另有同源警告：Attribute Conversion Operator *"only works on original object data, not including the results of modifiers"* → **参数化生成的属性在 Apply 前不等于最终属性**。

### 2.3 几何节点

For-Each Geometry Element Zone 页官方警告：*"it will likely **always be slower** than working on fewer larger geometries… it's recommended to design the node setup so that **iteration over tiny sub-geometries is not required**."*

→ **17 个拱券若用 For-Each 逐个生成须注意该限制；更稳的是「少量大几何 + Array/Screw 等原生修改器 + 实例化」。**

### 2.4 Cycles 出图可复现性（官方方案）

Sample Subset + Offset/Length + `bpy.ops.cycles.merge_images()` 跨机分片：须**关去噪**、**Max Samples 设为各分片之和**，否则"the subsets will have incompatible noise"。

→ **冻结交付要求「同一命令可复现同一张图」有官方路径。**

### 2.5 大场景性能（社区共识）

`hide_viewport`（显示器图标）**不会**求值隐藏对象；眼睛图标与 H 快捷键**会**求值。例外：**Surface Deform 强制求值其 target 对象**，即使已隐藏。

→ 提速第一手段是 `hide_viewport` 而非眼睛图标；Surface Deform 链路两端必须同时隐藏。

## 3. 协作与版本控制（Blender Studio 官方实测）

`https://studio.blender.org/blog/benchmarking-version-control-git-lfs-svn-mercurial/`（Sebastian Parborg, 2024-10-01）：
- *"**Note though that we only expect linear workflows to work well.** So for example **branching and merging branches is not a workflow we are looking for.**"*
- 评论补充：*"it is only feasible to have **one person working on a .blend file at a time**."*
- 官方解法是「链接 + 库覆盖」。

→ **本项目把参数放 Python/JSON、让 .blend 可从零重建，恰好绕开这条边界——应作为方法论正当性论据。**

## 4. 国外实践规范

### 4.1 Historic England ⚠️ 全部 403 未获全文
HEAG099（Levels of Recording 四级）/ HEAG066（SfM 实践指南）/ HEAG317（度量级测绘合同规范）/ HEAG155（TLS）。**编号与标题多源一致，但所有数值条款未能一手核实，不得写进判据。**

### 4.2 Open Heritage 3D（已读 FAQ 全文）
CyArk + Historic Environment Scotland + USF Libraries。数据类型仅 5 类采集方式；每数据集有 DOI；CC 许可。两条关键提示：*"note that data is often **not georeferenced**"*；*"raw 3D data … is **not suitable for direct printing**"*。

→ **全世界最专业的遗产 3D 仓储，交付物是原始采集数据+元数据+DOI，不是 BIM 语义模型。Blender 在这条生态里的位置是下游「清理/参数化/出图」环节。**

### 4.3 CIPA（已读全文）
1968 年由 ICOMOS 与 ISPRS 联合创立。使命含 *"transfer technology from the **measurement and visualisation sciences**"*，自述 *"a **bridge** between the producers of heritage documentation and the users of this information"*。

→ **CIPA 世界观里「测量科学」与「可视化科学」是两个并列下游学科——这是把「摄影测量成果」与「参数化复原」分开验收的理论依据。**

## 5. 摄影测量 vs 参数化

### 5.1 伦敦宪章给的是「评估义务」不是「答案」

Denard 在官方导言里说得很直白：
> "A common misconception is that the Charter prescribes absolute precepts governing which particular method or approach should be used… **Nothing could be further from the truth:** the Charter consistently, and insistently, **throws the ball back into the court of those about to undertake computer-based heritage visualization**, asking them to articulate the particular aims and requirements of each project."

→ **选型对比的正确写法是「按宪章 2.2 我们书面评估并公开依据」，不是「国外指南说该扫还是该建」。**

### 5.2 摄影测量结构性失效的五种场景（多源实践共识）
1. 无纹理/少纹理的规则平面 → SfM 找不到特征点
2. 强镜面/透明材质 → 鬼影几何与破洞
3. 深凹遮挡区（券洞、栏杆之间）→ 蛛网化表面
4. **需要「理想化」而非「实测」的表达** → 摄影测量在平面引入微起伏，与古建筑的对称性/模数性直接冲突
5. 动态环境（水面、植被、游客）→ 破坏静态场景假设

> **第 4 条对本项目最致命也最重要**：我们判据要比对的恰恰是**对称性、模数性、拱券圆弧规则度**——这些正是摄影测量**最不可靠**、参数化重建**最可控**的量。**这是选「参数化+正交出图比对」而非「实拍扫描比对」的最强技术理由。**

### 5.3 ★ Paul Bourke — Workflow for comparing two reconstructed meshes（CloudCompare, 2015-01，已读全文）

`https://paulbourke.net/reconstruction/cloudcompare/` —— **可直接改写为本项目「正交渲染图 ↔ 实拍照片」定量比对协议**：

1. 网格 → 采样为点云（**推荐 100 万–200 万点**）
2. **把纹理颜色传给点**（"greatly assists the corresponding point selection"）
3. 对齐：推荐**基于人工对应点**，**至少 4 个点且必须在三轴上都有深度分布**——"relatively poor alignment can result if the points are almost co-linear or co-planar"；**对应点选取顺序必须一致**
4. 度量：**C2M（cloud-to-cloud）distance**
5. **归一到真实世界单位**：*"one should **scale the models based upon a known distance, or measure a known distance and apply the scaling**"*

> **跨角度衔接**：角度 B/C 报告指出「照片比对在论文里是空白区」。本条的 CloudCompare 工作流正是**论文之外的成熟实践范式**，恰好补上该空白。

## 6. Blender 的已知硬边界（汇总）

| # | 边界 | 性质 | 对 E30 的影响 |
|---|---|---|---|
| 1 | float32 单精度 | **不构成边界** | ±100 坐标下 ±0.06mm，富余三个数量级。唯一真陷阱是套用 GIS/UTM/经纬度绝对坐标 |
| 2 | 无 BIM/语义内核 | **硬边界** | 不能产出合规测绘成果。定位为复原与传播工具 |
| 3 | `.blend` 二进制无法合并协作 | **硬边界（官方实测）** | 必须以脚本+数据为真相源，`.blend` 为可重生成产物——**我们正是这么做的** |
| 4 | 修改器栈复杂度/求值成本 | 软边界，可管理 | 提速用 `hide_viewport`；避免碎片化迭代 |
| 5 | evaluated vs base 陷阱 | **硬陷阱（易静默出错）** | 量取/导出/检查必须先 `evaluated_get(depsgraph)` |
| 6 | 出图可复现性 | 可解决 | Sample Subset + merge_images 有官方路径 |
| 7 | 面数上限 | **非边界** | 官方 Working Limits 页未列面数上限；「20亿面」为 2008 社区转述，**未获当前官方证实** |

### 「不要用 Blender 做 X」的具体场景（社区共识）
1. 需要制造/施工依据（CNC、钢结构详图）→ 不用
2. 需要测量的法律/合同效力成果（带误差界、检核点、正射比例尺）→ 不用
3. 需要按图纸尺寸驱动全局重算（特征树式参数化）→ Blender 无原生几何约束求解器，`CAD Sketcher` 插件只是覆盖层
4. 需要 BIM 语义（耐火/传热/材料层/造价）→ 无

## 7. 顾虑（主控必读）

1. **《伦敦宪章》归属极易写错**（见 §1）
2. 宪章 PDF 抬头印 "DRAFT 2.1"（正文与官网索引均为正式 2.1）
3. **Historic England 全部 403**，数值条款未核，不得写进判据
4. **搜索引擎 AI 摘要已产出两处不可信内容并剔除**：①称 Open Heritage 3D 常见工具"包括 Blender"——读 FAQ 全文，**通篇未提 Blender**；②称 Meshroom 是"CGI 建筑事务所"——同名噪音
5. **「Blender 支持 20 亿面」未经当前官方证实**，仅 2008 社区帖转述
6. **Seville Charter 未获全文**，不引用其内容
7. 两篇关键论文仅书目可用：Rahaman & Champion *Heritage* 2019 2(3):1835-1851（MDPI 403）；ISPRS 2026 "Photogrammetry on 3D Renders of Parametric Built…"（403，书目细节未核实）
8. 「几何符合性判据与史料符合性判据应分开」是从 HE 文件划分推出的**结构性推断**，非该机构原文
9. 「隐藏物体仍被求值」来源是社区帖而非官方文档，建议在本项目 Blender 5.2 LTS 上最小复现后再固化
10. 官方文档部分为一手原文可直接引用；社区部分建议落地前各做最小验证
