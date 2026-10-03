# E21《魏公村·高梁河畔的畏吾村》档案纪实与地图驱动实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 E21《魏公村·高梁河畔的畏吾村》视频工程，承接 E20 确立之「档案证据驱动 (Archival Documentary Realism) ＋ 空间地图母语 (Layered Viewport)」体系，实现高精度地图视口漫游、古籍原刻影印展示、1915 京西实测地形图切片，并通过 QA v2 双档零发现验收。

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
- Create: `scripts/extract_weigongcun_assets.py`
- Create: `assets/hist_weigongcun/sources.csv`
- Test: `tests/test_weigongcun_assets.py`

**Interfaces:**
- Consumes: `/Users/mac/Downloads/清 佚名 三山五园图51x88.tif` (10468×6072)
- Produces: `assets/hist_weigongcun/sanshanyuan_haidian_roi.png` + 1915 地图切片 + 古籍影印 + `/tmp/chemistry-video/public/weigongcun/` 资产包

- [ ] **Step 1: 编写资产测试套件 `tests/test_weigongcun_assets.py`**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 编写生成脚本 `scripts/extract_weigongcun_assets.py` 并产出全部切片与素材**
- [ ] **Step 4: 同步至 `/tmp/chemistry-video/public/weigongcun/` 并跑通测试**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 2: 视口与组件复用与特化 (Viewport Engine Specialization)

**Files:**
- Create: `remotion-template/src/weigongcun/viewport/index.ts`
- Create: `remotion-template/src/weigongcun/viewport/PanZoomView.tsx`
- Create: `remotion-template/src/weigongcun/viewport/CrossFadeViewport.tsx`
- Create: `remotion-template/src/weigongcun/viewport/MapMarker.tsx`
- Test: `tests/test_weigongcun_viewport.py`

- [ ] **Step 1: 编写视口组件测试 `tests/test_weigongcun_viewport.py`**
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 实现视口引擎组件集并同步 `/tmp/chemistry-video/`**
- [ ] **Step 4: 运行测试并确认全部通过**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 3: E21 知识库与事实本体入库 (Knowledge Base Calibration)

**Files:**
- Create: `haidian_kg/calibration/weigongcun.py`
- Test: `tests/haidian_kg/test_weigongcun_entry.py`

- [ ] **Step 1: 编写本体与校准测试 `tests/haidian_kg/test_weigongcun_entry.py`**
  - 断言《元史·廉希宪传》确证实录与“畏吾村”得名；
  - 负控制断言：严禁将汉姓魏姓作为始源事实，必须存在反向伪说驳斥；
  - 断言大慧寺明正德八年建置与国保 5-199；
  - 断言李东阳《怀麓堂集》祖茔出处；
  - 断言 1915 京西图实测定名；
- [ ] **Step 2: 运行测试并确认失败**
- [ ] **Step 3: 编写 `haidian_kg/calibration/weigongcun.py` 并注入知识库**
- [ ] **Step 4: 跑通全库回归测试（确保 856+ 项全过）**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 4: E21 旁白定稿与 TTS 录制 (Narration & Audio Pipeline)

**Files:**
- Create: `weigongcun_video/narration/all.json`
- Create: `weigongcun_video/build_remotion_data.py`
- Create: `remotion-template/src/weigongcun/data/narration.ts`
- Create: `remotion-template/src/weigongcun/data/durations.json`
- Create: `remotion-template/src/weigongcun/data/subtitles.ts`
- Test: `tests/test_weigongcun_audio.py`

- [ ] **Step 1: 编写 8 段旁白定稿 `all.json`，时长控制在 180~250s**
- [ ] **Step 2: 使用 Qwen3-TTS (ref_user_E) 录制音频并生成双别名（`p1.wav` 与 `p01.wav`）**
- [ ] **Step 3: 运行 `build_remotion_data.py` 生成时间戳、字幕与配置**
- [ ] **Step 4: 编写并跑通 `tests/test_weigongcun_audio.py` 严格测试**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 5: 页面与槽位系统开发 (Storyboard & Slot System)

**Files:**
- Create: `remotion-template/src/weigongcun/data/slots.json`
- Create: `remotion-template/src/weigongcun/data/pages.config.ts`
- Create: `remotion-template/src/weigongcun/data/pageMap.ts`
- Create: `remotion-template/src/weigongcun/SlotPage.tsx`
- Create: `remotion-template/src/weigongcun/WeigongcunCourse.tsx`
- Create: `remotion-template/src/weigongcun/pages/Page01.tsx` ~ `Page08.tsx`
- Modify: `qa_v2/run.py` (注册 `weigongcun -> WeigongcunCourse`)
- Modify: `qa_v2/names.txt` (注入 E21 专名)

- [ ] **Step 1: 编写 `slots.json` 与 `pages.config.ts`（全部卡片配 backing: true）**
- [ ] **Step 2: 编写 Page01 至 Page08 8 个分镜组件与主入口**
- [ ] **Step 3: 同步至 `/tmp/chemistry-video/` 并在 `Root.tsx` 注册**
- [ ] **Step 4: 运行快档 QA：`python3 -m qa_v2.run weigongcun`，确认 fail 0 / warn 0**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 6: 渲染全片与 QA v2 全档验收 (Render & Double QA Validation)

**Files:**
- Produce: `/tmp/chemistry-video/out/weigongcun.mp4`
- Produce: `/tmp/chemistry-video/out/verify_e21/` 8 帧终态抽检图

- [ ] **Step 1: Remotion 渲染 `out/weigongcun.mp4`（1920×1080@30fps, CRF=20）**
- [ ] **Step 2: ffprobe 检查音视频完整性**
- [ ] **Step 3: 运行快档 QA 与全档 OCR QA，实现双档零发现（fail 0 / warn 0）**
- [ ] **Step 4: 抽取 8 页终态帧并目验无文字压图与溢出**
- [ ] **Step 5: 提交 git 并输出审查包**

---

### Task 7: 交付归档与知识沉淀 (Delivery & Documentation)

**Files:**
- Create: `weigongcun_video/DELIVERY.md`
- Modify: `anheqiao_video/series_registry.md`

- [ ] **Step 1: 编写 `weigongcun_video/DELIVERY.md` 交付文档**
- [ ] **Step 2: 在 `anheqiao_video/series_registry.md` 中登记 E21 交付**
- [ ] **Step 3: 最终 Git 提交并推送到 main 分支**
- [ ] **Step 4: 向用户输出完整交付报告与经验总结**
