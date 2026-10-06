# QA v2 核心缺陷修复报告（C1 / C2 / I1 / I2 + Minors）

- **日期**：2026-10-01
- **分支**：`qa-v2`
- **关联审查**：`.superpowers/sdd/final-review.md`

---

## 1. 修复清单与修改位置

### C1（Critical）：负控制平移结构性假阳性修复
- **修改位置**：`qa_v2/checks_render.py` (`assert_negative_control`, `_find_negative_control_rect`, `NegativeControlResult`)
- **修改内容**：
  1. **自适应几何避让与不相交搜索**：实现 `_find_negative_control_rect`，平移候选落点必须与**所有真槽及自身原矩形不相交**（`overlap_ratio == 0`）。优先尝试四向基础位移（±shift）、槽宽/槽高外推位移（`s.w + 50`, `s.h + 50`）与对角位移；若全部碰撞或超出板面边界，则回退至 100px 步长的网格搜索。
  2. **跳过无法构造负控制的槽位**：若在板面上无论如何都找不到不撞任何槽位的空白落点（例如密集表格 P3 的部分内嵌单元格、全屏覆盖槽位），将该槽标记为 `untestable` 并**跳过**，绝不误计入 `not_caught`。
  3. **负控制路径容差归零**：负控制路径上的 `text_at` 强制设置 `pad=0`（正常检测保持 `pad=25`），彻底消除了宽槽在边缘 25px 容差处罩住自身或邻槽字迹的问题。
- **单测补充**（`tests/test_checks_render.py`）：
  - `test_negative_control_avoids_neighbor_slot_and_does_not_false_fail`：平移落点撞邻槽时自动避让到空旷区，不计未命中。
  - `test_negative_control_uses_pad_zero`：验证 `pad=0` 生效（15px 外不命中，槽内命中，35px 外都不命中）。
  - `test_negative_control_skips_untestable_slots`：全板满槽无法构造时跳过并记录 untestable，不误判 fail。

### C2（Critical）：L4-a 两侧归一口径不一致修复
- **修改位置**：`qa_v2/checks_content.py` (`check_l4a`)
- **修改内容**：
  `got` 侧由 `set(extract_numbers(normalize_punct(got_raw)))` 改为 `set(extract_numbers(got_raw))`。
  `normalize_punct` 会把 `1799 → 1800 → 1801` 中的箭头剥离，压缩成单个 token `179918001801`，导致与 `want` 侧 `{1799, 1800, 1801}` 不一致而报 `NUMBER_MISMATCH`。改后两端统一直接使用 `extract_numbers`，保证归一口径完全对称。
- **单测补充**（`tests/test_checks_content.py`）：
  - `test_l4a_arrow_separated_numbers_match`：钉住真实 E11 P7 `"1799 → 1800 → 1801"` 场景不报 `NUMBER_MISMATCH`。

### I1（Important）：L1 平台一致性检查补齐
- **修改位置**：`qa_v2/checks_data.py` (`check_l1`), `qa_v2/data.py` (`Episode`, `load_episode`)
- **修改内容**：
  1. `Episode` 支持 `data_dir` 属性并在 `load_episode` 中自动绑定；若无数据目录（如单元测试的 mock episode）则安全跳过外部文件检查，不破坏既有 113 个测试。
  2. `check_l1` 增加对 `pageMap.ts` 与 `subtitles.ts` 的存在性检查，缺失报 `PAGEMAP_MISSING` / `SUBTITLES_MISSING`。
  3. 增加页数一致性比对：
     - 使用 `_nums` 正则剥除注释后解析 `pageMap.ts` 的 `PAGE_DURATIONS_SEC` 数组（防止匹配到 `// p01` 中的数字），比对页数。
     - 解析 `subtitles.ts` 顶层页码键 `re.findall(r"[\{\,]\s*[\"']?(\w+)[\"']?\s*:\s*\[", text)`，比对页数。
     - 若与 `ep.pages` 不符，报 `PAGE_COUNT_MISMATCH`。
  4. 检查槽位配置总数与单页槽数，空槽报 `NO_SLOTS` / `PAGE_HAS_NO_SLOTS`。
