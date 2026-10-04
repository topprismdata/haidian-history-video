# 颐和园研究资料存档总账（ARCHIVE INDEX）

> 立卷：2026-10-04。原则：**先存档后动笔**；一切结论以官方资料为准（A1/A2 分级见 SOURCES.md）。
> 本文件是全档案清单。每个文件都能溯源到原始 URL/出处。

## 一、官方文字（A1：颐和园管理处官网）

- `official_pages/raw_*.html` ×59 —— 四个分区全部详情页原始 HTML（court_life 11 / longevity 31 / gallery 2 / laka_spot 15）
- `official_pages/txt_*.txt` ×59 —— 抽取后的正文纯文本
- `official_pages/img/` ×113（56MB）—— 官网内容图（图片文件名为 md5 前缀，对应关系在 `image_urls.txt`）
- 关键事实（官网口径，直接可引用）：
  - 全园 3.009 km²，遗产区 2.97 km²，水面约 3/4，古建 7 万 m²
  - 1750 始建清漪园 → 1860 英法联军烧毁 → 1886 重工（「挪用海军经费等款项」，官网原文如此）→ 两年后改名 → 1900 八国联军破坏 → 1902 修复
  - 复建清单：四大部洲、苏州街、景明楼、澹宁堂、耕织图、颐和园博物馆
  - **佛香阁：八面三层四重檐，通高 36.44 米**（耸立于 20 米石台基上；常被引的「41 米」与官网冲突，须按官网）
  - 佛香阁内：铜铸金裹千手观音，高 5 米重万斤，**明代万历年间所造**（官网原文）
  - 长廊：始建乾隆十五年，东起邀月门西至石丈亭；听鹂馆=乾隆为其母看戏所建（官网原文）

## 二、国际官方（A1：UNESCO 名录 whc.unesco.org/list/880）

- 1998-12-02 列入，标准 (i)(ii)(iii)；评价三条（官网中文版已存）
- OUV 陈述关键点：乾隆 1750–1764 建清漪园（Garden of Clear Ripples）；**昆明湖=元大都时期水库**；光绪为慈禧重建改名；1900 再毁；**1924 起为公共公园**
- 国保：第一批 1961-03-04（国务院）；北京市保 1957-10-20
- 一池三山：昆明湖三大岛（OUV 原文 "three large islands"）
- `images/unesco/site_0880_0048-*.webp` —— 名录官方照片 1 张（其余 5 张 URL 失效待补）

## 三、清代官方文献（A2）

- `documents/rxjwkc_084.wiki` ——《钦定日下旧闻考》卷八十四（清漪园主卷：清漪园×32、昆明湖×20）
- `documents/rxjwkc_085.wiki` —— 卷八十五（少量涉及）
- `documents/rxjwkc_086/087.wiki` —— 卷八十六/八十七（对照用）
- 来源：维基文库（E26 期抓取，本集复用）

## 四、西方史料（A2/A3：Malone 1934，archive.org 公版）

- `documents/malone_1934_peking_summer_palaces.pdf` —— *History of the Peking Summer Palaces under the Ch'ing Dynasty*（Carroll Brown Malone, 1934；256 页扫描）
- `documents/malone.txt` —— 全书 OCR 文本（581KB）
  - 第五章 *Other Summer Palaces in the Reign of Ch'ien Lung*（印刷页 102–133）= 清漪园专节（PDF 页 113–136）
  - 第九章 *The New Summer Palace*（印刷页 194–）= 颐和园重建章（PDF 页 197–）
  - 书内点名《清漪园全景图》（Ching I Yuan Ch'un T'u，中英双语古图）为史料线索 → **待找原件**
- `maps/malone/malone_1934_三山五园区域草图_p16.png` —— **手绘三山五园区域草图**（印刷页 16；古今结合的古侧底图候选）
- `documents/malone_p116~130_*.png` ×8 —— 1934 年实拍清漪园/玉泉山遗址照片页（佛香阁一带/玉峰塔/万寿山昆明湖碑/昆明湖远眺/石舫/长廊/智慧海/园中遗迹）

## 五、历史影像（公有领域，Wikimedia Commons）

- `images/commons_historic/` ×27，全部 PD 或自由许可（清单 `images/commons_manifest.csv`）：
  - 亜東印画輯（1920s）：石舫/宝云阁/佛香阁远景/喇嘛塔/十七孔桥/玉带桥（駝脊橋）/万寿山眺望
  - 亜細亜大観（1900s–20s）：铜牛/龙王岛（南湖岛）/昆明湖俯瞰/万寿山远望/石舫/长廊/弓桥/玉泉山/耶律楚材像/圆明园废墟
  - 清漪园废墟老照片 ×2（约 1870–80s）：佛香阁台基与转轮藏石塔、御碑亭双亭组——**1891 重建前的「照前」影像**
  - LACMA 清代外销画 ×2、Wellcome 旧景画 ×1、文昌阁白玉雕 Belvedere ×1
- ⚠ 文件名经清洗（原 Commons 名见 manifest csv）

## 六、现代卫星底图（Esri World Imagery，署名：© Esri, Maxar, Earthstar Geographics）

- `satellite/yihheyuan_z17_full.jpg` 4194×3650（全域：39.985–40.015N / 116.250–116.295E）
- `satellite/yihheyuan_z18_core.jpg` 5034×5354（核心区：39.988–40.010N / 116.258–116.285E）
- 说明：Google Earth 同源影像家族（Maxar）；直接抓 Google 瓦片违反 ToS，故用 Esri 合法通道

## 七、民国史料（国图扫描，Commons 公版）

- `documents/nlc_簡明萬壽山遊覽指南.pdf`（52 页）—— 民国游览指南，含沿革章（万寿山明湖源流）+ 景点旧照
- ⚠《萬壽山名勝核實錄》多卷未下载（体积待查）——按需补

## 八、待办（下一阶段：GPT 协查 + 内容研究）

1. UNESCO 其余官方图（改用 400px 缩略 URL 重试）
2. 《清漪园全景图》原件线索追踪（Malone 引用；国图/故宫数字库）
3. GPT 协查分区问题清单（见 `GPT_QUERIES.md`，待写）——答案全部回 A1/A2 源核验
4. 《日下旧闻考》卷 84 清漪园部分的白话要点提取（从 wiki 文本）
5. NLC《萬壽山名勝核實錄》卷 1/2 按需下载
