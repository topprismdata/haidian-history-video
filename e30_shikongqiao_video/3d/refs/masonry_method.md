# 逐块砌筑建模调研：从程序化噪声贴图到真块石砌筑

- 调研日期: 2026-10-05
- 任务: 回答三问——①学术/HBIM 离散块体(discrete voussoir)做法 ②Blender GN/bmesh 实操配方 ③十七孔桥真实砌石数据——并给出本项目逐块化 Top5 动作与每孔券石数建议。
- 方法: web_search 一手渠道（论文出版页/官方仓库/Discourse API/Stack Exchange API/官方文档/基金会与学会原文）+ 本地实拍照片量化采样（延续 balustrade_count.md 的图像推导纪律）。已逐条验证 URL 存在性（GitHub API 逐一 200 校验；Archipack"券石拱"参数经 features 页核实**不存在**，相关 AI 综述说法已剔除）。
- 收录标准: 论文/官方仓库/官方手册/学会基金会原文/社区一手实做帖（附可下载文件或具体参数）；拒绝内容农场（obj.cc 系已被本项目 abutment_design.md 判为农场，本文一律不用）。他桥数字只作方法学参照，禁止移植为本桥事实（FACTS §4 M0 纪律）。
- 项目约束对齐: 纯 bmesh/GN、无外部网格/贴图、Python 3.9.6、Blender 5.2.2 LTS；核心历史尺寸走 `Python facts → deterministic generator`，GN 只做表现层（FACTS.md L265-266 教训条）；本体三对象处于 CONDITIONAL_RECONSTRUCTION_FREEZE 候选（freeze_manifest §9，未锁定待裁决）。

---

## 一、学术/HBIM：石拱桥离散块体建模怎么做的

> 共同结论：主流谱系是 **"参数化生成器产出块体几何 → 块体作为离散单元(带界面缝) → HBIM/结构分析"**。几何层算法高度一致：拱圈按放射楔块 N 等分（N 奇数、拱顶居中一块），缝宽作独立参数；桥墩/腹拱按层错缝。对本项目可复用的是**块体数据结构与生成算法**，不是扫描管线。

