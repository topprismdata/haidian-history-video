# P3 逐石建造动画 build-film 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 P2 的 408-stage 建造序列渲染成 4 分钟 1080p30 逐石建造动画（Blender EEVEE 画面 + Remotion 合成旁白），状态一致性可机验（G4 门）。

**Architecture:** 纯 python 帧→状态机（film_state.py，blender-free 可测）+ pace.json 单一节奏源（渲染器/验收器/Remotion 三方只读，唯一写通道 pace_writeback）+ Blender 无头驱动按帧写 GN 域属性出帧 + 独立 validator 双实现对拍 + Remotion 挂 TTS/字幕。P2 工件与代码零修改。

**Tech Stack:** Python 3.9.6（stdlib+numpy，blender-free 测试）、bpy（仅渲染驱动）、Remotion+TS（合成）、mlx TTS（既有）。

## Global Constraints

- Python 3.9.6：`Optional[X]`、无 match、无 walrus 于 3.9 不兼容处（walrus 3.8+ 可用，仓内风格禁之则从仓）
- **P2 工件只读**：sequence.json(1cefc071)/event_ledger(a908f60d)/ledger_sequenced(f7e26c2f)/beats(d19d037d)/g3_report(content 7188388d)；P2 代码（centering/sequencer/g3_check/narration 判据面）零修改，只 import
- pace.json 唯一写入通道 = `pace_writeback.py`；其余消费者只读；**禁 Remotion 侧自算时间轴**
- 新常数（wedge_drop/堆场锚点/剪影位）入 P3 自有 `film_geometry.py`，标 `[工程参数·敏感性]`/`[设计选择]`
- 渲染绿灯门：Task 1-7 全绿 + 30 帧试渲预算表**用户签字**前禁夜跑
- 长命令前台跑（本机后台通道限流 ~2.4% CPU 已知问题）
- 中文 commit `feat(e30): P3-Tn ...`；全量 pytest 零红为每任务收尾；sidecar 纪律：pace.json 与交付工件入 `3d/refs/artifact_sha256.txt`
- 旁白/题卡文案必过 `narration.py::narration_lint`；四铁律口径不得弱化

## 文件结构

| 文件 | 职责 | 新建/改 |
|---|---|---|
| `3d/film_state.py` | pace 加载、frame→stage、state_at_frame（在场集/券架/λ） | 新建 |
| `3d/film_geometry.py` | wedge_drop、堆场/吊运锚点、剪影位、相机位表 [工程参数] | 新建 |
| `3d/pace_build.py` | 由 sequence+权重规则生成初版 pace.json | 新建 |
| `3d/pace_writeback.py` | 音频秒数→pad_frames 唯一回写通道 | 新建 |
| `3d/film_render.py` | bpy 无头驱动：逐帧写 GN 属性+相机+出 PNG+选择记录 JSONL | 新建 |
| `3d/film_verify.py` | 独立 frame→stage 重实现 + 期望集 vs 驱动记录对拍 CLI | 新建 |
| `3d/film_silhouette.py` | 剪影 SVG 生成（证据头注）+ 材质组 collection 名规范 | 新建 |
| `tests/test_p3_state.py` `test_p3_pace.py` `test_p3_verify.py` `test_p3_render_smoke.py` `test_p3_silhouette.py` `test_p3_script_lint.py` | 各任务 TDD | 新建 |
| `3d/out/film/pace.json` | 节奏源（入 sidecar） | 产物 |
| `src/e30film/`（video-projects 根 Remotion） | 合成工程 | 新建 |

---

### Task 1: pace.json 生成器（pace_build.py）

**Files:** Create `3d/film/pace_build.py`（放 `3d/film/` 子包，新建 `__init__.py`）; Test `tests/test_p3_pace.py`

**Interfaces:**
- Consumes: `3d/out/sequence.json`（stages 列表，每项含 id/事件区间）
- Produces: `pace.json` = `{"fps":30,"total_frames":N,"stages":[{"id":"S001","first_event":1,"last_event":10,"frames":18,"pad_frames":0,"start":0,"end":18}...]}`；`load_pace(path)->dict`、`stage_at_frame(pace,f)->int`（后续任务共用，定义在 `film_state.py`，本任务先建 pace_build 与 schema 校验）

- [ ] **Step 1: 失败测试**——schema 校验 + 守恒 + 目标时长

