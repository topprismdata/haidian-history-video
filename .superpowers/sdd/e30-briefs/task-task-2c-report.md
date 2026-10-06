# Task 2c 报告：文献线索追踪 + 方法论对照 + 可信度缺口登记

- 生成：2026-10-04（所有 URL 可访问性均于当日核查）
- 执行：T2cLiterature（子任务）
- 本报告只写此文件，**未改动仓库任何其他文件**（含 FACTS.md / facts.py / design.md），未提交 commit
- 输入依赖：Task 2 的 `FACTS.md`（M0 检索日志 §4）已先读，避免重复劳动

---

## 0. 检索纪律声明（重要）

1. 本任务期间，搜索引擎的 **AI 综合摘要两次产出了互相矛盾、且无真实引文支撑的"论文内容概述"**（详见线一第 1 条的 ⚠️ 记录）。这类文本在引文层面全部指向新闻页/教师页而非论文本身，按项目禁令（编造来源比承认没有来源严重）**全部拒用**。
2. 学术 API（Semantic Scholar / Crossref）仅用于书目核验与摘要拉取；凡标注"逐字"的引文均来自当日直接抓取的页面/PDF 正文。
3. CNKI / 万方 / 读秀 / 超星 / 国家图书馆 OPAC 均未获得全文接口；凡付费墙后的条目一律标注"未获全文"。

---

# 线一：学术与官方线索追踪

## 1.1 严雨、贾珺《清漪园十七孔桥"桥景"分析》（2022 厦门，170-177 页）

**结论：只追到书目 + 论文集出版实体。全文/摘要完全未在线获取。"其中有无具体尺寸数字"不可核实。**

### 已核实（逐字）

① 作者书目页（北京理工大学设计与艺术学院，教师"严雨"页，URL 核查日 2026-10-04 可访问）：
<https://design.bit.edu.cn/sz2/szdw/hjyzsjx/b133625.htm>

> "严雨, 贾珺. 清漪园十七孔桥"桥景"分析[C].中国建筑学会建筑史学分会年会暨学术研讨会2022年论文集：发展中的建筑史研究与遗产保护. 中国厦门,2022: 170-177."（论文条目 [5]，逐字）

同页确认作者身份与同系列论文（全部书目级核实）：

> "长聘副教授 特别研究员 博士生导师""中国园林数字创新研究中心（中国园林博物馆合建） 主任"

同系列已正式发表的期刊论文（均为书目核验，同一页逐字）：
- [3] 严雨, 贾珺. 濠梁观鱼：清漪园惠山园知鱼桥的桥景探析[J]. 风景园林，2022，29（8）：33-38.
- [4] 严雨, 贾珺, 杨建明. 以点带面：圆明园规月桥的景致模式探析[J].古建园林技术,2022,No.161(04):89-93.
- [7] 严雨,贾珺*. 圆明园夹镜鸣琴"桥景"分析[J].装饰,2020(09):80-83.
- [11] 严雨,贾珺*. 清漪园绣漪桥"桥景"分析[J].装饰,2019(08):78-82.
- [9] 严雨. 清漪园界湖桥"桥景"分析[A]. 中国古典园林造园艺术研究——纪念颐和园建园270周年学术论文集[C].北京颐和园管理处.机械工业出版社,2020.

② 论文集实体确认（OverDrive 电子书库条目，URL 可访问）：
<https://halifax.overdrive.com/media/12258042>

> 书名："中国建筑学会建筑史学分会年会暨学术研讨会2022论文集"；编者："中国建筑学会建筑史学分会""华侨大学建筑学院编"；Publisher: CNPeReading（中国出版集团数字传媒）；Release date: September 1, 2022；Formats: PDF ebook, File size: 494447 KB

> 简介（逐字）："本书为2022年中国建筑学会建筑史学分会年会暨学术研讨会论文集，研讨会主题为'发展中的建筑史研究与遗产保护'。全书共收录学术论文120余篇，分为建筑历史与理论研究，古代营造技术、近现代建筑与城市研究、遗产保护与利用、乡村振兴与文化遗产、旧城更新及街区保护，建筑文化跨境传播互鉴七大版块。"

→ **该论文集以 CNPeReading 电子书形式正式出版**，馆外借阅渠道存在（OverDrive 需图书馆卡；样章阅读器为 JS 应用，自动化取不到文本）。

### 追全文的完整尝试清单（全部落空）

| 渠道 | 结果 |
|---|---|
| OverDrive epub 样章 | 样章阅读器为 JS 会话页，无法取到目录/正文 |
| CNKI / 万方 / 维普 / 读秀 / 超星 | 检索未返回该会议论文的公开条目页（会议论文集未入 CNKI 会议库，或未公开索引） |
| archive.org 全文检索 | 0 命中 |
| Google Books | API 限流（HTTP 429），无预览命中 |
| 百度学术 / 通用检索 | 只回教师页与新闻转载，无论文页 |

