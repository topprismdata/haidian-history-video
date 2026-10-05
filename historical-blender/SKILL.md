---
name: historical-blender
description: 历史建筑程序化复原的 agent-neutral 工作流纪律——事实/参数/代码是唯一真相，Blender 只是执行器；MCP 只做交互检查；verifier 分层（measure 与 vision 不混级）；失败先分类再修。任何 agent（omp/Claude Code/Cursor/Codex/OpenCode）进入本仓库做三维复原时必须先读本文件。
---

# historical-blender：历史建筑复原的建模纪律

**Agent-neutral**：模型可换、agent 可换、Blender 可升级，但历史事实、几何约束、验收标准与 build pipeline 不换。本 skill 不绑定任何特定 agent 或 MCP 客户端。

## 0. 一句话哲学

> **facts + parameters + code 才是 source of truth。**
> `.blend` 不是真相（它是构建产物）；MCP 实时场景不是真相（它是交互视图）；截图不是真相（它是 verifier 的输入之一）。

任何"在 Blender 里手动改好"的修复，最终必须回写为 **参数或 Python 源码**，再 clean headless rebuild。否则下一次重建就丢。

## 1. 执行层选择：headless CLI 是主路，MCP 是辅路

主路（80–90% 的工作）：

```
读 facts.py / assumptions.py
   → 改参数或 bpy 源码
   → blender --background --factory-startup --python build.py
   → 跑 geometry verifier（bridge3d / qa_l2）
   → 固定机位 renders（scripts/regression_views.py）
   → 读检查报告 JSON
   → 只修失败项
   → clean rebuild
```

MCP **只**用于：看当前场景、选对象、截 viewport、查 modifier、临时移灯试效果。
**MCP 的修改不得直接成为最终真相**——见 §0。

不装 MCP 的额外理由（本项目机器上有真实浏览器登录态与全部项目数据）：
Blender 官方 MCP 警告 "will execute LLM generated code in Blender **without any guards**"，
建议在 VM 或无敏感数据环境运行。headless 脚本路线天然规避该风险。

## 2. Verifier 分层：measure 与 vision 不混级

两层 verifier，职责不重叠：

| 层 | 工具 | 回答的问题 | 例子 |
|---|---|---|---|
| **measure**（事实层） | bridge3d 判据 / qa_l2 / 直接量 mesh | 拱净跨多少？栏板几只？狮 centroid 在哪？穿模吗？ | `assert abs(measured-expected)<=tol` |
| **vision**（观感层） | 固定机位渲染 + 人/agent 目视 | 比例怪吗？轮廓像吗？材质失真吗？构图异常吗？ | 近景狮"看得出头/鬃/前足" |

**vision 不得裁决事实**（"看起来孔数对"不算通过）；**measure 不得裁决观感**（IoU 达标不等于不像桥）。
每条 measure 判据必须有负控制证明非恒真（见 [[detector-needs-negative-control]]）。

## 3. 失败先分类，再只修对应层

"不像"不是诊断。修之前先归类（cc-blender-skill 的 refinement-loop 思想）：

```
geometry failure?      拓扑/构件缺失/穿模      → 改 build_*.py 几何
proportion failure?    尺寸比例错              → 改 facts/参数（须有来源）
camera failure?        机位/焦距/裁切错        → 改相机（不动几何）
material failure?      材质/贴图失真           → 改 materials/tex
lighting failure?      光比/雾/曝光            → 改灯光体积
reference failure?     参照本身错/口径互斥     → 回研究层登记冲突（C 表）

**一次只修一类**，修完重跑该层 verifier + 全量回归。多类同修会让归因失效。

## 4. 冻结与可复现

- 回归哈希必须哈希**像素数据（PNG IDAT 流）**，不得哈希整文件字节：实测同场景同 seed
  两次渲染像素 100% 相同，但整文件 sha256 不同——差异全在 tEXt 元数据块（渲染耗时/统计，
  每次运行都变）。用整文件 sha 做回归信号会永远报"变"（假回归）。
- 关键源文件哈希进 `refs/freeze_manifest.md`；改锁死文件必须走 `refs/body_changelog.md` 记依据 + 同步哈希（`test_freeze_manifest.py` 硬门）。
- 渲染确定性：`cycles.seed` 固定、`use_animated_seed=False`、denoise 设置固定。否则同机位两次渲不出同像素，回归对照必然假失败。
- 体积/雾出现"水平硬边"先查相机 `clip_end`（默认 1000m 会把雾盒出射面截断成二元开关），不要先调雾。

## 5. 固定机位回归

- 回归相机**必须钉在世界坐标**，不得用 auto-frame（bbox 推导的相机会随几何变化而移动，回归对照就失去基准）。
- 首次运行 `scripts/regression_views.py` 会把相机位姿**固化为字面量**写进 views JSON；此后所有回归用字面量。
- 机位集合至少覆盖：正立面 / 侧立面 / 45° / 顺桥轴线 / 券洞近景 / 桥墩近景 / 栏板近景 / **石狮近景** / 俯视。
- 每次几何改动后跑回归，diff 报告里**预期内的变化要写明归因**（"狮重做"），未归因的变化 = 回归。

## 6. 材质证据链

- 贴图选型必须**实测像素**，不得凭资产名（PolyHaven 17 个 marble 类无一汉白玉；ambientCG Marble001 实测 224,221,215 才是）。
- 贴图是否启用按**镜头尺度**决定：同一贴图远景增益为零（150m 桥在 1600px 里栏杆不足 30px）、近景有效（0.3m 狮在 1m/85mm 下占 708px）。启用前做 A/B 量化（变化像素占比 + 高频能量）。
- 无 UV 的程序化几何用世界坐标三平面投影（Geometry.Position → Mapping → Image Texture）。
- 授权分级记录：CC0 可不入库只留取件脚本；CC-BY-SA 需入库并留 SOURCES.md 署名。

## 7. 等级与来源

- 来源六级：测绘 > 档案 > 官方实测 > 官方散文 > 图像推导 > 工作值。
- **"官方"不等于"可映射到几何"**：科普散文数字（无测点无基准）禁直接映射，冲突登记 C 表。
- 文档里的尺寸必须从代码回读，不得凭记忆转录。

## 目录约定

```
historical-blender/
├── SKILL.md                      本文件
├── references/
│   ├── verifier_layering.md      measure/vision 分层 + 失败分类细则与实例
│   └── source_of_truth.md        真相链、冻结门、MCP 边界细则
├── scripts/
│   └── regression_views.py       固定机位回归渲染 + 哈希/diff 报告
└── templates/
    └── facts_template.py         新项目 facts 骨架（bridge3d 契约）
```

verifier 本体在仓库 `bridge3d/`（框架，判据不写死项目常数，见
[[heritage-reconstruction-is-a-framework-not-a-project]]）；本项目生成器在
`e30_shikongqiao_video/3d/build_scene2.py`。本 skill 不重复实现它们。
