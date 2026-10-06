# Task 6: 本体重建全链绿 + 正交出图

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 6: 本体重建全链绿 + 正交出图

**Files:**
- Modify: `e30_shikongqiao_video/3d/build_scene2.py`（仅当 Task 4 冒烟暴露本体相关错时；`pier_plinth/deck_cornice/abutment_ground` 属附属/环境，不动）

**Interfaces:**
- Consumes: facts, bridge_geom2, build_scene2, qa_l2
- Produces: 与 facts 一致的 `e30_bridge.blend`

- [ ] **Step 1: 全链重建**

Run: `cd /Volumes/macstudio/video-projects/e30_shikongqiao_video/3d && blender -b --factory-startup --python build_scene2.py 2>&1 | grep -E "SAVED|翻转|Error"`

- [ ] **Step 2: 正检必须全绿**

Run: `blender -b e30_bridge.blend --python qa_l2.py -- /tmp/l2.json`
Expected: `QA_L2_OK`
Run: `cd /Volumes/macstudio/video-projects && python3 -m pytest e30_shikongqiao_video/tests -v`
Expected: 全过

- [ ] **Step 3: 正交立面出图（M2.5 素颜机位之一）**

Run: `blender -b --python ortho.py -- side 2200 2>&1 | grep WROTE`
Expected: `WROTE .../ortho_side.png`

- [ ] **Step 4: Commit（如有改动）+ 判据快照入库**

```bash
cd /Volumes/macstudio/video-projects
cp /tmp/l2.json e30_shikongqiao_video/3d/refs/l2_baseline.json
git add e30_shikongqiao_video/3d
git commit -m "feat(e30): 本体M2重建全链绿, L2基线快照"
```

---