### "里面有没有任何具体尺寸、跨径、构件数量的数字？"——不可核实

在未获全文的情况下，按事实纪律**只能回答"不知道"**。任何"该文分析了……包含……"的概述在本任务中均不可采信。

### ⚠️ 两次 AI 综合摘要互相矛盾（留档拒用证据）

- 第一轮搜索 AI 称该文内容为"空间轴线缝合/视景网络/历史考据+图像解析+空间视廊分析"，引文锚全部落在教师页与新闻页（无一是论文）；
- 第二轮搜索 AI 又称该文内容为"蓬莱仙山意象/'九'的吉祥寓意/观桥成景与立桥观景"，引文锚同样全落在教师页与新闻页。
两次概述互不一致且均无法回溯到论文原文 → 判定为生成文本，**禁止进入事实链**。M3/M4 需要桥景空间分析素材时，唯一合规路径是：获取论文集实体（图书馆馆际/购买 CNPeReading 电子书）或直接联系作者（严雨：yanyu@bit.edu.cn，教师页公开邮箱）。

**对 M3/M4 的可用替代**：同系列 [3]《濠梁观鱼…知鱼桥》发表于《风景园林》期刊（该刊官网 lalavision.com 有开放获取传统），但其全文在本次检索中同样未直接命中——若需引用其"桥景"方法框架，须先按同标准获取全文，不得以摘要转述充当。

## 1.2 夔中羽等颐和园布局遥感考证（约 2004）

**结论：追到原文全文（新浪科技页当日可访问），逐字核对完毕。确认：无任何米制数据；且"龟颈"归属有转述链分层。**

来源页：<http://tech.sina.com.cn/d/2004-10-22/0953444947.shtml>（《北京科技报》2004-10-22 09:53 稿，新浪科技转载；页顶导航注明属"圆明园湖底防渗工程引争议专题"）

逐字引文：

> "2004年10月22日 09:53 北京科技报"

> "照片上的昆明湖霎时变成了一个寿桃，万寿山忽然展翅成了一只蝙蝠，连十七孔桥也成了一只长长的龟颈。"（报道自身对遥感影像的描述）

> "当年修建颐和园是为了给慈禧祝寿。皇帝下令要在园林中体现'福、禄、寿'三个字，雷家第七代雷廷昌却巧用心思，完成了皇上交代的任务。他设计了一个人工湖，将这个人工湖挖成一个寿桃的形状……而十七孔桥连着的湖中小岛则设计成龟状，十七孔桥就是龟颈，寓意长寿。"（转引《中国电视报》第46版《样式雷：七代皆为清代皇家建筑设计总管的辉煌望族》一文——即"龟颈"话语的第一环是媒体转述，非测绘）

> "这张照片是1983年我国返回式遥感卫星拍摄回来的……夔中羽是中国测绘科学研究院的研究员"

> "到目前为止，颐和园里的几个碑文中，都没有提及这个东西。"（碑文证据排除）

> "虽然能够证明颐和园'福山寿海'的直接证据暂时还没找到"（报道自认无直接档案证据）

**米制数据：零。** 全文只有年代（1750/1860/1886/1888）、构图意象与人物考证。与 FACTS.md §3 登记一致：[二手文献] 布局意象考证，不进计量链。**追认一个升级细节**：该报道把"寿桃/蝙蝠"意象归于夔中羽对 1983 年彩色红外卫星影像的解读，而"龟颈"出自其所引《中国电视报》的样式雷家族叙事（雷廷昌曾孙雷章宝口述）——引用时应写成"媒体报道的样式雷家族口述+遥感意象解读"，不得写成"夔中羽考证测得"。

## 1.3 梁雪《颐和园测绘笔记》（三联书店 2015）第 18 节

**结论：追到出版信息与完整目录（含第 18 节标题，逐字）。正文数值不可在线获取（电子书已下架）。**

来源页（得到 APP 电子书详情页，当日可访问，标注已下架）：
<https://www.dedao.cn/ebook/detail?id=z4R9BQ7pP4ZEaXYkx8KvRdljeyqo608ENAW1m2bMAO9NnDL7gBGQr5VzJqrvmEVN>

逐字引文：

> "本书是天津大学建筑学教授梁雪带学生近距离观察、测绘颐和园后，以笔记形式呈现的作品。"

> "其中所记录的测绘生活和工作状况是目前建筑专业开展的古建筑测绘课程的真实写照，也是对现场测量部分的完整记录。"（← 这句证明该书性质即"实测记录"，是工作值升级的最优候选源）

> 目录（逐字节选）："二○○六年测绘笔记7月23日—7月29日 / 14 花承阁遗址，宜芸馆，玉澜堂 / 15 玉澜堂，宜芸馆 / 16 养云轩，无尽意轩，北宫门，后溪河，鉴远堂 / 17 后溪河，苏州街 / **18 十七孔桥，玉带桥，景福阁** / 19 介寿堂，听鹂馆，画中游 / 20 福荫轩，样式雷，假山"

