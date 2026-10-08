# P3-T1 任务报告：pace.json 生成器

- **commit**: `8771447` `feat(e30): P3-T1 pace生成器(单一节奏源+最大余数精确缩放)`
- **文件**: `3d/film/__init__.py`、`3d/film/pace_build.py`、`tests/test_p3_pace.py`（+`.gitignore` 白名单块 6 行，见 §5）
- **日期**: 2026-10-08；Python 3.9.6；blender-free

## 1. sequence.json 真实字段名（供 T2/T3 消费，实测非计划稿）

sha256 = `1cefc0717528380dc8ceefecc4cc48a88d819f4f2ecad4a125999ee6c2e56e04`（前 8 `1cefc071`）。

- 顶层键：`["events", "frontier_trace", "meta", "sequence"]`
- **stage 表在 `d["sequence"]`**，408 项，每项字段（实测键面）：
  - `id`：`"S001"`…（唯一，S009=首孔合龙、S379=ARCH17 合龙、末项 S408=ARCH17.FILL）
  - `stage`：stage 名，`ARCHxx.<ROLE>` 或全局波次 `DECENTER.*`，如 `ARCH01.IMPOST.C02`、`ARCH01.CLOSE_RING`、`ARCH01.CENTER_ERECT`、`DECENTER.DSTART.WAVE`
  - `event_range`：**[first_event, last_event] 二元组**（闭区间，seq 号），不是两个独立字段
  - `centering_id`（可 null）、`depends_on`（列表）、`evidence`（如 `"C:A2"`）
- **event 表在 `d["events"]`**，4118 项，每项字段：`seq`(1..4118 连续)、`etype`、`stone_id`、`hole`、`load_lambda`、`prereq`、`affects`、`evidence`、`grade`
- 实测 etype 分布：`PLACE_STONE 3931 / HOLD_EVENT 68 / CLOSE_RING 17 / DECENTER_START 17 / WEDGE_RELEASE 68 / CENTERING_CLEAR 17`
- **落架是全局波次、不挂在孔名 stage 下**：`DECENTER.DSTART.WAVE`(1 stage 装 17 个 DECENTER_START)、`DECENTER.WEDGE.1.L25`~`WEDGE.4.L100`(各 17 个 WEDGE_RELEASE)、`DECENTER.CLEAR.WAVE`(17 个 CENTERING_CLEAR)
- T2 注意：事件按 `seq` 排序即等价 `event_range` 顺序；`stone_id` 才是石 id（序列 stage 无 stone 字段）

## 2. 权重规则落地（计划表 → 真账词表的 3 处消歧）

w = 事件数(每事件 1) + stage 级类型加成，ARCH01.* 乘 2，末段 +60：

| 计划措辞 | 真账落地 | 实测命中 |
|---|---|---|
| `CLOSE_RING +40` | stage 名 `*CLOSE_RING` | 17 |
| `WEDGE_RELEASE +4` | `.WEDGE.` | 4 |
| `CENTER_ERECT +6` | **是 stage 名后缀非 etype**（etype 无此名），`*CENTER_ERECT` | 17 |
| `DECENTER_START/CLEAR +8` | `.DSTART.` / `.CLEAR.` | 2 |
| `R7 组 +3` | `.R7.`（sequencer.py:52：真账无 PAVING/RAIL/POST/CARVE 角色 → **0 命中，规则保留**） | 0 |
| 首孔 ARCH01 ×2 | 前缀 `ARCH01.`，作用于 (事件数+加成) | 16 |
| 末段 BRIDGE_DONE +60 | **真账无 BRIDGE_DONE stage** → +60 落在末段 S408 ARCH17.FILL（`is_last or 'BRIDGE_DONE' in name`，不叠乘） | 1 |

**设计选择（已写进 pace_build docstring）**：加成为 stage 级平加、不随事件数放大——DSTART/CLEAR 波次各装 17 事件，若按事件乘会得到 +136/+136，压过 CLOSE_RING +40，颠倒"合龙=最大单点停顿"的节拍意图。

