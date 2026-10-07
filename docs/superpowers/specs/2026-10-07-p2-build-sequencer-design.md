# Spec#2（P2）：建造序列器 sequencer + G3 力学门
状态：**v2**（自审×3 → GPT 评审 8.6/架构PASS/G3暂缓 → 主控裁决：六项全采纳，见 v2 标记）。上游：M22 路线图；输入=G1 封版几何+P1 ledger+G0 史料库。

## 0. 已定决策（用户拍板 2026-10-07）
- 券架=**结构可信型**：按清式木作逻辑程序化生成（排架柱+楞木+弧形券胎板+卸架楔），每孔一副随跨变化；**不入打印账**（ledger 中 evidence=inferred_construction, print.excluded=True）
- G3=**①③④实做+②规则化**：时窗支撑 DAG、落架压力线、多孔不平衡推力极限平衡全实现；逐 stage 接触力 LP 用"对称砌筑+合龙前不落架"规则代替（μ 无史料值，LP 成本 5935×百 stage 不值）

## 1. 目标与非目标
**目标**：把 5935 石 + 券架排成一份**史实可挂账、力学可验证**的建造序列（sequence.json），供 P3 动画直接消费（stage 整数即 GN 显隐键），并输出 G3 报告作为 P3 开工门。
**非目标**：动画镜头（P3）、灰浆凝结材料模拟（规则化）、围堰/抽水水下工程（旁白带过，无几何）。

## 2. 工序规则（每条挂史料编号，见 refs/construction_history.md）
| 规则 | 内容 | 依据 |
|---|---|---|
| R0 冬期开工 | `preferred_season=WINTER [historical-context]`——**非 DAG 硬前提**（御制诗语境非本桥专属条文） | A:御制诗(等级已降) |
| R1 墩身自下而上 | 每墩列带 z 升序；丁顺层间依赖 | C:B组 砌体通则 |
| R2 券架先行 | 每孔 RING 石依赖该孔 centering 对象已立（support_edges type=centering 时窗 [立架,合龙后落架]） | B14 孔庆普实证：无架拱圈不能自持 |
| R3 对称砌筑 | **荷载平衡度**判据：\|W_L−W_R\|/(W_L+W_R) ≤ ε（默认 0.15），不锁 L-R-L-R 严格交替（无史料的伪精度）；负控=一侧前沿大幅领先必红 | B14 + v2 |
| R4 合龙→持荷→**分级卸架** | 龙门石=该孔 RING 末件；`MIN_HOLD_EVENTS=3`（事件数非时长，无史料养护值不冒充）；卸架=DECENTER_START→WEDGE_RELEASE_×k→CENTERING_CLEAR 事件链，support_edge 携 `capacity_factor` 1.0→0 阶梯，λ∈{0,.25,.5,.75,1} 逐档核 | C:A2 + B14 + v2 |
| R5a **pre-strike 锁固肩** | 合龙后、架上仍承载时，先砌满足四条件的下部拱肩/背衬：RING 完成∧不与券架实体冲突∧有确定下承/侧承∧左右荷载增量近对称（含 475 环肩咬合石） | v2 裁决: 裸环脱架=人为最不利态; 环肩本非独立体系 |
| R5b post-strike 回填 | 卸架完成后才砌受架占位的上部背衬/芯胞/余肩 | 空间约束 |
| R6 孔序由中向外 | ARCH09→两侧交替；**并行度显式化**：每孔携 frontier 状态 OPEN→CENTERED→RING_BUILDING→CLOSED_SUPPORTED→PREBACKED→DECENTERING→SELF_SUPPORTING→FILLED，允许的跨孔状态组合是序列器约束（不是隐含在排序里） | [推断] 主控签署（v2: 状态机取代序字符串） |
| R7 桥面→栏→狮→兽 | PAVING→RAIL/POST→CARVE 全局后置 | C:A2 名目层级 |
每 stage 输出 `evidence` 字段=规则编号；旁白红线 lint 表（禁词清单来自 G0 §三）作为 CI 检查。