### 1.1 COMPAS 生态（ETH Block Research Group）——块体装配的开源参考实现
- 来源: https://github.com/compas-dev/compas ；块体装配 https://github.com/BlockResearchGroup/compas_assembly （GitHub API 200 实测）；
- 要点: `compas_assembly` 把砌体表达为 **Block 列表 + Interface(界面) 图**：块体=网格，界面=相邻块接触面集合，天然对应"逐块 + 真实灰缝"的几何语义； RhinoVAULT2/`compas-RV`(https://github.com/BlockResearchGroup/compas-RV) 与 `compas_tna`(https://github.com/BlockResearchGroup/compas_tna) 演示"曲面 → 分块(tessellation) → 逐块 voussoir"的完整链路。
- 可落地参数: Python 包（pip，支持 3.9）；数据结构可抄——`Assembly(blockmeshes, interfaces)`；界面即缝。**本项目 Python 3.9.6 可直接 pip 安装参考其数据结构**（不必引入运行时依赖，纯参考）。

### 1.2 Sacco, Ridella & Calderini (2026)《A Parametric HBIM Approach to Geometric Uncertainty Modelling for Heritage Bridge Structural Analysis》
- 来源: Buildings 16(15):3054, 2026-08-02, https://www.mdpi.com/2075-5309/16/15/3054
- 要点: 桥梁 HBIM 逐块参数化族（跨径/矢高/圈厚/块数/缝厚为族参数）；因内部砌筑不可扫，用参数化生成**多套几何上可能的内部块体配置**做敏感性分析——与本桥"无测绘值、走工作值+敏感性"处境同构。
- 可落地参数: 族参数集 = {span, rise, ring thickness, voussoir count, joint thickness}；"几何不确定性 = 参数带宽"的做法可直接映射到本项目 facts 工作值 ± 带。

### 1.3 Jing, Sheil & Acikgoz (2022)——多跨石拱桥**合成生成器** BridgeNet
- 来源: Automation in Construction, "Segmentation of large-scale masonry arch bridge point clouds with a synthetic simulator and the BridgeNet neural network", https://www.researchgate.net/publication/362053439
- 要点: 其 synthetic simulator 就是一个**程序化多跨拱桥生成器**（逐孔跨径序列、墩、拱圈逐块、腹拱、栏杆），用于渲染训练数据——证明"整桥逐块程序化"在学界是成熟路径；分割端按拱圈/墩/腹拱语义分块。
- 可落地参数: 逐孔参数化 + 块体级语义标签（本块属于第几孔第几块）→ 本项目生成器建议给每块写 `arch_index/block_index` 自定义属性，供 QA 与材质按孔渐变。

### 1.4 Valero, Bosché & Forster (2018)——砌缝自动提取（2D 连续小波）
- 来源: Automation in Construction, "Automatic segmentation of 3D point clouds of rubble masonry walls", PDF: https://cyberbuild.eng.ed.ac.uk/sites/cyberbuild.eng.ed.ac.uk/files/publications/journals/Valero-2018-AutoCon.pdf
- 要点: 把表面展开成 2D 参数域后，对深度/强度图做 **CWT(2D 连续小波)** 检测缝线再聚类成块。对本项目的用法不是扫描，而是**同款思路可搬到照片**：将来拿到近正面高清照，可在"沿券圈展开的强度剖面"上做一维小波/极值检测数缝——本文 §3 的照片计数就是其手工简化版。
- 可落地参数: 展开域 + 一维强度剖面 + 平滑窗 + 极小值显著度阈值（本文实测用 25 点滑窗 + >6 灰阶显著度，见 §3.2）。

### 1.5 YADE 开源 DEM——块体=显式顶点多面体、缝=界面本构
- 来源: https://gitlab.com/yade-dev/trunk （examples/PotentialBlocks、examples/Polyhedra）；文档 https://yade-dem.org/doc/potentialparticles.html ；方法学论文 https://pureadmin.qub.ac.uk/ws/portalfiles/portal/620424330/YADE-CPC.pdf
- 要点: voussoir = 按顶点列表构造的凸多面体（楔块 8 顶点），块间摩擦/黏聚界面；3D DEM 模拟拱桥的通行做法（如 ResearchGate 327688854 一类工作）。几何生成部分与渲染建模完全同构：**块=极坐标楔盒**。
- 可落地参数: 楔块 8 顶点 = 内弧两点(R1,θ0/gap、R1,θ1∓gap) + 外弧两点(R2,θ1∓gap、R2,θ0/gap) × 桶轴深度两端；缝以角度收缩表达（内窄外宽，与中式灰缝"外宽内窄"一致）。

### 1.6 孔庆普《中国古代石拱桥——古桥各部名称重新命名》(2009) + 《两项古桥结构分析》(2011)
- 来源: 北京茅以升科技教育基金会·古桥委员会学术著作，https://www.mysf.org.cn/Detail/index.html?id=691&aid=291 、 https://www.mysf.org.cn/Detail/index.html?id=691&aid=293 （全文已逐字回读）
- 要点: ①1951 年交通部部颁古桥术语：拱碹/主拱圈/护拱/碹脸/拱眉石/龙门石/撞碹/海墁/分水体/凤凰台——**建模对象命名以此为准**（本项目 FACTS 术语表同源）；②虎坊桥**拆桥实测**：五边折线形"纵联分段并列式"结构，石板厚 32cm、跨 5.10m、矢高 2.25m，拆除侧墙后自行坍塌——一手证明北京古桥券体是**纵联分段并列**（多道平行拱圈、段间错缝），且依赖周围砌体共同工作。
- 可落地参数: "纵联分段并列"= 桶轴方向分道、每道内放射分块、相邻道错缝半块——正是本项目券圈离散化的砌法模板。

### 1.7 小结（算法配方，学术侧收敛）
拱圈: `N = 奇数`, `step = π/N`（半圆）, 中央块=龙门石（常加宽 1.2–1.5×）, 缝=独立参数(8–25mm)以角度收缩实现; 纵联: 桶轴分道 M 道, 相邻道错缝 0.5 块; 墩/侧墙: 层高 h、层内错缝 0.5L、转角用大块。以上每个量都应对应本项目一个 facts 常量。

---

## 二、Blender 实操配方：GN / bmesh 逐块生成

> 结论：**本项目主几何走 bmesh（可测、可哈希、可进 QA），GN 用于曲线驱动的表现层阵列**。社区配方在"楔块拱"上没有现成权威节点图（Archipack 无 arch 原语，已证伪），但"曲线→点位→实例化+中央块替换"与"网格+取模错缝"两套底层的社区一手材料齐全，楔盒生成数学见 §1.7/下述参考实现。

### 2.1 BagaPie Arch Generator（Bagattini Antoine，免费 GN 拱生成器）
- 来源: 80.lv 报道(2022-04-11, 附作者/Gumroad/视频): https://80.lv/articles/an-amazing-arch-generator-made-using-blender-s-geometry-nodes ；工具: https://gumroad.com/a/310542163 ；演示: https://www.youtube.com/watch?v=FlLotEd0zFU
- 适用对象: 拱（洞门/拱圈），GN 实现，Blender 3+。
- 配方摘要: 曲线主控 + 实例化 + 参数面板（高度/厚度/细节块数等可调）；是社区最接近"拱券逐块"的现成节点图。
- 可落地参数: 面板组织方式（块数/厚/高/seed）可抄；**核心尺寸仍须走本项目 facts→Python**（GN 不作尺寸数据库，FACTS 教训条）。
- 风险: 生成的是装饰性拱，无中式券脸/龙门石语义；5.2 导入旧节点组需探针。

### 2.2 Blender SE #311786: GN 在任意物体表面铺砖（Chris, 2024）
- 来源: https://blender.stackexchange.com/questions/311786/how-do-i-create-bricks-on-an-object-using-geometry-nodes （附节点图与 blend-exchange 文件）
- 配方摘要: Grid/Curve→点阵；`row_index = floor(z/step)`；`offset = (row_index % 2) × (L+g) × 0.5` 加到 X → Set Position → Instance on Points；缝隙=g。
- 可落地参数: 错缝系数 0.5（running bond），步距 = L+g，行距 = h+g；把 0.5 暴露成参数即可切一顺一丁/三顺一丁。
- 风险: 平面网格铺到曲面需按曲率重排——桥身曲面用"沿桥轴曲线 + 法向偏移"代替 Grid。

### 2.3 Blender SE #294914: 曲线+自定义截面生成柱/拱（含中央特殊块）
- 来源: https://blender.stackexchange.com/questions/294914/how-to-create-a-geometry-node-based-generator-for-columns-with-a-custom-side-pro
- 配方摘要: Resample Curve(Count=N) → Curve to Points(旋转=切线) → Instance on Points；用 `Index == (N-1)/2` 比较驱动 Switch，把中央实例换成 Keystone 网格——**这就是 GN 版"N 块+龙门石"**。
- 可落地参数: N 奇数、中央索引 (N−1)/2、Align Euler to Vector 轴向按截面建模方向选。
- 风险: 实例化块之间无缝几何（需缩实例留 g，缝宽=常数缩放不精确）。

### 2.4 Blender Artists #1282351: 程序化石墙+**随机灰缝**（pitibonom/Akikun，附 4 个 .blend）
- 来源: https://blenderartists.org/t/realistic-procedural-stonewall-for-2-8/1282351 （2021-02，Discourse API 全文回读）
- 配方摘要: shader 层砖缝：基本砖纹 + 噪声扰动 (Akikun distortion 组) + **水平/垂直缝厚各自随机**（pitibonom H/V thickness variation 参数置 0 得规则缝、非 0 得随机缝）+ 第二层小尺度噪声叠缝。
- 可落地参数: 缝宽随机带 ±30%、扭曲噪声 scale 与砖尺寸同量级；全部纯程序节点，5.x 安全（无 AO hack 依赖）。
- 预期收益: 真几何块上线后，此法降级为**缝内凹凸细节**（几何给缝位置，shader 只给缝面质感），替代现 materials.py 的 noise-joint 假缝。

### 2.5 Blender 官方手册: Brick Texture（缝/错缝的官方基元）
- 来源: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/brick.html
- 要点: 内置 Offset(默认 0.5=半砖错缝)/Squash/Bias/频率参数，Color1/2/Mortar + Mortar Size/Smooth/Bias。
- 可落地参数: Offset=0.5；Mortar Size 即缝宽比例；作为几何块的**低 LOD 远景回退**（或缝内细节）足够。
- 风险: 2D 纹理在洞口侧曲面会漂移——须用对象/世界坐标映射（本项目 materials.py 已是此路）。

### 2.6 OSArch #698: 纯 Python 砖墙代码（bmesh 路线一手帖）
- 来源: https://community.osarch.org/discussion/698/blender-brick-wall-code-in-python
- 配方摘要: 双层循环（行×列）生成盒体、奇数行偏移 0.5、缝隙用逐块缩边实现；与 OSArch(BIM) 社区对"真几何块"的偏好一致。
- 可落地参数: 行高/块长/缝宽/随机种子四参数；bmesh 直出无需 modifier 依赖。
- 风险: 帖内代码面向规则墙，弧面/楔块须自改（见下）。

### 2.7 Grant Abbitt《Procedural Pathways》(GN, Blender 4, 2024-01-28, 25:52)
- 来源: https://www.youtube.com/watch?v=MC_MXaGZfqM （频道一手，简介含免费工程文件 gdev.tv/grants-assets，文件夹 "Geometry nodes - Path through grass"）
- 配方摘要: 画曲线→GN 沿线实例化石板并自动裁切草地——桥头引道/海墁石铺装可直接套用。
- 可落地参数: 曲线采样距=石板长+缝；法向对齐+随机旋缩小抖动。

### 2.8 参考实现：bmesh 放射楔块拱（综合 §1.5/§1.7/§2.6 数学，可直接进 bridge_geom 系）
```python
import math
def voussoir_blocks(R1, R2, N, depth, gap, key_w=1.35):
    """半圆拱 N 块(奇数)+中央龙门石；gap=灰缝宽(m)；返回每块 8 顶点列表。
    角度统一收缩 dphi=gap/R_mid → 缝宽内窄外宽(中式灰缝特征)。"""
    step = math.pi / N; key = N // 2; Rm = 0.5 * (R1 + R2); dphi = gap / Rm
    out = []
    for i in range(N):
        a0, a1 = i * step, (i + 1) * step
        if i == key:                       # 龙门石居中加宽
            c = 0.5 * (a0 + a1); half = 0.5 * (a1 - a0) * key_w
            a0, a1 = c - half, c + half
        a0 += dphi; a1 -= dphi             # 收缝
        pts = [(r, a) for r in (R1, R2) for a in (a0, a1)]      # 4 角 (r,θ)
        out.append([((r*math.cos(a), s*depth/2, r*math.sin(a))) for s in (-1, 1) for (r, a) in pts])
    return out                             # 每块 8 顶点 → bm.verts + 6 quads
```
- 落地要点: 每块**独立 8 顶点、不共享**（Random per Island 逐块色差的前提，community_techniques §2.3）；深度方向再乘 M 道纵联（相邻道 index 错 0.5 块 → `step*(j%2)/2`）；龙门石可整体下沉少许做"装饰下垂"由 facts 参数控制（缺文献则默认 0）。

---

## 三、十七孔桥真实砌石数据：可引用的与可测的

### 3.1 文献/档案侧（含书目级线索）
| # | 来源 | 等级 | 关键内容 / 可用数字 |
|---|---|---|---|
| 1 | 王璧文《清官式石桥做法》，《中国营造学社汇刊》5卷4期(1935) 56-136 页 | 一手文献(线下,国图/汇刊影印) | 清官式石桥唯一系统做法文献：以《营造算例·第九章桥座做法》+《石桥分法》+《工程备要随录》+《崇陵工程做法》互校排比，分石作/瓦作/土作/搭材作四章。**券/伏、券石分档、龙门石的官式数字源此**。出处考据见来源[2][19]（白鸿叶 2022, https://www.jgcm.ac.cn/jah/cn/article/pdf/preview/10.12329/20969368.2022.03011.pdf ，已全文回读：明确"1935年6月王璧文在《汇刊》发表《清官式石桥做法》，被后人尊为开创相关研究的杰作"） |
| 2 | 梁思成《清官式三孔石桥做法要略》图稿（57.5×40cm，国立北平图书馆藏，见白鸿叶文附录3 #57） | 一手图档(线下) | 三孔石桥做法要略图——与本项目跨径序列最近的官式图样；线下调阅目标 |
| 3 | 孔庆普 1951 部颁《古桥各部名称重新命名》(mysf aid=291, 2009 发表) | 一手(部颁标准转述) | 拱碹/碹脸/拱眉线/龙门石(雕兽头则称龙头,古称蚣蝮)/护拱/撞碹/海墁/金边/仰天石/地伏/分水体/凤凰台——逐块建模的构件命名清单 |
| 4 | 孔庆普《中国古代桥梁的四点思考》(mysf aid=293, 2011) | 一手(拆桥实测) | 北京虎坊桥拆桥: 五边折线"纵联分段并列式"，石板厚 32cm、段(中线)长 1.53m、跨 5.10m、矢高 2.25m——北京石拱**纵联分段并列**砌法+块件尺度量级的一手证据 |
| 5 | 官方散量（已入 FACTS，本文仅复述边界）: 中新网/北京青年报 2025-12-09、颐和园管理中心 2023-12-01、visitbeijing | 官方 | 仿卢沟桥兼收苏州宝带桥；**青石筑桥体、汉白玉栏杆**；17 孔对称渐变、中孔最大；望柱 544 —— 材质分区与逐块化的外观边界 |
| 6 | 券/伏制度: forgemind《什么是砖——从砖构造到砖墙立面》 https://forgemind.net/media/%E4%BB%80%E9%BA%BC%E6%98%AF%E7%A3%9A-%E5%BE%9E%E7%A3%9A%E6%A7%8B%E9%80%A0%E5%88%B0%E7%A3%9A%E7%89%86%E7%AB%8B%E9%9D%A2-%E9%83%BD%E8%83%BD%E5%B1%95%E7%8F%BE%E5%BB%BA%E7%AF%89%E7%BE%8E%E5%AD%B8/ ；明孝陵碑亭"五券五伏"(钱逸琼复原研究, scribd 842945390) | 二手文献-学会 | "伏"=《营造法式》"缴背"，《工程做法》称"伏"；"X券X伏"是**径向叠砌层数**（等级），≠每层块数；券石楔形(上窄下宽)、合龙打入龙门石、缝外宽内窄 |
| 7 | 卢沟桥（方法学旁证，**数字禁止移植**）: zh.wikipedia 卢沟桥（优良条目，本项目 abutment_design.md 已逐字回读其尺寸引注） | 二手文献-志书引 | 大型联拱石桥砌法参照: 拱圈厚 ~1m 量级、纵联分砌、块件间银锭铁/铁柱拉结——说明同级皇家石桥用大尺寸条石、块数不多 |
| 8 | **线下高优清单**: 国图《清官式石桥做法》原文（券石每层块数分档表）；样式雷《颐和园卷》（2026-08 国图出版社发布，颐和园图档 840 幅册在国图，见白鸿叶文 §2.3）；孔庆普《中国古桥结构考察》(2014，abutment_design.md §3 已提级) | 待调阅 | 目标数字: 每孔券石块数/每券伏层数/券脸石长宽厚/龙门石尺寸。**在拿到前，本文 §3.2 的图像推导值是唯一实测锚** |

**术语澄清（重要）**: "三券三伏/五券五伏"说的是**径向层数**；"每层多少块"由跨径与石料长档决定（来源[6]明确"块数无死数、由跨度与券石尺寸定，常取奇数以居中置龙门石"）。二者不可混用。"轧巴砖/伏兔"两词在孔庆普术语表与王璧文目录级资料中**均未检出**，网络解释无一手出处——按项目纪律**不采信、不写入建模**，列线下待核。

### 3.2 照片量化采样（本任务实测，[图像推导-弱]，可复现）
样本: `refs/community_photos_wide/bridge_01_Seventeen_Arch_Bridge_20201221160537.jpg`（7106×4737，2020-12-21 16:05，金光穿洞+湖面封冻，全程最近景一孔完整可见）。

**实测 A：墩身/侧墙砌层**（券圈厚以 facts RING_T=0.40m 作像素标定基准）
- 层高 ≈ 0.33–0.45 m；层内条石长 ≈ 0.9–1.4 m；错缝 ≈ 半块（running bond 清晰可见）；转角/碹脸用规整大块。
- 与现脚本对照: materials.py M8-5 的 course_h=0.46/joint=0.024 与实测量级一致；逐块化后可校准到 0.40/1.1 中值。

**实测 B：券圈放射缝检测**（强度剖面极小值法，即 §1.4 的手工一维版）
- 方法: 近景孔拱腹椭圆拟合（crop 内 center=(324,351), a=181px, b=252px）→ 沿法向 1.03–1.30 倍环带取灰度均值 → 25 点滑窗 → 极小值(显著度>6 灰阶)。
- 结果: 极小值位于 **25.8°/73.3°/106.4°/153.2°**（自右拱脚起量）；镜像对称差 **≤1.0°**（25.8↔26.8, 73.3↔73.6）——随机污渍不可能伪造这种对称，判定为真实放射缝。
- 拟合: 对奇数 N 模板逐个配准，**N=7 最优**（均匀 25.7° 分档下 4 个检测缝最大角偏差 3.8°，其余 N≥9 均无 <5° 匹配）；龙门石角宽 33.1° vs 常规块 ~24.5° ≈ **1.35× 加宽**。
- 推论: 该孔（近景端孔，跨≈4.5m）券脸 **7 块**；常规块角宽 24.5° → 弦长 2R·sin(12.25°)=0.424R、弧长 0.428R ≈ **0.95m**（R=2.25）；缝内窄外宽、约 2cm 量级（与 materials joint=0.024 吻合）。
- 复现: `python3` 脚本 20 行（椭圆参数化+环带采样+滑窗极小值），参数与坐标已全录于本节；近正面高清照到手后应按同法复核（分辨率门槛: 块弧 0.95m 在该图最近孔约 60px，满足 >3px 可判线）。
- 洞内附加观察: 拱腹亮带内可见**嵌套弧线**（桶轴方向的多道平行拱圈缝=纵联），道间距在此分辨率不可数——建模按 2–3 道表现层处理（§四 动作 2）。

### 3.3 数据结论（当前证据状态下可信的写法）
1. 砌法 = **纵联分段并列**（桶轴分道 × 道内放射分块 × 相邻道错缝）——孔庆普拆桥实测(北京) + 照片洞内嵌套弧共同支持；
2. 每孔券石**奇数**块、居中龙门石（官式通则, 来源[6][7]）+ 照片 N=7 实测锚；
3. 块件尺度量级 = 长条石 ~0.95–1.4m × 高 0.33–0.45m × 厚(径向) 0.40m(RING_T)；
4. 每孔块数的逐孔官方数字**仍缺**（与 FACTS §4 M0"逐孔测绘值缺失"一致），建模值须标 [工作值+图像推导]。

---

## 四、本项目逐块化改造 Top5 动作

> 前置裁决项（主控决策，不属五动作）: 逐块化触碰 **M2.5 冻结本体三对象**（bridge_body/voussoir/impost）。freeze_manifest 状态是"候选、未锁定待用户裁决"——建议**在锁定前把逐块化并入冻结候选**（一次重哈希），或裁决为本体 v2 里程碑重新走 T4–T7；两条路都只需更新 manifest §2 哈希与 §8 豁免表，判据框架不变。

**动作 1 — 券圈离散化：`voussoir_blocks()` 进 facts→generator 链**
- 按 §2.8 参考实现新增纯函数（math-only，3.9 兼容），消费 `facts.SPAN_DISTINCT/RING_T/SPRINGER` + 新常量 `VOUSSOIR_JOINT=0.02`、`VOUSSOIR_W_TARGET=1.00`、`KEYSTONE_W=1.35`；每孔块数按 §五 表（奇数、7→13）。每块写 `arch_index/block_index`（BridgeNet 惯例，§1.3）；龙门石居中。
- 验收: 17 孔逐孔块数==表值；全部奇数；块体外缘不出 RING_T 带；接现有 `VOUSSOIR_IN_VOID` 净空判据不变。

**动作 2 — 桥身/墩/桥台真砌层（running bond 几何化）**
- 按 §3.2-A 实测: `COURSE_H=0.40`、`BLOCK_L∈[0.8,1.4]`（种子随机）、错缝 0.5、竖缝 0.02；沿桥轴曲线铺（§2.2 网格换成曲线采样，法向偏移贴合收分轮廓）；顶带（金边/仰天石）与起拱线 impost 保持**通长连续石**（孔庆普术语，与现有 34 impost 锚点一致），洞口端面露 2–3 道纵联缝（相邻道错半块，§1.6）。
- 现有燕翅桥台/岸坡（环境件，不在冻结内）可先行试点。

**动作 3 — 材质迁移：几何给缝、shader 给质感**
- 真块上线后: 启用 Random per Island 逐块色差（community_techniques §2.3 已验证配方；逐块独立顶点是动作 1/2 的硬前提）；**废弃** qingshi_material 的 noise-joint/course_h 假缝层（joint=0.024/course_h=0.46 由几何接管），保留微 bump 供缝面颗粒；汉白玉构件（栏板/望柱/龙门石面）沿用现贴图管线不动。
- A/B 纪律: 同 blend、同机位、seed=20261004 + use_animated_seed=False；逐像素 IDAT 对比（项目回归器既定口径）。

**动作 4 — 判据升级 + 回归闸门**
- qa_l2/qa_bridge 新增: 逐孔块数==facts 表、N 全奇、龙门石中心偏差 ≤0.02m、缝宽 0.02±0.005m、块不入净空；负控三件: 删任一块、任意孔 N±2、龙门石平移 0.05m——三者都必须 fail（先自证判据能抓）。
- register_overlay 复跑: 2cm 缝 @13.87px/m ≈ 0.28px，低于掩膜分辨率，预期 IoU/void 表不动（理论预言，跑完留档）；freeze_hash 三对象 sha 变更走 manifest 回填。

**动作 5 — 数据补课（把 [工作值] 换成 [档案]）**
- 线下调阅优先级: ①王璧文《清官式石桥做法》原文（券石分档/伏层数表——若载"每层块数取奇"即为 §五 奇数规则的直接文献锚）②梁思成《清官式三孔石桥做法要略》图稿（国图）③《国家图书馆藏样式雷图档·颐和园卷》查十七孔桥图档 ④孔庆普《中国古桥结构考察》(2014) 查颐和园诸桥拆检记录。任何内容农场转述（obj.cc 系）一律不采信；拿到即更新 facts 来源等级并复跑 §五 表。
- 同时降级清理: "轧巴砖/伏兔"两词无一手出处，从建模词汇表移除（保留在待核清单）。

---

## 五、每孔券石数建议（附依据）

**公式**: `N(跨) = 取奇数( round( π·(跨/2) / W ) )`，`W=1.00m`（券石弧长档，取实测锚 0.95m 圆整）；中央块=龙门石，加宽 `×1.35`。桶轴分道 M=3（表现层，相邻道错半块）。

| 孔位(自端起) | 净跨 facts | R | πR | **建议 N** | 常规块弧长 | 龙门石弧长 |
|---|---|---|---|---|---|---|
| 1/17 (端孔) | 4.50 | 2.25 | 7.07 | **7** ★照片实测锚 | 1.01 | 1.36 |
| 2/16 | 4.90 | 2.45 | 7.70 | **7** | 1.10 | 1.49 |
| 3/15 | 5.40 | 2.70 | 8.48 | **9** | 0.94 | 1.27 |
| 4/14 | 5.90 | 2.95 | 9.27 | **9** | 1.03 | 1.39 |
| 5/13 | 6.40 | 3.20 | 10.05 | **11**（9/11 边界，取 11 保块长≤1.15） | 0.91 | 1.23 |
| 6/12 | 6.90 | 3.45 | 10.84 | **11** | 0.99 | 1.33 |
| 7/11 | 7.40 | 3.70 | 11.62 | **11** | 1.06 | 1.43 |
| 8/10 | 8.00 | 4.00 | 12.57 | **13** | 0.97 | 1.31 |
| 9 (主孔) | 8.50 | 4.25 | 13.35 | **13** | 1.03 | 1.39 |

全桥券脸块合计 = 2×(7+7+9+9+11+11+11+13) + 13 = **169 块**（单道计；3 道纵联 ≈ 507 块圈体）。

**依据三角**（每条独立可查）:
1. [图像推导] §3.2-B: 最近孔（≈4.5m 跨）放射缝对称检测 → N=7、龙门石 1.35×、W≈0.95m；
2. [二手文献-学会] 官式券石分档取奇数、居中龙门石（forgemind 券伏文；明孝陵碑亭五券五伏复原；王璧文 1935 为该制度的一手载体，原文待调阅）；
3. [一手实测-他桥] 孔庆普虎坊桥拆检条石 1.53m×0.32m 量级 + 本桥墩身实测 0.9–1.4m×0.33–0.45m —— 支持块长档 ~1m 常数跨全桥（**隐含假设**: 各孔用同一石料长档，N 随跨递增；若将来档案证明"各孔同块数、块长随跨放大"，表值改为全桥统一 7–9，风险已登记）。

**诚实边界**: N 表整体为 [工作值+图像推导]；单孔样本、斜拍投影、椭圆近似引入 ±1 块不确定性（6.4m 孔已在表中标 9/11 边界）；逐孔档案数字到手（动作 5）即为终裁。在渲染分辨率上，券圈 0.40m 在远景立面仅 2.7px/块缝不可辨——**逐块化的收益集中在近景/洞内/金光穿洞机位**，远景靠 shader 层兜底即可。
