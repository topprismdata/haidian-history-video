# E30 桥头靠山兽 v2 重雕 — 交付报告(beasts2)

日期: 2026-10-05 / agent: BeastSculpt / 分支: e30-bridge-body(未 commit)
任务: 重做桥头 4 只靠山兽几何, 使近景可辨识(旧 `beasts` 384 顶点/288 面 = 每只 72 面, 近景白块)。

## 0. 命名与等级(不凭空给)

| 项 | 值 | 等级/出处 |
|---|---|---|
| 名称 | **靠山兽**(全篇未用「石象」) | C3 裁决 + FACTS.md §86-89: 京报网官方转载逐字「桥东西两端有**4只石刻靠山兽**」→ [官方转载] |
| 只数 | 4(桥东西两端各 2) | 同上, 官方转载口径 |
| 材质 | 汉白玉(与栏杆/望柱/狮同档) | 京报网 2025-12-24 口径(FACTS.md §65) |
| 尺寸 | 高 1.12m(工作值带 1.05-1.20 取中)/座长 1.37m(=Lg1.25×1.10)/座宽 0.67m(=Wd0.50×1.35)/全长含头尾探出 1.50m(实测 bbox) | **[工作值]**, 园方无测点, 承旧 build_scene2.py:166 工作值与 freeze_manifest.md §8-16; 物种无文献定论, 造型取「异兽」程式, 不映射具体物种 |
| 造型依据 | 剪影程式: 后掠双角+卷云鬃/双层眉弓凸眼/宽吻鼻卷+口裂/伏卧前肢(立肘+前探爪+趾)/脊线/贴臀卷尾 | 任务书指定; 参照照见 §4(参照降级如实声明) |

## 1. 交付形态(主控 2026-10-05 变更口径, 已执行)

**不合并单 bmesh** —— mesh 共享 + 对象自有 transform(Blender linked duplicate):
- `3d/beasts2.py`(新, Python 3.9 兼容):
  - `beast_bm(size=1.12, variant=0, seed=0) -> bmesh`: 单只, 原点=须弥座底面中心, 朝 +X;
  - `place_beasts(spots, name="beasts", size=1.12, material=None) -> [objects]`:
    spot=(x,y,z,idx,facing)(与 build_lions_bm spots 同构); 每 variant 只建一次 mesh
    (同 variant 固定 seed → mesh 可共享), 对象 `rotation_euler.z = 0/π` 按 facing 翻转;
  - `dispose_cache()` / `count_components(bm)`。
- 内部工艺(承 lions2.py 已验证管线): ~71 闭合体块(椭球 f.smooth / 盒)→ 顺序 EXACT 布尔并
  → **连通域=1 硬断言**(_build_master 内, 浮壳即刻 RuntimeError 拒绝出厂)→ 归一化高=1.0 → 母模缓存。
  **不做全域 subdivide**: 实测 `subdivide_edges(smooth=1.0)` 在布尔缝合处掷出 4 个 2边2面退化鳍状
  顶点(飞出体外 0.27, 污染 bbox), 已在代码注释记录; 近景密度改由部件分辨率(18×10)承担。

## 2. 验收实测(主控独立复核口径)

| # | 验收项 | 实测 | 判定 |
|---|---|---|---|
| 1 | 近景(~1m, 85mm)可辨头/肢/尾 | v0 三机位图(§4 路径): 正面 3.2m(角尖/眉/口裂/须卷/前肢趾全入画); 3/4 侧 3.4m(头+立肘前肢+脊线+**卷尾**全剪影); 正面特写 1.6m(距吻端 ~0.95m: 口裂/鼻卷/须珠逐件可辨) | ✅ |
| 2 | 单只面数 ≥3000 | **v0=5036 面/5794 顶点; v1=5010 面/5790 顶点**(size=1.12, 两次独立构建一致) | ✅ |
| 2b | 单只 mesh 连通域=1 | v0=1, v1=1(顶点洪泛; 且母模构建时有硬断言) | ✅ |
| 2c | 对象数=4; unique mesh ≤2 | place_beasts 实测 `objects=4 unique_meshes=2`(beasts_0/beasts_1) | ✅ |
| 3 | hero 远景不退化 | 同管线 A/B(唯一变量=兽): `reg_hero_A_old_beasts.png` vs `reg_hero_B_beasts2.png`, 640×360/16spp/seed 20261004/钉死机位 → **0.0% 像素差(>8), mean 0.005**; 桥体轮廓/孔韵逐位不动(sha 仍变来自兽端部 ≤8 级亚阈像素, 属预期)。与现状 `shot_hero.png`(1600px)目视: 轮廓/拱数/栏杆节奏一致 | ✅ |
| 4 | pytest 全绿 | **375 passed, 1 failed** — 唯一失败 `test_freeze_manifest::test_frozen_file_hashes_match_disk`: `3d/materials.py` 盘上哈希 ≠ manifest 记录。该文件 mtime=09:47:00(本报告撰写前 1 分钟), 为并行 agent(WaterFix 材质 A/B / MaterialSplit)中途落盘, **不在本人改动集**(本人只 import 未写); manifest 对账属主控收尾职责 | ⚠️ 如实报 |
| 5 | 尺寸/只数/等级入报告 | §0 表 | ✅ |

### 3. hero 回归的归因记录(防"假回归"误诊)
- 首轮新旧对比曾见 20%/50% 像素差 —— 逐层归因: ①同输入重渲 0.0%(排除渲染非确定,
  本机当前配置下逐位可复现); ②盘上 `e30_bridge.blend` vs 现脚本新建场景差 47% ——
  根因是**共享树并发漂移**(M7 青石勘误等在本人会话期间落盘, 旧 blend 是旧 imports 产物)。
