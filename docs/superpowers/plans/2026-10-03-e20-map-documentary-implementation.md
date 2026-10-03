# E20《勺园·淑春园·未名湖》档案纪实与地图驱动实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 E20《勺园·淑春园·未名湖》视频工程，落地海淀历史地名系列首个「档案证据驱动 (Archival Documentary Realism) ＋ 空间地图母语 (Layered Viewport)」体系，实现高精度地图平滑漫游、四时代半透明叠合、吴彬长卷真迹展示，并通过 QA v2 双档验收。

**Architecture:** 采用分层视口引擎（Layered Viewport Engine）。底层通过 `PanZoomView` 实现 4000px 级古地图 GPU 缓动漫游与 `CrossFadeViewport` 实现多时代图层半透明渐变，顶层固定 1920×1080 画布承载带有 `backing: true` 卡纸物理隔离的 DOM 文字槽与证据标签，彻底规避 QA 负控制假阳性。

**Tech Stack:** Remotion 4.x, React, TypeScript, Python 3.9.6, PIL, MLX Audio (Qwen3-TTS ref_user_E), PaddleOCR, Pytest, FFmpeg.

## Global Constraints

- **Python 3.9.6 语法禁令**：严禁使用 `X | None` 联合类型（必须使用 `Optional[X]`），严禁使用 `match` 语句。
- **QA 物理隔离铁律**：所有浮在地图与长卷上方的文字卡片，必须且绝对配置 `backing: true`（底色 `rgba(247, 240, 223, 0.95)`），防止文字墨迹与古地图底图字形粘连导致负控制崩溃。
- **标记物隔离规则**：地图呼吸框（MapMarker）、虚线圈、指针一律作为视口 SVG 叠加层渲染，严禁写入 `slots.json` 文字槽。
- **真图槽类型**：所有地图视口与书画视口在 `pages.config.ts` 中一律配置 `kind: "photo"`，使 QA L1/L3/L5/L6 自动排除。
- **Git 执行环境**：所有 Git 操作必须在 `/Volumes/macstudio/video-projects` 下执行，分支为 `main`，中文提交信息。
- **音画同源纪律**：`PAGE_DURATIONS_SEC`（含 1.6s 留白）供 Series offset 累加，`narration.ts PAGE_AUDIO_SEC` 记录纯音频，Enter 锚点按纯音频结算。

---

### Task 1: 地理切片与视觉资产预处理 (Geo-ROI Slicing & Asset Curation)

**Files:**
- Create: `scripts/extract_shaoyuan_map_roi.py`
- Create: `assets/hist_shaoyuan/sources.csv`
- Test: `tests/test_shaoyuan_assets.py`

**Interfaces:**
- Consumes: `/Users/mac/Downloads/清 佚名 三山五园图51x88.tif` (10468×6072)
- Produces: `assets/hist_shaoyuan/sanshanyuan_haidian_roi_4000.png` (4000×2400) + `/tmp/chemistry-video/public/shaoyuan/` 资产包

- [ ] **Step 1: 编写资产测试**

```python
# tests/test_shaoyuan_assets.py
import os
import pathlib
import pytest
from PIL import Image

ASSET_DIR = pathlib.Path("assets/hist_shaoyuan")

def test_sanshanyuan_roi_4000_exists_and_dimensions():
    p = ASSET_DIR / "sanshanyuan_haidian_roi_4000.png"
    assert p.exists(), "切片地图必须存在"
    im = Image.open(p)
    assert im.size == (4000, 2400), "切片必须严格为 4000x2400 像素以适配 1080p 2.2x 视口"
    # 文件大小受控（<= 15MB）
    assert p.stat().st_size <= 15 * 1024 * 1024, "切片文件大小必须受控防止 OOM"

def test_sources_csv_contains_mec_and_vec_fields():
    csv_file = ASSET_DIR / "sources.csv"
    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8")
    assert "MEC-" in content or "VEC-" in content, "sources.csv 必须包含证据分级列"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python3 -m pytest tests/test_shaoyuan_assets.py -v`  
Expected: FAIL with "切片地图必须存在"

- [ ] **Step 3: 编写地理切片预处理脚本并执行**

