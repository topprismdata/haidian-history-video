# E23《挂甲屯·杨六郎传说与清初额驸城》实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 E23《挂甲屯·杨六郎传说与清初额驸城》视频工程，延续 E20/E21/E22 确立之「档案证据驱动 (Archival Documentary Realism) ＋ 空间地图母语 (Layered Viewport)」体系，实现高精度地图视口漫游、正史《宋史》《清实录》与官书原刻影印展示、1915 京西实测地形图切片，并通过 QA v2 双档零错误验收。

**Architecture:** 采用分层视口引擎（Layered Viewport Engine）。底层通过 `PanZoomView` 实现《三山五园图》与 1915 实测地图的平滑缓动漫游，`CrossFadeViewport` 实现四时代半透明渐变，顶层 1920×1080 画布承载带有 `backing: true` 卡纸物理隔离的 DOM 文字槽与证据标签，彻底阻断 QA 负控制假阳性。

**Tech Stack:** Remotion 4.x, React, TypeScript, Python 3.9.6, PIL, MLX Audio (Qwen3-TTS ref_user_E), PaddleOCR, Pytest, FFmpeg.

## Global Constraints

- **Python 3.9.6 语法禁令**：严禁使用 `X | None` 联合类型（必须使用 `Optional[X]`），严禁使用 `match` 语句。
- **QA 物理隔离铁律**：所有浮在地图与图片上方的文字卡片，必须且绝对配置 `backing: true`（底色 `rgba(247, 240, 223, 0.95)`），防止文字墨迹与古地图底图字形粘连导致负控制崩溃。
- **标记物隔离规则**：地图呼吸框（MapMarker）、虚线圈、指针一律作为视口 SVG 叠加层渲染，严禁写入 `slots.json` 文字槽。
- **真图槽类型**：所有地图视口与书画视口在 `pages.config.ts` 中一律配置 `kind: "photo"`，使 QA L1/L3/L5/L6 自动排除。
- **Git 执行环境**：所有 Git 操作必须在 `/Volumes/macstudio/video-projects` 下执行，分支为 `main`，中文提交信息。
- **音画同源纪律**：`PAGE_DURATIONS_SEC`（含 1.6s 留白）供 Series offset 累加，`narration.ts PAGE_AUDIO_SEC` 记录纯音频，Enter 锚点按纯音频结算。

---

### Task 1: 地理切片与视觉资产预处理 (Geo-ROI Slicing & Asset Curation)

**Files:**
- Create: `scripts/extract_guajiatun_assets.py`
- Create: `assets/hist_guajiatun/sources.csv`
- Test: `tests/test_guajiatun_assets.py`

**Interfaces:**
- Consumes: `/Users/mac/Downloads/清 佚名 三山五园图51x88.tif` (10468×6072), 中研院北京百年历史地图 1915 WMTS 图层
- Produces: `assets/hist_guajiatun/` 切片资产 ＋ `/tmp/chemistry-video/public/guajiatun/` 资产包

- [ ] **Step 1: 编写资产测试套件 `tests/test_guajiatun_assets.py`**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 编写生成脚本 `scripts/extract_guajiatun_assets.py` 并产出全部切片与素材**
- [ ] **Step 4: 同步至 `/tmp/chemistry-video/public/guajiatun/` 并跑通测试**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 2: 视口与组件复用与特化 (Viewport Engine Specialization)

**Files:**
- Create: `remotion-template/src/guajiatun/viewport/index.ts`
- Create: `remotion-template/src/guajiatun/viewport/PanZoomView.tsx`
- Create: `remotion-template/src/guajiatun/viewport/CrossFadeViewport.tsx`
- Create: `remotion-template/src/guajiatun/viewport/MapMarker.tsx`
- Test: `tests/test_guajiatun_viewport.py`

- [ ] **Step 1: 编写视口组件测试 `tests/test_guajiatun_viewport.py`**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 实现视口引擎组件集并同步 `/tmp/chemistry-video/`**
- [ ] **Step 4: 运行测试并确认全部通过**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 3: E23 知识库与事实本体入库 (Knowledge Base Calibration)

