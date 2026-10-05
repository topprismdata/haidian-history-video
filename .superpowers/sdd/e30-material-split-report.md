# E30 C2 材质分工报告：桥体=青石 / 栏杆望柱狮=汉白玉

- agent: MaterialSplit · 日期: 2026-10-05 · 结论: **来源证实，材质已追加，A/B 已出，接线待主控**
- 状态: 工作树未 commit（多 agent 并行纪律）

---

## 1. 来源核实（C2 由疑转实）✅

**逐字引文**（两处原文**直接抓取全文**核对，非搜索摘要）：

> 「……特在南湖岛与东堤之间仿照北京卢沟桥，兼收苏州宝带桥特点，**以青石筑成桥体，以汉白玉为栏杆**，因有17个拱券，故名十七孔桥，又称长桥。」

- **京报网**《十七孔桥的金光穿洞，你知道它的来龙去脉吗？》
  https://news.bjd.com.cn/2025/12/09/11451647.shtml （2025-12-09 07:14，来源：北京青年报）
- **中新网**（同文转发）
  https://www.chinanews.com.cn/cul/2025/12-09/10529704.shtml （2025-12-09 10:53，来源：北京青年报）
- **互证（快照级，未抓全文）**：京报网 2025-12-24《颐和园里的这些建筑，蕴含着奇特的数字密码》 https://news.bjd.com.cn/2025/12/24/11482771.shtml 搜索快照同样逐字出现「以青石筑成桥体，以汉白玉为栏杆」——与 `materials.py` 模块注释先前记录的「京报网 2025-12-24」口径吻合。

