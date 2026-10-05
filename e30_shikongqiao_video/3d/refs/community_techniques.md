# 社区技法调研：十七孔桥程序化复原（水/石/狮/度量）

- 调研日期: 2026-10-05
- 方法: web_search（site: 限定 blenderartists.org / reddit.com / github.com / youtube.com / isprs 等一手渠道）+ 原文抓取（Blender Artists 走 Discourse API、GitHub 走 repo API、YouTube 取时间戳字幕摘要）。
- 收录标准: 一手经验帖、官方仓库/文档、带时间戳教程；拒绝内容农场。每条含：来源URL / 适用对象 / Blender 版本相关性 / 配方摘要 / 预期收益 / 风险。
- 项目背景: Cycles GPU、纯程序化几何+shader（无外部贴图）；残留扣分点 = ①水面远距倒影高频缺失/过平滑 ②石作风化不够照片级 ③石狮/靠山兽面部程序化上限 ④与实拍照片的相似度度量。

---

## 一、水面远距真实感（Cycles）

### 1.1 倒影破碎的最小可靠配置：灰度程序纹理 → Bump → 所有 BSDF 的 Normal
- 来源: https://blenderartists.org/t/water-ripples-bump/651747 （Photox / cgCody / eppo，附可下载 blend）
- 适用对象: 水
- 版本相关性: 节点名 2.7x 至 5.x 不变，通吃。注意 **Musgrave 纹理节点已在 Blender 4.1 移除、功能并入 Noise Texture**——照搬旧 blend 时需替换。
- 配方摘要:
  - 灰度程序纹理（eppo 静水配方：Noise+Musgrave 混合）→ Bump 节点 Height；Bump 的 Normal 输出必须接入混合器里**每一个** BSDF（Glass/Transparent/Glossy）的 Normal 输入，漏接任何一个都会出现"部分反射不碎"。
  - Bump Strength 保持小值：过强会在反射里出现"暗心"伪影。
  - 小 ripple 需要网格密度：低模上 bump 仍可走 Normal，但真位移必须有细分（cgCody：静帧建议纯纹理+bump，ocean modifier 只为动画）。
- 预期收益: 直接命中缺陷①——倒影出现可辨识高频破碎，且渲染开销近零。
- 风险: bump 强度大出黑斑；单一频率在广域水面上会显"均质"。

### 1.2 Fresnel 驱动反射量 + 各向异性把倒影"拉向相机" + 远处倒影内伪造大气
- 来源: https://blenderartists.org/t/water-shader-with-hdri/684253 （Secrop / CarlG）
- 适用对象: 水（大景观/远距，正是本项目机位）
- 版本相关性: 全版本；Anisotropic BSDF 或 Principled 的 Anisotropic 参数均可。
- 配方摘要:
  - Glossy（或 IOR=1.33 的 Principled）× Fresnel 驱动反射比；"复杂光交互（体积吸收/散射）放在反射之下"，只有能看到水底/岸坡时才需要 Volume Absorption。
  - CarlG 技巧：**各向异性 glossy + Tangent 输入 + Rotation 0.25**，把倒影沿视线方向拉长——远距水面高频不足时最有效的"假高频"手段。
  - 关键洞见（直指缺陷①）：环境 HDRI 是无限远，但远距倒影应模拟**近处大气**（霾/雾/远距散射）——"把雾伪造进反射"，不要指望渲染器替你建模大气。
- 预期收益: 远段水面不再镜面般干净；倒影带距离感与雾感。
- 风险: 各向异性对切线方向敏感，需按桥体/湖面朝向调 Rotation；与 1.1 的 bump 叠加时逐层 A/B。

### 1.3 实测参数起点：Roughness ≈ 0.1 + Noise Scale ≈ 35
- 来源: https://www.youtube.com/watch?v=sxWJqMJdL04 《Hyper Realistic Water is this EASY in 3D Graphics》，时间戳 [5:30]–[5:39]
- 适用对象: 水
- 版本相关性: Blender 4.x Principled；思路通用于 Cycles 任意版本。
- 配方摘要: 不用 ocean modifier：Noise Texture → Bump → Principled Normal；Roughness 降到 ~0.1，Noise Scale 提到 ~35 作细节层；[5:39] 提醒大尺度场景需另行处理低频大波。
- 预期收益: 一分钟给静水加可感知微高频；参数可直接当本项目起点（昆明湖尺度上再叠低频层）。
- 风险: 单一 scale 近看显重复；必须 2–3 个频率分层（低/中/高）。