```python
def test_pace_build_schema_and_conservation():
    import json, subprocess, sys, os
    out = "/tmp/p3test/pace.json"; os.makedirs("/tmp/p3test", exist_ok=True)
    subprocess.run([sys.executable, "3d/film/pace_build.py",
                    "--sequence", "3d/out/sequence.json",
                    "--target-sec", "240", "--out", out], check=True, cwd=REPO3D)
    p = json.load(open(out))
    assert p["fps"] == 30
    assert len(p["stages"]) == 408
    # 守恒: start/end 连续无缝, 末帧==total_frames
    assert p["stages"][0]["start"] == 0
    for a, b in zip(p["stages"], p["stages"][1:]):
        assert a["end"] == b["start"]
    assert p["stages"][-1]["end"] == p["total_frames"]
    # 时长在 240s ±2%（缩放后）
    assert abs(p["total_frames"] - 7200) <= 144
    # 单调: frames>=1
    assert all(s["frames"] >= 1 for s in p["stages"])
```

- [ ] **Step 2: 跑到红**（`ModuleNotFoundError`/文件不存在）
- [ ] **Step 3: 实现 pace_build.py**——权重规则（完整表）：stage 权重 w = 事件数基础 1/事件，另加类型加成：`CLOSE_RING +40`、`WEDGE_RELEASE +4`、`CENTER_ERECT +6`、`DECENTER_START/CLEAR +8`、`R7 组 +3`、首孔 ARCH01 全部 ×2（教学段）、末段 BRIDGE_DONE +60。frames_raw = w；全表缩放到 target×fps（最大余数法保证 Σ 精确），pad_frames 初始 0。CLI 参数如上；输出含 `"generated_by":"pace_build"`, `"source_sha":<sequence.json sha256 前 8>`。
- [ ] **Step 4: 绿 + 附加测**：`test_pace_scale_exact`（Σframes==total_frames 对 3 个不同 target-sec）；`test_pace_close_ring_boost`（CLOSE_RING stage 的 frames ≥ 同事件数普通 stage 的 2 倍）
- [ ] **Step 5: commit** `feat(e30): P3-T1 pace生成器(单一节奏源+最大余数精确缩放)`

### Task 2: film_state.py 帧→状态机

**Files:** Create `3d/film/film_state.py`; Test `tests/test_p3_state.py`

**Interfaces:**
- Consumes: pace.json（Task 1 格式）、sequence.json、ledger_sequenced.json
- Produces（签名钉死）：
  - `load_pace(path) -> dict`；`stage_at_frame(pace, f) -> int`（越界 raise `IndexError`）
  - `state_at_frame(pace, sequence, f) -> dict`，返回 `{"stage":int,"event_cursor":int,"visible":frozenset[str],"centering_up":frozenset[str],"wedge_lambda":dict[str,float],"phase":str}`
  - `visible` 语义：PLACE_STONE 事件 ≤ event_cursor 的石 id 集；`centering_up`：已 CENTER_ERECT 未 CLEAR 的 CEN-ARCHxx；`wedge_lambda[arch]`：该孔当前 WEDGE_RELEASE 档 λ（未 START=0.0，已 CLEAR=1.0）
  - 幻影 2004 永不进 visible（sequence 里本无其事件，测试钉）

- [ ] **Step 1: 失败测试**（合成 6-stage mini sequence，逐帧断言）

```python
def test_state_at_frame_synthetic():
    pace = {"fps":30,"total_frames":60,"stages":[
        {"id":f"S{i:03d}","first_event":i*5+1,"last_event":i*5+5,
         "frames":10,"pad_frames":0,"start":i*10,"end":i*10+10} for i in range(6)]}
    seq = {"events":[{"seq":i+1,"etype":"PLACE_STONE","stone":f"ARCH01.X.{i:02d}"} for i in range(30)]}
    s0 = state_at_frame(pace, seq, 0)      # stage0: 事件1..5 → 前5石
    assert len(s0["visible"]) == 5 and s0["stage"] == 0
    s59 = state_at_frame(pace, seq, 59)    # 末帧 = 30 石全在
    assert len(s59["visible"]) == 30 and s59["event_cursor"] == 30
```

另两支：`test_stage_at_frame_boundaries`（每 stage start 帧归属本 stage、total_frames raise）；`test_wedge_lambda_ladder`（合成 DECENTER 事件流：START=0→四档 WEDGE λ=.25/.5/.75/1→CLEAR 后恒 1）。

- [ ] **Step 2 红 → Step 3 实现**（纯函数，事件按 seq 排序 bisect；PLACE_STONE/DECENTER 词表从 `3d/events.py` import 常量，禁字面复制词表） **→ Step 4 绿 → Step 5 commit** `feat(e30): P3-T2 帧状态机(在场集/券架/λ档纯函数)`

### Task 3: 真账接线 + 独立 validator 双实现对拍

**Files:** Create `3d/film/film_verify.py`; Test `tests/test_p3_verify.py`

