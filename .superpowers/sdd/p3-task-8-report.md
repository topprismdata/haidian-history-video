# P3-T8 任务报告: 序幕段 + 30 帧试渲 + 预算表(绿灯材料, 夜跑待用户签字)

- Commit: `feat(e30): P3-T8 序幕段+试渲预算表(绿灯材料, 夜跑待用户签字)`(只含本任务路径)
- 分支: `e30-bridge-body`; 计划依据: `docs/superpowers/plans/2026-10-08-p3-build-film.md` Task 8 + Step 2b
- **停点**: 预算表 `3d/out/film/TRIAL_BUDGET.md` 交主控转用户, 未签字禁全量渲染

## 交付物

| 文件 | 内容 |
|---|---|
| `3d/film/pace_build.py` | `--prologue-sec S`: 前置 S000 题卡段(无事件 `(0,0)`, cursor=0), 内容段节拍零改动, total 相应增长; `generated_by="pace_build --prologue-sec 5"` 记变更; `validate_pace` 序幕合同(无事件段只许 stages[0] 恰 (0,0)) |
| `3d/film/film_verify.py` | `_seq_tables` 放行 stages[0] 的 (0,0) 无事件段(桶宽 0, 不占事件覆盖); 其余位置 (0,0) 一律红 |
| `3d/film/film_render.py` | ①`--cam-track auto\|BUILD\|DECENTER\|DONE`(缺省 auto=T5 原行为, 试渲 10 stage×3 机位用); ②内置**按 (帧,机位) 去重断点续跑**(T5b 遗留二选一选定写死); ③变体机位 PNG 加轨名后缀(正片帧名 `f%06d.png` 不变, Remotion 帧图源零影响) |
| `3d/out/film/pace.json` | 重生成: 409 stage(S000 150 帧), **total 7350**(=7200+150), generated_by 记序幕 |
| `3d/out/film/TRIAL_BUDGET.md` | 预算表(入库: .gitignore 逐条开洞, P1-T8 out/print 同机制) |
| `3d/refs/artifact_sha256.txt` | pace.json 登记(sha 29af1720…, 含生成链注记; writeback 原地补 pad 后须随写轮更新) |
| `tests/test_p3_pace.py` | 追加 `test_pace_build_prologue_s000`(S000 语义/内容段零改动/双实现同读/序幕合同负控); Remotion 对拍重钉 7350/409 |
| `tests/test_p3_state.py` | 真账钉重钉(7350/409/IndexError@7350/末段 idx408); 追加 `test_real_prologue_s000_empty` |
| `tests/test_p3_verify.py` | 双实现全帧钉重钉(7350/409/n=1050) |
| `tests/test_p3_render_smoke.py` | 过期字面量注释清除(其余逻辑本就 TOTAL 动态, 零改自适配) |
| `tests/test_p2_g3_thrust.py` | BLK-1 sidecar 完备性钉 8→9 条(+pace.json, 同轮扩) |
| `src/e30film/src/segments.ts` | seg-01 过期注释更新(S000 已存在, 窗自动张开); **逻辑零改动** |

## 序幕裁决落地(与 T7 报告移交项逐条对齐)

- **Remotion 零改动确认**: pace.ts/segments.ts 查表派生, S000 落地后 seg-01 字幕窗
  0→stageStart("S001")=150 自动张开; `tsc --noEmit` 过; bun 执行 print_pace.ts 读数
  duration=7350/fps=30/stages=409 与 pace.json 逐项一致
- **绝对帧号钉扫改**(grep 7199/7200 全 tests): test_p3_state(7200→7350/408→409/
  7199→7349/407→408), test_p3_verify(1029→1050), test_p3_pace(duration==7350);
  T5b 冒烟测试本就 `TOTAL=pace["total_frames"]` 动态取帧(0/首券架/末帧), 零改自适配;
  T3 stride 全帧自适应确认(仅 n 计数钉改)
- 双实现全帧对拍: `film_verify --stride 1` → **7350/7350 全帧一致**(7.5s)

## 30 帧试渲(前台实录)