### 1.4 Fresnel → Roughness（掠射更锐）与距离雾组合
- 来源: https://www.reddit.com/r/blender/comments/17qryh1/trying_to_get_realistic_render_in_cycles_what 、 https://www.reddit.com/r/blender/comments/x1uahj/i_feel_like_something_is_missing_in_this_shot_any
- 适用对象: 水/整体真实感
- 版本相关性: 全版本（Fresnel 节点）。
- 配方摘要: Fresnel 接 Roughness——掠射角（远距水面正是掠射）反射更锐更亮；评论常挂的组合是"更大的波 + Fresnel on water + distance-based fog"。
- 预期收益: 修复"远距过平滑"的另一面：不是加噪声，而是让掠射反射携带高光能与雾衰减。
- 风险: 近处倒影会跟着变糊，需与相机距离权衡；建议把 Fresnel→Roughness 的映射过 Map Range 压缩。

### 1.5 GGX vs Multiscatter GGX（Principled 分布选项）
- 来源: https://www.youtube.com/watch?v=hxOdY8QOhZM 《All Blender Principled BSDF Settings Explained》[10:46–11:01]；https://blenderartists.org/t/cycles-principled-bsdf-violating-energy-conservation/1194732
- 适用对象: 水/石（所有 glossy 表面）
- 版本相关性: Principled v2（Blender 4.0+）才提供 Multiscatter GGX 选项；旧版只能靠独立 Glossy BSDF。
- 配方摘要: Multiscatter GGX 把反射能摊得更开、多次微面弹射，粗糙表面上更亮、更接近能量守恒（单次 GGX 在 roughness 高时偏暗偏灰）；光滑表面差异小。粗水面/湿石建议 multiscatter，镜面级光滑保持普通 GGX。
- 预期收益: 远距粗水面反射亮度更接近实拍；纯选项切换，零建造成本。
- 风险: 略慢；BA 帖实测 multiscatter 下材质观感变化，切完要重校曝光再做 A/B。

### 1.6 bump vs displacement 取舍（小结）
- 来源: 同 1.1（cgCody/Roygee 结论）+ 1.3
- 结论: 静帧+远距 → 纯 bump（便宜、不受网格限制）；近景大波形/轮廓扰动 → 真位移（需细分或 adaptive displacement，Cycles 早已无需 experimental 开关）。本项目机位远距，bump 为主，仅近岸水线可考虑局部位移。

---

## 二、程序化石作风化

### 2.1 AO 节点"魔法"竖向雨痕/污水渍（Thomas Kole streaks）
- 来源: https://blenderartists.org/t/procedural-streaks-leaks-in-cycles/1388126 （作者 ThomasKole，62 赞、9.7k 浏览；相关官方 issue: https://projects.blender.org/blender/blender/issues/136303 ）
- 适用对象: 石（桥身/券洞/栏板的竖向雨痕污渍）
- 版本相关性: **关键风险点**——该 hack 在 2.8–4.x 有效；官方在 5.x 修复了 AO 采样方向偏差（issue #136303），silex 明确警告 "this will break any setup that used this hack"。本项目 Blender 5.2 LTS **必须先做兼容性探针**；失效则换：silex 的 OSL streaks / Hydraulic Occlusion（同帖 14 楼，采样弧可调，速度与 AO 节点相当）或 blenderesse Smudge Mask Generator（几何节点实现，EEVEE 也能用，作者在 6 楼推荐：https://blenderesse.gumroad.com/l/smudgemaskgenerator ）。
- 配方摘要: 用 Ambient Occlusion 节点做定向采样生成竖向 streak 掩码，叠噪声断条；2025 年 silex 修正参数：**Map Range 的 To Max 提到 ≈20、同时降低 AO Distance**，可大幅减轻斜向偏差并保持条纹密度。AO 节点逐射线采样，开销大，大场景慎用大 Distance。
- 预期收益: 竖向雨痕是"照片级风化"辨识度最高的一级特征；对大面积构件（桥身、雁翅、券洞内壁水渍线）收益最大。
- 风险: ①5.x 兼容性（先探针）②AO 采样慢 ③方向偏差在不同尺度模型上表现不一（silex: "YMMV"）。