**Interfaces:** Consumes Task 1/2 产物与真账三工件；Produces `expected_state(frame, pace_path, seq_path) -> dict`（**独立实现**：从事件表逐 stage 前缀和重算，不 import film_state）+ CLI `python3 3d/film/film_verify.py --pace ... --sequence ... --sample 408+100` 输出 JSON 对拍报告。

- [ ] **Step 1 失败测试**：

```python
def test_dual_impl_frame_by_frame_real():
    # 真账 pace(Task1 产物)+全帧 0..total-1 双实现逐帧等值
    a = json.load(open(PACE)); s = json.load(open(SEQ))
    for f in range(0, a["total_frames"], 7):   # 每7帧抽样=全 stage 覆盖
        assert film_state.state_at_frame(a, s, f) == \
               film_verify.expected_state(f, PACE, SEQ), f
def test_phantom_never_visible_real():
    # 末帧 visible == 入日程集 3931, 且与 in_void 2004 交集空
    ...
def test_verify_negative_tamper(tmp_path):
    # 副本: 删一条 PLACE_STONE 事件 → 双实现必不一致(或 validator 报缺), 不许静默同错
    ...
```

- [ ] **Step 2 红 → Step 3 实现 film_verify（不同算法：stage 前缀和表+二分）→ Step 4 绿 → Step 5 commit** `feat(e30): P3-T3 双实现状态对拍+幻影缺席钉`

### Task 4: film_geometry.py（渲染侧参数单源）

**Files:** Create `3d/film/film_geometry.py`; Test `tests/test_p3_state.py`（追加）

**Interfaces:** Produces `WEDGE_DROP_M=0.04`（模型米，[工程参数·敏感性]）、`yard_anchor(stone_id)->tuple`（堆场分区：按 zone+族散列到岸边 4 列网格）、`lift_anchor(stone_id)->tuple`（吊运过路点=就位位上方 deck+2m）、`SILHOUETTE_SLOTS`（剪影站位表，含证据号字段）、`CAMERA_TRACKS`（侧视/鸟瞰/特写机位，段→机位映射）。全部纯函数/常量，docstring 标 [设计选择]。

- [ ] **Step 1 失败测试**：`test_anchors_deterministic`（同 id 两次调用逐位同）；`test_yield_no_overlap_with_body`（yard/lift 锚点 y 向在 hw+0.5m 外或 deck 上方 2m——桥体净空检查，用 facts.pier_w/hw 反查）；`test_wedge_drop_positive_small`（0<WEDGE_DROP_M<0.1）
- [ ] **Step 2 红 → Step 3 实现 → Step 4 绿 → Step 5 commit** `feat(e30): P3-T4 渲染侧参数单源(锚点/λ下沉/机位)`

### Task 5: Blender 无头驱动（film_render.py）+ 3 帧冒烟

**Files:** Create `3d/film/film_render.py`; Test `tests/test_p3_render_smoke.py`

**Interfaces:** Consumes e30_bridge.blend（build_scene2 产物，**只读打开另存 out/film/work.blend**）、Task 2 状态机、Task 4 几何；Produces 每帧：GN 域属性 `vis_idx`(int) 写入实例集（石按 placement_event 全局序排列的实例索引=visible 数）+ 券架 collection 显隐 + 楔石位移 + 相机位 + **选择记录 JSONL 行** `{"frame":f,"selected":[ids],"driver":"film_render"}`；CLI `--frames a-b --out out/film/frames/`。

- [ ] **Step 1 失败测试（blender 门控）**：

```python
@pytest.mark.skipif(not HAS_BLENDER, reason="blender-free CI")
def test_render_3frames_smoke(tmp_path):
    # 取 stage 边界 3 帧(首/中/末), 跑 film_render --frames 单帧×3
    rc = run_blender(["3d/film/film_render.py", "--frames", "0-0", "--out", str(tmp_path)])
    assert rc == 0 and (tmp_path/"f000000.png").exists()
    rec = json.loads((tmp_path/"selection.jsonl").read_text().splitlines()[0])
    import sys; sys.path.insert(0,"3d")
    import film_state as FS
    want = FS.state_at_frame(PACE, SEQ, 0)["visible"]
    assert set(rec["selected"]) == set(want)   # 驱动记录==状态机
```

- [ ] **Step 2 红 → Step 3 实现**：bpy 打开 blend→对每帧：`state_at_frame`→实例几何集合按全局 event 序排序→`vis_idx=len(visible)`（GN delete-by-index 阈值）→楔石物体 `delta_z = -λ*WEDGE_DROP_M`→相机按 `CAMERA_TRACKS[stage]`→`render.write_still`。**驱动不内嵌判据**：在场判定只 import film_state（单源），validator 独立。→ **Step 4 绿（本机 blender 在位，真跑）** → **Step 5 commit** `feat(e30): P3-T5 无头渲染驱动(GN阈值显隐+选择记录JSONL)`

