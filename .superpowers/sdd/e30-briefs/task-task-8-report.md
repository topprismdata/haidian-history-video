# Task 8 报告：M2.5 冻结包（冷重建 + manifest + 二态冻结）

- 执行: T8Freeze，2026-10-04
- 状态: **DONE_WITH_CONCERNS**（几何硬门全过；渲染像素级复现被本任务复测证伪，已如实降级）

## 1. 冷启动重建（G3 硬门）——已实测执行

主控开放窗口后实测执行：重采删除前态 → **删除 `e30_bridge.blend`+`e30_bridge.blend1`** → 干净状态 `blender -b --python build_scene2.py`（T4）→ L2 正检+负控（T5）→ 对照。渲染产物未删（T7 标定依赖 `ortho_side.png`，主控指令）。

### 哈希对照表（删除前 vs 重建后）

| 项 | 删除前 | 重建后 | 一致? |
|---|---|---|---|
| `bridge_body` sha_sorted | `861d8836b1704067…50f2` | 同 | **MATCH** |
| `bridge_body` sha_order | `5a5c923275057a12…3674` | 同 | **MATCH** |
| `voussoir` sha_sorted/order | `b4421770a9e79519…047f` / `1c7ded704ed26238…3a49` | 同 | **MATCH** |
| `impost` sha_sorted/order | `5154f49e49d7af1e…0c0a` / `13743527ae240699…adf9` | 同 | **MATCH** |
| 顶点/面数（3 对象） | 4409/2260, 1656/1242, 136/34 | 同 | **MATCH** |
| 世界 bbox（bridge_body） | x±34.864 y±72.273 z[−2.2,7.75] | 同 | **MATCH** |
| L1 fail / L2 正检 / L2 负控 | 0 / ok / 翻10面→FAIL(被抓) | 同 | **MATCH** |
| `.blend` 文件 SHA | `10b75021…` | `a3dcfcaa…` | 非判据（元数据层） |

**结论：顶点内容与顶点顺序双一致——EXACT 布尔求解器同 build 完全确定，无浮点非确定、无隐藏状态。主控已独立复核（`6194d02d5557cc91` 与其法线修复后实测一致）。**

## 2. 最有价值的产出：渲染像素级复现被证伪

主控在窗口开放时给出"seed 固定后 IDAT 一致、可作对照"的口径；T8 按其执行冷重建渲染对照时发现该口径**不成立**：

- **arch 视图同 blend、同 seed（20261004）、同脚本 5 渲 5 异**（IDAT 全不同）；其中一组在 **GPU 空闲条件下背靠背两渲仍异**——排除 T6 并发污染假设。
- hero 视图 2 渲一致，属单视图偶证。
- **归因**：`use_adaptive_sampling=True` + Metal 后端下，自适应采样调度运行间非确定；seed 只固定采样序列，不固定逐步收敛判定。与几何无关（核心哈希逐位一致）。
- **处置**：渲染像素/文件哈希均**不作冻结判据**；渲染层证据降级为配置锁定（seed/samples/分辨率/脚本哈希）。manifest §6/§7/§8-11 已改写并分层标注"几何硬门（已过）vs 渲染加分项（不成立）"。M4 建议：`use_adaptive_sampling=False` 后独占 GPU 复测，再决定是否恢复像素判据。

## 3. 交付物

