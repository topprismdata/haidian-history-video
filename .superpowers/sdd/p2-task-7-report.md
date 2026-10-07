# P2-T7 报告: g3_check.py ④墩推力包络不平衡(λ 卸架档 + 核距双指标 + 排程停车线)

日期: 2026-10-07 | 基线: T6 终态(`d4b6053` 父提交) | Python 3.9.6 |
全量 `cd e30_shikongqiao_video && python3 -m pytest tests -q`: **446 passed, 14 warnings in 192.58s**
(基线 429 + 新增 17, 零红; T6 成果 acceptance/robustness 17/17 无回退)

> **〔§8 包络连续性裁决轮取代声明, 2026-10-07〕**: 本报告 §0-§7 写于首轮
> (事件孔取 Hmax 的包络口径), 其"真账 16/16 墩红 + raise"结论已被 **§8
> 主控三层裁决轮**取代(事件孔 λ×Hmin 物理口径 + 全桥同波落架序重锚 →
> 真账 gate_imbalance 全绿正常返回); §0-§7 保留为首轮裁决链存档。
> 全量测试数在 §8 轮为 448 passed(429 基线 + 19: +17 首轮, +2 裁决轮
> 连续性/同波钉, 实际见 §8.4)。
> **〔§9 T7b 出口审查轮再取代, 2026-10-07〕**: §8 的"同波序可行"与
> "串行不可行(真发现)"再降档为条件式/临界定(判据主张条件化 R1 + V
> 完整性 R2 + 史实标签撤回 R3) —— 以 §9 为准。

## 0. 主控裁决项(先读): 真账触发排程侧停车线 —— **逐孔串行卸架序 [工程推断·非史料] 在首轮静力图式下不可行**(规则号勘误: 卸架序属 R4/R6, 非 R5; 见 §9 R3)

**真账 17 孔全事件逐墩双指标: 16/16 内墩超阈, 159/192 事件-墩组合红**
(`IMB_KERNEL_RED` 105 + `IMB_RATIO_RED` 54, 其中 54 双红)。`run_g3` 已按停车线纪律
`raise G3_DECENTER_ORDER_CONFLICT`(异常携带完整报告 `.report`, 三节齐, 见 §5)。
本任务**未调 λ 档/裕度 1.5/核宽 B/6/包络口径任何参数自救**(红线遵行见 §2/§6)。

- **失稳机理(已诊断)**: 逐孔串行落架 [工程推断·非史料] 为(全 17 孔先合龙(seq≤2084), 再
  ARCH01→ARCH17 依次卸架(seq≥2113); ARCH0k 卸架时东邻 ARCH0k+1 尚驻架, 回馈=0)
  → 每墩在邻孔卸架窗内承受**单孔满包络推力**(事件孔 λ×Hmax, 对侧 0):
  中央细墩(宽 2.17m, 基底 3.20m, 核半宽 0.533m)扛 Hmax≈40-48 →
  e_kernel≈1.3-1.7 ≫ 0.53, ratio≈0.92-1.23 < 1.5。
- **两指标独立性的真账表达**: 51 个事件-墩组合 **ratio 绿但 kernel 红**
  (kernel 严于 1.5 裕度: 等作用高时 e≤B/6 ⟺ ratio≥3; 差异表达域 = B/6<e≤B/3 带 +
  两侧作用高异高); 反向(kernel 绿 ratio 红)真账 0 个 —— 该方向由合成微账测出
  (Step1④b: 两孔推力矩精确对消时, 见 §3), 两指标互不掩盖双向成立。
- **判据非恒真自证**: 收账态探针(全孔清账 λ=1, 无事件孔, 双侧取 Hmin 反馈)下
  **16/16 墩全绿**(最不利 e=0.379/0.517@PIER01, ratio=4.69; 镜像对 dH 逐位反对称
  ±9.93/±8.36/±0.65...) —— 红是建造期卸架序的真现象, 非门系统性误报。