**Files:**
- Create: `haidian_kg/calibration/guajiatun.py`
- Test: `tests/haidian_kg/test_guajiatun_entry.py`

- [ ] **Step 1: 编写本体与校准测试 `tests/haidian_kg/test_guajiatun_entry.py`**
  - 断言《宋史·杨延昭传》确证杨延昭镇守河北三关；
  - 负控制断言：严禁断言“杨六郎曾在海淀挂甲屯驻军”，判定为 DISPROVEN；
  - 断言《日下旧闻考》卷七十六确证挂甲屯即吴应熊额驸府第遗址；
  - 断言顺治十年吴应熊尚主、康熙十三年三藩之变伏诛实录；
  - 断言 1915 京西图实测定名「掛甲屯」；
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 编写 `haidian_kg/calibration/guajiatun.py` 并注入知识库**
- [ ] **Step 4: 跑通全库回归测试（确保 721+ 项全过）**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 4: E23 旁白定稿与 TTS 录制 (Narration & Audio Pipeline)

**Files:**
- Create: `guajiatun_video/narration/all.json`
- Create: `guajiatun_video/build_remotion_data.py`
- Create: `remotion-template/src/guajiatun/data/narration.ts`
- Create: `remotion-template/src/guajiatun/data/durations.json`
- Create: `remotion-template/src/guajiatun/data/subtitles.ts`
- Test: `tests/test_guajiatun_audio.py`

- [ ] **Step 1: 编写 8 段旁白定稿 `all.json`，时长控制在 180~250s**
- [ ] **Step 2: 使用 Qwen3-TTS (ref_user_E) 录制音频并生成双别名（`p1.wav` 与 `p01.wav`）**
- [ ] **Step 3: 运行 `build_remotion_data.py` 生成时间戳、字幕与配置**
- [ ] **Step 4: 编写并跑通 `tests/test_guajiatun_audio.py` 严格测试**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 5: 页面与槽位系统开发 (Storyboard & Slot System)

**Files:**
- Create: `remotion-template/src/guajiatun/data/slots.json`
- Create: `remotion-template/src/guajiatun/data/pages.config.ts`
- Create: `remotion-template/src/guajiatun/data/pageMap.ts`
- Create: `remotion-template/src/guajiatun/GuajiatunCourse.tsx`
- Create: `remotion-template/src/guajiatun/pages/SlotPage.tsx`
- Create: `remotion-template/src/guajiatun/pages/Page01.tsx`–`Page08.tsx`
- Test: `tests/test_guajiatun_pages.py`

- [ ] **Step 1: 编写 8 页槽位与页面结构测试 `tests/test_guajiatun_pages.py`**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 实现全部 8 页 TSX、槽位配置与 Remotion 根组件**
- [ ] **Step 4: 同步至 `/tmp/chemistry-video/`，注册 Composition 并跑通测试**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 6: 渲染全片与 QA v2 全档验收 (Full-Length Render & Dual-Tier QA)

**Files:**
- Output: `/tmp/chemistry-video/out/guajiatun.mp4`
- Cache: `/tmp/qa_cache/guajiatun_*.json`

- [ ] **Step 1: 运行快档 QA（DOM 几何/L1/L2/L6/越界检查）**
- [ ] **Step 2: 执行 Remotion 4K/1080p 全片渲染**
- [ ] **Step 3: 运行全档 OCR QA (`python3 -m qa_v2.run guajiatun --ocr`)**
- [ ] **Step 4: 终态帧逐页抽检目视走查（验证无文字溢出与负控制有效性）**
- [ ] **Step 5: 确认双档零错误通过**

---

### Task 7: 交付归档与知识沉淀 (Delivery & Knowledge Crystallization)

**Files:**
- Create: `guajiatun_video/DELIVERY.md`
- Update: `anheqiao_video/series_registry.md`
- Update: `.superpowers/sdd/progress.md`

- [ ] **Step 1: 编写 `guajiatun_video/DELIVERY.md` 交付文档**
- [ ] **Step 2: 更新 `anheqiao_video/series_registry.md` 登记 E23 交付**
- [ ] **Step 3: 最终 Git 提交并推送到 main**