> 出版信息（逐字）："生活·读书·新知三联书店"；"124千字 字数"；"2015-02-01 发行日期"；"33.49 元 **已下架**"

其他渠道：archive.org 全文检索 0 命中；Google Books API 限流无预览；豆瓣目录与搜索 AI 转引同源（dedao 页）。

**注意**：第 18 节是"十七孔桥，玉带桥，景福阁"三处合记，非十七孔桥专章；书中数值是否有逐孔跨径/墩厚表格，未获正文，无法判定。**升级路径（线下）**：图书馆借阅纸质本（ISBN 7108050579 / 9787108050571，AbeBooks/亚马逊书目在架可证）。

## 1.4 孔庆普《中国古桥结构考察》

**结论：只追到书目 + 出版方内容简介（逐字）。目录不可读，书中是否含十七孔桥数据未证实，未获任何数值。**

来源页（微信读书书目页，当日可访问）：
<https://weread.qq.com/web/bookDetail/210324a0811e289bcg015893>

逐字引文（页面 meta 简介）：

> "本书是一部纪实性科技资料书，从北京的古代桥梁、古桥结构技术研究、北方四省古桥、江南古桥、古代桥梁结构考察等方面记录了中国古桥结构技术资料。其资料来源主要是在从事北京桥梁建设、桥梁养护及其技术研究实践中所积累的材料，以及对各省主要古代桥梁的考察，并参加著名古桥的大修工程等取得的第一手材料。"

出版信息：东方出版社，ISBN 978-7-5060-4951-1（京东渠道条目转引）。

关键疑点（**负面证据，需线下核实**）：作者孔庆普系北京市政工程系统专家，其考察实践（简介逐字）为"北京桥梁建设、桥梁养护及其技术研究"——即市政/交通桥梁；颐和园十七孔桥属园林文物，**是否在该书考察范围内本身就是未证实项**。archive.org 0 命中；微信读书页无目录展示；搜索 AI 曾给出"该书称桥长约150米/宽约8米"的概述——引文锚全部落在新闻页而非书，**拒用**。**升级路径（线下）**：国图/首图借阅后查目录与北京古代桥梁章节。

## 1.5 北京市公园管理中心官网"6.56/14.6"原始页（2019）

**结论：2019 原始专题页完全追不到（活页与存档均未定位）。在网最早可核验锚点前推至 2023-12-22（央视新闻微博稿）。**

当日核查：
- 活网检索（精确短语"桥面上宽6.56米"）只命中：中新网 2025-12-09（FACTS.md 已锚定）、gamersky 2023-12-22、若干旅行平台页面（无作者/日期体系，仅转述）。
- Wayback CDX 定向探测 `gygl.beijing.gov.cn`（domain/host，2018-2020，.html 过滤）：2019-2020 存在旧版文章页捕获（形如 `/dwjj/dwjj_*/201911/t20191128_*.html`），**但未定位到任何十七孔桥/金光穿洞专题页**；两次探测（一次域级 300 条、一次限时 80 条）均未命中；域级全量列举因 CDX 响应超时（>300s）未完成。
- 公园管理中心老域名 `bjmacp.gov.cn` CDX 前 300 条（collapse=urlkey）均为样式/控件资源，无文章页命中。
- 另试 cernet 2010 中秋专题页（URL 含 t20100914）：TLS 证书验证失败（HTTP 层拒绝），Wayback 无该页存档（404）——无法验证。

在网最早锚点（新增，逐字）：游民星空 2023-12-22 18:22 转载（来源标注"微博 作者：央视新闻"）
<https://www.gamersky.com/news/202312/1688734.shtml>

> "十七孔桥是一座联拱石桥，东西向，长150米，桥面下宽14.6米，桥面上宽6.56米，高7米，横卧在东堤与南湖岛之间。桥身由十七个发券孔组成，正中一孔最大两侧依次渐小。"

（注：此稿同时给"东西向"口径——C4 走向三值又添一例官方媒体侧表述，时间早于北京青年报 2025-12-09 稿两年。）

旁证（同日核对，颐和园志系统资料 PDF，公开挂载于阿里云 OSS，文末注明"本资料出自《北京导游（修订版）》、《颐和园志》、《颐和园的岁月小河山》等"）：
<https://oss-cn-beijing.aliyuncs.com/ata-ers/usp/ueditor%2Fuploadfile%2F20191028%2F204756653842.pdf>

> "南湖岛与东岸相连者是一座 17 孔的汉白玉长桥，名十七孔桥，仿卢沟桥而建。桥上望柱雕有石狮 544 只。桥长 150 米,宽 8 米,北额'灵鼍偃月',南额'修蝀凌波'。"

