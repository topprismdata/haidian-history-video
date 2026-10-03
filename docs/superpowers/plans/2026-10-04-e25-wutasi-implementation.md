# E25《五塔寺·把塔的落成年错当成寺的始建年》实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建 E25《五塔寺》视频工程，完成本系列第四例「时序否证」且首例「以物证时间为对象」，并通过 QA v2 双档零错误验收。

**Architecture:** 分层视口引擎。底层 `PanZoomView` 实现《三山五园图》长河北岸段与 1915 实测地图漫游；顶层 1920×1080 画布承载带 `backing: true` 卡纸物理隔离的 DOM 文字槽。

**Tech Stack:** Remotion 4.x, React, TypeScript, Python 3.9.6, PIL, MLX Audio (Qwen3-TTS ref_user_E), PaddleOCR, Pytest, FFmpeg.

## Global Constraints

- **Python 3.9.6**：禁 `X | None`（用 `Optional[X]`），禁 `match`。
- **物理隔离**：浮在地图/照片上的文字卡一律 `backing: true`。
- **负控制收敛**：纸雾渐变须在 **3%** 内达 0.99 不透明（E24 实测：12% 收敛点太晚，y=440 的底图字仍半透明可见）。
- **屏显纪年规范（E24 教训）**：禁用 U+3007 圆圈数字（宋体下不可见 → OCR 漏读）；阿拉伯数字在小字号下会被断字（`1068` → `1,168`）；连写汉字数字会被合并（`一一八九` → `2388`）。**三位／四位纪年不上小字号屏显**，只留相对量（如「早一百二十一年」），公历年由口播承担。
- **黑边防线（E23 教训）**：裁切前硬断言 `ox + crop_w <= mosaic_w`，裁切后量化右侧 260px 黑像素占比 < 0.02。
- **跨集污染防线（E23 教训）**：数据脚本从旧集复制后，提交前全文搜索他集路径名，并核对 `TEMPLATE_DATA`/`REMOTION_DATA` 落盘常量。
- **Git**：在 `/Volumes/macstudio/video-projects`，分支 `main`，中文提交信息。
- **音画同源**：`PAGE_DURATIONS_SEC`（含 1.6s 留白）供 Series offset 累加；`PAGE_AUDIO_SEC` 记录纯音频。

---

### Task 1: 地理切片与视觉资产预处理

**Files:**
- Create: `scripts/extract_wutasi_assets.py`
- Create: `assets/hist_wutasi/sources.csv`
- Test: `tests/test_wutasi_assets.py`

**必须含黑边量化断言**（E23 事故防线）。

- [ ] Step 1: 编写资产测试（含黑边断言）
- [ ] Step 2: 运行测试确认失败
- [ ] Step 3: 编写生成脚本并产出 7 件资产
- [ ] Step 4: 同步 public 并跑通测试
- [ ] Step 5: 提交 git

### Task 2: 视口与组件复用与特化

- [ ] Step 1: 编写视口测试（纯 SVG 根容器契约）
- [ ] Step 2: 测试确认失败
- [ ] Step 3: 实现并同步 `/tmp/chemistry-video/`
- [ ] Step 4: 测试全绿
- [ ] Step 5: 提交 git

### Task 3: E25 知识库与事实本体入库

**Files:** `haidian_kg/calibration/wutasi.py` ＋ `tests/haidian_kg/test_wutasi_entry.py`

**红线断言**：
- `prop_wutasi_ta_1473_as_si_founder`（塔年当寺年）必须 DISPROVEN
- `prop_wutasi_stele_only_proves_pagoda`（石匾只证塔）必须 VERIFIED（正向判据）
- `prop_wutasi_qianlong_bihuang`（避讳改名说）必须 DISPROVEN 或 CONTESTED（时序不通）
- 国保：第一批，1961-03-04；**不得出现「1-75」编号**
- 与 `extractor.py` 的 `top_zhenjuesi` / `top_wutasi` 同指挂钩，不重复建模

- [ ] Step 1: 编写本体与校准测试
- [ ] Step 2: 测试确认失败
- [ ] Step 3: 编写校准模块
- [ ] Step 4: 全库回归（1049+ 全过）
- [ ] Step 5: 提交 git

### Task 4: E25 旁白定稿与 TTS 录制

**Files:** `wutasi_video/narration/all.json`、`build_remotion_data.py`、`gen_tts_wutasi.sh` ＋ `tests/test_wutasi_audio.py`

**脚本纪律**：从 `dajuesi_video/` 复制后立即核对落盘常量并全文搜索他集路径名。

- [ ] Step 1: 编写 8 段旁白（180~280s）
- [ ] Step 2: TTS 录制并展平、建双别名
- [ ] Step 3: 运行 build_remotion_data.py
- [ ] Step 4: 测试通过
- [ ] Step 5: 提交 git（确认无跨集污染）

### Task 5: 页面与槽位系统开发

- [ ] Step 1: 编写槽位与页面结构测试
- [ ] Step 2: 测试确认失败
- [ ] Step 3: 实现 8 页 TSX 与配置
- [ ] Step 4: 同步并注册 Composition，快档 QA fail 0
- [ ] Step 5: 提交 git

### Task 6: 渲染全片与 QA v2 全档验收

- [ ] Step 1: 快档 QA
- [ ] Step 2: 全片渲染
- [ ] Step 3: 全档 OCR QA
- [ ] Step 4: 终态帧目视走查（含地图页主体可见性、无黑边）
- [ ] Step 5: 双档零错误确认

### Task 7: 交付归档与知识沉淀

- [ ] Step 1: 编写 DELIVERY.md
- [ ] Step 2: 登记 series_registry.md
- [ ] Step 3: 提交并推送 main
