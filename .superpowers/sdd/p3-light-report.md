# P3 灯光定版报告: AgX 钉 + 天穹/SUN 重标 + impost 卡材质, 试渲 5 帧达阈

- Commit: `feat(e30): P3灯光定版(AgX+天光/SUN重标, 试渲5帧达阈)`(只含 `3d/film/film_render.py` + 本报告)
- 任务: T8 签字后的灯光前置修(起点=T8 TRIAL_BUDGET §6 建议), 试渲 5 帧量桥面/天空对比达阈(≥30/255, 亮区带 40-120, 暗面非死黑), 迭代上限 3 轮
- 结论: **第 3 轮达阈**。判定阈值全过(对比 48.9-80.6, 亮区 79.7-111.3 全落带内, 暗面 P10 79-82 非死黑), 三机位(BUILD/DECENTER/DONE)目视核过, 全片渲染仍禁(主控挂账监督未变)

## 定版参数表(3d/film/film_render.py 模块常量)

| 参数 | T8 原值 | R1 | R2 | **R3 定版** | 依据 |
|---|---|---|---|---|---|
| `VIEW_TRANSFORM` | 未钉(blend 已 AgX) | AgX | AgX | **'AgX' 显式钉** | setup_render 内钉死防漂; 5.2 内置 |
| `SUN_LIGHT_ENERGY` | 3.0 | 2.0 | 2.0 | **2.0** | T8 建议值, 未再动 |
| SUN 方向 | euler(55°,0,35°) 日悬**南** | 同左 | **WNW 光行向 (0.760,-0.307,-0.574)** | 同 R2 | P1 实拍口径 RM-123108 逐字同源(build_scene2 Key); 南侧日把相机面照得比天空还亮(R1 实测) |
| SUN 色 | 白 | 白 | **(1.0,0.94,0.84) 暖阳** | 同 R2 | P1 Key 同源 |
| `SKY_STRENGTH` | 1.0 | 0.42 | 0.50 | **0.49** | T8 建议带 0.35-0.5 上沿; AgX 标定曲线解出(天穹线性 ≈0.407 → 160/255, 对齐 P1 参照天 179 同级) |
| impost 卡材质 | **无**(EEVEE 默认 0.8 白灰) | 无 | 无 | **MAT_P3_STONE_SCAFFOLD 线性 (0.21,0.20,0.185), rough 0.9** | 根因③, 见下 |

新增 `ensure_scaffold_material(scene)`(幂等: 只补无材质槽的 fam 卡, R3 实补 3509), 在 `main()` 内紧跟 `ensure_light_world` 调用; INIT 日志行追加 `matted=` 字段。

## 根因链(T8"近全白"三层, 探针留证)

1. **天穹 1.0 全穹顶 = 巨量环境填充**: R1 前整帧 188-201/255 无结构(行剖面逐行差 <3)。
2. **日悬南侧把相机面照亮**: R1(SUN 2.0 南向)桥面 164-167 **比天空 153 还亮**, 与 P1 参照(桥 69 暗于天)相反。
3. **impost 卡无材质(决定性)**: `layout_film.blend` 3527 个 fam 卡 **N_MAT=0**, EEVEE 默认 Principled 0.8 白灰。分光探针(both/sun-only/sky-only 三连渲): **sun-only 全桥响应 0.7/255**(WNW 日对南面近掠射, 卡主法线 ±Y(0.87)/±Z(0.49), N·toSun≈0.01), sky-only ≡ both → 桥体辐亮度 ≈ 0.94×天空, **任何灯参组合都出不了对比**(R2 实证: 方位改 WNW 后侧视对比仍 0.1-9.2)。
   → 必须给卡面挂低反照率石色(0.20), 让桥体落回中暗剪影; 这是最小必要 photometric 补全, 超出纯"灯参"但无它判据数学不可达。

**AgX 标定曲线**(EEVEE 16spp emission 色卡直测, 参数求解依据): 0.12→96, 0.15→108, 0.40→160, 0.60→177(/255)。解: sky 0.49→160.3 实测 ✓; ρ=0.20 南面 ≈85 实测 ✓(模型误差 <8/255)。

## 试渲 5 帧终值(R3, 16spp/1080p/EEVEE, 0.8-1.1s/帧)

输出 `3d/out/film/light_check/`(PNG + preview_*.png 标注采样位 + selection/probe/timing)。判据: 桥面/天空对比 ≥30/255; 亮区均值 P75 ∈ [40,120]; 暗面 P10 非死黑(诊断)。