**排除一条假证据**：新华网北京频道 2025-12-03《颐和园"金光穿洞"引客来》(http://www.bj.xinhuanet.com/20251203/1a4aac27bfec4a0d889c728effbe61a0/c.html ) 抓取原文正文**仅有图注，无任何石料表述**；搜索摘要声称的「桥栏汉白玉/铜牛基座青石」不在原文中，不采信。

**语义边界（防过度映射）**：原文只定**石材种类**分工——桥体侧（桥身/券圈/桥台石构）=青石；栏杆系统（栏板/望柱/狮）=汉白玉。望柱与蹲狮属栏杆系统组成部分（通行构件术语），「栏杆=汉白玉」涵盖之。按项目六级来源口径，本句属「官方散文」，**只映射材质种类、不映射任何几何尺寸**。

**与 M4 既有决策的关系**：M4 节曾把桥体基色定为暖白（实拍亮部 RGB 252,245,227, R−B=+25）并注「青石在阳光+大气散射下呈暖白」。本句证实的是**种类分工**，与「光照下呈暖白」不矛盾——青石基色本身冷灰，是否整体切换基色是主控的渲染裁决，本文 A/B 提供两版实测。

## 2. 代码改动 ✅（仅追加，零签名/行为变更）

`3d/materials.py` 末尾**纯追加**（既有 stone_material / marble_material / water / earth / fog 一字未动）：

```python
def qingshi_material(name, base_rgb=(0.305, 0.342, 0.381)):
    """青石(石灰岩)桥体: 冷灰蓝基色 + 可见砌缝 + 微斑驳。……"""
    return stone_material(name, base_rgb, joint=0.010, course_h=0.60,
                          weather=0.32, waterline_h=0.55, block_var=0.12,
                          bump_strength=0.30, base_rough=0.84)
```

- 基色推导：青石新出面 sRGB≈(149,157,165) → 线性 (0.305,0.342,0.381)，R<G<B 冷灰蓝向；砌缝/块差比现 stone_body 接法略强调（青石块石砌法可读）。
- 新哈希：`52c68ce3bcaf15c3160160bca6813f4bdf37d071032a8026edf3085a98c94b90`（已同步 `refs/freeze_manifest.md` §2 行；变更已登记 `refs/body_changelog.md` C2 节）。

## 3. 接线建议（主控执行；build_scene2.py 为冻结文件，本 agent 未动）

行号为**当前盘上状态**（注：LionSculpt agent 的 lions2 在途改动已使行号较 manifest 记录版整体上移 27 行，接线时以内容定位为准）：

| 位置 | 现状 | 建议改为 |
|---|---|---|
| **L189-191** `m_body` | `MAT.stone_material("stone_body", (0.790, 0.765, 0.700), joint=0.007, course_h=0.68, weather=0.24, block_var=0.07, bump_strength=0.24)` | `MAT.qingshi_material("stone_body")` |
| **L192-193** `m_ring` | `MAT.stone_material("stone_ring", (0.845, 0.830, 0.785), joint=0.010, course_h=0.24, weather=0.14, block_var=0.07)` | `MAT.qingshi_material("stone_ring", (0.350, 0.382, 0.418))`（略亮冷灰，保持券圈/伏券相对桥身亮半档的既有层次） |
| **L194** `m_rail` | `MAT.marble_material("marble")` | **不动**（栏杆/望柱/狮/靠山兽/仰天石已是汉白玉，分工正确） |

消费方自动跟随、无需改行：`bridge_body`(L240)、`abutment_ground`(L395) 吃 m_body；`voussoir`(L333)、`impost`(L332)、`pier_plinth`(L215) 吃 m_ring。即燕翅桥台随桥体转青石（与「以青石筑成桥体」一致；若主控想让桥台另调，需拆变量，属主控决策）。L188 注释可更新为中新网 2025-12-09 口径。

主控接线后须走冻结流程：body_changelog 登记 → 重跑 L1/L2 + freeze_hash → 更新 manifest §2 的 build_scene2.py 行。

## 4. A/B 证据（同 blend / 同相机 / 同 seed 纪律）

- 脚本：`3d/ab_qingshi_split.py`（自包含，复刻 shot_auto2 hero 相机与采样；**不改任何冻结文件**）
- 运行：`blender -b --factory-startup --python ab_qingshi_split.py -- hero 800 32`
- 设置：seed=20261004、use_animated_seed=False、denoise=on、GPU/METAL、clip_end=20000、800×450、32 samples
- A/B 只差材质：B 版将 m_body/m_ring 消费方 5 对象（bridge_body、abutment_ground、voussoir、impost、pier_plinth）换 qingshi；栏杆/狮/兽/水/岸/雾零接触

| 文件 | 说明 |
|---|---|
| `3d/ab_qingshi/ab_hero_A_warm.png` | A：现状暖白桥体 |
| `3d/ab_qingshi/ab_hero_B_qingshi.png` | B：青石桥体 |
| `3d/ab_qingshi/ab_hero_AB_side.png` | 并排对照（A 左 / B 右） |

**桥体带 RGB 实测**（掩膜 = 两图逐像素差>8 的材质生效区，占画面 17.7%，含桥体+券圈+桥台及其水面反射）：

| 版本 | mask-mean RGB | R−B | 亮度 |
|---|---|---|---|
| A 暖白 | (146.0, 147.8, 148.4) | −2.3 | 147.5 |
| **B 青石** | **(126.9, 132.1, 136.8)** | **−10.0** | **131.3** |

Δ：亮度 −16.2、R−B 冷移 −7.7（转冷方向正确、量级温和——雾与日光仍给亮部加暖）。掩膜外最大差 8/255（天空区 ≤1、近水区 ≤2，去噪/采样抖动级；=0 占 75.9%），无结构变化。目视复验：B 桥体青灰、栏杆白线保留、无伪影。测量脚本：`3d/ab_qingshi/measure_ab.py`。

## 5. 验证

- **freeze_hash**（blender 内跑）：三核心对象 sha_sorted 与冻结基线**逐位一致**（bridge_body `861d8836…` nv=4409 / voussoir `b4421770…` nv=1656 / impost `5154f49e…` nv=136）——纯 shader 追加零触几何。
- **L1**：`test_l1_body.py + tests/bridge3d/test_checks_l1.py` → **207 passed**。
- **L2**：正检 exit 0（ok=True，零 fail 零 skip）；负控 exit 0（护栏按预期抓到扰动）。
- **pytest 全套**（`e30_shikongqiao_video/tests tests/bridge3d`）：**375 passed, 1 failed**。唯一失败 = `test_frozen_file_hashes_match_disk` 报 `3d/build_scene2.py (盘上 abe787d9… != 记录 65ac1e39…)`——这是 **LionSculpt agent 的在途改动**（git diff 实证：lions.py→lions2.py 换入 + build_lions_bm 删除，与本次改动文件零交集，归其登记+主控终验时收口）。我名下的漂移（materials.py）已按流程修复：改前同一测试报 materials.py 不一致，登记 changelog + 同步 manifest 后该条已转绿。

## 6. 文件清单（本 agent 产出，全部未 commit）

| 文件 | 动作 |
|---|---|
| `3d/materials.py` | 纯追加 `qingshi_material` + 来源注记 |
| `3d/ab_qingshi_split.py` | 新增（A/B 渲染脚本，自包含） |
| `3d/ab_qingshi/ab_hero_A_warm.png` / `ab_hero_B_qingshi.png` / `ab_hero_AB_side.png` | 新增（A/B 证据） |
| `3d/ab_qingshi/measure_ab.py` | 新增（测量脚本） |
| `3d/refs/body_changelog.md` | 顶部新增 C2 节（冻结流程登记） |
| `3d/refs/freeze_manifest.md` | §2 materials.py 行：哈希回填 + C2 注记 |