- **单测补充**（`tests/test_checks_data.py`）：
  - `test_l1_platform_consistency_detects_missing_files`
  - `test_l1_platform_consistency_detects_page_count_mismatch`
  - `test_l1_platform_consistency_passes_when_aligned`
  - `test_l1_detects_no_slots`

### I2（Important）：快档 L3 处理（选择方案 b）
- **修改位置**：
  - `qa_v2/run.py`（更新 module docstring）
  - `docs/superpowers/specs/2026-10-01-qa-v2-design.md` §5.1
- **选择与论证**：选择 **(b) 同步修改 spec 与 docstring，诚实明示快档不含 L3**。
  - *原因*：L3 的核心判据是「槽内必须有属于该槽的 OCR 文本」。如果为快档制造一个无 OCR 的 L3 兜底（如单纯测是否有墨），会重蹈旧 QA 覆辙（对插画深色区域恒真，空白区 583 墨像素照样通过）。快档的设计定位是纯数据预检（L1/L2）与无 OCR 的渲染图层检查（L5/L6），高频秒级运行；依赖精确文本识别的 L3 与内容闭环 L4 统一收口在 `--ocr` / `--full` 档运行。代码与文档口径保持完全一致。

### Minors 顺手清理
- `qa_v2/run.py`：删除了未使用的 `typing.Dict` 导入。
- `qa_v2/checks_render.py`：合并了对 `qa_v2.geometry` 的双重导入（`Rect, plate_to_canvas`）。
- `qa_v2/checks_content.py`：删除了死常量 `_VOLUME_RE = None`。

---

## 2. C1 的新返回值语义

`assert_negative_control` 返回自定义结构体 `NegativeControlResult(int)`：
1. **继承 `int`**：数值大小代表 `not_caught`（负控制未命中的槽位数，即判据恒真的槽数）。
   - 保留原调用点所有语义：`if missed:` 在 `not_caught > 0` 时为真，`missed == 0` 完全兼容既有测试与判断。
2. **携带属性 `untestable`**：代表无法在板面上找到与任何槽位（及自身）不相交的空白区而被跳过的槽位数。
3. **支持解包**：`not_caught, untestable = assert_negative_control(page, ocr)`。
4. **格式化与打印**：`repr` 输出形如 `NegativeControlResult(not_caught=0, untestable=13)`，既能精准报警判据恒真，又能统计无法构造负控制的密集槽位。

---

## 3. 测试结果与执行输出

### 3.1 单元测试全量验证（121 passed）
```bash
$ cd /Volumes/macstudio/video-projects && python3 -m pytest tests/ -v
pytest: 121 passed in 0.60s
```
- 原 113 个测试全部 PASS。
- 新增 8 个针对性单元测试全过（C1: 3 个，C2: 1 个，I1: 4 个）。

### 3.2 快档验收（E11 树村）
```bash
$ cd /tmp/chemistry-video && python3 -m qa_v2.run shucun
=== shucun ===
  ⚠ [warn] P2/note_left  预计需 92px / 槽高 78px（3 行 @22px）
        lines=3
        ratio=1.18
  ⚠ [warn] P2/note_right  预计需 92px /槽高 78px（3 行 @22px）
        lines=3
        ratio=1.18
  ⚠ [warn] P5/note_left  预计需 112px / 槽高 86px（4 行 @20px）
        lines=4
        ratio=1.3
  -> fail 0 / warn 3 / skip 0 / info 0
  判定：通过
```
- **耗时**：0.92 秒。
- **结果**：`fail 0 / warn 3 / 判定：通过`。