```python
# scripts/extract_shaoyuan_map_roi.py
import os
import pathlib
from PIL import Image

def slice_map():
    src = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")
    assert src.exists(), f"未找到母版: {src}"
    
    out_dir = pathlib.Path("assets/hist_shaoyuan")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sanshanyuan_haidian_roi_4000.png"

    print("Opening 182MB TIF master...")
    im = Image.open(src)
    W, H = im.size # 10468, 6072

    # 海淀镇至畅春园、圆明园南部湿地核心区域 (x: 5200..9600, y: 2800..5600)
    # 转换为 16:9.6 (4000x2400 区域)
    crop_box = (int(W * 0.48), int(H * 0.45), int(W * 0.92), int(H * 0.93))
    print("Cropping ROI:", crop_box)
    roi = im.crop(crop_box)
    
    # 缩放到 4000x2400 标准工程底图
    target = roi.resize((4000, 2400), Image.LANCZOS)
    target.save(out_path, format="PNG", optimize=True)
    print(f"Saved {out_path} ({target.size})")

if __name__ == "__main__":
    slice_map()
```

Run: `python3 scripts/extract_shaoyuan_map_roi.py`

- [ ] **Step 4: 补齐 sources.csv 并同步资产到 public**

更新 `assets/hist_shaoyuan/sources.csv`，补充 MEC/VEC 分级、出处与 sha256。  
将所有切片、古画长卷、历史照片复制到 `/tmp/chemistry-video/public/shaoyuan/`。

- [ ] **Step 5: 验证测试通过并提交**

Run: `python3 -m pytest tests/test_shaoyuan_assets.py -v`  
Expected: PASS  
Commit: `feat(assets): E20 三山五园图 4000px 高清切片与证据级视觉资产包`

---

### Task 2: 分层视口漫游组件研发 (Layered Viewport Components)

**Files:**
- Create: `/tmp/chemistry-video/src/shaoyuan/viewport/PanZoomView.tsx`
- Create: `/tmp/chemistry-video/src/shaoyuan/viewport/CrossFadeViewport.tsx`
- Create: `/tmp/chemistry-video/src/shaoyuan/viewport/MapMarker.tsx`
- Test: `tests/test_viewport_math.py`

**Interfaces:**
- Produces: 
  - `PanZoomView: React.FC<{ src: string; startView: ViewSpec; endView: ViewSpec; durationInFrames: number; children?: React.ReactNode }>`
  - `CrossFadeViewport: React.FC<{ layers: Array<{ src: string; startOpacity: number; endOpacity: number }>; width: number; height: number }>`
  - `MapMarker: React.FC<{ x: number; y: number; label: string; color?: string }>`

- [ ] **Step 1: 编写视口数学插值单元测试**

```python
# tests/test_viewport_math.py
def interpolate_view(start, end, progress):
    """验证视口平滑插值算法边界安全性"""
    x = start["x"] + (end["x"] - start["x"]) * progress
    y = start["y"] + (end["y"] - start["y"]) * progress
    scale = start["scale"] + (end["scale"] - start["scale"]) * progress
    return {"x": round(x, 2), "y": round(y, 2), "scale": round(scale, 4)}

def test_viewport_interpolation_bounds():
    start = {"x": 0, "y": 0, "scale": 1.0}
    end = {"x": -800, "y": -400, "scale": 2.2}
    
    assert interpolate_view(start, end, 0.0) == start
    assert interpolate_view(start, end, 1.0) == end
    mid = interpolate_view(start, end, 0.5)
    assert mid["scale"] == 1.6
    assert mid["x"] == -400.0
```

- [ ] **Step 2: 实现 TypeScript 视口组件**

在 `/tmp/chemistry-video/src/shaoyuan/viewport/PanZoomView.tsx` 中编写 `PanZoomView`，使用 Remotion 的 `interpolate` 和三次贝塞尔曲线，驱动 `transform: translate3d(...) scale(...)`。  
在 `CrossFadeViewport.tsx` 中实现 4 图层透明度渐隐渐现。  
在 `MapMarker.tsx` 中实现矢量 SVG 呼吸定位标。

- [ ] **Step 3: 运行测试并验证无 TypeScript 报错**

Run: `cd /tmp/chemistry-video && npx tsc --noEmit src/shaoyuan/viewport/PanZoomView.tsx`  
Expected: PASS with 0 errors.

- [ ] **Step 4: Commit**

Commit: `feat(remotion): E20 分层视口漫游组件 (PanZoomView / CrossFadeViewport / MapMarker)`

---

### Task 3: E20 知识库与事实本体入库 (Haidian KG Calibration: shaoyuan.py)

