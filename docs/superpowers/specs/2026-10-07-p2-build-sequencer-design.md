# Spec#2（P2）：建造序列器 sequencer + G3 力学门
状态：草案 v1（自审×3 → GPT 评审 → 主控裁决）。上游：M22 路线图；输入=G1 封版几何+P1 ledger+G0 史料库。

## 0. 已定决策（用户拍板 2026-10-07）
- 券架=**结构可信型**：按清式木作逻辑程序化生成（排架柱+楞木+弧形券胎板+卸架楔），每孔一副随跨变化；**不入打印账**（ledger 中 evidence=inferred_construction, print.excluded=True）
- G3=**①③④实做+②规则化**：时窗支撑 DAG、落架压力线、多孔不平衡推力极限平衡全实现；逐 stage 接触力 LP 用"对称砌筑+合龙前不落架"规则代替（μ 无史料值，LP 成本 5935×百 stage 不值）

## 1. 目标与非目标
**目标**：把 5935 石 + 券架排成一份**史实可挂账、力学可验证**的建造序列（sequence.json），供 P3 动画直接消费（stage 整数即 GN 显隐键），并输出 G3 报告作为 P3 开工门。
**非目标**：动画镜头（P3）、灰浆凝结材料模拟（规则化）、围堰/抽水水下工程（旁白带过，无几何）。

## 2. 工序规则（每条挂史料编号，见 refs/construction_history.md）
| 规则 | 内容 | 依据 |
|---|---|---|
| R0 冬期开工 | 叙事层：stages 分组标注"乘冬农务暇"（不强制几何） | A:御制诗 |
| R1 墩身自下而上 | 每墩列带 z 升序；丁顺层间依赖 | C:B组 砌体通则 |
| R2 券架先行 | 每孔 RING 石依赖该孔 centering 对象已立（support_edges type=centering 时窗 [立架,合龙后落架]） | B14 孔庆普实证：无架拱圈不能自持 |
| R3 对称砌筑 | 同孔券石按"离龙门石远→近"交替左右排布（abutment 侧起砌） | B14 + C:B组"对合龙口"语义正字（龙门石居中） |
| R4 合龙→凝→落架 | 龙门石位=该孔 RING 末件；落架 stage = max(合龙 stage + cure_stages, 相邻孔合龙约束)（cure_stages=全局 stage 数差，默认 3，敏感性见 §4）；卸架楔动作在落架 stage | C:A2 龙门石名目 + B14 |
| R5 拱肩后置 | 该孔 SPANDREL/BACK/CORE 依赖该孔落架完成（券带石例外：见 §4 环-肩咬合） | 拱架占用空间约束+通例 |
| R6 孔序由中向外 | 起拱孔序 ARCH09→两侧交替（灵鼍偃月叙事+平衡施工） | [推断] 主控签署：无本桥直接记载，理由=④不平衡推力的保守构造+清工法通例 |
| R7 桥面→栏→狮→兽 | PAVING→RAIL/POST→CARVE 全局后置 | C:A2 名目层级 |
每 stage 输出 `evidence` 字段=规则编号；旁白红线 lint 表（禁词清单来自 G0 §三）作为 CI 检查。

## 3. 组件
| 文件 | 职责 |
|---|---|
| `3d/centering.py` | 券架生成器：输入孔参数（span/ring_t/lift/springer），输出木作对象（排架柱间距 1.2m [推断]、楞木、券胎板沿 extrados+30mm 工作面、卸架楔对）；bmesh 局部网格+ledger 注册（role=CENTER, family=wood-<arch>） |
| `3d/sequencer.py` | 规则引擎：ledger+券架 → 拓扑排序 → sequence.json（{id, stage:int, t_order, depends_on[], centering_id, evidence}）；stage 数目标 200-600（P3 变速叙事的粒度基础） |
| `3d/g3_check.py` | ①DAG：时窗支撑图无环+每石就位时其支撑活跃（悬空=红）③落架瞬间：该孔环按刚块链做压力线检验（funicular polygon 在环带内，纯 python）④每 stage 每墩：已合龙未拆架孔对墩的单侧推力极限平衡 M_res≥1.5·M_unb（墩自重+已砌上方压重 vs 楔推力上界，公式在报告写明）②=R2/R3/R4 规则本身 |
| 输出 | `3d/out/sequence.json`、`3d/out/g3_report.json`、`3d/out/narration_beats.md`（stage→史料编号→旁白素材表） |

## 4. 已知难点与裁决
- **环-肩咬合石**（RING↔SPANDREL dedup 475 裁片）：被裁 SPANDREL 依赖其 RING 已就位（先砌环后砌肩的自然序），sequencer 从 support_edges 的 dedup 记录直接推依赖；裁片 parent_ids 谱系（T9 run 升格）已备好
- **CORE 满墙胞**：与环/肩同 stage 带依赖（先环后胞），落架前禁砌（占架空间）
- **④公式保守性**：楔推力取"半环重×cot(合龙角)"上界，不精算——报告标[工程近似]，G3 只拒"明显失衡"序列（如相邻孔跳孔落架）
- **cure_stages 参数**：灰浆凝结无本桥史料（B15 糯米灰浆性质通例）→ 参数化，默认 3 个全局 stage；语义=该孔落架不早于合龙后第 3 个全局 stage（相邻孔施工在此期间正常推进）；敏感性 1/3/6 记报告

## 5. 验收
- sequence.json：5935 石+17 副券架全覆盖、无环、stage 单调；validate_ledger 兼容（CENTER role 词法扩展进 _ID_RE）
- g3_report：①③ 全 PASS + 每条检验的负控（人为：悬空石/提前落架/跳孔落架/逆对称砌筑 四组注入必红）
- 旁白 lint：红线禁词 0 命中
- 全门：e30 239+新增 / bridge3d 312 / L2 / 33 断言 / freeze 逐位（P2 零触本体）
- 叙事抽验：中央孔一孔的完整 stage 序列（立架→17 券石对称→龙门石→凝→落架→拱肩）人工对 G0 编号逐条可查

## 6. 下游接口
- P3 消费：sequence.json（stage→GN attribute 驱动显隐/飞入序）+ 券架对象（显隐+卸架动画）+ narration_beats.md
- P4 消费：无（券架不打印，print.excluded 已标）
- 门：G3 PASS = P3 开工前置
