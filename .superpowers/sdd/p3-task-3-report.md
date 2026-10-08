# P3-T3 任务报告：film_verify.py 独立 validator 双实现对拍

- **commit**: `e20d92d` `feat(e30): P3-T3 独立validator双实现对拍(前缀和算法+import隔离钉)`
- **文件**: `3d/film/film_verify.py`(389 行)、`tests/test_p3_verify.py`(124 行)，仅此两文件入 commit
- **日期**: 2026-10-08；Python 3.9.6；blender-free；P2/P3 工件零修改只读
- **语义规格**: 唯一来源 p3-task-2-report §2 判定规则全表(=film_state docstring §1-6)；实现未读 film_state 判定代码路径，算法按本任务 brief 钉的「stage 前缀和表+逐 stage 重算」独立重造

## 1. 接口落地（签名与 brief 钉死一致）

- `expected_state(frame, pace_path, seq_path) -> dict`：**收路径不收 dict**（与 film_state 收 dict 的签名刻意不同，缓存按 abspath+mtime_ns+size 键控）；返回恰 6 键 {stage, event_cursor, visible(frozenset), centering_up(frozenset), wedge_lambda(dict), phase(str)}，测试对每帧钉键面+容器类型同构
- 边界契约同参照：frame ∉ [0, total_frames) → IndexError（-1 / 7200 / 1e9 三端实测）
- CLI：`python3 3d/film/film_verify.py --pace ... --sequence ... [--stride N] [--json]`；**--stride 默认 1=全帧对拍**；退出码 0=全帧一致 / 1=对拍违例（报告首违例帧+差异键+两实现截断值）/ 2=validator 报缺
- 词表单源 `from events import DECENTERING_TYPES, EVENT_TYPES` + import 期自检两事件名（film_state 同款纪律）；**本模块不 import film_state**——import 隔离由子进程探针钉（见 §3）
- film_state 的 import 只出现在 CLI 对拍路径（`main()` 内惰性 import，作参照物），模块导入路径零依赖

## 2. 算法独立性对照表（对拍的前提：同语义、异算法）

| 环节 | film_state（T2） | film_verify（T3，本实现） |
|---|---|---|
| 帧→stage | starts 有序数组 `bisect_right(starts, f)-1` | **帧前缀展开直接寻址表**：逐 stage 把 frames 份自身下标 append 进表，O(1) 查帧，**不读 start 字段**（用 Σframes==total_frames 前缀和自洽门替代） |
| 事件定位 | 事件按 seq 排序 + 全局 bisect cursor | **seq 前缀展开表分桶**：stage event_range 逐段扩展 seq2stage 直接寻址，事件落入所属 stage 桶，无全局排序、无 bisect |
| 状态推进 | 每次查询按 cursor 全局扫描事件流 | **逐 stage 重算的 stage 前缀和表**：visible/erected/cleared/λ/phase 全在 stage 边界自上一快照增量重算（整拍语义：状态只在 stage 边界变），查询=表项重组 6 键 |
| wedge_lambda | 每查询逐孔判 | stage 边界对 touched 孔重算，dict 写时复制快照不可变 |
| 完整性防线 | 无（缺事件静默吞掉，visible 悄悄少石） | **恰覆盖计数门**：stage range 无缝恰覆盖 [1..N]、每桶计数==range 宽——缺/多/重 seq 一律 ValueError 报缺 |

## 3. TDD 过程与对拍战果

- 4 支测试（三支计划钉 + import 隔离探针）全绿；`tests/test_p3_verify.py::test_import_isolation_probe` 三层钉：①子进程 `import film_verify` → `'film_state' not in sys.modules`（exit 3 兜底）；②**探针自证有效**（阴性对照：同环境 import film_state 必在 sys.modules，防探针静默失效）；③`expected_state` 源码级不含 film_state 字样（inspect.getsource 断言）
- **双实现对拍首跑即抓到我一处语义分歧**（§4.1：帧 0 wedge_lambda `{}` vs 17 孔全 0.0）——这正是「两实现同错=互相失守」反面的直接证据：独立算法暴露了规格文本的含糊点
- 负控篡改测（真账只读，副本删中段 PLACE_STONE）：validator ValueError 报缺 ✅；同账下参照实现**不报错**、末帧 visible 悄悄少一块石（测试内钉死该事实）——证明「单靠双实现等值」在删事件场景会静默同错，报缺门是必要的独立防线
- CLI 三退出码实测：stride-7 全绿 exit 0；--json 机读字段 compared/equal/first_violation/validator_error；篡改副本 exit 2 报「stage #407 声称覆盖至 seq=4118，但事件总数仅 4117(疑缺事件)」

## 4. 语义分歧清单（对拍全绿后仍须留给 T5 的接口精度）