### 2.2 Pointiness 的几何节点重建（渲染器无关 + 可控）
- 来源: https://blenderartists.org/t/lets-recreate-pointiness-cavity-in-geometry-nodes/1445560 （silex；16 楼 MediumSolid 提供 Blender 4.1 验证的 gn_pointiness.blend）
- 适用对象: 石（腔隙积垢 + 边缘磨损掩码）
- 版本相关性: 原理（arccos(dot(顶点法线, 面法线)) 符号角，源自官方 patch D1086）全版本；GN 节点组 4.1 验证；**EEVEE/Cycles 通吃**（attribute 两端都能读）。
- 配方摘要: GN 内按 pointiness 源码公式重建 → 存为 Named Attribute → shader 里 Attribute 节点读取；**Blur Attribute 迭代 1 次 ≈ 原生 pointiness 的柔化**（3 楼）。原生 pointiness 仅 Cycles 可用且低模上很糟（12–13 楼实测：低模表现差是因为实现里省略了边法线平均）。
- 预期收益: 积垢/磨损统一掩码，且比 Cycles 原生快得多，可在 EEVEE 预览调参后 Cycles 出图。
- 风险: 低模网格效果差——程序化构件（bm_from_py）需保证接缝处局部密度；模糊过头顶磨损会"漫"到平面。

### 2.3 打破平铺与逐块色差（Object Info Random / Random per Island / 双噪声 bump）
- 来源: https://blenderartists.org/t/any-tips-on-breaking-this-repetitive-procedural-noise-pattern/1516150 （Debuk / thinsoldier / etn249 / nezumi.blend，附多个 blend）
- 适用对象: 石（券石/栏板/地袱逐块色差；大面积程序化纹理去重复）
- 版本相关性: 3.6 LTS 实测帖；Random per Island 是 Geometry(几何) 输入节点，4.x 同名。
- 配方摘要:
  - 逐物体随机：Object Info → Random 加进纹理 Vector（或接 W 通道）（6 楼 Debuk 配图）。
  - nezumi 变体：Random → Map Range（避开 ~0）→ Vector Scale——尺度差异也参与去重复。
  - 单 mesh 内逐块：Geometry → Random per Island → ColorRamp 明度/色相**微移**（3 楼 etn249："a very small amount"）。
  - etn249 双 bump 配方（8 楼，附 blend）：两种不同设置的 Noise bump 用第三个 Noise 做掩码混合——同一平面上出现两种"石面性格"，是桥面大平面不重复的关键。
  - 近地加重：Z 世界坐标梯度 × 噪声做 dirt 高度权重（3 楼）。
- 预期收益: 直接消灭"程序化=均匀塑料感"；券石逐块色差是实拍照片可辨识特征，收益集中在桥身与栏板。
- 风险: Random per Island 要求逐块真是独立 island——本项目若多块合并进单 mesh，须确认块间不共享顶点；色差幅度要小，过花即假。

### 2.4 边缘磨损 = Pointiness × 噪声掩码（Neil Blevins 路线）
- 来源: https://blenderartists.org/t/worn-edges-texturing-tricks-from-neil-blevins/661288 ；Neil Blevins 原文: http://www.neilblevins.com/cg_education/vertex_map_wear/vertex_map_wear.htm
- 适用对象: 石（望柱柱头、券圈棱线的磨损圆角）
- 版本相关性: 全版本；讨论基于 pointiness attribute（Cycles only，配合 2.2 的 GN 重建可跨渲染器）。
- 配方摘要: pointiness 掩码 × Musgrave/Noise 破碎 → 混两种材质（磨损亮芯 + 风化面）；CDMJ 用 vertex dirt 当 stencil。社区结论（8 楼 Ace Dragon / 14 楼 Fatesailor）：pointiness 实为 AO 类衰减而非真曲率，硬表面细棱要么加密网格、要么烘焙曲率，且烘焙路线受贴图分辨率限制。
- 预期收益: 望柱头、仰天石/地伏棱线的"岁月圆角"，与 2.2 组合成本极低。
- 风险: pointiness 无距离参数，磨损带宽不可直接控制；无 UV 项目走程序化掩码而非烘焙。