- **裁决选项**(修正走 sequencer, 非本门放松):
  (a) **R4 排程改法(推荐)**: 卸架按邻孔对 `(ARCH01,ARCH02)…(ARCH15,ARCH16),ARCH17`
  **同 stage 逐档交错**释放(每档两孔 WEDGE_RELEASE 入同一 stage, 档差≤一档)。
  探针实测: 159/192 → **116/192**, 即把"满档包络瞬时"从整窗压缩到首达满档孔的
  单事件; sequencer 落法 = `LAMBDA_LADDER` 逐档循环内两孔各 `emit` 一档
  (stage 边界不变), `check_sequence` 的 R4_LADDER 逐孔断言改对内。
  (b) **包络口径裁决**: 事件孔末档取 Hmax、对侧取 Hmin 是 brief 冻结的保守包络;
  收账态全绿+成对探针说明残余 116 红集中于该口径的末档瞬时(物理上末楔释放后
  推力向 Hmin 收敛, Heyman 最小推力原理)。**放松它=调判据, 本门禁做**, 须主控
  显式裁决口径(如"末档后沉降期按 Hmin 记") 后由本门按新口径重跑(判据先行, 数字后置)。
  (c) **冻结几何变更流程**: 加宽中央墩基底(PIER_FOUND_W_C 3.20→使 B/6≥e_max) ——
  同 T6 停车线出口纪律, 走冻结几何流程后重跑本门。

## 1. 交付物

| 文件 | 内容 |
|---|---|
| `3d/g3_check.py`(扩展) | T7④节: `pier_imbalance`/`imbalance_gate`/`_pier_calc`/`_pier_dims_from_ledger`/`_pier_statics`/`_pier_advice`/`G3_DECENTER_ORDER_CONFLICT`; `run_g3` 串接 `gate_imbalance` 同形节 + 排程停车线 raise |
| `tests/test_p2_g3_imbalance.py`(新, 17 测) | Step1 四测(双向) + 五负控 + 接口契约 + 独立性子进程探针 + 真账全链(存在性 skip) |
| `tests/test_p2_g3_dag.py`(1 处) | 真账测的 `run_g3` 调用按新协议捕 `G3_DECENTER_ORDER_CONFLICT`(T5 断言全保留) |
| `tests/test_p2_g3_thrust.py`(1 处) | 同上(T6 断言全保留 + 钉 `gate_imbalance` 节在报告中) |

Commit: `feat(e30): P2-T7 G3④墩推力包络不平衡(λ卸架档+核距双指标)`

## 2. 物理模型(实现口径, 冻结, 判据先行数字后置)

落一孔的架 → 该孔以水平推力外推其两侧墩顶; 邻孔仍驻架/未合龙 → 不回馈反向推力
→ 墩身承受不平衡水平力+弯矩。sequencer 把 DECENTERING 建模为渐进
(λ=环已承载份额∈[0,1], 架吸收 1−λ; `WEDGE_RELEASE.load_lambda` 1/4 栅格单源,
`DECENTER_START`=0, `CENTERING_CLEAR`=1, 越界/缺值 ValueError fail-closed):

- **有效推力**: 事件孔(正在卸架) `H_eff = λ × Hmax`(区间上界, 保守最大推力);
  其余孔(含已清账) `H_eff = λ × Hmin`(区间下界, 保守最小反推力; 未落架 λ=0 → 0)。
- **双指标**(独立输出, 阈值互不派生 —— 一个红一个绿要能表达):
  1. 倾覆裕度 `ratio = M_res/M_unb ≥ 1.5` [现代裕度·敏感性, 非史料常数]:
     `M_unb = |dH|×h_ref`(h_ref=两侧作用高较大者, 保守单臂), `M_res = V×B/2`
     (竖向合力 V 作用于基底形心, 抗倾臂 B/2)。
  2. 核距(中三分律) `e_kernel = |H_L·h_L − H_R·h_R|/V ≤ B/6`(矩形基底核半宽):
     绕基底中线**精确合力矩**(逐侧各自作用高)/竖向合力; 超核 → 基底出现拉应力区
     (砌体抗拉≈0)即失稳。等作用高时 kernel 严于 ratio(⟺ratio≥3), 差异表达域 =
     B/6<e≤B/3 带 + deck camber 引起的两侧异高(真账相邻孔 springer 差 ~0.1-0.3m)。
- **墩静力(保守最小)**: 墩重 = 基底(`assumptions.BODY_BOTTOM`=-2.20)至两邻孔
  起拱线较低者(立架前必须在位的拱座支承体); 纵深 = `2×geom_math.width_at`
  (收分单源)Simpson 积分(width_at 对 z 线性 → 积分精确); 墩宽 `facts.pier_w`;
  上构(拱肩填充)在位性随排程, 保守不计。**基底宽: ledger PIER 石
  params.found_w 优先 —— 实查真账 5935 石仅 SPANDREL/BACK/CORE/RING/IMPOST,
  无 PIER 石(墩在 bridge_body 不进石账) → `facts.PIER_FOUND_W` 回退
  (中央对 k∈{8,9} 取 `PIER_FOUND_W_C`=3.20, 余 3.10), 不硬编码;
  `_pier_dims_from_ledger` 为前向兼容接口(合成账可注入 PIER 石, 测试已钉)。**