→ 《颐和园志》口径（150/8/544）与 FACTS.md C2 的"宽8米"口径一致，可作为"8 米=志书口径"的旁证锚（等级仍 [二手文献]转述，不得覆盖 DECK_UP_W）。

公园管理中心 2023-12-01 活页（当日重取逐字，FACTS.md 已锚定）：
<https://gygl.beijing.gov.cn/xxgk/xxgk_gyxx/202312/t20231201_3336230.html>

> "十七孔桥桥身宽8米，桥洞最高达7米，夕阳覆盖面积大，再加上昆明湖对太阳光的反射，使得长150米、由十七个桥洞组成的'金光穿洞'更加磅礴大气、蔚为壮观。"

> "桥是西北、东南走向"／"虽然在现有的史料中没有找到'金光穿洞'的相关记载"

### 线一小结

| 线索 | 状态 | 数值产出 |
|---|---|---|
| 严雨 2022 十七孔桥"桥景" | 只追到书目+论文集实体；全文未获 | 无（不可核实） |
| 夔中羽遥感考证 | 追到原文全文 | 无米制数据（确认）；"龟颈"话语系媒体转述链 |
| 梁雪《颐和园测绘笔记》§18 | 追到目录+出版信息；正文不可获取 | 无（待线下） |
| 孔庆普《中国古桥结构考察》 | 只追到书目+简介；是否含颐和园桥未证实 | 无（待线下） |
| 公园管理中心 2019 原始页 | 完全追不到 | 无；6.56/14.6 在网最早锚点=2023-12-22 央视新闻稿 |

**FACTS.md 零改动建议**：本轮未产生任何 ≥[官方] 的新数值；唯一建议级更新是"6.56/14.6 在网最早可核验锚点"可从 2025-12-09 前推至 2023-12-22（gamersky 转载央视新闻），以及《颐和园志》系资料佐证"宽 8 米"口径——是否回填由主控裁决。

---

# 线二：方法论对照

## 2.0 我方管线 vs 学术标准管线（逐步对照表）

| # | 学术标准（遗产三维重建） | 我方管线 | 对应强度 | 证据锚 |
|---|---|---|---|---|
| 1 | 史料/历史信息搜集（historic information） | T2/T2b/T2c 事实任务 + FACTS.md 等级体系 | ✅ 等同，且我方等级纪律（五级+三禁令）与 London Charter 的 research sources 分级同构 | Martínez-Carricondo 2021 workflow 图一环："acquiring... all the available historical information"；London Charter Principle 3 |
| 2 | **标定**摄影测量/TLS 点云采集（GCP+PPK，Agisoft Metashape 等） | **未做** | ❌ 缺失 | 同上："obtaining the topographic survey... by means of UAV photogrammetry"；17 个 GCP、579 张照片、TLS 级 <3cm |
| 3 | 点云管理/分割 | **未做** | ❌ 缺失 | Diara & Rinaudo 2020："point clouds management and segmentation" |
| 4 | 参数化/逆向建模（Revit+As-Built 插件 / FreeCAD / Rhino NURBS / Blender 程序化） | Blender 参数化生成 | ✅ 对应（工具不同：学界主流 Revit/FARO、FreeCAD、Rhino；Blender 属程序化网格路线，见 2.4） | Diara & Rinaudo 2020 §4-5；Barazzetti 2016 "Parametric as-built..." |
| 5 | **几何验证**：模型 vs 点云（FARO As-Built 插件校核，案例值 ±0.05 m） | 实拍照片轮廓比对 | ⚠️ 职能对应但**强度差级**：无标定→无米制三角量测→只能核"像"，不能核"是"（线三展开） | Martínez-Carricondo 2021："The veracity of the BIM model must be checked by means of a geometric validation"；"accuracy of ± 0.05 m" |
| 6 | 验收判据/分级（Grade 1/2/3、GOG1-10、M3C2 LoD） | 判据+负控制 QA 闸门 | ✅ 方法论同构（负控制纪律比多数论文自查更严），但**判据输入缺米制基准** | Chiabrando 系 Grade 分级（转引自 Martínez-Carricondo 2021）；Banfi GOG 分级（转引自 Diara & Rinaudo 2020） |
| 7 | 冻结+paradata 文档、可持续与公开 | FACTS.md 冻结、SOURCES 带 URL | ✅ 等同；FACTS.md 的等级标注实质就是 London Charter 定义的 paradata | London Charter Principle 4.5/4.6、Glossary "Paradata" |

**一句话总结**：我方管线在 1→4→6→7 四步与学术工作流同构，缺的是第 2、3 步（标定采集与点云），导致第 5 步从"米制几何验证"降级为"定性视觉核对"。这正是 FACTS.md 已登记的可信度缺口，本报告给出其学术定位与措辞边界（线三）。

## 2.1 推荐引用的方法学论文（≥3 篇有流程有精度指标，全部当日核验）