1. **规则 5 key universe 的时点含糊（对拍实抓）**：规格写「key universe = {e.hole | etype∈DECENTERING_TYPES}」但未写 universe 何时生效。我的第一版按「孔随其首个落架事件入场」实现 → 帧 0 得 `{}`；参照实现是**全宇宙开局即在场**（帧 0 时 17 孔全 0.0）。已裁定对齐参照并在 docstring 钉死「全宇宙键开局即 0.0」。T5 若自写任何 λ 消费侧，须按「键面恒为全宇宙」理解，勿按事件渐显理解。
2. **WEDGE_RELEASE 的 load_lambda=null 未定义**：真账 68 条 WEDGE_RELEASE 零 null（四档 0.25/0.5/0.75/1.0），但规格未规定 null 行为。两实现都按字段透传（null 会流入 λ dict）。T5 驱动楔石位移前应显式防 None；若 P2 未来发射 null-λ 楔事件，属词表/schema 演进，须先改规格。
3. **报缺门是 validator 的加法**（参照实现无此防线）：真账输入下零行为差；事件表任何增删必红。这不是语义分歧而是防线差异，列入防「T5 把 sequence.json 当可变中间物改写」——一改即红是设计行为。
4. **帧→stage 数据源不同**：我用 Σframes 前缀、参照用 start 字段。T1 契约下二者恒一致（真账 Σ=7200 实测）；若 pace 的 start 字段被单独篡改而 frames/total 自洽，表现为**对拍违例**（exit 1）而非报缺（exit 2）——属预期分工，T5 读报告时按违例帧定位即可。
5. **立架两指针扫描依赖 cursor 随 stage 下标单调**：恰覆盖门保证 range 无缝连续 → 单调成立；病态非连续 range 会被门先拒。规则 4 的「event_range[1] ≤ cursor」逐立架扫描在其前提破坏时两实现等价性不再由构造保证。
6. **零宽 stage（frames<1）拒收**：本实现报 ValueError（pace 契约外，真账 min frames=2）；参照的 bisect 语义可容忍零宽。合成账若引入零宽 stage，对拍会以报缺形式分歧——非真账风险，记录在案。
7. **CLI 形态**：brief 钉的 `[--stride N] [--json]` 落地；计划稿 `--sample 408+100` 未采纳（brief 后至为准）。--stride 默认 1（全帧，7.8s 可承受），抽样对拍请显式给 7。

## 5. 真账验证与性能自测（3d/out 只读）

- **stride-1 全帧对拍：7200/7200 帧逐键一致**（CLI 实测 7.83s，含参照实现 7200 帧全扫）
- 分侧计时（stride-7，1029 帧）：参照 0.992s / 本实现 0.038s（**×26.0**）
- 本实现性能自测：**前缀和表冷构建 15.7ms**（408 stage + 4118 事件）；**全 7200 帧连扫 0.263s = 0.037ms/帧**（参照 T2 实测 0.95ms/帧）。T5 逐帧驱动若改用本实现查询侧，7s 量级预算可再压缩，但**驱动单源纪律仍须用 film_state**，本模块只作 validator
- 幻影钉（双实现分别断言）：末帧 visible == PLACE_STONE 日程集 3931（不多不少）∧ 与 5935 石账 − 3931 = **2004** 块幻影交集空；universe/scheduled/phantom 三口径数字全钉进测试

## 6. 全量 pytest 分片明细（前台逐片，P4 红窗口径）

**分母以 --collect-only 实测为准：492 collected**（命令 `pytest tests/ --collect-only -q --ignore=tests/test_p4_section.py`，实测于本任务分片前）。逐片结果：

| 片 | 文件 | 结果 | 耗时 |
|---|---|---|---|
| 1 | facts / freeze_manifest / l1_body / no_literals / p1_export / p1_families | 89 passed | 0.3s |
| 2a | p1_ledger / p1_masonry2 / p1_printcheck / register | 89 passed | 0.6s |
| 2b | p1_scene / p1_slice | 65 passed | 109.2s |
| 3 | p2_centering / p2_events / p2_geom_math / p2_ledger_v2 / p2_sequencer | 160 passed | 74.5s |
| 4 | p2_full / p2_g3_dag / p2_g3_imbalance / p2_g3_thrust | 71 passed | 123.6s |
| 5 | p3_pace / p3_state(8) / **p3_verify(4)** / p4_scale | 18 passed | 2.4s |

**合计 492 passed / 0 红**（= P2 末基线 480 + T2 的 8 + 本任务 4，口径自洽）。

- **P4 红窗留痕（沿 T1/T2 先例）**：`tests/test_p4_section.py` 本轮 collect-only **已干净**（5 tests collected，section_pack 模块已由 P4 线落地），红窗已关；但仍按先例 `--ignore` 收全量——P4T2Section 同胞 agent 仍在运行演进其文件，并发窗口内跑对方在途用例会收进幻影红。全收口径为 492+5=**497**，P4 线冻结后由主控复核。
- **流程事故留痕**：片 2b/3/4 三度被 harness 转 >55s 后台通道（T2 报告同款现象）；当日通道实测仍全速（2b 109s≈T2 的 107s、片 4 124s≈T2 的 122s），结果照收未重跑。2b 曾因杀首跑产生一次重复执行，两轮均 65 passed 互相印证。
- 单条全量命令会进后台通道，故沿 T2 分片口径；各片命令与数字如上可复现。

## 7. 给 T5 的交接注记

1. 驱动单源纪律不变：film_render 逐帧消费**只用 film_state**；film_verify 是独立审计面，二者互不 import（探针已钉）。
2. λ 消费（楔石位移档）注意 §4.1/§4.2：键面恒为全宇宙（无落架事件的账为空 dict）；load_lambda 理论可为 null，驱动侧显式防。
3. 渲染后抽查可用本模块单帧查询做三方对账：`expected_state(f, PACE, SEQ)` vs `film_state.state_at_frame(...)` vs selection.jsonl 驱动记录——三方同错概率被算法独立性压到最低。
4. sequence.json 是 validator 的恰覆盖对账对象：任何工具不得增删其 events（报缺门必红）；pace_writeback（T7）只准经 writeback 通道改 pace.json。