### Task 6: 剪影资产 + 文案 lint CI

**Files:** Create `3d/film/film_silhouette.py`、`3d/film/narration_script.md`（占位结构，正文由主控走 ChatGPT 流程产出后入库）; Test `tests/test_p3_silhouette.py`、`tests/test_p3_script_lint.py`

- [ ] **Step 1 失败测试**：`test_silhouette_svg_evidence_header`（每个生成的 SVG 首行注释含 `evidence:` 号或 `[设计选择]`，无出处即 raise）；`test_script_passes_lint`（narration_script.md 全文过 `narration_lint`，红则测试红）；`test_script_carries_four_iron_rules`（四条铁律关键词逐条在文中可指认：裸环自承/模型族/工程推断非史料/对称同步）
- [ ] **Step 2 红 → Step 3 实现**：SVG 生成=参数化人形轮廓（挑杆/杠杆/剁斧三姿态，纯 path，无外部素材）；script 骨架=按 pace 段填 beats 素材（文案正文由主控人工经 ChatGPT 流程回填，任务内先落结构+lint 通过的最小真文案：开场/首孔教学/合龙/落架高潮/桥成五段） → **Step 4 绿 → Step 5 commit** `feat(e30): P3-T6 剪影SVG(证据头注)+旁白骨架过lint`

### Task 7: pace_writeback + Remotion 工程接线

**Files:** Create `3d/film/pace_writeback.py`、`src/e30film/`（Composition/Root 注册/Sequence 组件/音频槽）; Test `tests/test_p3_pace.py`（追加）

- [ ] **Step 1 失败测试**：`test_writeback_only_writer`（给定 `{stage:audio_sec}` 表→pad_frames 更新+start/end 重算+其余字段逐字节不变；非 writeback 路径改 pace 会被 sidecar 测拦——沿用 BLK-1 纪律）；`test_remotion_reads_pace_not_selfcompute`（src/e30film 的 TS 里 grep 禁出现自算帧逻辑标记 `fps*stage` 类常量——以配置注入为准，测试读 pace.json 断言 duration 一致）
- [ ] **Step 2 红 → Step 3 实现**（writeback：读 beats 表拍点→音频秒数入→padding 出，原子写+两连跑幂等；Remotion：复制 `src/shucun` 工程模式，Composition `E30Film`，帧图源 `out/film/frames/f%06d.png`，音频锚=pace 边界） → **Step 4 绿 → Step 5 commit** `feat(e30): P3-T7 音频回写唯一通道+Remotion接线`

### Task 8: 30 帧试渲 + 预算表 + 绿灯材料

**Files:** Create `3d/out/film/TRIAL_BUDGET.md`

- [ ] **Step 1** 选 30 帧（10 个关键 stage×3 机位）跑 film_render（前台，实测分钟/帧）
- [ ] **Step 2** TRIAL_BUDGET.md：分钟/帧×总帧数(7200)=墙钟预估、分段夜跑切点（每段 ≤6h 避休眠窗口）、断点续跑验证（杀→续→逐字节同）
- **Step 2b 终态回归（spec §3.4.3）**：末帧渲染 PNG 与 P1 建成桥出图（`3d/cmp_side.png` 同机位重渲）做非空气区 RMS 比对（阈值先测后定并记录），且末帧选择记录 == 3931 入日程集（== validator 期望）；红→停报。
- [ ] **Step 3** 全量 pytest 零红 + sidecar 登记 pace.json → commit `feat(e30): P3-T8 试渲预算表(绿灯材料, 夜跑待用户签字)`
- [ ] **Step 4 停：**把预算表交用户，**未签字禁全量渲染**（spec 渲染节奏铁律）

---

## 已知欠账（计划内如实声明，不假装没有）

- 抽帧"像素级"验收只覆盖终态回归（末帧 vs P1 出图 RMS）；建造中段像素→石 id 反读不可行（无标记），以**驱动选择记录+双实现对拍**为等价机验——选择记录由驱动写，驱动薄（只 import 状态机），信任面=Task 5 冒烟测的"记录==状态机"断言 + validator 独立重算。
- 压力线叠加特写（E3 镜 3）依赖 g3 折线导出——`pressure_line` 返回 polyline 已在接口内，Task 5 相机特写段落地；若帧内叠加复杂度过高，降级为静帧题卡（如实改 §3.2 口径需主控批）。