| # | 论文 | 出处/DOI | 核验等级 | 关键流程/精度证据 |
|---|---|---|---|---|
| 1 | Martínez-Carricondo, P., Carvajal-Ramírez, F., Yero-Paneque, L., Agüera-Vega, F. (2021). *Combination of HBIM and UAV photogrammetry for modelling and documentation of forgotten heritage. Case study: Isabel II dam in Níjar (Almería, Spain)* | **Heritage Science 9:95**，DOI 10.1186/s40494-021-00571-8（OA，nature.com 全文当日可读） | 全文逐字 | UAV 摄影测量→点云→HBIM→几何验证全流程；**17 个 GCP（PPK GNSS）**、579 张照片、Agisoft Metashape；**"the obtained point cloud had an accuracy similar to that of a TLS, with a total error below 3 cm"**；**"The results show that with this methodology it is possible to obtain models representative of reality with an accuracy of ± 0.05 m"**（HBIM 模型对点云的验收值）；建模精细度 Grade 1(coarse)/2(medium)/3(fine) 分级 |
| 2 | Barazzetti, L. (2016). *Parametric as-built model generation of complex shapes from point clouds* | **Advanced Engineering Informatics 30:298-311**，DOI 10.1016/j.aei.2016.03.005（Crossref 书目核验；Elsevier 付费墙未获全文） | 书目核验（被引逐字） | **"parametric as-built" 术语的直接出处**；被 ISPRS 开源 HBIM 文献逐字引用："BIM of existing buildings and facilities (as-built BIM) is still a challenge..."（Diara & Rinaudo 2018 引） |
| 3 | Diara, F., Rinaudo, F. (2018). *Open source HBIM for cultural heritage: a project proposal* | **ISPRS Archives XLII-2:303-309**，DOI 10.5194/isprs-archives-XLII-2-303-2018（OA，PDF 当日全文可读） | 全文逐字 | 遗产 HBIM 的开源工具链（FreeCAD+IfcOpenShell+PostGIS）与局限："The last one is not suitable for historical buildings, due to the usual complexity of shapes and geometries"；"simplification is a necessary step to create an IFC parametric model of an historical building" |
| 4 | Diara, F., Rinaudo, F. (2020). *Building archaeology documentation and analysis through open source HBIM solutions via NURBS modelling* | **ISPRS Archives XLIII-B2-2020-1381**，DOI 10.5194/isprs-archives-XLIII-B2-2020-1381-2020（OA，PDF 当日全文可读） | 全文逐字 | **scan-to-BIM 标准链**："this project is based on scan-to-BIM methodology, which starts from metric acquisition of the case study, continues with point clouds management and segmentation and then entities classification inside the BIM platform"；LiDAR 12 站→NURBS（Rhino）→FreeCAD 参数化；GOG1-10 建模等级 |
| 5 | Remondino, F., El-Hakim, S. (2006). *Image-based 3D modelling: a review* | **The Photogrammetric Record 21(115):269-291**，DOI 10.1111/j.1477-9730.2006.00383.x（Crossref/S2 书目核验；Wiley 付费墙） | 书目核验 | 图像三维建模经典流程综述（采集→定向→点云→网格→纹理），被上述 OA 文献广泛引用 |

备选（同样书目核验通过，用于术语溯源）：
- Murphy, M., McGovern, E., Pavia, S. (2009). *Historic building information modelling (HBIM)*. DOI 10.1108/02630800910985108（HBIM 术语起点；付费墙未获全文）；
- Murphy et al. (2013). *Historic Building Information Modelling – Adding intelligence to laser and image based surveys of European classical architecture*. ISPRS JPRS 76:89-102（书目出处：Diara & Rinaudo 2020 参考文献逐字）；
- Haegler, S., Müller, P., Van Gool, L. (2009). *Procedural Modeling for Digital Cultural Heritage*. **EURASIP Journal on Image and Video Processing**，DOI 10.1155/2009/852392（Crossref 核验）；
- Müller, P. et al. (2006). *Procedural modeling of buildings*. SIGGRAPH 2006，DOI 10.1145/1179352.1141931（Crossref 核验）；
- Tang, P., Huber, D., Akinci, B., Lipman, R., Lytle, A. (2010). *Automatic Reconstruction of As-Built Building Information Models from Laser-Scanned Point Clouds: A Review of Related Techniques*. DOI 10.1016/j.autcon.2010.06.007（Crossref/S2 核验；**"as-built BIM"综述起点**）。

## 2.2 "参数化/程序化重建 + 摄影测量校核"在学界的名称

学界没有唯一名称，而是一族重叠术语，各有侧重（全部当日核验）：