## 3. 组件
| 文件 | 职责 |
|---|---|
| `3d/centering.py` | 券架生成器：输入孔参数（span/ring_t/lift/springer），输出木作对象（排架柱间距 1.2m [推断]、楞木、券胎板沿 extrados+30mm 工作面、卸架楔对）；bmesh 局部网格+ledger 注册（role=CENTER, family=wood-<arch>） |
| `3d/sequencer.py` | 规则引擎：ledger+券架 → 拓扑排序 → sequence.json（{id, stage:int, t_order, depends_on[], centering_id, evidence}）；stage 数目标 200-600（P3 变速叙事的粒度基础） |
| `3d/g3_check.py` | **事件驱动**：每个结构事件（PLACE_STONE/CLOSE_RING/ADD_PREBACKING/DECENTER_STEP/CENTERING_CLEAR/ADD_FILL）后生成 structural snapshot，逐 snapshot 核：①支撑 DAG 活跃（capacity_factor>0 才算活着，悬空=红）③压力线：acceptance case=**RING+PREBACKED**（落架瞬间真实存在物），robustness case=裸环（裸环不过而带锁固肩过=肩石属结构工序，不判红；两者都过=鲁棒性加分）④**与③同模型**：压力线导出可行推力区间 H∈[Hmin,Hmax]，墩不平衡 ΔHmax=max|H_L−H_R|（λ 逐档），现代裕度 M_res≥1.5·M_unb **明示为现代安全系数**+无系数核距指标 e=M_unbal/V 并行输出 |
| 输出 | `3d/out/sequence.json`、`3d/out/event_ledger.json`（event_id/hole/type/prerequisites/affected_support_edges/load_transfer/snapshot_id/evidence_id/inference_grade）、`3d/out/g3_report.json`、`3d/out/narration_beats.md` |

## 4. 已知难点与裁决
- **环-肩咬合石**（475 裁片）：归 R5a pre-strike 组（其依赖=对应 RING 就位+冲突检查通过），parent_ids 谱系已备
- **schema 连锁**：support_edges 由 `{type,active_from,active_to}` 升 `{type,capacity_curve:[(event_id,factor)]}`——ledger schema v2（minor+迁移脚本，G2 工件重放验证）；**券架/卸架事件永不进 stone ledger 实体账**（5935 真源纯度保持），独立 event_ledger
- **冻结防污染红线**：若出现"裸环与带锁固肩都过不了"——**停下报主控**，严禁回调封卷的 0.56 矢跨/墩宽/券厚来凑门
- **CORE 满墙胞**：与环/肩同 stage 带依赖（先环后胞），落架前禁砌（占架空间）
- **④公式保守性**：楔推力取"半环重×cot(合龙角)"上界，不精算——报告标[工程近似]，G3 只拒"明显失衡"序列（如相邻孔跳孔落架）
- **cure_stages 参数**：灰浆凝结无本桥史料（B15 糯米灰浆性质通例）→ 参数化，默认 3 个全局 stage；语义=该孔落架不早于合龙后第 3 个全局 stage（相邻孔施工在此期间正常推进）；敏感性 1/3/6 记报告

## 5. 验收
- sequence/event ledger：5935 石+17 副券架全覆盖、DAG 无环、stage 单调、每孔 frontier 状态轨迹合法（允许组合表校验）；validate_ledger v2 兼容（CENTER 词法+capacity_curve）
- g3_report：①③④ 全 PASS（acceptance+robustness 双 case）+ 五组负控（悬空石/提前 CLEAR/跳孔落架/一侧前沿领先/λ 档推力破坏）逐组注入必红
- 旁白 lint：红线禁词 0 命中
- 全门：e30 239+新增 / bridge3d 312 / L2 / 33 断言 / freeze 逐位（P2 零触本体）
- 叙事抽验：中央孔一孔的完整 stage 序列（立架→17 券石对称→龙门石→凝→落架→拱肩）人工对 G0 编号逐条可查

## 6. 下游接口
- P3 消费：sequence.json（stage→GN attribute 驱动显隐/飞入序）+ 券架对象（显隐+卸架动画）+ narration_beats.md
- P4 消费：无（券架不打印，print.excluded 已标）
- 门：G3 PASS = P3 开工前置