- **作用高**: `h = facts/geom_math.arch_springer_z(孔) − BODY_BOTTOM`(推力在
  起拱线水平传入墩顶; 单源现算, 测试同式复算不硬编码)。
- **H 区间单源**: `stress_gate` 的 acceptance 可行区间(T6b §8.3 表), run_g3 内
  直接取 `gate_stress.holes[zh].acceptance.H`, 不重算不造第二套。

## 3. Step1 四测(brief 原文; 先红 17 failed → 实现后全绿)

| # | 测 | 结果 |
|---|---|---|
| ① | 对称双孔同步卸架(邻孔对逐档交错) → 共享墩 dH≤一档(0.25H)且末档精确 0, 两指标皆绿 | ✓ |
| ② | 一侧提前 CLEAR 另一侧未合龙 → 单侧满包络, ratio 3.37(λ=.25 绿)→0.84(λ=1 **红**) | ✓ |
| ③ | λ=0 档(架上满承载) → dH=0 精确绿(ratio=None); 同流 λ=0.25 即非零(证 λ 门活着, 非恒零) | ✓ |
| ④ | 独立性双向: ④a 矮胖墩大水平力 → ratio 2.51 绿 + e_kernel 1.088>1.0 **红**; ④b 两孔推力矩精确对消(H_R=H_L·h_L/h_R) → e≈0 绿 + ratio 0.89 **红**, 且同流 dstart 事件 kernel 红与末档 kernel 绿并存(逐事件独立表达) | ✓ |

## 4. 五负控(全部按预期, 每条内嵌"判据活着"对照)

| # | 注入 | 实测 |
|---|---|---|
| ① | λ 档归零(WEDGE_RELEASE λ→0 ∧ 去 CLEAR —— CLEAR 语义自带 λ=1 非档位) | 基线有非零 dH(判据非恒真) → 归零后全事件 dH/H_L/H_R 精确 0、零违例 ✓ |
| ② | H_env 全置 0 | 全 entry dH=M_unb=M_center=e_kernel=0、verdict 全 ok、violations=[](不假红) ✓ |
| ③ | 单孔(ARCH02)H 翻倍 | 其两侧墩 PIER01/PIER02 的 ratio 严格降、e_kernel 严格升、\|dH\| 严格升 ✓ |
| ④ | 墩基底加宽 3.1→6.2 | 核距利用率 e/(B/6) 严格降(核半宽∝宽) 且 ratio 严格升(M_res∝B, 不误伤) ✓ |
| ⑤ | 邻孔清账态翻转(ARCH01 λ=1↔0) | dH 符号按回馈方向翻转(+1.195 ↔ −8.74); 与无回馈态之差恰 = +Hmin_01=31.0(1e-12) ✓ |

另: 接口契约测(brief 字段 `{H_L,H_R,dH,M_unb,M_res,ratio,e_kernel,verdict}` 齐 +
gate 节与 gate_dag 同形 `{violations,violation_counts,ok,elapsed_s}`)、
PIER 石→facts 回退链测、事件孔缺 H 区间 fail-closed 跳过注记测、λ 越界
ValueError 测、桥台边界(k=0/17)不评测、**子进程探针**(imbalance 全路径
`'sequencer' not in sys.modules`, 与 T5 独立性同构)。

## 5. 真账全链: 三种卸架序对比 + 停车线协议

`imbalance_gate`(真账, 102 个 DECENTERING 事件 × 邻墩, 192 事件-墩组合, 0.006s):

| 卸架序 | 违例 | 最不利 kernel | 最不利 ratio |
|---|---|---|---|
| **逐孔串行序** [工程推断·非史料](ARCH01→17) | **159/192 红**(16/16 墩) | e=1.690 > 0.517@PIER15 | 0.917 < 1.5@ARCH15 |
| 邻孔对逐档同步探针(§0-a) | 116/192 红 | e=1.611@PIER08 | 0.967@ARCH16 |
| 收账态(全孔清账, 稳态锚) | **0/16 全绿** | e=0.379/0.517@PIER01 | 4.69@PIER01 |

结论: **逐孔串行卸架序 [工程推断·非史料] 在首轮包络口径下力学不可行**; 排程侧最好可达
(邻孔对逐档同步)仍不能清零 —— 残余红集中于"事件孔末档取 Hmax"的包络瞬时
(§0-b 裁决项), 排程只能压缩不能消除; 建成态自洽(全绿)。