| 术语 | 含义与出处 | 与我方路线关系 |
|---|---|---|
| **Scan-to-BIM** | 从点云到 BIM 模型的逆向流程。定义（逐字，Martínez-Carricondo 2021）："The term Scan-to-BIM incorporates the exploration process by scanning data in the form of point cloud data (PCD) that contain geospatial information about the building and its surroundings." | 方向相反：学界是"点云→模型"；我方是"参数→模型→照片核"。我方缺的正是起点（点云） |
| **Parametric as-built** | Barazzetti 2016 论文题名即此词（逐字："Parametric as-built model generation of complex shapes from point clouds"） | 我方"参数化生成+已建物校核"的意图与此同族，但缺 as-built 数据 |
| **HBIM** | Murphy et al. 2009 提出，历史建筑信息模型（参数化构件库+遗产语义） | 我方无 IFC/语义层，Blender 网格不属于 HBIM |
| **Procedural modeling / shape grammar** | Müller et al. 2006（SIGGRAPH）、Haegler et al. 2009（遗产应用） | 我方 Blender 程序化生成在方法论上最接近这一支 |
| **Scan-to-openBIM via NURBS** | Diara & Rinaudo 2020 对其自由形开源流程的命名（逐字："can be renamed scan-to-openBIM via NURBS"） | 表明这类命名是流程自定义的，学界并无强制标准 |

**精度验收标准是否存在公认数值？** 不存在单一 ISO 式阈值；学界以"报告实例值+分级"为主：
- 摄影测量点云本身对标 TLS 的实例值：**总误差 <3 cm**（Martínez-Carricondo 2021，逐字见上）；
- HBIM 模型对点云的几何验证实例值：**±0.05 m**（同上，逐字"accuracy of ± 0.05 m"）；
- 建模精细度分级：**Grade 1(coarse)/2(medium)/3(fine)**（Chiabrando 系分级，转引同上）；**GOG1–10**（Banfi 系分级，逐字："from the simple extrusion (GOG1) to the interpolation of curves and surfaces on a wired profile (GOG9) and on points clouds (GOG10)"，Diara & Rinaudo 2020）；
- 点云-模型对比的通用判据见 2.3（M3C2 LoD 等）。
→ 对我方的可操作含义：若未来做测绘升级，"重建与实测偏差 <5 cm"即可达到上述 HBIM 实例验收水平；而在无点云的现状下，任何厘米级声明都不成立。

## 2.3 点云/BIM 与实物比对的常用验收指标（IoU 之外）

| 指标 | 定义与出处（当日核验） | 适用场景 | 典型量级/阈值 |
|---|---|---|---|
| **Chamfer distance (CD)** | 逐字（Fan, Su, Guibas, ICCV 2017, DOI 10.1109/CVPR.2017.264，CVF 开放 PDF 全文）："We propose two distance metrics for point sets – the Chamfer distance and the Earth Mover's distance."；"For each point, the algorithm of CD finds the nearest neighbor in the other set and sums the squared distances up." | 两片**无对应关系**的点云（重建/生成 vs 参考集）；对少量离群点稳健 | 无绝对单位（依赖归一化尺度，Fan 论文以包围盒尺度归一）；越接近 0 越好 |
| **Earth Mover's distance (EMD)** | 同上（逐字公式 (4)，双射最小传输）；"For typical inputs, the algorithm gives highly accurate results (approximation error on the magnitude of 1%)." | 同 CD，对形状"质量分布"更敏感，常与 CD 并报 | 同上 |
| **Hausdorff distance** | 逐字（Fan 2017）："robust against small number of outlier points in the sets (e.g. Hausdorff distance would fail)" | 需要最大偏差上界的场合；**对离群点极敏感** | 报 max/95 分位两种 |
| **F-score@τ** | Knapitsch, Park, Zhou, Koltun (2017). *Tanks and Temples*，ACM TOG 36(4)，DOI 10.1145/3072959.3073599；摘要逐字："We present a benchmark for image-based 3D reconstruction... Ground-truth data was captured using an industrial laser scanner." | 重建/补全基准（精度+召回在距离阈值 τ 下的谐平均）；点云补全基准常报 F-score@τ | τ 与场景尺度绑定（大场景常用厘米级阈值），须随报告注明 τ |
| **M3C2 / LoD（置信局部距离）** | Lague, D., Brodu, N., Leroux, J. (2013). *Accurate 3D comparison of complex topography with terrestrial laser scanner: Application to the Rangitikei canyon (N-Z)*，**ISPRS J. Photogramm. Remote Sens.**，DOI 10.1016/j.isprsjprs.2013.04.009（Crossref 书目核验；摘要未在 Crossref 公开，CloudCompare wiki 页当夜 404，**未获逐字摘要**） | 两点云的**逐点局部**距离+显著性水平（95% 置信的 LoD），监测/验证主流工具（CloudCompare 内置） | LoD 由局部粗糙度与点密度算出，量级随数据；报告须附 LoD 图/值 |
| **RMSE/平均/最大偏差（model-to-cloud）** | scan-to-BIM 几何验证通用做法；实例逐字（Martínez-Carricondo 2021）："accuracy of ± 0.05 m"（FARO As-Built for Revit 插件校核） | BIM/HBIM 模型 vs 配准点云的验收 | 实例 ±5 cm；配准本身先做（ICP/控制点） |
| **IoU（体素交并比）** | 逐字（Fan 2017）："Volumetric representation based metric 1 - IoU" | 粗粒度形状比较（体素化），**不适合**构件级验收 | 类别相关，无普适阈值 |
| **体积差（DoD/volume difference）** | M3C2/DEM-of-difference 方法族在形变监测中的应用（侵蚀方量、维修量） | 需要体积量（土方/缺损量）时 | 以 M3C2-LoD 过滤后积分 |