| 文件 | 内容 |
|---|---|
| `3d/refs/freeze_manifest.md` | 七类信息：facts/assumptions 快照（SHA256+等级分布 官方6/图像推导1/工作值12/**测绘0/档案0**）、管线文件哈希（commit `35e0ccf` 为冻结前管线 HEAD；build_scene2 随 `bc485a5` abutment_ground 旋转补正更新为 `b93c93f0…`，本体三对象几何 SHA 不变）、Blender **5.2.2 LTS build `d13f752e3b9c`**、参考资产哈希（与 FACTS §6.1 一致）、容差配置表（每条含依据出处）、渲染图哈希+seed（存档快照，非判据）、冷重建对照表、已知偏差豁免表 **14 条**（含渲染自适应采样非确定 + 主控 M3 首轮迭代三条）、§9 冻结状态声明、§10 接口契约指针、§11 T7 占位 |
| `3d/refs/FACTS.md` §7 | M2.5 冻结节（指向 manifest，未锁定） |
| `docs/superpowers/specs/2026-10-04-e30-bridge-facts-design.md` §9 | **附属构件接口契约**：坐标系与摆放（桥轴局部系/Z=0 水位/rotation −112°）、桥面边界线（`deck_z(x)` 抛物线、顶半宽 3.28、底半宽 7.30、线性收分公式）、栏板基线（底边=顶面、y∈±3.28 带内、望柱 128 根间距 150/63≈2.3810 m）、狮/异兽锚点（4 只官方口径、骑顶面）、水位线与地形接口（x=±75 端面、BODY_BOTTOM=−2.20）、执行锁（反改禁令+body_changelog 后果）。**全部为冻结 facts 经 bridge_geom2 公式的推导值，无新数字** |
| `3d/freeze_hash.py` | 核心几何哈希唯一定义点（evaluated mesh、量化 0.1mm、sorted+order 双哈希） |
| `tests/test_freeze_manifest.py` | 10 条冻结完整性测试（哈希硬锁+篡改负控+二态声明一致性+工作值逐条+契约事实同步锁） |
| `3d/refs/body_changelog.md` | 初始化（基线 commit 待冻结包批准后回填） |

## 4. 冻结状态声明（如实）

**`CONDITIONAL_RECONSTRUCTION_FREEZE`（候选，未锁定，待用户裁决）。** `FACTUAL_FREEZE` 不适用：本项目 **测绘 0 / 档案 0**（19 条中官方 6、图像推导 1、工作值 12）。依赖工作值 12 条逐条：DECK_Z_TOP 7.75 / DECK_Z_END 5.05 / SPRINGER 2.50 / RING_T 0.40 / SPAN_DISTINCT [4.50,4.90,5.40,5.90,6.40,6.90,7.40,8.00,8.50] / PIER_W 2.50 / PIER_MAIN_W 2.80 / PIER_FOUND_W 3.10 / PIER_MAIN_W_C 2.90 / PIER_FOUND_W_C 3.20 / BRIDGE_ABUT 1.35 / DECK_Z_AT_PIER [5.30…7.55]（另 ARCH_RATIO 0.50 为图像推导）。升级路径：梁雪《颐和园测绘笔记》/孔庆普/严雨 2022（线下）。

## 5. 测试与判据一行结果

- pytest：**47 passed**（37 基线 + T8 冻结包 10 条，全绿）
- L1：fail=0；L2 正检 ok=true（fail=0 warn=0）；L2 负控：翻 10 面 → FAIL（被抓）——删除前后同判
- 冷重建：核心几何 sha_sorted/sha_order/计数/bbox 全 MATCH

## 6. Commits

- `6d8a838` docs(e30): M2.5 冻结包候选(条件冻结声明+附属接口契约+冻结完整性测试)
- 本报告随最终冻结包 commit（`docs(e30): M2.5 冷重建验证回填+渲染非确定如实降级`），哈希见交付消息
- 期间上游并行 commit（非本任务产出，冻结包已纳入其结果）：`cf11ac3` T6 五机位+桥轴 112° 修正、`bc485a5` abutment_ground 旋转补正、`7996220`/`c02f412` M3 首轮迭代清单（含第 3 条撤回）

## 7. 顾虑清单

1. **渲染像素级复现不成立**（§2）：M4 渲染契约需关自适应采样后复测；当前交付不声明任何像素级精度。
2. ~~T7 依赖项未闭环~~ **已闭环（后续同步）**：T7 `d30502f` 交付 L3 判据 OVERLAY_IOU_MIN=0.76 / VOID_XC_TOL=0.02（扰动标定），基线实测 0.8070 PASS 余量 0.047，重渲前后基线 4 位小数不变；manifest §5/§8-10/§11 已同步。
3. **ortho_side.png 已被我重渲替换**（主控裁决）：T7 标定所用 23:18 版 IDAT `58db0658…`，新基线 `86fe24ec…`（mtime 1791127424）——已向 T7 报备 mtime+IDAT；差异属渲染噪声级，几何逐位一致。
4. **24 个旧 v1 渲染/衍生图未删**（cmp_*/shape_*/frontal_* 等）：属 FACTS §6.3 登记物，非本链产物，保留未动。
5. 冻结包**未锁定**——用户批准后才回填 body_changelog 并锁 facts 本体节；未批准则按用户意见走变更记录重跑判据。
6. 竖向比例偏高 27%（§8-12）与 17 孔序列对称正确并存：本体几何判据全绿 ≠ 与照片无差异，交付措辞仍受 FACTS §4b 约束。

## 8. 收尾

**冻结包已提交，等待用户裁决，本任务 STOP。**