**Files:**
- Create: `haidian_kg/calibration/shaoyuan.py`
- Modify: `haidian_kg/calibration/bibliography.py`
- Create: `tests/haidian_kg/test_shaoyuan_entry.py`

**Interfaces:**
- Consumes: `shaoyuan_video/research.md` (v1.1 裁决), `cishousi.py` 模式
- Produces: `ENTITIES`, `STATES`, `FACTS`, `PROPOSITIONS`, `ADOPTIONS`, `TRANSFORMATIONS`, `REFERENCES`

- [ ] **Step 1: 编写 E20 入库测试与红线守卫**

```python
# tests/haidian_kg/test_shaoyuan_entry.py
import pytest
from haidian_kg.calibration import shaoyuan as S
from haidian_kg.ontology.epistemic import EpistemicStatus

def test_shaoyuan_vs_shuchunyuan_distinct_entities():
    """勺园与和珅海淀赐园（淑春园）必须分立为两个实体"""
    assert "ent_shaoyuan" in [e.id for e in S.ENTITIES]
    assert "ent_shuchunyuan" in [e.id for e in S.ENTITIES]

def test_he_shen_garden_naming_dispute_modeled_as_contested():
    """E01/E02: 和珅园是否即淑春园必须建模为学术争议 CONTESTED"""
    adopt = [a for a in S.ADOPTIONS if a.proposition_id == "prop_shuchunyuan_he_shen_identity"][0]
    assert adopt.status == EpistemicStatus.CONTESTED
    assert "何瑜" in adopt.rationale and "郝黎" in adopt.rationale

def test_1784_excluded_from_confirmed_facts():
    """E03: 1784 赐和珅年份不得作为确证事实入库"""
    facts_str = " ".join([f.verbatim_quote for f in S.FACTS])
    assert "乾隆四十九年赐和珅" not in facts_str

def test_house_count_is_1003_not_1030():
    """E04: 房数必须为 1003 间，严禁 1030"""
    f = [f for f in S.FACTS if "1003" in f.id or "一千零三间" in f.verbatim_quote][0]
    assert "一千零三间" in f.verbatim_quote
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python3 -m pytest tests/haidian_kg/test_shaoyuan_entry.py -v`  
Expected: FAIL with "module shaoyuan not found"

- [ ] **Step 3: 编写 `haidian_kg/calibration/shaoyuan.py`**

实现实体分立（`ent_shaoyuan`, `ent_shuchunyuan`, `ent_yanjing_campus`, `ent_weiming_lake`）、1003间房一手事实（A10）、乙卯吴彬卷（1615）、第五批国保 5-475（未名湖燕园建筑）、以及 E01~E06 闸门裁决。

- [ ] **Step 4: 运行入库测试与全量回归**

Run: `python3 -m pytest tests/ -q`  
Expected: ≥ 774 passed.

- [ ] **Step 5: Commit**

Commit: `feat(kg): E20 勺园·淑春园入库——争议建模与国保 5-475 (774 passed)`

---

### Task 4: E20 旁白定稿与 TTS 录制 (Narration & Audio Pipeline)

**Files:**
- Create: `shaoyuan_video/narration/all.json`
- Create: `shaoyuan_video/narration/durations.json`
- Create: `/tmp/chemistry-video/src/shaoyuan/data/narration.ts`
- Create: `/tmp/chemistry-video/src/shaoyuan/data/subtitles.ts`

- [ ] **Step 1: 编写 8 页旁白 JSON**

严格遵守白名单与发音规则：
- P1: 未名湖开场，点亮地名公案；
- P2: 1615 吴彬画卷，米万钟筑园；
- P3: 两个园址系统（勺园在西南，和珅园在东北）；
- P4: 乾隆后期和珅园（房一千零三间，不说1784，不说独资）；
- P5: 石舫残基与石屏（明确石屏为圆明园移入）；
- P6: 1920 燕大建校与墨菲规划总图；
- P7: 未名湖定名过程（钱穆非最初命名者）；
- P8: 1982 条石出土与四时代叠合。

- [ ] **Step 2: 执行 TTS 生成**

Run:
```bash
cd /Volumes/macstudio/video-projects && \
TTS_HOME=/Volumes/macstudio/video-projects/tts \
AUDIO_DIR=/tmp/chemistry-video/public/audio \
TTS_REF=/Volumes/macstudio/video-projects/tts/voices/ref_user_E.wav \
TTS_REF_TEXT="$(cat tts/voices/ref_user_E.txt)" \
./gen_tts.sh shaoyuan shaoyuan_video/narration/all.json
```