### 2.5 完整风化石材节点拓扑（视频级示范）
- 来源: https://www.youtube.com/watch?v=vtzdAFgUGCs 《Procedural Weathered Cast Stone Material》(Ryan King Art, 2026-09, 402k 频道)；姊妹篇 https://www.youtube.com/watch?v=luQv93hwQxQ 《Procedural Rocky Ground》[26:26 起讲 Color→Displacement 数据转换]
- 适用对象: 石
- 版本相关性: Blender 4.x+/5.x 时代教程，节点与现行版本一致。
- 配方摘要: Noise(detail 提高) → Bump 控 Strength；Displacement+Bump 混合：高度同时喂 Bump Height 与极低强度 Displacement（只做轮廓微扰）；颜色层用风化色 ColorRamp 叠沉积色。纯程序化，符合本项目"无外部贴图"约束。
- 预期收益: 提供一套可直接照抄的节点骨架，与 2.1–2.3 组合成完整"汉白玉风化"材质链。
- 风险: 视频无字幕可抓，配方需按画面逐节点抄录；作者参数是"铸石"基调，汉白玉要整体提亮降饱和。

---

## 三、中式石狮/石兽雕刻工作流

> 约束提醒：本项目承诺"纯程序化"，而社区对石狮面部的共识是程序化不可达。以下按"若走雕刻改型/扫描参考"路线收集，供主控决策；扫描件仅取**造型参数**（比例/卷鬃数/眉眼浮雕深度/爪趾瓣数），不引入任何版权网格或贴图。

### 3.1 鬃毛卷曲的基网法：曲线卷 → 网格 → 雕刻收束
- 来源: https://www.youtube.com/watch?v=wu_TkcQZqJg 《Easiest Way To Create EVERY Stylized Hair》[0:31]；https://www.youtube.com/watch?v=ethg2nYSjqg 《FAST Stylized Hair/Fur in Blender 4.0》[5:37]；https://www.youtube.com/watch?v=YezI_bL4OFA 《Hair Sculpting Tutorial》[1:03]
- 适用对象: 狮（鬃毛层片 / 卷毛螺髻）
- 版本相关性: Blender 3.x–4.x；曲线 Turn/Steps 参数与 Sculpt 笔刷 5.x 同名。
- 配方摘要: 曲线（Path+Circle，提高 Turns/Steps，Spheric 型）生成螺旋卷基网 → Convert to Mesh → Sculpt 模式用 Draw Sharp / Crease / Smooth / Grab / Snake Hook / Wrap 收束成"束"；全程开 X 对称。中式石狮的卷鬃（螺髻）= 同一卷网按球面阵列 + 每卷随机旋转/缩放（阵列去重复可用 2.3 的 Object Info Random 思路）。
- 预期收益: 把"程序化摆卷毛"升级为有雕刻感的层片结构，突破缺陷③的第一层。
- 风险: 卷网转网格拓扑脏，需 voxel remesh 统一后再叠细节。

### 3.2 狮像分块雕刻顺序（体块 → 头 → 眉眼 → 鬃 → 爪 → 饰件）
- 来源: Kasucast #1 《Sculpting a Conceptual Lion in ZBrush》 https://www.youtube.com/watch?v=ee7uOUfyPmc （13:52 头部 blocking、随后鬃毛 blocking）；《ZBrush 2020 – Detailing Hair and Body Lion Statue》 https://www.youtube.com/watch?v=HQMQMVlaCck ；中文一手：bilibili https://www.bilibili.com/video/BV1z5411t7pr （zbrush 狮子雕像雕刻教程）、 https://www.bilibili.com/video/BV1QL411p7qv （零基础狮子头装饰品雕刻）
- 适用对象: 狮
- 版本相关性: ZBrush 教程，流程可平移到 Blender（笔刷对应：Standard→Draw Sharp、hPolish→Crease 类）。
- 配方摘要: 顺序 = 体块 → 头颅/吻部 → **眉弓-眼窝（表情关键，先于一切细节）** → 鬃毛层片（先大束后小卷）→ 爪趾分瓣（爪尖单独 DynTopo 加密再收型）→ 铃铛/绶带等饰件最后。中式石狮要点：眉/眼/鼻是"浮雕化"几何而非写实解剖，深度与圆角度比解剖正确性更重要。
- 预期收益: 面部程序化上限的突破口——先低频雕出眉弓/眼窝/鼻翼三组结构，高频细节才有承载面。
- 风险: ZBrush 手感差异；中文教程均为 ZBrush 而非 Blender，需自行翻译笔刷。

