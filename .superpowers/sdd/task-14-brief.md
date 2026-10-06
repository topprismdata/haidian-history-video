## Task 14: 端到端验收与负控制留证

**Files:**
- Create: `docs/qa/2026-10-01-qa-v2-e11-report.md`

**Interfaces:**
- Consumes: 全部
- Produces: 验收报告文档

- [ ] **Step 1: 跑 E11 全档并留证**

```bash
cd /tmp/chemistry-video
python3 -m qa_v2.run shucun --full 2>&1 | tee /tmp/qa_e11_full.txt
```

- [ ] **Step 2: 故意破坏，验证判据能抓**

```bash
cd /tmp/chemistry-video
cp src/shucun/data/pages.config.ts /tmp/pc_backup.ts
# ① 改错一个数字
python3 - <<'PY'
import pathlib
p = pathlib.Path("src/shucun/data/pages.config.ts")
s = p.read_text(encoding="utf-8")
p.write_text(s.replace('"1485"', '"1486"', 1), encoding="utf-8")
PY
python3 -m qa_v2.run shucun --ocr 2>&1 | grep -E "NUMBER_MISMATCH|判定"
# 期望：出现 NUMBER_MISMATCH，判定：不通过
```

记录输出，然后恢复：

```bash
cd /tmp/chemistry-video
cp /tmp/pc_backup.ts src/shucun/data/pages.config.ts
```

再验第二类（重叠）：

```bash
cd /tmp/chemistry-video
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("src/shucun/data/slots.json")
d = json.loads(p.read_text(encoding="utf-8"))
# 让 p02 的两个说明框叠在一起
s = d["p02"]["slots"]
for x in s:
    if x["id"] == "note_right":
        x["x"] = s[[y["id"] for y in s].index("note_left")]["x"]
p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
PY
python3 -m qa_v2.run shucun 2>&1 | grep -E "SLOT_OVERLAP|判定"
# 期望：出现 SLOT_OVERLAP，判定：不通过
git checkout src/shucun/data/slots.json
```

- [ ] **Step 3: 跑全量测试确认无回归**

```bash
cd /tmp/chemistry-video && python3 -m pytest tests/ -v
```
Expected: 全部 PASS

- [ ] **Step 4: 写验收报告**

`docs/qa/2026-10-01-qa-v2-e11-report.md` 内容模板：

```markdown
# QA v2 在 E11《树村》上的验收报告

日期：2026-10-01
命令：`python3 -m qa_v2.run shucun --full`

## 结果

（粘贴 /tmp/qa_e11_full.txt 全文）

## 负控制留证

| 判据 | 负控制方法 | 实际结果 |
|---|---|---|
| L3 | 槽位平移 300px 到插画区 | 0 个槽位仍判有文本 ✓ |
| L4-a | 文案 1485 → 1486 | 报 NUMBER_MISMATCH ✓ |
| L1 | 两个说明框坐标改为重叠 | 报 SLOT_OVERLAP ✓ |

## 各层耗时

| 层 | 单页耗时 | 8 页合计 |
|---|---|---|
| L1+L2 | （填实测） | |
| L3+L5+L6 | （填实测） | |
| L4 | （填实测） | |

## 已知限制

（照抄 spec §8 风险表里仍然成立的项）
```

- [ ] **Step 5: 提交**

```bash
cd /Volumes/macstudio/video-projects
git add docs/qa/2026-10-01-qa-v2-e11-report.md
git commit -m "test(qa): E11 端到端验收 + 负控制留证

三类破坏均被抓：改错数字(NUMBER_MISMATCH) / 槽位重叠(SLOT_OVERLAP) /
负控制证明 L3 非恒真。报告含各层实测耗时。"
```

---

## Self-Review

**1. Spec 覆盖检查**

| Spec 章节 | 对应 task |
|---|---|
| §5.2 L1 数据一致性（6 项检查） | Task 5 ✓ |
| §5.2 L2 几何可行性 | Task 6 ✓ |
| §5.2 L3 渲染存在性 | Task 8 ✓ |
| §5.2 L4-a 数字严格 | Task 11 ✓ |
| §5.2 L4-b 专名严格 | Task 11 ✓ |
| §5.2 L4-c 字幕交叉 | Task 12 ✓ |
| §5.2 L5 溢出检测 | Task 9 ✓ |
| §5.2 L6 tag 槽 | Task 10 ✓ |
| §5.1 开关（`--ocr` / `--full` / `--json`） | Task 13 ✓ |
| §6 负控制 | Task 8（`assert_negative_control`）+ Task 14（留证） ✓ |
| §7 实现顺序 | 本计划顺序一致 ✓ |
| §8 风险：OCR 版本差异 | Task 7 `_assert_box_format` ✓ |
| §8 风险：专名表缺失报 skip | Task 11 ✓ |
| §8 风险：warn 不阻塞退出码 | Task 4 + Task 13 ✓ |
| §8 风险：OCR 速度 | Task 7 缓存 ✓ |
| §9 验收标准 | Task 14 ✓ |

**2. 占位符扫描**：无 TBD / TODO / 「类似 Task N」。

**3. 类型一致性检查**

- `Finding(layer, page, slot, level, code, message, detail=None)` —— Task 4 定义，Task 5/6/8/9/10/11/12 使用，签名一致 ✓
- `Slot(id, x, y, w, h)` —— Task 3 定义，Task 5/8 使用 ✓
- `Page(number, plate, slots, items)` —— Task 3 定义，全书一致 ✓
- `OcrResult(texts, boxes, scores)` —— Task 7 定义，Task 8/11/12 使用 ✓
- `text_at(ocr, rect, pad=25)` 返回 `[(text, (x,y,w,h), score)]` —— Task 7 定义，Task 8/11 使用 ✓
- `plate_to_canvas(plate, x, y, w, h)` —— Task 1 定义，Task 8/9/10/11/12 使用 ✓
- `check_l1(ep)` / `check_l2(ep)` 返回 `List[Finding]` —— Task 5/6 定义，Task 13 使用 ✓
- `run_episode(name, use_ocr, full)` 返回 `List[Finding]` —— Task 13 定义 ✓

**Self-Review 发现并已修复的一处**：`qa_v2/run.py` 的 `_frame_for` 原先调用
`render_frame(ep, ...)`，而 Task 7 的 `render_frame` 内部用
`"%sCourse" % ep.capitalize()` 拼 Composition 名。`shucun`/`dazhongsi` 等恰好对，
但 `gaoliangqiao` → `Gaoliangqiao`，实际注册名是 `GaoLiangQiaoCourse`
—— 在旧集上会直接报「Composition 不存在」。

已改：`render_frame(composition, frame, out)` 收显式注册名，调用方从
`COMPOSITION_OVERRIDES` 取；并补
`test_composition_overrides_covers_all_registered_episodes` 守住这条。

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-10-01-qa-v2-implementation.md`**

Two execution options:

**1. Subagent-Driven (recommended)** — 每个 task 派一个全新 subagent，task 之间我来 review，迭代快

**2. Inline Execution** — 在当前 session 里按 batch 执行，带检查点

**Which approach?**
