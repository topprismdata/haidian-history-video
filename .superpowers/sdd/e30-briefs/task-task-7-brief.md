# Task 7: L3 正交立面配准比对工具

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 7: L3 正交立面配准比对工具

**Files:**
- Create: `e30_shikongqiao_video/3d/register_overlay.py`
- Create: `e30_shikongqiao_video/tests/test_register.py`

**Interfaces:**
- Consumes: `ortho_side.png`（Task 6）、参考图（M0 认可的近正面/立面照, 存 `3d/refs/ref_elevation.jpg`）
- Produces: `overlay(image_a, image_b) -> (iou: float, out_png: str)`；常量 `OVERLAY_IOU_MIN`

- [ ] **Step 1: 写工具（掩膜=非天空非水像素；归一化对齐：按桥体包围盒宽度缩放+底线对齐）**

```python
# -*- coding: utf-8 -*-
"""L3: 渲染正交立面 vs 参考立面 掩膜 IoU 比对。
掩膜定义: 桥体像素 = 亮度非(天空高亮)且非(水面暗蓝) -> 用饱和度+亮度双阈。
阈值是判据参数, 标定后写死并注明依据。"""
from PIL import Image
import numpy as np, os

OVERLAY_IOU_MIN = 0.60   # [工作值] 初值; Task 7 Step 3 用当前基线标定后可修订, 修订须写依据

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

def overlay(path_a, path_b, out_png):
    ma = _crop_bbox(_mask(Image.open(path_a)))
    mb = _crop_bbox(_mask(Image.open(path_b)))
    W = 1200
    ma_r = np.asarray(Image.fromarray(ma * 255).resize((W, int(ma.shape[0] * W / ma.shape[1])))) > 127
    mb_r = np.asarray(Image.fromarray(mb * 255).resize((W, int(mb.shape[0] * W / mb.shape[1])))) > 127
    H = max(ma_r.shape[0], mb_r.shape[0])
    def _pad(m):
        o = np.zeros((H, W), bool); o[:m.shape[0], :] = m; return o
    A, B = _pad(ma_r), _pad(mb_r)
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
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"))
    assert iou > 0.99

def test_shift_lowers_iou(tmp_path):
    m = np.zeros((200, 800), np.uint8); m[50:150, 50:750] = 255
    m2 = np.zeros((200, 800), np.uint8); m2[50:150, 90:790] = 255   # 平移40px
    a = _save(m, str(tmp_path / "a.png")); b = _save(m2, str(tmp_path / "b.png"))
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"))
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