**前置条件**：以上所有指标都要求先做**配准**（ICP 或控制点/坐标系对齐）——这正是我方缺的第 2、3 步。没有配准，任何指标都无定义。

## 2.4 Blender 在学术遗产管线中的定位与局限

**核验结果：未检索到同行评审论文以"Blender 做遗产复原的局限"为专门命题**（Crossref/ISPRS/Heritage Science 定向检索当日完成）。可核实的学术定位证据如下：

① Blender 已进入学术空间管线（开放获取，摘要逐字）：
Gorup, G., Lesar, Ž., Marolt, M., Bohak, C. (2025). *Procedural Point Cloud and Mesh Editing for Urban Planning Using Blender*. **Land 14(4):815**，DOI 10.3390/land14040815（即任务线索所指 MDPI Land 论文；MDPI 网页当日反爬 403，摘要经 Semantic Scholar API 核验）：

> "Recent advancements in open-source 3D modeling software—Blender, have introduced powerful procedural editing tools like geometry nodes alongside robust mesh and curve manipulation capabilities. These features position Blender as a viable and cost-effective alternative to proprietary solutions in urban planning workflows."

（注意：该文场景是**城市规划**，非遗产计量；其管线是"程序化网格/点云编辑"，恰好是我方路线的学术同类。）

② 遗产 HBIM 学术文献为何选 Rhino/Revit/FreeCAD 而非 Blender——**类级局限**（逐字，Diara & Rinaudo 2020）：

> "actual BIM platforms, including open source solutions as FreeCAD, are affected by modelling limitations, based essentially on predefined libraries of theoretical architectural elements as well as the simplified parametric modelling starting from geometric primitives"

> "BIM software, both commercial and open source, have objective limitations concerning 3D modelling tools, based essentially on predefined architectural libraries that hardly fit with Cultural Heritage domain."

> "NURBS surfaces and objects aren't parametric models and for this reason they cannot be directly implemented inside a BIM platform"

→ 学术遗产管线的验收要点是 **IFC 语义 + 参数约束 + 米制核验**；Blender 原生是网格/程序化工具（无 IFC、无参数约束系统、无大地坐标/配准语义），因此不在 HBIM 主流工具之列。这不是"Blender 论"专文结论，而是 HBIM 工具选择文献的一致取向；将 Blender 接入 BIM 语义的已知路径是开源 IFC 生态（IfcOpenShell/BlenderBIM），FOSS HBIM 综述（Diara, F. (2022). *HBIM Open Source: A Review*. ISPRS Int. J. Geo-Inf. 11(9):472，DOI 10.3390/ijgi11090472；摘要逐字："the possibility of creating and managing HBIM projects by using open source solutions opened new research paths in 2016"）覆盖该谱系。

③ 对我方管线的定位结论：我方用 Blender 做**示意性参数化可视化**，学术对应物是 procedural modeling（Haegler 2009 一支），其验收维度是**视觉/构图一致性**；若声称计量复原则必须换到 scan-to-BIM/HBIM 管线（米制+配准+IFC）。两条线的验收标准不可互相借用。

---

# 线三：我方可信度缺口（学术定位与措辞边界）

## 3.1 我方做法的学术定性

**我方做法不是 shape-from-silhouette。** shape-from-silhouette / visual hull 是需要**多视角标定**下轮廓求交的三维重建方法（Laurentini, A. (1994). *The visual hull concept for silhouette-based image understanding*. IEEE TPAMI 16(2):150-162，DOI 10.1109/34.273735，Crossref 书目核验）——我方既无标定，也未做轮廓求交重建。

**准确定性：基于未标定照片的定性视觉核对（qualitative visual verification against uncalibrated photographs）。** 它处于 London Charter 所要求的知识声明分级的最低档：只能支撑"该模型与可见实景在**外观/构图层面**一致（形似）"，不能支撑"几何尺寸正确（是）"的声明。London Charter 2.1（2009-02-07 版 PDF，londoncharter.org，当日全文可读）逐字：

