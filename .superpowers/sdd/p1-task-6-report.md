# P1 Task 6 报告: export_print.py（inset 吃公差 / STL+3MF / manifest 分批 / coupon + 雕件白名单）

日期: 2026-10-06 · 隔离树 `/tmp/e30_p1/`（git archive HEAD=6651bcf + bridge3d/docs 软链 + 独立 git init，基线复现 **147 passed**）→ 绿后同步主树。

## 交付（TDD：新套件先对无实现跑红 ModuleNotFoundError，实现后绿）

**`3d/export_print.py`（新）**
- `inset(verts, clearance_model_mm)`：三轴各面内缩 clearance/1000 模型米；顶点逐轴按 bbox 界分类（下界 +c / 上界 −c / 内部不动 / 扁轴不动），只缩不涨，c=0 恒等。
- `fit_for_block(dims_m)`：最小维 <0.3m→TIGHT(0.15) / <1.0m→NORMAL(0.3) / 否则 LOOSE(0.5)，边界值归更松档。
- `flip_outward(verts, faces)`：signed_volume<0（族库实测内翻，wedge=−0.4）→ 每面反序成朝外右手序；幂等；不改写输入。
- `export_stone(stone, verts, faces, out_dir, scale=1/50, fit="NORMAL")`：fit=None 走自动分档 → inset → flip → `check_stone`（S3 post-inset 时序，不过即 raise）→ 二进制 STL + 最小 3MF（zip+XML，打印件毫米，材质分组目录）。返回 `{stl, stl3mf(全路径), volume_cm3(打印件), fit, clearance_mm}`。
- `export_ledger(led, mesh_fn, out_dir, roles=None, scale=1/50)`：基础校验（坏账 raise）→ 角色白名单（默认 `MASONRY_ROLES` = RING/SPANDREL/PIER/IMPOST/BACK/CORE/PAVING；CARVE/RAIL/POST 归 P4，过滤件记 `manifest.skipped` 不静默消失）→ 逐石自动分档 → clearance 只置在深拷贝出的 `ledger_print.json`（时序纪律；输入账目零改写；写盘前后 `validate_ledger` 双验）→ 220×220 床贪心货架装箱（超床件独占 oversize 批）→ `manifest.json`（meta/families×count×volume/stones/batches/materials/skipped）。
- `coupon_set(out_dir)`：三档间隙楔形对 ×3 = 6 件 STL(+3MF)，名义拼装成对间隙 = 2×clearance。

**`3d/ledger.py`（T1-I1）**：`validate_ledger(led, allow_clearance=False)`；True 放行已置 clearance 记录，其余判据不豁免；默认行为逐位不变。

## 负控制（全部钉进 24 条新测试）
- `CLEARANCE_PREMATURE` 默认仍拒 / `allow_clearance=True` 放行但坏 id 照报（不整体豁免）。
- inset 精确断言 ±1e-9（每轴 bbox 收缩 = 2c/1000 m）+ **不外扩**（符号反转必红）+ c=0 恒等。
- FIT 分派边界负控：0.2999→TIGHT、0.3→NORMAL、0.9999→NORMAL、1.0→LOOSE。
- flip 确实反序（`f2[0][::-1]==f[0]`）+ 幂等 + 输入不改写 + flip 后 check_stone ok。
- STL：头 80B/三角数 2×quad/文件长 84+50n/不以 "solid" 撞 ASCII；逐三角求体积 = 解析值（float32 放宽 rel 2e-4）且 >0（外翻）。
- 3MF：三成员 zip、unit="millimeter"、顶点/三角计数。
- manifest：family 聚合、fit/clearance 可追溯、材质分组目录、skipped 白名单、超床独批、坏账 raise、manifest 纯 JSON 回读一致。
- coupon：6 件存在、pair_gap = 2×clearance（几何复核 + `gap_check` 名义拼装不穿透）、三档互相可分（TIGHT<NORMAL<LOOSE）。

## 体积模型注记
wedge-std 是剪切平行六面体（体积 = w·h·d 与 hw 收分无关）；inset 只动 bbox 界顶点 → 底面缩 2c、顶面不动，post-inset 体积 = (w−2c)(h−2c)(d−c)。测试按此解析式 ±rel 1e-9 断言。

## 验证
- 隔离树：`pytest tests/ -q` = **171 passed**（基线 147 + 新 24）。
- 主树同步后：`pytest tests/ -q` = **171 passed**。
- 装箱不变量 smoke：60 随机件 → 6 批全部 ≤220×220，assign/成员一致；超床分支 oversize=True。
- 端到端 smoke（非测试）：真砖谱 `3d/stones/stones_p0.json` → `masonry2.face_stones`（15 SPANDREL 楔石）→ `export_ledger`：15 石全导出、ledger_print 时序双验通过、0 缺文件、总体积 122.1 cm³。