- 选帧: 10 关键 stage(S000 题卡/S004 首立架/S009 首孔 CLOSE_RING/S193 中段/
  S379 末孔合龙/S386 落架开始波/S390 WEDGE.4/S391 CLEAR 波/S392 首 FILL/S408 末段)
  × 3 机位 = 30 帧; (S408,DONE) 取 7349 末帧(终态回归口径), 其余取段首帧
- 实测: **0.764–1.170 s/帧, mean 0.9075 s**(16spp/1080p/EEVEE); init≈0.5s/调用
- 过程修复两缺陷: ①续跑去重键初版只按 frame → 同帧三轨互跳(改 (frame,cam_track));
  ②PNG 名按帧 → 三轨互覆(变体轨加后缀, 正片名不变); 修复后清目录全量重渲 30 帧

## 断点续跑(选定方案, 已验证)

- **内置 (帧,机位) 去重**: selection.jsonl 为提交凭据(有记录必有 PNG), 重跑即续
- 验证: 300-302 整跑 vs 中断续跑 → selection/probe **逐字节同**, PNG **IDAT sha 同**
  (整文件字节差异=Blender tEXt 渲染元数据, 非像素层, 已知边界)
- pace 语义变更⇒必须清 frames/ 重渲(T5b 冒烟 7 帧旧账已归档 `frames_t5b_smoke/`)

## 终态回归(Step 2b, 详见 TRIAL_BUDGET §5)

- **四层一线全绿**: 末帧 7349 场景实例=vis_idx=选择记录=状态机=账目日程=**3931**;
  30 帧选择记录==状态机 30/30; S000 帧 0 空场 cursor=0
- **末帧 PNG vs P1 同机位**(P1 桥轴=Y↔film=X 等价机位 (38,0,7); water/fog 隐藏):
  控光对照 RMS **26.3**(MAE 15.8); 换光基线(同几何仅换光/引擎)RMS **75.4** →
  面值 RMS 104.9 的主项是光度学非几何; 桥影包含率 **97.5%**(IoU 0.62, 差额=栏板/
  石狮 P1 有而 408-stage 账外 + 竖向小错位); **EPS 敏感表入档**(film 侧 2→15:
  IoU 0.624→0.008, 悬崖 5→8 = 脚手架灯下桥面对天空对比仅 0.8–3/255)
- 判读为**条件式**: 几何/账目层通过(无 Step 2b 停报项); 像素绝对亮度对照在现行
  脚手架灯下不可判 → TRIAL_BUDGET §6 灯光建议(AgX 视图变换/天光 1.0→0.35–0.5/
  SUN 3.0→2.0, 验收口径对比 ≥20/255)签字后首段回填复跑

## 预算表要点(TRIAL_BUDGET.md)

- 16spp 全片 7350 帧 ≈ **1.85h 单段**; 64spp≈7.4h(2 段, 切 f=3678 S309 前);
  128spp≈14.8h(3 段, 切 f=2462/4993), 全部 ≤6h/段、切点落 stage 边界
- 外推公式 墙钟(h)≈帧数×0.9075×(spp/16)/3600; >16spp 未实测, 首段回填校核

## 验证(先红后绿 + 全量零红)

- 红: sidecar 钉先行扩 9 条而 sidecar 未登记 → 2 failed(差集 pace.json) → 登记 → 12 passed
- 绿: p3_pace/state/verify 20 passed; render_smoke 3 passed(blender 真跑, auto 相机
  回归兼容); p2_g3_thrust 12 + p2_sequencer 46 + p1_slice 42 + p2_full/dag/imbalance 59
  + p4 系(见下)等全量 34 文件分片前台**零红**
- Remotion: tsc --noEmit 过; bun print_pace.ts 读数与真账对拍一致

## 移交与边界

- **禁全量渲染直到用户在 TRIAL_BUDGET 签字**(16spp 单段 / 64spp 两段 / 128spp 三段 /
  先修灯光, 四选一或组合)
- writeback 原地补 pad 后 sidecar pace.json 行 sha 须随写轮更新(注记已写)
- >16spp 墙钟为线性外推未实测; P4 线(section_pack/print_status)未触碰, 且经查无
  pace.json 依赖, 序幕重生成对 P4 零影响