**run_g3 真账协议**(已被 `test_real_ledger_gate_imbalance_fullchain` 钉死):
`raise G3_DECENTER_ORDER_CONFLICT`, `exc.report` 三节齐 ——
`gate_dag.ok=True`(4118 事件 0 违例) + `gate_stress.ok=True`(**acceptance/
robustness 仍 17/17, T6 成果零回退**) + `gate_imbalance.ok=False`
(violations + piers 逐墩 worst_ratio/worst_kernel + advice)。
**建议样例**(逐超阈墩一条, 事件时刻邻孔态冻结):
`PIER08(seq=2753 ARCH08 WEDGE_RELEASE λ=1.00 ratio=0.99<1.50): 邻孔当前态(ARCH09 λ=0.00)下本孔 λ≤0.30 可过(现 1.00); 卸架顺序建议: 与邻孔 ARCH09 同 stage 逐档同步落架(档差≤0.25) / 先落架邻孔 ARCH09 至 λ=1 再落本孔; 同 stage 逐档同步(档差≤0.25)末档残余核算: 仍超阈(KERNEL_RED) —— 须两孔同档同时释放或走冻结几何变更流程(加宽基底, 非本门可放)`

## 6. 工程注记

- **独立性**: g3_check 导入闭包仍不含 sequencer(既有 T5 钉 + 新增子进程探针);
  λ 栅格步长 0.25 与 `sequencer.LAMBDA_LADDER`/`events.LAMBDA_GRID` 同一裁决值
  各自声明(互证纪律); H 区间取③门产物(同报告单源, 无第二套压力线)。
- **性能**: 真账 imbalance 门 0.006s(纯落架事件流)+ snapshots 推进(与 gate_dag
  共享状态机, 无重扫); run_g3 全链耗时增量 ~1s(总 ~27s 仍由 W1 吞没扫描主导)。
- **同形节**: `gate_imbalance` 含 `violations/violation_counts/ok/elapsed_s`
  (与 gate_dag/gate_stress 对齐) + `n_evals/n_skipped_events/skipped_note/
  piers{base_w,V,dims_source,worst_ratio,worst_kernel,n_evals}/events[逐墩账]/
  advice`。entry 含 brief 全字段 + `seq/hole/etype/lam_active/lam_L/lam_R/
  M_center/h_L/h_R/h_ref/kernel_half_w/dims_source/env_missing`。
- **fail-closed 面**: λ 缺值/越界 ValueError; H 区间形状非法(0≤min≤max) ValueError;
  事件孔缺 H 区间跳过+注记(不静默); dims 条目缺 base_w/weight 或非正数 ValueError;
  ratio 在 M_unb≈0 时为 None(无不平衡水平力, verdict ok; 无 inf/NaN 入报告)。
- **Python 3.9.6**: `Optional[X]`/type comment 同仓风格, 无 match, 无 walrus;
  测试 blender-free; 测试不 import sequencer(含 fixture, 纯手搭落架事件流)。

## 7. 验收复跑账

- 全量 `cd e30_shikongqiao_video && python3 -m pytest tests -q`:
  **446 passed, 14 warnings in 192.58s**(429 基线 + 新增 17, 零红)。
- T6 成果: `test_real_17_holes_acceptance_feasible_and_report` 通过 ——
  acceptance(结构带) 17/17 / robustness(裸环) 17/17 / LOCK_BAND_M=0.35 钉 /
  纯消融负控 {A08..A11} 全部原样; run_g3 协议变更(新增④raise)已按"更新坏掉的
  契约测试"最小适配(两处 except 分支, 断言全保留)。
- Step1 四测 + 五负控 + 契约测 17/17 绿(先红后绿: 实现 前 17 failed)。
- 五负控全过且各带"判据非恒真"对照(§4)。
- 真账三节齐 + 双门不受影响 + 排程建议可执行(§5), 停车线纪律遵行
  (λ/裕度/核宽/包络口径零触碰; 红即结论, 未凑绿)。

---

## 8. 包络连续性裁决轮(主控三层裁决落地; 2026-10-07)

> 主控裁决(IRC 三层): ①修包络内部不一致(正确性修复非放松) ②采纳成对
> 同步落架 ③拒绝冻结几何改动。判据先行数字后置; 判据红线遵行: λ 档/
> 裕度 1.5/核宽 B/6/PIER_FOUND_W/砖谱零触碰。

### 8.1 裁决落地