- [ ] **Step 3: 测量时长并同步三件套**

写入 `durations.json`，生成 `narration.ts` 与 `subtitles.ts`，同时生成无前导零的别名 `p1.wav`–`p8.wav` 防 404。

- [ ] **Step 4: Commit**

Commit: `feat(audio): E20 旁白文本与 TTS 配音生成 (ref_user_E)`

---

### Task 5: 页面与槽位系统开发 (SlotPage, pages.config.ts, slots.json)

**Files:**
- Create: `/tmp/chemistry-video/src/shaoyuan/data/slots.json`
- Create: `/tmp/chemistry-video/src/shaoyuan/data/pages.config.ts`
- Create: `/tmp/chemistry-video/src/shaoyuan/data/pageMap.ts`
- Create: `/tmp/chemistry-video/src/shaoyuan/SlotPage.tsx`
- Create: `/tmp/chemistry-video/src/shaoyuan/ShaoyuanCourse.tsx`
- Modify: `/tmp/chemistry-video/src/Root.tsx`
- Modify: `qa_v2/run.py`

- [ ] **Step 1: 编写 slots.json 与 pages.config.ts**

- 配置 1920×1080 标准设计空间坐标；
- 所有地图视口、照片镜框槽位配置 `kind: "photo"`；
- 所有文字卡片强制配置 `backing: true`；
- 所有证据标签配置 `kind: "tag"`。

- [ ] **Step 2: 实现 Page01 至 Page08**

- P1: 现代燕园底图 + 未名湖实拍；
- P2: `ScrollPanView` 漫游吴彬 1615 真卷；
- P3: `PanZoomView` 漫游《三山五园图》4000px 切片，点亮双系统；
- P4: 1793 使团档案 + 石舫残基；
- P5: 实物鉴证：石舫榫卯 + 乾隆石屏拓片；
- P6: 墨菲 1920s 总图 + 1860 Beato 燃灯塔照片；
- P7: 未名湖文献与校刊书影；
- P8: `CrossFadeViewport` 四时代半透明叠合收官。

- [ ] **Step 3: 注册组件与快档 QA 验证**

在 `Root.tsx` 注册 `ShaoyuanCourse`，在 `qa_v2/run.py` 注册 `shaoyuan: ShaoyuanCourse`。  
Run: `cd /tmp/chemistry-video && python3 -m qa_v2.run shaoyuan`  
Expected: fail 0 / warn 0 / skip 0。

- [ ] **Step 4: Commit**

Commit: `feat(shaoyuan): E20 8 页地图驱动分镜与槽位系统实现`

---

### Task 6: 渲染全片与 QA v2 全档验收 (Render & Double QA)

**Files:**
- Output: `/tmp/chemistry-video/out/shaoyuan.mp4`
- Test: `tests/test_run.py`

- [ ] **Step 1: 渲染成片**

Run: `cd /tmp/chemistry-video && npx remotion render src/index.tsx ShaoyuanCourse out/shaoyuan.mp4 --codec=h264 --crf=20`  
Expected: 渲染完成，输出 1080p MP4。

- [ ] **Step 2: 执行 QA v2 全档 `--ocr` 验收**

Run: `cd /tmp/chemistry-video && rm -f /tmp/qa_cache/shaoyuan_*.json && python3 -m qa_v2.run shaoyuan --ocr`  
Expected: fail 0。

- [ ] **Step 3: 抽帧目验**

抽取 8 页终态帧（`起点 + 音频时长 - 0.2s`），核验无文字压图、底图推拉清晰无模糊、四时代叠合平滑。

- [ ] **Step 4: Commit**

Commit: `test(qa): E20 全片渲染完成并通过 QA v2 双档全绿验收`

---

### Task 7: 交付归档与知识沉淀 (Delivery & Documentation)

**Files:**
- Create: `shaoyuan_video/DELIVERY.md`
- Modify: `anheqiao_video/series_registry.md`

- [ ] **Step 1: 撰写 DELIVERY.md**

记录成片规格、MEC/VEC 资产分布、学术争议建模结论、地图视口引擎技术复盘。

- [ ] **Step 2: 更新 series_registry.md**

将 E20 标记为已交付，宣布海淀历史名园 W2 批次全线收官。

- [ ] **Step 3: 最终 Git 提交并推送到 main**

Run: `cd /Volumes/macstudio/video-projects && git push origin main`  
Expected: 远端分支同步完成。
