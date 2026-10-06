# 角度 A：Blender 在文化遗产/建筑遗产三维复原中的实际案例

> 检索日期 2026-10-04。检索工具：OpenAlex API（`title_and_abstract.search` + `fulltext.search` + 按 ISSN 限定刊种）、ISPRS Archives 全文直取。
> 所有引文均已回到可访问原文（ISPRS Archives 为 CC-BY 全文 PDF，逐页读取）；标注「未获全文」者仅依据可核验的书目元数据与官方摘要。

## 0. 一句话结论

「用 Blender 做真实建筑遗产复原」这条路在文献里**确实存在且已成建制**，但它不是以"Blender 作为遗产建模工具"的名义存在——它主要以**一个具体项目的连续论文群**（法国 INSA Strasbourg / iCube 的 *Châteaux Rhénans – Burgen am Oberrhein* Interreg VI 项目，2023–2025）形式出现，2024–2026 年间在 ISPRS Archives（3D-ARCH / LowCost3D-Sensors / CIPA Symposium）连续产出 5 篇以上论文，另有 1 篇 MDPI *Heritage* 期刊长文与 1 篇 JOCCH 论文。

**没有找到任何一篇专门以"Blender 在遗产工作流中的定位或局限"为题的专论**；局限散落在方法论文的讨论段里。类级论证充分且全部出自同行评审原文，可拼成完整链条。

## 1. 证据链（全部 ISPRS 部分为 CC BY 全文，已逐页读取）

| 环节 | 文献 | DOI |
|---|---|---|
| 建模方法论 | Sommer, Koehl & Grussenmeyer 2024, ISPRS Archives XLVIII-2/W4-2024:405 | 10.5194/isprs-archives-XLVIII-2-W4-2024-405-2024 |
| 期刊版 | Sommer, Koehl & Grussenmeyer 2025, Heritage 8(1):31 | 10.3390/heritage8010031（未获全文，MDPI 403 / HAL 伪 PDF） |
| 选型对照 | Koehl, Heitz, Rigaud & Guillemin 2024, ISPRS Archives XLVIII-2/W4-2024:263 | 10.5194/isprs-archives-XLVIII-2-W4-2024-263-2024 |
| 工具链手册 | Koehl, Heitz, Sommer & Fuchs 2024, ISPRS Archives XLVIII-2/W8-2024:235 | 10.5194/isprs-archives-XLVIII-2-W8-2024-235-2024 |
| 局限论证核心 | Sommer, Manfredi, Bolognesi, Koehl & Grussenmeyer 2026, ISPRS Archives XLVIII-2/W12-2026:447 | 10.5194/isprs-archives-XLVIII-2-W12-2026-447-2026 |
| 渲染判据 | Sommer, Koehl & Grussenmeyer 2025, ISPRS Archives XLVIII-M-9-2025:1387（CIPA Symposium 30th, Seoul） | 10.5194/isprs-archives-XLVIII-M-9-2025-1387-2025 |
| 并行旁支 | Zhang, Shu, Yuan & Xiao 2026, ACM JOCCH | 10.1145/3842757（未获全文；清代官式木构 + LLM + Blender 程序化，与 E30 同构度最高） |
| 对照组 | Lopez et al. 2018 (10.3390/mti2020021)、Heritage 8(10):410 | 未读全文 |

## 2. Blender 的已知硬边界（全部出自同行评审原文）

- 无 parametric BIM 语义
- 程序化纹理过不了 FBX/IFC
- 实例不可导出，且转真实几何时可能致软件崩溃
- 非实时渲染引擎
- 渲染数十分钟至数小时/帧
- 不管理地图坐标系
- 程序化贴图须 bake 才能外传

对应的选择理由：免费开源 + Python 脚本 + 曲面贴图界面更简 + 社区更活跃；HBIM 本身"缺参数化对象库"正是 Blender 的机会窗口。

## 3. 对 E30 判据验收最直接的两点

1. **完整的渲染质量判据方案**：MSSIM + 0.95 阈值，阈值源自独立观察者实验；真值图用 10k vs 100k spp 的 MSSIM>0.99 自证；做了双视点复现验证。
2. **明确警告**："模型几何被改动时 SSIM 会被几何结构变化污染，无法归因"——**几何判据与图像判据必须分开走**。这与 E30 把 L1（数据）/L2（网格）/L3（配准）分层的做法一致。

## 4. 反面教训（对 E30 高度相关）

论文承认其早期 Birkenfels 模型主要依据**网络图片和 LiDAR 近似尺寸**，后续才计划用现场摄影测量与激光扫描获得精确尺寸。

> **参数化模型 ≠ 测绘模型。程序再严谨，若输入只是近似值，最终仍只是"严谨生成的假设模型"。**

这直接支持 E30 的 `facts.py != assumptions.py` 与"generator 不得自行补历史事实"。

## 5. 检索方法学教训

- ISPRS Archives/Annals 全开放且 PDF 直取稳定，是本领域最可靠一手来源（title/abstract 含 Blender 者共 27 篇）
- OpenAlex API 可用，其 `abstract_inverted_index` 可反推官方摘要全文（不涉 AI 生成）
- Semantic Scholar graph/v1 端点与 MDPI 全站在本环境不可用
- 通用 web 搜索在本主题上信噪比极低（首轮 10 条 0 条相关），**学术检索必须走 API**