| # | 裁决 | 实现 |
|---|---|---|
| ① | **事件孔 H_eff = λ×Hmin**(Heyman 最小推力: 逐档缓释木楔拱向最小推力收敛; 事件孔与已清账孔同式, λ=1 处无 Hmax→Hmin 突跳, 与收账态连续) | `_pier_calc` 全孔同式 λ×Hmin; 旧"事件孔 Hmax"包络降为**保守敏感性对照**(entry.`dH_hmax/M_unb_hmax/ratio_hmax/e_kernel_hmax` 仅记录不判红); 连续性钉 `test_step1_lambda1_event_hole_equals_cleared_continuity`(同墩"末档事件孔"与"清账后非事件孔"H_L/双指标逐位同) |
| ② | **成对同步落架**: sequencer 波2 卸架序改对称同步 | 全桥同波逐档(每档全部孔 WEDGE_RELEASE 同 stage 同档, 档差=0 —— "邻孔对同 λ"对**每一对**邻孔成立, 是裁决档差=0 的完全不动点): stages `DECENTER.DSTART.WAVE / DECENTER.WEDGE.{1..4}.L{25,50,75,100} / DECENTER.CLEAR.WAVE` + 逐孔 FILL(依赖各自 CLEAR)。R6_ADJ 判据改**对内同档**: 任一落架事件时相邻落架孔 λ 差 ≤ 一档(`sequencer._check_adj_rung_lock` + `g3_check._check_r6` 两实现互证); 乱序同落架(插块/连升多档)仍红(既有负控 test_r6_negative_adjacent_decenter_forbidden / test_neg5b 原样通过); R4_LADDER 逐孔 λ 全阶不变("对内同档"落在 R6_ADJ) |
| ③ | **拒绝 (c)**: 不碰冻结几何 | PIER_FOUND_W(_C)/PIER_W_INT/一切封卷参数零触碰; 墩不平衡是卸架顺序问题(收账态全绿已证墩尺寸对稳态足够) |

### 8.2 两口径对比(重锚后真账, 全桥同波落架序, 192 事件-墩)

| 口径 | 判定 | 最不利 |
|---|---|---|
| **Hmin 物理口径(PASS 判据)** | **ok=True, 0/192 红** | e=0.472 ≤ 0.517@PIER13; ratio=3.438 ≥ 1.5 |
| Hmax 保守敏感性对照(仅记录) | —(不判) | e=1.379; ratio=1.154(上界裕度记录) |

**全桥同波对称同步卸落在最小推力读数下不违例** —— 本轮结论(条件化: 不违例 ≠ 可行证明, 见 §9 R1)。

### 8.3 串行失败 robust 证明 + 卸架序方案对比(Hmin 口径, 同一 H_env 同一评估器)

| 卸架序 | 红事件-墩 | 最不利 e |
|---|---|---|
| 逐孔串行(首轮评估序) | **77/192** | 1.293(≈2.5×核半宽) |
| 顺序邻孔对 (01,02)..(15,16)+17 solo | 39/192 | 1.293 |
| 顺序邻孔对 (02,03)..(16,17)+01 solo | 38/192 | 1.171 |
| 镜像对 (01,17)(02,16)..+09 solo(对照) | 66/192 | 1.293 |
| **全桥同波逐档(采纳)** | **0/192** | 0.472 |

- **头条发现 robust**: 逐孔串行在 Hmin 物理口径下仍深红(77 红, 落 ARCH0k
  时东邻 λ=0 无回馈 → 单孔 Hmin≈20-32 无对冲) —— **"串行单侧满推力无对冲时刻超核"对 H 读数轴稳健**(该半句后于 §9 R2 进一步条件化: 亦依赖图式保守缺省 δ=0/μ0=0)(钉: `test_real_ledger_gate_
  imbalance_fullchain` ③段, 同账卸架块重排探针, reds>30 ∧ worst_e>1.0)。
- **顺序成对方案的残余红如实归因**(裁决②若按两两顺序执行): 残红集中于
  **对间过渡瞬时** —— 新对 dstart 时西邻已清账(Hmin 全力)而新对 λ=0 无对冲
  (如 (03,04) 启动时 PIER02 见 Hmin_02=20.4 无对冲, e≈0.57>0.517); 这是
  顺序方案的**内禀过渡**, 非判据伪影。镜像对则只平衡全局矩、不解决局部墩
  (66 红)。消除过渡的唯一同步结构 = 全部邻孔对并发 = **全桥同波**(细分档
  的极限, 恰为"档差=0"约束的不动点) —— 采纳。
- 镜像协变旁证: 收账态/H同波 worst 逐墩表 PIER01↔PIER16 逐位镜像
  (±9.93/±8.36/±0.65..., e 0.379 对称)。

### 8.4 重锚与复现账(波2 只重排卸架事件与 stage, 石账零触碰)

