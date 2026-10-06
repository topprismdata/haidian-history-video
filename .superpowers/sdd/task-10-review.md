# Task 10: L6 tag 槽判据 Review 报告

- **审查对象**：Commit `95b02bd`（`feat(qa): L6 tag 槽独立判据`），Base: `50b4afe`
- **审查输入**：
  - Brief: `/Volumes/macstudio/video-projects/.superpowers/sdd/task-10-brief.md`
  - Diff: `/Volumes/macstudio/video-projects/.superpowers/sdd/review-50b4afe..95b02bd.diff`

---

## 1. Spec 合规审查

| 审查项 | 要求 | 实测/代码现状 | 结论 |
|---|---|---|:---:|
| **接口与函数** | `check_l6(page: Page, png: Path) -> List[Finding]` | 函数签名、入参及返回类型完全匹配 | ✅ |
| **阈值常量原样保留** | `WHITE_MIN = 200`, `WHITE_MAX_RATIO = 0.40`, `WHITE_MIN_RATIO = 0.01` | 3 个常量原样定义在模块级别，附带显式类型注解 | ✅ |
| **判定级别区分** | < 1% 为 `fail` (`TAG_SLOT_EMPTY`)；> 40% 为 `warn` (`TAG_SLOT_ALL_WHITE`) | 代码完全按此分支生成不同级别的 `Finding` | ✅ |
| **RGB vs 灰度判据** | `convert("RGB")` + `sub.min(axis=2) > WHITE_MIN` | 严格使用 RGB 三通道最小值阈值，未退化为灰度 | ✅ |
| **tag 槽识别机制** | 使用 `items[0].is_tag`（非硬编码 ID） | 按 `items[0].is_tag` 过滤槽位，单元测试亦匹配此机制 | ✅ |
| **L3 / L5 零改动约束** | L3 / L5 相关代码及测试一行不改 | 检查 diff，L3/L5 逻辑零修改，全部为尾部追加 | ✅ |
| **测试完备度** | 4 个新测试（含合成图与 E11 真帧测试） | 4 个测试全部追加在 `test_checks_render.py` 中 | ✅ |
| **真帧测试与资源防漏** | `if not png.exists()` 保护；输出至 `/tmp`；无 PNG 入 git | 测试带存在性缓存保护；帧落在 `/tmp`；git diff 仅 2 个代码文件 | ✅ |

### 细项核验

1. **L3 / L5 零改动确认**：
   - `qa_v2/checks_render.py`：仅在 `check_l5` 函数下方追加了 L6 常量及 `check_l6` 函数（第 27~71 行），没有改动、删除或替换 L3/L5 的任何现有代码。
   - `tests/test_checks_render.py`：仅在 `test_l5_fails_when_text_touches_edge` 下方追加 L6 测试及 `_tmp_png` 辅助函数（第 88~148 行），历史测试全部保持原样。

2. **RGB 判据纯粹性**：
   - 代码严格采用 `a = np.array(Image.open(str(png)).convert("RGB"))`。
   - 判据为 `white = (sub.min(axis=2) > WHITE_MIN).mean()`。
   - 物理语义：取 RGB 三通道的最小值与 `WHITE_MIN (200)` 比较，只有当 R、G、B 均大于 200 时才确认为白像素，彻底避免了深色彩色底板在灰度化或均值运算下被误算为白字的问题。这与 L5 专门针对浅色底板提取深墨而采用灰度（`convert("L")`）形成了合理的物理分工。

3. **tag 槽识别源头**：
   - 遍历 `page.slots`，查找挂载的 `items`，通过 `items[0].is_tag` 进行分支过滤。
   - 这直接对应了底层数据模型 `TextItem` 的真实语义（`kind == "tag"`），而非依赖 `TAG_IDS = {"evidence_tag"}` 等脆弱的名称集合，使得判据具备跨集通用性。

4. **阈值与上下界级别语义**：
   - `WHITE_MIN_RATIO = 0.01`（1%）：白像素占比低于 1% 产生级别为 `"fail"` 的 `TAG_SLOT_EMPTY`，表明 tag 槽完全未渲染出白字；
   - `WHITE_MAX_RATIO = 0.40`（40%）：白像素占比高于 40% 产生级别为 `"warn"` 的 `TAG_SLOT_ALL_WHITE`，提示可能截到了浅色底板而非文字块；
   - 两者级别一严（确定性缺陷）一松（可疑预警），逻辑严密。

5. **真帧测试实现与环境安全**：
   - `test_real_shucun_passes_l6` 检查了 E11《树村》全 8 页。
   - 具备 `if not png.exists():` 保护，已抽取的帧不再重复渲染，保证了回归测试的秒级运行。
   - 正确适配了 `render_frame("ShucunCourse", ep.final_frame(p.number), png)`（修复了 Brief 伪代码中参数个数与合成名的小偏差）。
   - 帧图片保存在 `/tmp/qa_shucun_frames/`，完全独立于代码仓库。检查 diff 确认只有两个 `.py` 文件变动，没有任何临时图片或二进制文件被提交。

---

## 2. 代码质量审查

### 2.1 Python 3.9 兼容性
- 函数签名与局部变量使用 `List[Finding]`, `page: Page`, `png: Path`, `int`, `float` 等类型注解，未引入 Python 3.10+ 的联合类型（如 `X | None`）或 `match-case` 语法。
- 语法与标准库使用与目标环境 Python 3.9.6 完全兼容。

### 2.2 几何与边界防御
- **跨空间坐标变换**：正确调用 `plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)`，将板面槽位坐标换算至渲染帧画布像素空间。
- **四向越界截断**：
  - `x1, y1 = min(W, rx + rw), min(H, ry + rh)`
  - `sub = a[max(0, ry):y1, max(0, rx):x1]`
  - 对画布上、下、左、右四个边界做了严密裁剪，即使槽位部分甚至全部飞出画布边缘也不会产生 slice 越界崩溃。
- **空切片防护**：
  - `if sub.size == 0: continue`
  - 防御了当槽位完全在画布外侧时切片大小为 0 导致后续 `.mean()` 抛出 `ZeroDivision` 或 NaN 警告。
- **空槽处理**：
  - `if not items or not items[0].is_tag: continue`
  - 对无文本关联的槽或非 tag 槽静默跳过，无多余误报。

### 2.3 Docstring 与工程可维护性
- docstring 直击核心痛点：明确交代了旧版 `qa_all.py` 直接排除导致证据标签零覆盖的严重盲区，并基于 E11 实测 8 个证据槽的真实数据给出了有效性背书。

---

## 3. 分级发现 (Findings)

- **Critical**：无
- **Important**：无
- **Minor**：
  - `qa_v2/checks_render.py` 中的 `from PIL import Image` 写在 `check_l6` 函数内部。由于文件顶部在 Task 9 时已导入过其他工具库，后续例行整理时可将 `Image` 移至文件顶部。当前行为正确且无副作用。
  - `tests/test_checks_render.py` 内部 `_tmp_png` 使用了 `tempfile.mkdtemp()` 创建目录，若测试异常中断可能在系统 `/tmp` 留下孤儿空目录（pytest 会在系统重启或自身策略下清理）。可考虑在未来统一使用 pytest 的 `tmp_path` fixture。当前单测运行完全正常。

---

## 4. 结论

- **Spec 合规**：✅
- **代码质量**：Approved (无阻碍性缺陷，架构与工程实践良好)