> "…the outcomes of research that include computer-based visualisation should accurately convey to users the status of the knowledge that they represent, such as distinctions between evidence and hypothesis, and between different levels of probability."

> Principle 4.4: "It should be made clear to users what a computer-based visualisation seeks to represent, for example the existing state, an evidence-based restoration or an hypothetical reconstruction of a cultural heritage object or site, and the extent and nature of any factual uncertainty."

> Glossary — "Intellectual transparency": "The provision of information, presented in any medium or format, to allow users to understand the nature and scope of 'knowledge claim' made by a computer-based visualisation outcome."

按 4.4 的三分类，我方模型属于 **hypothetical reconstruction（假设性重建）一侧**（部分锚定官方宏观值 + 参数化推测的混合体），不是 evidence-based restoration，更不是 existing state 的计量记录。

## 3.2 "不能说什么 / 该说什么"清单（可直接进交付文档）

### 不能说（禁止出现在任何成片文案/字卡/简介中）

| 禁用表述 | 理由 |
|---|---|
| "精确复原 / 精确重建" | 无测绘支撑；学术验收下不成立（对照 2.1/2.3 阈值） |
| "1:1 还原 / 等比还原" | 无米制基准；尺寸混合了官方值与工作值 |
| "毫米级/厘米级精度" 类任何精度声明 | 无配准点云，任何偏差指标无定义 |
| "数字孪生" | 学界该词要求数据级实时对应；此处为示意模型 |
| "按实测数据建模 / 依据测绘成果" | 逐孔跨径、墩厚、矢高、纵坡、桥台均为 [工作值] |
| "文物部门审定 / 与文物本体一致性经过科学验证" | 无此程序 |
| "结构安全/工程参考" 类用途暗示 | 模型无计量地位 |

### 该说（替代措辞，按强度从高到低）

| 场景 | 建议措辞 |
|---|---|
| 模型性质 | "示意性三维重建"／"形制参考模型"／"参数化推测重建" |
| 尺寸依据 | "宏观尺寸（全长 150 米、17 孔、桥面上宽 6.56 米等）采用北京市公园管理中心及媒体公布的官方口径；其余构件尺寸为制作工作值" |
| 校核方式 | "以实景照片进行了构图与轮廓层面的一致性核对（未进行摄影测量或点云比对）" |
| 严谨声明模板 | "本片三维模型为视觉示意，非测绘复原；不作为建筑、文物或工程依据。" |
| 图像来源披露 | "画面参考了公开历史照片与当代实拍；未使用超分辨率放大的图像进行任何尺寸测量"（与三禁令一致） |
| 与官方值冲突时 | "关于桥宽存在 6.56 米与 8 米两种官方口径，本片采用 XX"（C2 冲突显式化，不静默二选一） |

### 必须随模型归档的 paradata（London Charter 4.5/4.6 对应物）

FACTS.md 及其等级标注本身就是 paradata：等级表（测绘>档案>官方>图像推导>工作值）、三禁令、闭合差 C1（−2.50 m 未归因）、走向三值 C4、全部来源 URL。交付时随片附上即可满足"intellectual transparency"。

## 3.3 若要消除缺口的升级路径（按性价比排序）

1. **文档级（零成本）**：图书馆渠道获取梁雪《颐和园测绘笔记》§18 与孔庆普《中国古桥结构考察》目录/正文——若含逐孔跨径表，即可把 SPAN_DISTINCT 等 [工作值] 升 [档案/测绘]。
2. **联系作者（低成本）**：向严雨（北建大教师页公开邮箱 yanyu@bit.edu.cn）索取 2022 论文全文/预印本，确认其中有无构件数量与尺寸；其团队若做过桥体实测，价值极高。
3. **测绘级（需许可+设备）**：若获准在园区做**标定摄影测量**（GCP+环拍，手机/微单即可，参照 Martínez-Carricondo 2021 流程），CloudCompare（M3C2/模型-点云距离）自检到 ±5 cm 档，即可按 HBIM 实例验收标准把整桥升级为"实测支撑的重建"，同时可一并裁决 C1 闭合差与 C4 走向。

---

# 附：本轮检索产生的可回填 FACTS.md 事项（供主控裁决，未代改）

1. 6.56/14.6 的在网最早可核验锚点：2023-12-22 央视新闻微博稿（gamersky 存档 URL）——建议作为 DECK_UP_W/DECK_DOWN_W 的补充 URL 锚。
2. "宽 8 米"口径可加《颐和园志》系旁证（OSS PDF 逐字"桥长 150 米,宽 8 米"）。
3. C4 走向：官方媒体侧"东西向"又添一例（2023-12-22 稿），不影响 C4 open 状态。
4. 严雨 2022 论文集为 CNPeReading 电子书（华侨大学建筑学院编，2022-09-01）——可补进 §3 书目条目。
5. 本报告"可信度缺口"三清单（线三）建议并入最终交付文档的"局限与声明"部分。
