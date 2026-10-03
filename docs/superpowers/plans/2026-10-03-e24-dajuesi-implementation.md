# E24《大觉寺·阳台山麓的千年清水院》实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 E24《大觉寺·阳台山麓的千年清水院》视频工程，延续 E20–E23 确立之「档案证据驱动 ＋ 空间地图母语」体系，以辽咸雍四年（1068）碑为首要一手实物，完成本系列第三例「时序否证」，并通过 QA v2 双档零错误验收。

**Architecture:** 采用分层视口引擎（Layered Viewport Engine）。底层 `PanZoomView` 实现《三山五园图》旸台山麓与 1915 实测地图的平滑缓动漫游；顶层 1920×1080 画布承载带 `backing: true` 卡纸物理隔离的 DOM 文字槽，彻底阻断 QA 负控制假阳性。

**Tech Stack:** Remotion 4.x, React, TypeScript, Python 3.9.6, PIL, MLX Audio (Qwen3-TTS ref_user_E), PaddleOCR, Pytest, FFmpeg.

## Global Constraints

- **Python 3.9.6 语法禁令**：严禁 `X | None`（必须 `Optional[X]`），严禁 `match`。
- **QA 物理隔离铁律**：浮在地图/照片上方的文字卡一律 `backing: true`（`rgba(247,240,223,0.95)`）。
- **负控制收敛纪律**：负控制路径的纸雾渐变须在 12% 内达 0.99 不透明（E23 事故教训：34% 才达 0.93 时平移候选落进地图「頤」字）。
- **标记物隔离**：`MapMarker` 纯 SVG 叠加，不写入 `slots.json`。
- **真图槽类型**：`pages.config.ts` 中地图/书画槽一律 `kind: "photo"`。
- **跨集数据污染隔离**（E23 教训）：数据构建脚本改写后必须核对 `TEMPLATE_DATA` / `REMOTION_DATA` 常量落盘目标，提交前复核其他集数据未被覆盖。
- **Git 执行环境**：所有 Git 操作在 `/Volumes/macstudio/video-projects`，分支 `main`，中文提交信息。
- **音画同源纪律**：`PAGE_DURATIONS_SEC`（含 1.6s 留白）供 Series offset 累加；`PAGE_AUDIO_SEC` 记录纯音频。

---

### Task 1: 地理切片与视觉资产预处理

**Files:**
- Create: `scripts/extract_dajuesi_assets.py`
- Create: `assets/hist_dajuesi/sources.csv`
- Test: `tests/test_dajuesi_assets.py`

**Interfaces:**
- Consumes: `/Users/mac/Downloads/清 佚名 三山五园图51x88.tif` (10468×6072), 中研院 1915 WMTS
- Produces: `assets/hist_dajuesi/` 7 件资产 ＋ `/tmp/chemistry-video/public/dajuesi/`

**🔴 E23 事故防线（必须写进测试）**：
拼接窗口宽度必须 `>= ox + crop_w`，否则 PIL 黑色补齐导致成片黑边。
测试必须断言右侧 260px 带的黑像素占比 `< 0.02`。

- [ ] **Step 1: 编写资产测试套件（含黑边量化断言）**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 编写生成脚本并产出全部资产**
- [ ] **Step 4: 同步 public 并跑通测试**
- [ ] **Step 5: 提交 git**

---

### Task 2: 视口与组件复用与特化

**Files:**
- Create: `remotion-template/src/dajuesi/viewport/{index.ts,PanZoomView.tsx,CrossFadeViewport.tsx,MapMarker.tsx,ScrollPanView.tsx}`
- Test: `tests/test_dajuesi_viewport.py`

- [ ] **Step 1: 编写视口组件测试（纯 SVG 根容器契约）**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 实现并同步 `/tmp/chemistry-video/`**
- [ ] **Step 4: 测试全绿**
- [ ] **Step 5: 提交 git**

---

### Task 3: E24 知识库与事实本体入库

**Files:**
- Create: `haidian_kg/calibration/dajuesi.py`
- Test: `tests/haidian_kg/test_dajuesi_entry.py`

**红线断言**：
- 辽碑（1068）「院之興止於近代」必须为 VERIFIED 一手实物；
- `prop_dajuesi_jinzhangzong_founder`（始建于金章宗）必须 DISPROVEN；
- `prop_dajuesi_bayan`（金章宗八院）必须为 CONTESTED（明人追述）；
- `prop_dajuesi_magnolia_age`（白玉兰植栽年代）必须 UNSUBSTANTIATED；
- 府县保批次：第六批（2006-05-25）。

- [ ] **Step 1: 编写本体与校准测试**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 编写校准模块并注入知识库**
- [ ] **Step 4: 全库回归（1010+ 全过）**
- [ ] **Step 5: 提交 git**

---

### Task 4: E24 旁白定稿与 TTS 录制

**Files:**
- Create: `dajuesi_video/narration/all.json`, `build_remotion_data.py`, `gen_tts_dajuesi.sh`
- Create: `remotion-template/src/dajuesi/data/{narration.ts,durations.json,subtitles.ts}`
- Test: `tests/test_dajuesi_audio.py`

**🔴 脚本纪律**：从 `guajiatun_video/build_remotion_data.py` 复制后，**必须逐行核对 `TEMPLATE_DATA` / `REMOTION_DATA` 常量指向 `dajuesi`**，并在提交前 `git status` 确认 `remotion-template/src/*/data/` 无其他集被改动。

- [ ] **Step 1: 编写 8 段旁白定稿（180~280s）**
- [ ] **Step 2: Qwen3-TTS 录制并展平目录、建双别名**
- [ ] **Step 3: 运行 build_remotion_data.py**
- [ ] **Step 4: 编写并跑通测试**
- [ ] **Step 5: 提交 git（确认无跨集污染）**

---

### Task 5: 页面与槽位系统开发

**Files:**
- Create: `remotion-template/src/dajuesi/data/{slots.json,pages.config.ts,pageMap.ts}`
- Create: `remotion-template/src/dajuesi/{DajuesiCourse.tsx,SlotPage.tsx,ui.tsx}`
- Create: `remotion-template/src/dajuesi/pages/Page01.tsx`–`Page08.tsx`
- Test: `tests/test_dajuesi_pages.py`

- [ ] **Step 1: 编写槽位与页面结构测试**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 实现 8 页 TSX 与配置**
- [ ] **Step 4: 同步并注册 Composition，跑通快档 QA（fail 0）**
- [ ] **Step 5: 提交 git**

---

### Task 6: 渲染全片与 QA v2 全档验收

**Files:**
- Output: `/tmp/chemistry-video/out/dajuesi.mp4`
- Cache: `/tmp/qa_cache/dajuesi_*.json`

- [ ] **Step 1: 快档 QA（fail 0）**
- [ ] **Step 2: Remotion 全片渲染**
- [ ] **Step 3: 全档 OCR QA（fail 0）**
- [ ] **Step 4: 终态帧逐页目视走查（含地图页主体可见性、MapPage 无黑边）**
- [ ] **Step 5: 双档零错误确认**

---

### Task 7: 交付归档与知识沉淀

**Files:**
- Create: `dajuesi_video/DELIVERY.md`
- Update: `anheqiao_video/series_registry.md`, `.superpowers/sdd/progress.md`

- [ ] **Step 1: 编写交付文档**
- [ ] **Step 2: 登记 series_registry.md**
- [ ] **Step 3: 提交并推送 main**