### 3.3 高模 → 重拓扑 → 细节烘焙
- 来源: https://www.youtube.com/watch?v=JHlfbVyuSYc 《Creating a Stylized Lion Mane in Blender (Sculpting & Retopology)》（18min 全流程）
- 适用对象: 狮（以及任何需要并回程序化管线的雕刻件）
- 版本相关性: Blender 2.9+ 流程；Blender 4.x 已内置原生重拓扑（BMesh/RetopoFlow 生态），思路不变。
- 配方摘要: 高模雕刻 → Snap to Vertex + Shrinkwrap 手动重拓扑 → Bake 高模细节到低模法线/置换。配套坑：Multires 低 level 回改会破坏高层（https://blenderartists.org/t/multires-modifier-sculpting-keep-breaking-the-model/1635007 ）。
- 预期收益: 雕刻件可退化为低模+法线。
- 风险: **与本约束冲突**——烘焙产物是外部贴图；若坚持无贴图，目标应改为保留 Multires 高层或 GN 内部位移。需主控拍板。

### 3.4 Dyntopo vs Multires 的选择
- 来源: https://www.youtube.com/watch?v=m21APVQmZ2g 《How to Use Dyntopo in Sculpt Mode》；https://blenderartists.org/t/multires-modifier-sculpting-keep-breaking-the-model/1635007
- 适用对象: 狮/靠山兽雕刻通用
- 配方摘要: 大形变/体块调整用 Dyntopo（拓扑自由）；分层细化、需低层回改用 Multires。石狮建议链：体块 Dyntopo → 定型 voxel remesh → Multires 叠细节。
- 预期收益: 避免中途返工崩形。
- 风险: Dyntopo 网格量爆炸，控制 detail resolution；remesh 会洗掉 UV（本项目无 UV，无碍）。

### 3.5 扫描造型参考库（只取形制参数）
- 来源与清单:
  - 风化石狮完整扫描（Artec Leo，作者注明 weathered、细节缺失）: https://sketchfab.com/3d-models/chinese-guardian-lions-c981456846cc49f59cfa92553b7a7506
  - RealityScan 石狮（St. Augustine）: https://sketchfab.com/3d-models/chinese-guardian-lion-statue-realityscan-8abc615ebd814a069b993f850e7f2331
  - 瓷狮高清扫描（RangeVision Spectrum）: https://sketchfab.com/3d-models/chinese-guardian-lion-afdb632cc23f4c0c9bbaa1100010039f
  - 亚洲艺术博物馆（旧金山）狮，Zenodo 存档: https://zenodo.org/records/21527748
  - Scan the World 专页（自由扫描文物聚合）: https://www.myminifactory.com/users/Scan%20The%20World
- 用途: 从 viewer/描述提取卷鬃数量、比例、眉眼浮雕深度、爪趾瓣数等形制参数，写进程序化生成器的参数表。
- 风险: 许可各异（多为 CC-BY 或馆方版权）——**只取参考描述，不下载重分发**；扫描件本身风化，不能当"新雕"基准。

---

## 四、复原-照片相似度度量

### 4.1 fSpy 相机配准（开源事实标准）
- 来源: https://github.com/stuffmatic/fSpy （2.6k★，GPL，BLAM 作者继任作）；Blender 导入器 https://github.com/stuffmatic/fSpy-Blender ；原理文档 `doc/Using Vanishing Points for Camera Calibration.pdf`；`project_file_format.md`（可自写导入器）。
- 适用对象: 度量
- 版本相关性: 独立 app 与 Blender 版本无关；导入器 repo 声明面向 Blender 2.8x+，**5.x LTS 兼容性需实测（风险项）**。
- 配方摘要: 消隐点/控制线标定 → 导出 .fspy → 导入器生成相机（焦距/位移/朝向一次到位）→ 照片设为相机背景。含 1-VP 与 2-VP 两种标定模式与参考距离设定。
- 预期收益: 把"手工调相机"变成可复现标定流程；是渲染-照片对齐的地基，直接服务缺陷④。
- 风险: 正交/长焦场景消隐点趋远、标定不稳；照片镜头畸变未校正会引入系统误差。