Σw=5128（Σevents=4118）；权重极值 ARCH09.FILL 240 / ARCH02.RING.bank05 1。

## 3. 算法与 schema

- **最大余数法纯整数实现**（`allocate_frames`）：先每段保底 1 帧再按 `w_i/wsum` 分配余量、最大余数取整，`Σframes == total_frames` 严格相等，无浮点；余数并列按权重降序+下标升序，结果确定。Σw=5128 < 7200，真账不会触底，但 total<n 或 wsum≤0 显式 raise。
- schema：`{fps:30, total_frames, stages:[{id,first_event,last_event,frames,pad_frames,start,end}]×408, generated_by:"pace_build", source_sha:"1cefc071"}`；`validate_pace()` 机检键面/连续无缝/Σ==total/frames≥1。
- CLI：`--sequence --target-sec [--out]`；**--out 缺省 = `<sequence 目录>/film/pace.json`**（与 cwd 无关）；原子写（tmp+os.replace）；stdout 打印对账行。

## 4. 验证（口径按 Main 裁定）

- TDD 红→绿：先 3 测全红（`can't open file ... pace_build.py`），实现后 3 passed。
- 真账 240s：`对账: total_frames=7200  Σframes=7200  一致`；产物已生成 `3d/out/film/pace.json`（未入库，sidecar 归 T8）。
  - 节奏抽检：ARCH01 教学段 375 帧=12.5s/16 段；ARCH01.CLOSE_RING 110 帧≈3.7s（1 事件普通对照 2 帧 → **55× ≥ 2×** ✓）；末段 ARCH17.FILL 116 帧。
- **全量门：477 passed 0 红（474 P2 基线 + 3 新增）**，口径 `pytest tests -q --ignore=tests/test_p4_scale.py`。
  - **ignore 原因（跨线红灯窗口）**：P4 线已按 TDD 落盘 `tests/test_p4_scale.py`（顶层 `import scale_params`）而 `3d/scale_params` 尚未存在，collection 阶段 `ModuleNotFoundError` 打断全量。已报 Main，Main 裁定：本门按 ignore 口径收，**全仓无 ignore 复验由 Main 在两线 T1 都落地后跑一次兜底**。
  - 附注：报告落盘前 `3d/scale_params.py` 已出现（P4 落地中），但 P4 测试仍处红灯窗口，维持 ignore 口径不变。
  - 执行注记：全量单命令会被 harness 自动转后台通道（已知限流），按 3 块前台跑：104+215+158=477。

## 5. 偏差申报：commit 含第 4 个文件 `.gitignore`（6 行）

本仓 `.gitignore` 是全局 `*` + 白名单制，`!3d/*.py` 只放行 3d 直属文件，**`3d/film/` 子包整体被忽略**——直接 commit 等于静默失联（P2 终审 C1 同机制：clean clone 缺文件）。按仓库逐阶段追加白名单的惯例加了：

```
!e30_shikongqiao_video/3d/film/
!e30_shikongqiao_video/3d/film/*.py
```

不加则 T2 的 `film_state.py`、T5 的 `film_render.py` 都会重演 C1。该块只涉及我方新目录，未触碰 P4 任何路径；如 Main 判定不当可 revert 该 6 行，三个主文件不受影响。

## 6. 给 T2/T3 的交接注记

1. `load_pace()/stage_at_frame()` 定义在 `3d/film/film_state.py`（T2），pace 键面以 §3 为准，勿再加字段（T7 writeback 断言其余字段逐字节不变）。
2. 全量验证若再遇 P4 红灯文件：**--ignore 并报数，勿改对方文件**（Main 裁定）。
3. 长命令前台跑；单条全量 pytest 会被 harness 自动转后台限流通道（~50× 慢），分块跑是已验证的绕法（本次 3 块）。
4. 落架事件在全局波次 stage（`DECENTER.*`），wedge_lambda 按 hole 从事件流取，别从 stage 名前缀猜孔号。
