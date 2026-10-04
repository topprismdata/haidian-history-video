# Task 7: L3 正交立面配准比对工具

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 7: L3 正交立面配准比对工具

**Files:**
- Create: `e30_shikongqiao_video/3d/register_overlay.py`
- Create: `e30_shikongqiao_video/tests/test_register.py`

**Interfaces:**
- Consumes: `ortho_side.png`（Task 6 渲染）、**T3.5 已冻结的人工掩膜 `3d/refs/ref_mask.png`**（不要重跑自动阈值）
- Produces: `overlay(mask_a, mask_b) -> (iou: float, out_png: str)`；`void_table(mask) -> list[(xc, w)]`；常量 `OVERLAY_IOU_MIN`

**关键约束（2026-10-04 主控量化后确立）**：T3.5 实测 `ref_mask.png` 的桥带 bbox 仅 **843×44 px**，按宽度缩放到 1200 后桥带只有 **62 px 高**，单拱 25-38 px。在这个尺度上，简报原本的自动 `_mask()`（RGB 亮度+饱和度双阈）必然把桥身/水面/天空混在一起——**所以参考侧必须直接读 T3.5 的人工掩膜，禁止重新自动阈值**。渲染侧（`ortho_side.png`）是净色背景，可以自动阈值，也可以让 T6 一并输出人工确认过的掩膜。

- [ ] **Step 1: 写工具（参考侧读人工掩膜；渲染侧自动阈值；两者统一到同尺度）**

```python
# -*- coding: utf-8 -*-
"""L3: 渲染正交立面 vs 参考立面 掩膜 IoU 比对。

参考侧: 直接读 T3.5 冻结的人工掩膜 refs/ref_mask.png(桥带仅 62px 高, 自动阈值必然混桥/水)
渲染侧: 净色背景, 可自动阈值
两者按各自掩膜 bbox 的**宽与高各自独立**归一化到 1200x300(消除比例失配, 见 Step 1.5)
"""
from PIL import Image
import numpy as np, os

OVERLAY_IOU_MIN = 0.60   # [工作值] 初值; Task 7 Step 1.6 扰动标定后修订, 修订须写依据

def _load_mask(path, is_ref):
    """参考侧: 读人工掩膜(白=桥体)。渲染侧: 净色背景自动阈值。"""
    if is_ref:
        a = np.asarray(Image.open(path).convert("L"), np.float32) > 127
        return a.astype(np.uint8)
    return _mask(Image.open(path))


def _mask(im):
    a = np.asarray(im.convert("RGB"), np.float32)
    lum = a.mean(axis=2)
    mx = a.max(axis=2); mn = a.min(axis=2)
    sat = (mx - mn) / (mx + 1e-6)
    # 天空: 高亮低饱和; 水: 低亮度蓝; 桥体: 中高亮度中等饱和的暖白
    return ((lum > 90) & (lum < 235) & (sat > 0.05)).astype(np.uint8)

def _crop_bbox(m):
    ys, xs = np.where(m > 0)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

W, H = 1200, 300   # 宽高各自独立归一化(见 Step 1.5: 比例失配不该由 IoU 承担)


def _norm(m):
    """按 bbox 归一化到 (W,H): 宽高各自独立缩放, 消除两图比例失配。"""
    return np.asarray(Image.fromarray(m * 255).resize((W, H), Image.BILINEAR)) > 127


def overlay(path_a, path_b, out_png, a_is_ref=False, b_is_ref=True):
    ma = _norm(_crop_bbox(_load_mask(path_a, a_is_ref)))
    mb = _norm(_crop_bbox(_load_mask(path_b, b_is_ref)))
    A, B = ma, mb
    inter = (A & B).sum(); union = (A | B).sum()
    iou = float(inter) / max(1, float(union))
    vis = np.zeros((H, W, 3), np.uint8)
    vis[A & B] = (255, 255, 255); vis[A & ~B] = (255, 60, 60); vis[~A & B] = (60, 120, 255)
    Image.fromarray(vis).save(out_png)
    return iou, out_png

if __name__ == "__main__":
    import sys
    iou, out = overlay(sys.argv[1], sys.argv[2], sys.argv[3])
    print("IOU %.4f -> %s" % (iou, out))
```