| 帧 | 段(事件) | 机位 | 天空 | 亮区 P75 | 对比 | 带内 | 暗面 P10 | 判 |
|---|---|---|---|---|---|---|---|---|
| f000075 | S000 题卡 | BUILD | 160.3 | — | — | — | — | **N/A: 空场**(cursor=0, 四层一线 T8 已钉; 题字在 Remotion 后期) |
| f000317 | S009 首孔(ARCH01 CLOSE_RING) | BUILD | 160.3 | 89.0(全局石体带) | **71.3** | ✓ | — | **过** |
| f004444 | S379 合龙(ARCH17 CLOSE_RING) | BUILD | 160.3 | 95.0 | **65.3** | ✓ | 81.7 | **过** |
| f004590 | S388 落架波 | DECENTER | 160.3(背景穹顶) | 111.3 | **48.9** | ✓ | 81.7 | **过** |
| f007349 | 末帧(终态回归口径) | DONE | 160.3 | 79.7 | **80.6** | ✓ | 79.0 | **过** |

目视核(f007349/f004444/f004590): 桥体中暗剪影、17 孔券洞透空可辨、券石/栏板层理可读、西端顶缘有 WNW 暖阳微量 modeling, 无死黑无泛白; P1 参照同级剪影观感。

### 量测口径(预登记, 全帧同规则)

- 天空/背景: 顶部 6% 行 × 中央 50% 列。
- 石体带: 桥面投影线以下 120px, 石体像素 = 比天空暗 ≥30; 在场柱 = 石体像素 ≥10; 亮区 = 石体像素 P75。柱采样不足 5(首孔=0.4m 薄环弧)时用全局石体带兜底(同阈值)。
- 桥面投影: 从 probe.jsonl 相机回读 + CAMERA_TRACKS target 重建相机(world_to_camera_view 需 `view_layer.update()`, 新建物体矩阵惰性), `geom_math.deck_z` 单源。
- 鸟瞰帧无天空为投影学事实: 顶缘射线仰角 -28.87°(<0, 45° 俯角 + 16.1° 半竖直视场), 对比量对"背景穹顶"读了同一 world 底色, 已在表中注明。
- 部分建造帧语义: 合龙帧(S379)=17 环闭合而桥面石未铺(S392 首 FILL 在后), 量的是环拱/墩身受光面 —— 与"桥面亮区"判据的等价受光面口径。

## 迭代史(上限 3 轮, 第 3 轮达标)

| 轮 | 参数 | 结果 | 判 |
|---|---|---|---|
| R1 | T8 建议直用: SUN 2.0 南向 + 天光 0.42 + AgX 钉 | 对比 0.2-22.2, 桥比天亮 | 红 |
| R2 | SUN 转 WNW(P1 方位) + 天光 0.50 | 对比 0.1-16.4, 南面入影但卡无材质洗白依旧 | 红 → 触发根因探针 |
| R3 | + 卡面石色 0.20 + 天光 0.49(AgX 曲线解) | 对比 48.9-80.6, 亮区 79.7-111.3 | **全过** |

## 验证与边界

- `tests/test_p3_render_smoke.py` 3 passed(改动后真跑 blender); 全量分片见下方补记。
- 对 P1 layout blend 零写入(只读打开纪律不變, work.blend 另存链不变); probe/selection 记录 schema 不变(仅 INIT 打印行加字段)。
- **全片渲染仍禁**: 本报告只覆盖灯光前置, 主控挂账监督不变。
- 后续可选(不在本轮): 鸟瞰帧前景水面/岸坡 dressing、题卡帧后期题字亮度、64spp 全片预算复核(TRIAL_BUDGET 外推公式不因灯改而失效, 帧时 0.9s 级持平)。

## pytest 补记(前台分片 + 双人分账口径)

- 本任务(灯修)侧分片, **450 passed / 0 failed**(27 文件, 每片前台零红; p1_slice 四片 -k 曾漏 2 支, 已单跑补齐并更正):
  - shard facts/freeze/l1_body/no_literals/p1_export/p1_families/p1_ledger: 104 passed
  - p1_masonry2/printcheck/scene: 87 passed
  - p1_slice(分 4 片+2 支补跑): 13+10+7+10+2 = 42 passed(42/42 全覆盖)
  - p2_centering/events/geom_math: 86 passed
  - p2_g3_dag/imbalance/ledger_v2: 67 passed
  - p2_full(分 2 片): 11+9 = 20 passed
  - p3_film_layout/geometry/script_lint: 9 passed(含 film_render 源码 lint, 改动后过)
  - p3_render_smoke(blender 真跑): 3 passed(改动后)
  - p3_pace/state/verify/register: 30 passed
  - p3_silhouette: 2 passed
- P4T6Close 侧(双人分账, IRC 对齐留痕): scale 3 + status 6 + thrust 12 + conservation 6 + section 9 + sequencer 46(含 clean-clone 单测 1, 独占串行) = **82 passed / 0 failed**
- 两账合计 **532 passed / 0 failed = collect-only 532 逐支对平, 33/33 测试文件全覆盖**(我 450 + P4 82)。我片跳过 `tests/test_p2_g3_thrust.py`(P4 同轮 +8 行 sidecar 钉)与 `tests/test_p4_status.py`(P4 新文件), 归 P4 账避免撞半成品报假红(IRC 对齐留痕)。
