# P1 Task 2 报告 — families.py 族库

## 状态
DONE。TDD 五步全部按 brief 执行。

## Commit
- `0d9329d feat(e30): P1-T2 族库(楔形/直盒确定性网格+unique烘焙curve_hash失效)`
- 仅含本 task 两文件：`e30_shikongqiao_video/3d/families.py`（48 行）、`e30_shikongqiao_video/tests/test_p1_families.py`（40 行）。未触碰 T1/其他在途文件。

## 测试
- Step 2（实现前）：`ModuleNotFoundError: No module named 'families'` →  collection error，符合预期失败。
- Step 4（实现后，隔离树 /tmp/e30_p1 与主树各跑一次）：
  `python3 -m pytest tests/test_p1_families.py -q` → **3 passed in 0.01s**
- Python 3.9.6 语法合规：`ast.parse` 通过；无 `X | None`、无 match（typing + type-comment，照抄 brief）。

## 自审
- 实现与测试均逐字取 brief Step1/Step3 代码，无擅自扩展。
- 接口与 brief 契约一致：`family_mesh(family, params) -> (verts, faces)`；`bake_unique(stone_id, verts, faces, cache_dir, curve_hash) -> str`；`FAMILIES: Dict[str, callable]`。
- 流形性由测试断言（12 条无向边各属 2 面）；确定性由两次调用 `==` 断言（纯算术无随机/时间源）。
- curve_hash 进 sha1 tag → 文件名变 → 旧文件不覆盖、缓存自然失效重烘，符合"产物不入库、代码入库"分层。

## 顾虑（不阻塞，供 T3/T4 与审查参考）
1. **`wedge-std` 忽略 `params["d"]`**：楔形深度由 `back`(+batter) 决定，测试却传 `d:1.2`。brief 实现即如此；T3 调用方勿指望 d 生效。
2. **`test_wedge_std_follows_batter` 判据偏松**：`ys_front` 实际收集全部顶点 y（含背面），即使 `hw_b==hw_t`（无收分）也会因背面前后差而通过。它验证的是"y 非均匀"而非"前脸上下沿随收分倾斜"。逐字照抄未改；若需强化建议 T3 前加一条 `f1-f0 == hw_b-hw_t` 的直接断言（新判据，非放松既有）。
3. `bake_unique` 同键重复调用会重写同一路径（无存在性短路）——幂等无害，但若 T5 想省 IO 可加 `if os.path.exists` 短路（brief 未含，未擅加）。
4. 面片绕序/法向一致性未测（仅拓扑流形）；OBJ 未写 `vn`。留给 T4 printcheck。

## 修复轮
审查结论 2 Critical + 1 Important + m2，按主控规格定向（U1: d 权威=back 兜底；U2 楔形原点不动移交 T7）修复。

### Commit
- `395d254 fix(e30): P1-T2审查修复(d权威深度+收分方向+带符号batter判据+slab测试)`——仅动 `3d/families.py` 与 `tests/test_p1_families.py`。

### 修复项（TDD：先加测试确认红，4 failed 于预期断点位，后转绿）
- **C1 深度由 d 决定**：`d = params.get("d", params.get("back", 0.3) + proud)`（U1 语义：d=从前脸向墙内起算的整石深度，back 仅缺失时兜底）；背沿 `b0=f0-d, b1=f1-d`（上下沿各自）。新测试 `test_wedge_std_depth_follows_d`：yspan(d=2.4)−yspan(d=1.2)=1.2>0.3；负控制 d 相等跨度差==0；跨度绝对值==d+batter；d 权威时 back=9.9 被忽略。另加 `test_wedge_std_back_fallback_when_d_missing`（无 d 时跨度==proud+back=0.32）。
- **C2 收分方向**：`f1 = proud − (hw_b−hw_t)`（顶沿内收，原实现符号反了；b1 随动）。新测试 `test_wedge_std_top_edge_batters_inward`：带符号 `前脸顶沿y−底沿y == pytest.approx(-(hw_b-hw_t))`。
- **I1 恒真判据删除重写**：`test_wedge_std_follows_batter` 改为带符号断言（原 `abs(span-0)>1e-6` 恒真版按纪律删除不保留），负控制①hw_b==hw_t→差==0；②反坡 hw_b<hw_t→断言同公式成立且 d_rev>0（证方向关系非数值巧合）。辅助函数 `_front_top_minus_bottom` 按 z 层取 y 最大者为前脸，正反坡均无歧义（前提 d>|batter|，测试参数满足）。
- **m2 slab 测试**：`test_slab_deterministic_and_manifold`（两次调用相等 + 8顶点6面 + 12条无向边各属2面）。
- 既有测试期望值核查：`deterministic_and_manifold` 与 `bake_unique` 均同时含 d/back 键且无 y 值断言，d 语义变化后无需改期望，跑绿确认。

### 测试
```
$ cd /Volumes/macstudio/video-projects/e30_shikongqiao_video && python3 -m pytest tests/ -q
86 passed in 0.63s
```
单文件：`python3 -m pytest tests/test_p1_families.py -q` → 7 passed in 0.01s。基线 82→86（+4 净新增）。Python 3.9.6 `ast.parse` 双文件通过。

### 顾虑处置
- 上轮顾虑 1（wedge 忽略 d）、顾虑 2（batter 判据恒真）本轮已闭环消除。
- 顾虑 3（bake 无短路）、4（绕序/法向）不在本轮修复清单，维持原状。
- 提醒 T3/T7：d 语义变更后，楔形 y 向总跨度≈d+|hw_b−hw_t|，局部原点仍为左下前角（U2 归 T7）。