- [ ] **Step 1.5: 拆指标 + 扰动标定（G2 修订, 调度者 2026-10-04 数值实测后追加）**

**简报的归一化有结构缺陷**：两个掩膜按各自 bbox 宽度缩放、顶部对齐后直接算 IoU。实测：实体**完全相同**、仅 bbox 比例差 19% 时 IoU 已掉到 **0.631**；内容平移 40px 时 0.802。也就是说 IoU 同时混着"复原对不对"和"两张图对齐没有"，而 `SPAN_DISTINCT` 的跨度尚未归因（T2b 开放项），跨度错会被当成复原错。

**因此拆成两个独立指标**：

1. **实体轮廓 IoU（silhouette IoU）**：先按 bbox **宽、高各自独立**归一化（`Image.resize` 到 1200×300，强制同尺寸），消除比例失配，只剩"形状像不像"。
2. **券洞位置表（void table）**：对每个券洞输出 `（包围盒归一化 x 中心, 归一化宽度）`，与参考图逐孔比对。孔洞位置是**尺度无关**的（`xc/桥长`），不受跨度待定影响。

- [ ] **Step 1.6: 扰动标定阈值（G2 裁决: 禁止拍脑袋定 ?值）**

`OVERLAY_IOU_MIN` 不许用初值 0.60。执行标定实验并把结果写进 `register_overlay.py` 顶部的依据注释：

对同一张基线渲染**故意破坏**，记录 IoU(跨度)/IoU(对称性)/IoU(矢高比) 三条曲线：
- **可接受区间**（不改 facts 也能存在的偏差）：±0.5m 纵向分段扰动、墩宽 ±10%
- **不可接受区间**（应当被抓）：跨度整体 ±5%、矢高比 ARCH_RATIO 0.45↔0.55、缺 1 个券洞

在"可接受"与"不可接受"之间取阈值。**若两区间 IoU 无可分性**（即这个指标在本项目上不具判别力），**如实报告无判别力**并写进 FACTS.md，不许挑一个能过的数当阈值。标定脚本留 `3d/refs/calibrate_iou.py` 供复现。

- [ ] **Step 2: 测试（合成掩膜 IoU=1 与故意错位 IoU 下降）**

`e30_shikongqiao_video/tests/test_register.py`：

```python
# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
from PIL import Image
import register_overlay as R

def _save(arr, p):
    Image.fromarray(arr).save(p); return p

def test_perfect_overlap(tmp_path):
    m = np.zeros((200, 800), np.uint8); m[50:150, 50:750] = 255
    a = _save(m, str(tmp_path / "a.png")); b = _save(m.copy(), str(tmp_path / "b.png"))
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"), a_is_ref=True, b_is_ref=True)
    assert iou > 0.99

def test_shift_lowers_iou(tmp_path):
    m = np.zeros((200, 800), np.uint8); m[50:150, 50:750] = 255
    m2 = np.zeros((200, 800), np.uint8); m2[50:150, 90:790] = 255   # 平移40px
    # 纯 bbox 比例差(实体相同)必须被归一化吸收, 不该拉低 IoU
    a = _save(m, str(tmp_path / "a.png")); b = _save(m2, str(tmp_path / "b.png"))
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"), a_is_ref=True, b_is_ref=True)
    assert iou < 0.95
```

- [ ] **Step 3: 用真实图定阈值 + 落判据**

准备 `3d/refs/ref_elevation.jpg`（Task 2 选定的参考立面照）。Run:
`python3 register_overlay.py ortho_side.png refs/ref_elevation.jpg refs/overlay_M2.png`（ortho.py 产物即 ortho_side.png）
记录实体轮廓 IoU 与券洞位置表；若低于标定阈值：先查掩膜/对齐 bug，排除后把真实差距写进 FACTS.md 待办（本体与参考的实际偏差），**不许调阈值迁就**。阈值修订必须在本文件注明依据。

- [ ] **Step 4: Commit**

```bash
cd /Volumes/macstudio/video-projects
git add e30_shikongqiao_video/3d/register_overlay.py e30_shikongqiao_video/tests/test_register.py e30_shikongqiao_video/3d/refs
git commit -m "feat(e30): L3 正交立面配准IoU比对+合成负控测试"
```

---