### 4.2 半透明叠加比对（社区标准验收做法）
- 来源: https://www.reddit.com/r/blender/comments/kt1en7 （fSpy 匹配渲染，评论："Blender doesn't have camera matching for still images built-in"）；https://www.reddit.com/r/BlenderSecrets/comments/19ei4n1 （fSpy→Blender 投影映射 part 1）；https://www.reddit.com/r/blenderhelp/comments/1gizlqk （相机与几何间放半透明照片做法）；https://www.reddit.com/r/archviz/comments/1sk1pmk （CameraMatch AutoSetup v6 作者承认 fSpy 与 Perspective Match 都"需要大量手动 fiddling"）
- 适用对象: 度量
- 配方摘要: fSpy 配准后两步走：①渲染半透明叠加在照片上（合成器 Alpha Over，或照片作相机背景 + 视口半透明）做**结构级**对齐验收（轮廓、券洞位置、栏板节奏、桥拱跨度）；②投影映射：以照片为底直接检查几何偏差。
- 预期收益: 社区对"像素级 vs 结构级"的实际共识 = **先结构级叠加对齐，再谈像素指标**；AutoSetup 帖证实全自动匹配不成熟，人工控制点仍必需。
- 风险: 叠加验收是定性的，不输出单一数字——需与 4.3/4.4 组合。

### 4.3 SSIM 的适用边界（几何变化时失真）
- 来源: ISPRS XLVIII-2-W2-2026（Politecnico di Milano）: https://re.public.polimi.it/retrieve/31612232-e5a5-4010-a14b-0e56320155de/isprs-archives-XLVIII-2-W12-2026-447-2026.pdf
- 适用对象: 度量
- 配方摘要/结论: 参数化建筑渲染研究实测：几何一旦改动，SSIM "could yield results that are not reflective of rendering quality"，作者因此**限定为定性比较**。对项目的推论：SSIM 只可用于"同相机、同几何、只变材质/光照"的 A/B（如水面配方对比、风化强度对比），**不可作为"复原 vs 实拍"的绝对分**。
- 预期收益: 防止用错指标产生假绿/假红（与本项目既往"判据恒真"教训同族）。
- 风险: SSIM 对平移/缩放敏感，必须严格同机位；这反过来要求 4.1 的配准先行。

### 4.4 量级参照带与指标套件（PSNR/SSIM）
- 来源: ISPRS L-4-W2-2026-9（Trabzon Saint Michael Church 文化遗产）: https://isprs-archives.copernicus.org/articles/L-4-W2-2026/9/2026/isprs-archives-L-4-W2-2026-9-2026.pdf ；SSIM 原始文献 Wang et al. 2004: https://www.cns.nyu.edu/pub/eero/wang03-reprint.pdf
- 适用对象: 度量
- 配方摘要: 同视角渲染 vs 照片对比的文献量级带：优秀 ≈ SSIM 0.920 / PSNR 29.71 dB（3DGS），差 ≈ SSIM 0.429（NeRF）。SSIM = 亮度×对比×结构三乘积，取值 [0,1]。
- 预期收益: 项目自评可用此带定档（如"0.6 = 结构可辨、亮度系统差"），避免"0.7 算不算好"的无依据争论。
- 风险: 数值来自真实照片重建管线（多视角、含纹理投影），与"CAD 复原 vs 单张实拍"任务不同源，只作量级参照不作门槛；直接定阈值重蹈"未量参照物先定阈值"的覆辙。

