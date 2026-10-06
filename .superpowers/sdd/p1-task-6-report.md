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