- `python3 3d/sequencer.py` 两连跑: sequence.json/ledger_sequenced.json
  **cmp 逐字节相同**(幂等保持)。事件数 **4118 不变**(6 事件/孔不变, 只重排);
  stages 419→408(17 DECENTER+17 FILL → 6 波 stage+17 FILL); 入日程石
  3931/in_void 2004/dm 剔除 29(清单幂等不变); R5a=**1342 不变**;
  **acceptance/robustness 17/17 零回退**(③门只吃石账几何+R5a 集, 全部不变)。
- sha256 重锚(sidecar `3d/refs/artifact_sha256.txt` 已同步, 记录值==盘上实算):
  sequence.json `55d9bdaa→1cefc071`; ledger_sequenced.json
  `c3406d28→f7e26c2f`; **ledger_full `80de7a45`/core_hash `513dfd93`/
  excluded_ids `fa1a4ef3`/central_slice manifest `45fed1e8` 逐位不变**
  (本体零触碰直接证据)。
- run_g3 现账: **正常返回**(排程停车线解除), 三节齐 gate_dag ok(4118 事件
  0 违例, R6 对内同档两实现) + gate_stress ok + **gate_imbalance ok=True
  (0/192)**。
- **附带修复(重写波2 时发现并修正的存量潜伏缺陷)**: `meta.holes[].n_dm_
  excluded` 原实现取**波1 循环残留变量**(与孔无关, 真账恒为末孔值 0) ——
  逐孔 dm 计数自 v1 起即失真。现改 `wave1[zone]["n_dm_hole"]` 逐孔携带,
  重出账逐孔值与 `meta.dm_excluded` 29 元清单按孔精确吻合(ARCH06×1,
  ARCH07×9, ARCH08-10×3, ARCH11×9, ARCH12×1, 合计 29; 既有测试未钉此
  字段值, 故此前未暴露)。
- 测试: 全量 `pytest tests -q` **448 passed, 零红**(429 基线 + 19 = 首轮 17
  + 裁决轮 2[连续性钉/同波合法+失档红钉]; 首轮 Hmin 口径改判后 Step1②
  合成墩重配重、真账测改钉"同波绿+串行红"双向)。
- 账目位移归因: 支撑边 capacity 曲线 knot=事件 seq 随重排平移(结构同式:
  centering 边 1−λ 阶梯/stone 边 λ 阶梯/逐孔 own-seq 链), Σ≥1 不变量全绿;
  无任何石增删/几何/参数变化。

---

## 9. T7b 出口审查修复轮(4 CRITICAL 落地; 2026-10-07)

> 出口审查(agent://P2T7Review)判上轮+裁决轮共 4 CRITICAL(C1 判据主张
> 条件化 / C2 史实标签 / C3 V 完整性与图式依赖 / C4 dm 回归钉缺失),
> 主控 T7b 裁决 R1-R4 落地。判据红线遵行: RATIO_MIN/KERNEL_FRAC/
> LAMBDA_GRID_STEP/封卷几何/砖谱零触碰(全程未改)。
> §9 数字全部为**本轮出货代码自测复现**(主控令: 不照抄审查数字);
> 审查者预 V 修复值在表中并列供追溯 —— 两列差异由 §9.2 的 R2 修复解释。

### 9.1 R1 判据主张条件化(C1)

- **PASS 判据保留 Hmin 读数**, 主张统一改为条件式: **H∈[Hmin,Hmax] 皆
  静力可及(Heyman 安全定理), Hmin 为拱自由偏好平衡的点估计非保守界
  (最小推力定理前提=沉降到位, 卸架中环仍被架约束位移, 无"必为最小"
  机制保证); 本门在该读数下不违例 ⇒ 不能判定可行, 只能判定不违例。**
- 门名去"包络"(现实现非包络): 节名/键名 `gate_imbalance` 保持兼容,
  标题改 **"④墩不平衡(最小推力读数)"**; `viol_uniform_hmax` 新增
  (一致 Hmax 读数 α=1 全孔同式的违例组合数, 机器可读) —— 真账波序
  实测 **=1**(组合 PIER16@ARCH16 L100, e=0.534 vs 0.517, util 1.033)。
- **α 轴**(H=(1−α)Hmin+α·Hmax 全孔同式, 全桥同波序; red=违例组合数/192):

| α | 0 | 0.20 | 0.50 | 1.0(一致 Hmax) | box(事件孔 Hmax/其余 Hmin) |
|---|---|---|---|---|---|
| 红组合(本轮, V 修复后) | 0 | 0 | 0 | **1** | **14** |
| 审查实测(V 修复前) | 0 | 1 | 2 | 14 | 77 |

  二分 α_crit: 本轮 ≥0.93(V 修复后全轴近绿, 仅一致上界 1 边缘组合);
  审查 V 修复前 ≈0.151。**两列差异=§9.2 R2 V 完整性修复的直接后果**
  (V 增大使全部读数的 util 下移), 非数字矛盾。