### 4.5 "照片级"的文献定义
- 来源: MDPI Remote Sensing 3(6):1104《Heritage Recording and 3D Modeling with Photogrammetry and 3D Scanning》: https://www.mdpi.com/2072-4292/3/6/1104
- 适用对象: 度量
- 结论: 文献把 photo-realism 定义为"**同视点渲染与照片无差异**"（靠投影真实纹理达成）。对项目：验收应产出"视点级差异列表"（逐构件偏差+成因），而非单一总分。
- 风险: 该定义依赖真实纹理投影，纯程序化项目达不到字面标准；应转为"结构叠加 + 分区统计"双指标。

---

## 五、本项目可直接落地的 Top5 动作（按 收益/成本 排序）

| # | 动作 | 对应缺陷 | 关键配方（出处） | 预期收益 | 首要风险 |
|---|------|----------|------------------|----------|----------|
| 1 | 水面"三频 bump + 掠射锐化 + 倒影内雾感" | ① 远距倒影过平滑 | Noise scale≈35 微层 + Roughness≈0.1（YouTube sxWJqMJdL04 [5:30]）；中频低频两层叠 bump（BA 651747）；Fresnel→Roughness（reddit 17qryh1）；各向异性 Tangent+Rot 0.25 拉伸倒影 + 远处反射伪造大气（BA 684253） | 倒影高频破碎、获得距离感，直击残留缺陷① | 多层叠加后需整体 A/B 重校曝光；各向异性方向敏感 |
| 2 | 石作竖向雨痕（先跑 5.2 兼容性探针） | ② 风化照片级 | Thomas Kole AO streaks（BA 1388126）+ silex 修正 Map Range To Max≈20 / 降 AO Distance；若 5.x 失效→ silex OSL 或 blenderesse GN 生成器 | 最显眼的风化一级特征，桥身/雁翅/券洞收益最大 | 官方 AO 修复（issue #136303）致 hack 失效；AO 采样慢 |
| 3 | 逐块色差 + 双噪声 bump 去平铺 | ② 程序化塑料感 | Object Info Random→vector/W（BA 1516150 6楼）；Random per Island→ColorRamp 微移；etn249 双噪声掩码 bump（附 blend）；近地 dirt Z 梯度 | 券石/栏板逐块差异，实拍可辨识特征 | island 划分需逐块独立顶点；色差幅度要小 |
| 4 | 相机配准 + 叠加验收流程（度量地基） | ④ 度量方法缺失 | fSpy 标定（github stuffmatic/fSpy）→ 半透明叠加结构比对（reddit kt1en7 / 1gizlqk）；SSIM 仅限同机位材质 A/B（ISPRS XLVIII-2-W12）；量级带 SSIM 0.92/PSNR 30dB 仅参照（ISPRS L-4-W2-2026） | 度量可复现、可辩护；为 1–3 的 A/B 提供同机位保障 | fSpy 导入器对 5.x 兼容未验证；畸变未校正引入系统误差 |
| 5 | 全场景 glossy 换 Multiscatter GGX + pointiness×noise 边缘磨损 | ② + 全画面低成本增益 | Principled v2 分布选项（YouTube hxOdY8QOhZM [10:46]）；pointiness（或 GN 重建+Blur 1 次，BA 1445560）×噪声掩码做望柱/券圈磨损（BA 661288） | 选项级成本，粗糙反射更亮更实、棱线有岁月感 | multiscatter 略慢；观感变化需重校；pointiness 低模效果差 |

> 石狮面部（缺陷③）：社区一致结论是程序化不可达，路径 = 曲线卷鬃基网 + 分块雕刻顺序 + 扫描形制参数（§3.1–3.5）。这与"纯程序化"约束冲突（雕刻属建模而非贴图，但若走烘焙法线则引入外部贴图）——**建议主控单独决策**，本报告不擅自纳入 Top5。

---

## 附：来源健康度备注
- Blender Artists 帖子均经 Discourse API 抓全文（含 2024–2025 追帖，非只看 2015 年首帖）。
- Reddit 条目为搜索摘要级（直接抓取被 bot 墙拦截），配方信息与多帖交叉一致。
- YouTube 条目均给出时间戳字幕引用；vtzdAFgUGCs / gsDpatxUzrY 两部无字幕，配方按页面摘要与社区转述收录，标注为需按画面抄录。
- ISPRS/MDPI 为同行评审一手文献；fSpy 为 GPL 开源官方仓库。