## 备注
- brief 的 `.superpowers/sdd/p1-task-6-brief.md` 实际在仓库根（非 e30_shikongqiao_video/ 下），已按其全局约束执行（Python 3.9 无 `X | None`/无 match；中文提交信息；测试在 `tests/test_p1_*.py`；合成数据不渲桥；隔离树先行）。
- 本任务未触碰几何冻结项（facts/砖谱 JSON/bridge_geom2 等）；`test_no_literals` 不扫描 export_print.py，新常量集中在模块头。

## 修复轮（审查 Approved-with-warnings 收口：3 Warning + 4 便宜 Suggestion）

### W3 物理标尺（主控裁决，语义变更）
- 档位常量改 **打印件毫米** 口径：`FIT_PRINT_MM = {TIGHT:0.15, NORMAL:0.3, LOOSE:0.5}` = 真实打印件上的配合缝；模型侧 inset 量 = `fit_print_mm/scale`（scale=1/50 → NORMAL 在模型上吃 **15 模型毫米**）。`fit_for_block(dims_m, scale)` 与 `export_stone(..., scale)` 全程参与换算。
- manifest 每石记 `clearance_print_mm` + `clearance_model_mm` 双值；`ledger_print.json` 的 `clearance_manufacturing_mm` 记**模型侧** inset（账本几何是模型单位）。
- 留证（smoke，NORMAL 楔对，scale=1/50）：成对缝 = 两石各退 15 模型毫米 → 模型缝 30mm → **打印当量 0.600mm = 2×fit_print_mm(0.3)**，±1e-9 钉进测试；三档打印当量 TIGHT 0.300 / NORMAL 0.600 / LOOSE 1.000mm 互分。
- 负控更新：①分派 scale 耦合（漏乘 scale 则 S50 与 1:1 同值必红）；②STL 体积解析式按新 c=0.015m 更新（(w−2c)(h−2c)(d−c)，rel 收紧 2e-4→1e-5，S1）；③薄层不塌：最薄 0.144m 层 NORMAL 下 144−2×15=**114mm** 仍正（打印当量 2.28mm > 1.2 最小壁，export 不 raise，体积>0）。
- smoke 双值行：`RING.C00.B00 fit NORMAL print 0.3 model 15.0`；`RING.C00.B01 fit TIGHT print 0.15 model 7.5`；ledger 字段 `[15.0, 7.5]`。

### coupon 改 1:1 打印（S2 裁决）
- `coupon_set(out_dir, scale=1.0)`：楔块用模型米真尺寸直接出——这才是可实测的打印机配合试片（旧 1:50 缩印缝只剩 6µm，无标尺意义）。缝 = 2×fit_print_mm 打印毫米，实测 STL x 跨度 NORMAL A 件 = **299.400mm**（=300−2×0.3；若仍按 S50 缩放会得 ~6mm，判据即拒）。
- 三档互分负控更新 + `gap_check` 名义拼装改 1:1 口径（scale=1.0）。

### W1/W2/S2/S3/S5
- W1：`from typing import ...` 补 `Dict`（原 type-comment 引用未导入名）。
- W2：`export_ledger` 在 `save_ledger` 之后 `load_ledger` 回读再 `validate_ledger(..., allow_clearance=True)` 一次——真「落盘双验」，顺带覆盖原子写损坏面；不过即 raise `ledger_print readback invalid`。测试同路回读断言。
- S2：`export_stone` 形参默认改 `fit=None`（自动分档），与 docstring 对齐；负控：0.2m 小块省略 fit → TIGHT(7.5 模型毫米)。
- S3：`import io` 挪模块头（`_3mf_bytes` 内删）。
- S5：私有 `_mesh` 键/`_coupon_mesh(rec, side)` 删除，改公开纯函数 `coupon_mesh(tier, side, scale=1.0)`（post-inset 已外翻；未知档/坏 side 直接 raise），`coupon_set` 与其共用同一真相；测试全走公开口。

### 验证（修复轮）
- 隔离树 `/tmp/e30_p1/`：`pytest tests/test_p1_export.py -q` = 26 passed（TDD：先对旧实现跑红 10 failed，实现后绿）；全量 = 171 passed + 2 环境性 fail（`test_freeze_manifest` 依赖真仓 git/冻结路径，本隔离树修复前后同态，非回归）。
- 主树同步后：`python3 -m pytest tests/ -q` = **173 passed**（基线 171 + 新增 thin_layer/coupon_mesh 两条负控）。