- **λ 栅格 N 轴**(全桥同波, Hmin 读数; worst util):

| N | 2 | 3 | 4(现行) | 8 | 64(∞ 近似) |
|---|---|---|---|---|---|
| 红/最差 util(本轮, V 后) | 0 / 0.661 | 0 / 0.569 | 0 / 0.540 | 0 / 0.495 | 0 / 0.456 |
| 审查实测(V 前) | 10 红 / 1.377 | 2 红 | 0 | util 0.806 | util 0.733 |

  结构结论两列一致: 档越细 util 越低(档内一事件拍前扫 = 残余不平衡源);
  V 修复后全 N 不违例。

### 9.2 R2 V 完整性(C3·正确性修复)

- `_pier_statics` V = 墩身自重积分 + **(W_top_L + W_top_R)/2**(墩顶两邻孔
  RING+R5a 带竖向反力经楔座传墩, 每 Springing 半跨分摊; 每孔
  W_top = RING 全重 + R5a 带重, 17 孔合计 **1911.9** = 审查者"全桥环+带重
  1912" 逐位同量级); **δ(反力偏心)保守取 0**(无对倾力臂 credit),
  **μ0(驻架孔回馈)保守取 0**(声明保守)。`_hole_top_loads` 单源,
  r5a 缺省 `load_r5a_shoulders()`; 合成账(空石账)自然退化为原 V。
- **真账复跑**: 全桥同波仍 **0/192 不违例**(V 增大只更绿) ✓;
  逐孔串行 **77→6 红组合, worst util 2.424→1.009**(e 0.521 vs 0.517) ——
  **仍违例但仅边际**(钉: 真账测 ③段 `ok is False ∧ reds≥1`)。
  **[主控提交前钉清·V 分解表]** 6 条红组合仅落两墩(同一物理态被 2-3 个
  事件重复评到: 末档 WEDGE_RELEASE/CLEAR 与邻孔 dstart 同状态):

  | 红墩 | V 分解 = 墩身 + (左孔 环+带)/2 + (右孔 环+带)/2 | V | 红组合(util) |
  |---|---|---|---|
  | PIER07 | 113.3 + (A07: 环56.4+带80.0)/2 + (A08: 环63.4+带86.0)/2 = 113.3 + 142.9 | 256.3 | 3 条, util 1.003 |
  | PIER13 | 132.4 + (A13: 环46.0+带81.3)/2 + (A14: 环40.5+带64.6)/2 = 132.4 + 116.2 | 248.7 | 3 条, util 1.009 |

  **无双重计数证明**: 每孔 W_top 在其两墩各记 ½, 全桥 Σ=1911.9=环+带总重
  (每孔恰计一次); 台侧半跨计入桥台不计本门 16 墩。与审查者 util 1.415 的
  差异: 其隐含 added(PIER08 口径)=68.1 = 本实现 153.4 的 0.44×, 即其探针
  按**约 ¼ 跨份额**记反力(或仅计部分带重); 本实现按**经典对称拱每
  Springing 半跨反力(W/2)** —— 两者皆系读法, 本实现为 R2 裁决字面
  ("两孔 RING+R5a 带竖向反力"每 springing 半重), 且总量 1911.9 与审查者
  自报"全桥环+带 1912"逐位同; 分歧不改变"边际"定性(1.415 与 1.009 均
  >1 但同数量级)。
- **δ/μ0 敏感性轴**(逐孔串行, 最小推力读数, V 已含孔顶反力; red/192):

| 图式参数 | δ=0, μ0=0(现行保守缺省) | δ=0.25B, μ0=0 | δ=0, μ0=0.5 | δ=0.25B, μ0=0.5 |
|---|---|---|---|---|
| 红 / worst util | **6 / 1.009** | 0 / 0.241 | 0 / 0.661 | 0 / 0.000 |

  δ 模型: 主导推力孔的竖向反力作用于其 springing(偏心 δ·B)取对倾恢复矩;
  μ0 模型: 驻架孔按 μ0 份额回馈其 Hmin。**结论(R3 措辞, 按 §9.2 分解再
  降半档)**: 修正 V 后串行仍违例但仅边际(6/192, util 1.009); 任何读数/
  图式微扰即翻绿 —— **本门对串行只能给"临界"判定, 不能给"不可行"**;
  "逐孔串行不可行"是本门静力图式(δ=0/μ0=0)的临界定, 非史实证明。
- 头条最终形态(统一措辞): **本门不能证明任何卸架序可行; 只能证明 ——
  所有 H 读数下、单侧满推力无对冲的时刻都超核 ⇒ 对称同步是安全族,
  错峰串行取决于未建模的架式细节(架式刚度/楔座偏心/驻架回馈),
  本门对后者至多给"临界"判定。**

### 9.3 R3 史实标签撤回(C2)

- 全仓 grep "史实" 在 T7 报告/sequencer 注释/g3 docstring/test 的出现处
  **清零**(本报告 §0-§8 同步改述); 卸架序相关表述一律 **[工程推断·
  非史料]**, 理由: C:A3 原文"则例无工序教科书, 序列细节靠通例+实物反推"
  (construction_history.md §三), 且本桥施工档案在 §五 未找到清单 ——
  两轮"史实"标签(先逐孔串行 §0/§5, 后全桥同波 §8.2)均无 G0 锚, 撤回。
- 规则号勘误: "R5 卸架顺序"→**R4/R6**(R5a/R5b=肩/背胞时序; 卸架序在
  R4 λ 全阶 + R6 frontier 组合表); 报告/sequencer 注释同步。
- sequencer 波2 注释已标注 [工程推断·非史料] 与裁决出处; "对称同步
  卸落"降格为**工法假说的安全族成员**(本门只证其不违例)。

### 9.4 R4+WARNING 清单落地

| # | 项 | 落地 |
|---|---|---|
| 1 | dm 逐孔回归钉 | `test_real_dm_per_hole_counts_match_top_level`(per-hole==Counter(dm by zone) ∧ sum==顶层 29) |
| 2 | snapshots λ fail-closed | 非法 load_lambda 即 raise(与 ④ `_lam_advance` 同语义, 去顺序耦合); DECENTER_START 显式归零 λ(重建架再卸路径良定, 词表不支持二次落架已注释) |
| 3 | λ 三常数跨文件钉 | `test_lambda_grid_constants_cross_file_pinned`(events.LAMBDA_GRID=4 / sequencer.LAMBDA_LADDER / g3.LAMBDA_GRID_STEP 互证) |
| 4 | dstart 潜伏路径 | 见 #2(注释+显式归零) |
| 5 | 记号统一 | 全文 "x/192" 一律 = **违例组合数/评估组合数**(红组合; 违例**条数**≈2×, 双指标各计一条, 文中凡"违例 159 条"处均已标注条数口径); §8.3 "(02,03)..+01 solo 38" 勘误: 该格为方法敏感值(审查复现 43/1.171, 差 5 疑 solo 放置位次), **V 修复后该轴重测=6/192 worst 0.521**(§9.2), pre-V 值不再作为结论引用 |
| 6 | 双建模输入 fail-closed + sidecar 重建半段 | `_double_model_ratios` 在 rbo_ids=None 且 excluded_ids.json 缺失 → SequencerError(静默空集曾产出 sha 70c90849 的"另一种合法"账); 微账测试全部显式 dm_ids=[](去 untracked 依赖); 新增 `test_sidecar_clean_clone_rebuild_matches_recorded`(git archive HEAD 干净克隆 + 拷 untracked 真账输入 + 重跑 sequencer → sha256==sidecar 记录 1cefc071, 实跑通过) |
| 7 | ratio 有牙性声明 | 本桥最小推力读数下 ratio 最松 **3.438 ≫ 1.5** —— 真账唯一有牙的判据是**中三分核距**; 1.5 裕度在本桥为装饰性第二读数(保留输出, 供他桥参数域) |
| 8 | FILL 覆盖缺口 | 已知限制: ④门只评 DECENTERING 事件, ADD_FILL 填筑期的不平衡(填筑偏载)不在本门 —— 记 P3 前补, 不扩本轮 |

### 9.5 验收账

- 全量 `pytest tests -q`: **451 passed, 零红**(448 + 3: λ 三常数跨文件钉 /
  dm 逐孔回归钉 / sidecar 干净克隆重建==记录钉)。
- 真账三门 ok=True 不回退(gate_dag / gate_stress 17/17 / gate_imbalance
  0 红 + `viol_uniform_hmax=1` 条件性在册); 串行(修正 V 后)仍红
  (6 组合, util 1.009)+ 条件化措辞; α/N/δ/μ0 四轴表全部本轮自测复现;
  "史实"零残留(grep 证明); 判据冻结项零触碰。
- Commit: `fix(e30): P2-T7b主张条件化+V完整性修复+史实标签撤回(出口审查4CRITICAL)`。
