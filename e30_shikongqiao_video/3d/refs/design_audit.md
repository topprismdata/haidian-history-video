# E30 本体设计审计留痕（design_audit.md）

对象：spec `docs/superpowers/specs/2026-10-04-e30-bridge-facts-design.md` + 计划 `docs/superpowers/plans/2026-10-04-e30-bridge-body-m0-m25.md`
流程：自审 3 轮（R1 几何/事实、R2 判据有效、R3 可执行）→ GPT 审 3 轮（G1 事实来源、G2 判据有效、G3 计划遗漏）→ 每条意见必须经我核实：接受（落改）/否决（记录理由）。

## 自审轮记录

### R1 几何/事实一致性
| 发现 | 严重度 | 处置 |
|---|---|---|
| geom 递推用 `BRIDGE_ABUT`(1.35) 而 plan derive 用 `BRIDGE_ABUT_TARGET`(2.00)，两者 PIER_X 不一致 | 高 | Task 4 增加递推修复（废回填机制，统一 TARGET）|
| facts 无 BRIDGE_ABUT 条目（geom 内部变量） | 低 | 由 TARGET 覆盖，geom 不再有独立值 |
| HALF_SPANS 中央孔 8.50 无据 | 高（已知） | M0 Task 2 首查项 |

### R2 判据有效性
| 发现 | 严重度 | 处置 |
|---|---|---|
| qa_l2 `--negative` 翻转发生在法线计数**之后**，负控无效 | 高 | 重排：先翻转再测 |
| 内壁法线瞄准向量三元表达式优先级错误（else 分支是 tuple，解包崩溃） | 高 | 重写为"拱腹面→圆心"两行版，只测 |r−a9|≤0.15 的 barrel 面 |
| SPANS_MONO 右半判断式写错（`<= ... -(-1e-9)` 恒真噪音） | 中 | 改两行 any() |
| L1 无"桥面必须中央最高"的历史事故回归？已有 DECK_DIR ✓ | — | 保留 |

### R3 可执行性
| 发现 | 严重度 | 处置 |
|---|---|---|
| Task 7 引用不存在文件 `shot_side_from_ortho.png` | 中 | 改 `ortho_side.png` |
| AST 白名单可能被滥加尺寸 | 中 | 加治理注记：尺寸一律进 facts |
| T1 测试计数 4 / T3 计数 8 复核 | — | 一致 |

## GPT 审查轮记录

（G1/G2/G3 逐条：意见 | 我的核实 | 处置[接受落改/否决+理由]）