- 终判采用**背靠背双构建隔离法**: 同一分钟内 `--keep-old` 与新版各建一 blend(imports 状态相同,
  唯一变量=兽), 各渲 hero → 0.0% 差。旧兽基线 blend 与新版 blend 均存盘可复查。

## 4. 证据图/数据路径

| 文件 | 说明 |
|---|---|
| `3d/qa_beasts2/beast_v0_front.png` | v0 正面 85mm@3.2m(验收#1 主图) |
| `3d/qa_beasts2/beast_v0_threeq.png` | v0 3/4 侧 85mm@3.4m(头/肢/尾/脊线全剪影) |
| `3d/qa_beasts2/beast_v0_frontclose.png` | v0 正面特写 85mm@1.6m(「距兽~1m」条款) |
| `3d/qa_beasts2/beast_v1_{front,threeq,frontclose}.png` | v1(闭口/前倾角/尾镜 -y)同机位 |
| `3d/qa_beasts2/reg_hero_A_old_beasts.png` | hero 基线(旧兽, 同管线背靠背构建) |
| `3d/qa_beasts2/reg_hero_B_beasts2.png` | hero 新兽(与 A 唯一变量=兽, 0.0% 像素差) |
| `3d/qa_beasts2/reg_hero_diskblend_baseline.png` | 盘上旧 blend 渲(存档, 含 imports 漂移, 见 §3) |
| `3d/qa_beasts2/regression_{A_old,B_beasts2}.json` `regression_views.json` | 渲染 manifest(sha/亮度/边缘能量)与钉死机位 |
| `3d/refs/kanshan_ref/` + `SOURCES.md` | 参照照 5 张(CC BY/CC BY-SA, 授权与检索过程如实记录) |
| `3d/_beasts2_hero.blend` / `3d/_beasts_old_hero.blend` | 新/旧兽全场景 blend(回归可复跑) |

## 5. 主控接线配方(建议; 本人未改任何冻结/他人文件)

```python
import beasts2
build_scene2.build()                       # 或主控现有建场流程
old = bpy.data.objects["beasts"]; bpy.data.objects.remove(old)   # 换兽
spots = []                                 # 与旧 build_beast_bm 锚点逐字同式
i = 0
for xe in (-G.BRIDGE_LEN/2 + 1.5, G.BRIDGE_LEN/2 - 1.5):
    z = G.deck_z(xe)
    for k, side in enumerate((-1, 1)):
        y = side * (G.DECK_UP_W/2 - 0.10) + side * k * 0.10
        spots.append((xe, y, z, i, 1.0 if xe > 0 else -1.0)); i += 1
obs = beasts2.place_beasts(spots, name="beasts", size=1.12, material=m_rail)
for ob in obs:                             # ⚠ 与桥体旋转名单同式: -112° 桥轴
    ob.rotation_euler.z -= math.radians(build_scene2.BRIDGE_AXIS_AZ)
beasts2.dispose_cache()                    # 母模缓存(0 用户)即弃
```
注意: 旧 `beasts` 对象在 build_scene2 的 `-112°` 旋转名单内, 新对象必须同样补转, 否则兽头朝向错。
水面/燕翅墙渲染时兽位于桥端面(~±73.5 桥轴坐标), 与 A/B 实测一致不遮拱。

## 6. 文件清单(本人改动; 全部未 commit)

| 文件 | 动作 |
|---|---|
| `3d/beasts2.py` | **新建**(唯一交付代码; 未动 build_scene2/lions*/materials/facts/ortho/shot_auto2) |
| `3d/_beast_preview.py` | 新建(近景快渲驱动, 仿 _lion_preview.py) |
| `3d/_beasts2_hero.py` | 新建(全场景换兽驱动; `--keep-old` 出旧兽基线) |
| `3d/_beast_preview_*.png` | 快渲产物(v0 当前版, v1 已归档至 qa_beasts2/) |
| `3d/_beasts2_hero.blend` `3d/_beasts_old_hero.blend` | 回归场景(gitignore 同现有 .blend 政策) |
| `3d/qa_beasts2/`(12 文件) | 证据图 + 渲染 manifest |
| `3d/refs/kanshan_ref/`(5 jpg + SOURCES.md) | 参照照与授权 |
| `.superpowers/sdd/e30-beast-report.md` | 本报告 |

## 7. 已知不足(如实)

1. **参照降级**: Commons 未检得靠山兽本尊近影(检索过程记于 SOURCES.md), 造型取颐和园铜狻猊/
   铜獬豸 + 望柱狮的官式程式 + 任务书剪影清单; 待实拍近景/文保图档可再做形制修订
   (freeze_manifest §8-16 原判仍有效: 形态属表现层 [工作值])。
2. **两变体非文献差异**: v0/v1(张口/闭口、角弧前倾档、鬃数 9/11、尾侧向)为构图多样性,
   无形制出处; 4 兽共用 ≤2 mesh 是交付形态约束(共享 mesh 优先于逐只独一)。
3. **~71 体块 EXACT 并的缝线**: 逆光下贴体部件(鬃/鼻卷)表面留浅 boolean 缝(近景 1m 可察,
   hero 不可见); 已比全域 subdivide 的退化鳍顶点更优, 消除需手雕级重拓扑。
4. **pytest 1 failed** 为并发态幻影(§2#4), 待主控落定 materials/manifest 对账后应回绿;
   本人文件集不在任何失败断言内。
5. 盘上旧 blend 与现脚本渲染差 47%(§3)——非本人引入, 主控收尾重建 blend 后自然消解。