### 3.3 `--ocr` 验收（清缓存后冷跑）
```bash
$ rm -f /tmp/qa_cache/shucun_*.json && cd /tmp/chemistry-video && python3 -m qa_v2.run shucun --ocr
=== shucun ===
  ✗ [fail] P4/-  负控制失败：1 个槽位平移后仍判有文本，判据恒真
  ✗ [fail] P3/r7_hall  数字对不上：期望 [65]，读回 [6539]
  ✗ [fail] P3/r7_officer  数字对不上：期望 [1485]，读回 [14851167]
  ✗ [fail] P3/r7_total  数字对不上：期望 [1550]，读回 [15501206]
  ✗ [fail] P3/r8_hall  数字对不上：期望 [26, 39]，读回 [3926]
  ✗ [fail] P3/r8_officer  数字对不上：期望 [315, 1167]，读回 [1167315]
  ✗ [fail] P3/r8_total  数字对不上：期望 [341, 1206]，读回 [1206341]
  ✗ [fail] P3/r3_flag  专名对不上：缺 正黄旗
  ✗ [fail] P8/ep1_text  专名对不上：缺 正黄旗
  ✗ [fail] P3/r1_officer  数字 [1485] 在该页口播稿里找不到
  ✗ [fail] P3/r1_total  数字 [1550] 在该页口播稿里找不到
  ✗ [fail] P3/r2_officer  数字 [1464] 在该页口播稿里找不到
  ✗ [fail] P3/r2_total  数字 [1529] 在该页口播稿里找不到
  ✗ [fail] P3/r3_officer  数字 [1485] 在该页口播稿里找不到
  ✗ [fail] P3/r3_total  数字 [1550] 在该页口播稿里找不到
  ✗ [fail] P3/r4_officer  数字 [1467] 在该页口播稿里找不到
  ✗ [fail] P3/r4_total  数字 [1532] 在该页口播稿里找不到
  ✗ [fail] P3/r5_officer  数字 [1485] 在该页口播稿里找不到
  ✗ [fail] P3/r5_total  数字 [1550] 在该页口播稿里找不到
  ✗ [fail] P3/r6_officer  数字 [1455] 在该页口播稿里找不到
  ✗ [fail] P3/r6_total  数字 [1520] 在该页口播稿里找不到
  ✗ [fail] P3/r7_officer  数字 [1485] 在该页口播稿里找不到
  ✗ [fail] P3/r7_total  数字 [1550] 在该页口播稿里找不到
  ✗ [fail] P3/r8_officer  数字 [315, 1167] 在该页口播稿里找不到
  ✗ [fail] P3/r8_total  数字 [341, 1206] 在该页口播稿里找不到
  ✗ [fail] P4/note_right  数字 [1000] 在该页口播稿里找不到
  ✗ [fail] P5/note_left  数字 [1600] 在该页口播稿里找不到
  ✗ [fail] P5/note_right  数字 [1626] 在该页口播稿里找不到
  ⚠ [warn] P2/note_left  预计需 92px / 槽高 78px（3 行 @22px）
  ⚠ [warn] P2/note_right  预计需 92px / 槽高 78px（3 行 @22px）
  ⚠ [warn] P5/note_left  预计需 112px / 槽高 86px（4 行 @20px）
  -> fail 28 / warn 3 / skip 0 / info 0
  判定：不通过
```

---

## 4. 仍然存在的已知限制（如实披露）

遵循测试纪律，**未调松阈值以迎合通过**，如实归因当前 `--ocr` 的 28 条 fail：

1. **P7/title 缺陷已消除**：
   - 之前因 `normalize_punct` 不对称报错的 P7 `1799 → 1800 → 1801`，在口径对齐后**完全消除**，0 误报。
2. **负控制假阳性已大幅消除**：
   - 修复前 8 页全报负控制失败（占 8 条 fail）；
   - 修复后除 P4 外，其余 7 页全部为 0 负控制 fail；
   - **P4 残留 1 条负控制 fail 的根因**：`note_right` 槽位平移到画布 `(1168, 456, 622, 176)` 后，恰好罩住了插画底图上的篆书印章背景大字「蜀」（OCR 置信度仅 0.109）。这属于极端底图插画文字误触发，后续可考虑在负控制判据中引入置信度过滤（例如只统计 OCR 置信度 ≥ 0.50 的框）。
3. **密集表格粘连（6 条 fail）**：
   - P3 表格的 `6539`、`14851167`、`15501206` 等为 PP-OCRv6 将密集相邻行合并成单框的已知机械限制。
4. **专名漏检（2 条 fail）**：
   - P3 及 P8 的「正黄旗」为印章/小字，属于 OCR 漏检真实阳性。
5. **口播稿交叉差异（19 条 fail）**：
   - 表格内部数据口播未逐项念出；文案「逾千年」对应数字 1000 口播未念。
