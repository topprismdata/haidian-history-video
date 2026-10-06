# Task 7 Review: 抽帧与 OCR 缓存审查报告

## 审查对象
- Brief: `/Volumes/macstudio/video-projects/.superpowers/sdd/task-7-brief.md`
- Commit: `6663f9b` (`feat(qa): 抽帧与 OCR 缓存`)
- Diff: `/Volumes/macstudio/video-projects/.superpowers/sdd/review-aca5c6e..6663f9b.diff`

---

## 1. 重点审查项核查

### 1.1 有没有把 OCR 的 box 再乘一次缩放（通过，守住核心红线）
- **核查结果**：**绝对没有二次缩放**。
- **细节证明**：
  - `ocr_page` 实现中：
    ```python
    boxes = r["rec_boxes"]
    boxes = boxes.tolist() if hasattr(boxes, "tolist") else boxes
    res = OcrResult(r["rec_texts"], boxes, r["rec_scores"])
    ```
    原始 `rec_boxes` 仅作类型标准化（numpy 数组转 list），未发生任何坐标乘除或偏移。
  - `text_at` 实现中：
    ```python
    for t, b, s in zip(ocr.texts, ocr.boxes, ocr.scores):
        x1, y1, x2, y2 = b
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        if (rx - pad <= cx <= rx + rw + pad
                and ry - pad <= cy <= ry + rh + pad):
            out.append((t, (x1, y1, x2 - x1, y2 - y1), s))
    ```
    仅完成 `[x1, y1, x2, y2]` 到 `(x, y, w, h)` 的几何表示转换，无任何缩放计算。
  - 依赖检查：本层未定义、未导入、也未调用任何 `scale_of` 或 `plate_to_canvas` 逻辑（换算全权交由外层调用方）。

### 1.2 `_assert_box_format` 是否真的抛异常（通过，硬断言有效拦截）
- **核查结果**：异常硬断言严格生效，非静默打印。
- **代码核查**：
  ```python
  def _assert_box_format(res: OcrResult) -> None:
      if not res.boxes:
          return
      b = res.boxes[0]
      if not (b[2] > b[0] and b[3] > b[1]):
          raise ValueError(
              "rec_boxes 格式异常：首个框 %r 不满足 x2>x1 且 y2>y1。"
              "本 QA 依赖 [x1,y1,x2,y2] 格式（E11 实测 93/93）。" % (b,)
          )
  ```
- **测试验证**：`tests/test_frames.py` 专门编写了 `test_assert_box_format_detects_invalid`，明确断言当首框为 `(800, 60, 300, 40)`（`x2 < x1`）时，`pytest.raises(ValueError, match="rec_boxes 格式异常")`，防呆机制完备。

### 1.3 `render_frame` 签名与参数使用（通过）
- **核查结果**：签名为 `render_frame(composition: str, frame: int, out: pathlib.Path) -> pathlib.Path`。
- **细节验证**：
  - 严格接收外部显式传入的 `composition`（如 `GaoLiangQiaoCourse`）。
  - 全文没有任何 `.capitalize()` 或由 `ep` 拼凑 Composition 名的投机逻辑。
  - 子进程命令直接使用 `["npx", "remotion", "still", "src/index.tsx", composition, str(out), "--frame=%d" % frame, "--log=error"]`，符合 Remotion CLI 标准规范。

### 1.4 `text_at` 用中心点判定与容差（通过，并修正了 brief 样例数值）
- **判定模型**：计算 `cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0`，判定 `cx`、`cy` 是否落在扩张 `pad`（默认 25px）后的槽位矩形内。
- **测试校准**：brief 样例中 `test_text_at_tolerates_small_pad` 给出的测试坐标在数学上并不契合 `(940, 75)` 中心点的越界断言。实现者敏锐发现了这一点，并将槽位坐标修正为：
  - 槽位 `(966, 65, 300, 60)`：左边界 `966 - 25 = 941 > 940`（偏离 26px，超容差被排除，返回 `[]`）。
  - 槽位 `(963, 62, 300, 60)`：左边界 `963 - 25 = 938 <= 940`（偏离 23px，在容差内保留，返回 1 条）。
  严谨性值得赞赏。

### 1.5 缓存失效说明（通过，按要求显著标明）
- **核查结果**：在 `CACHE` 变量定义处与 `ocr_cached` 的 docstring 中均做了醒目明确的警告：
  ```python
  # OCR 结果落盘缓存目录。
  # 注意：缓存文件名以 "%s_p%02d.json" % (ep, page) 命名，并未计算帧图像内容哈希（MD5）。
  # 若修改了文案、排版或样式并重新渲染帧，旧缓存不会自动失效！
  # 此时必须手动清空此缓存目录（rm -rf /tmp/qa_cache），否则 QA 会继续读取旧缓存。
  CACHE = pathlib.Path("/tmp/qa_cache")
  ```
  ```python
  def ocr_cached(...):
      """带落盘缓存的 OCR。同一帧重复跑不重复识别。

      注意：缓存键仅由 (ep, page) 构成，未绑定图像内容哈希。
      如果视频工程重新渲染帧（如修改文案/排版后），必须手动清理缓存目录（如 rm -rf /tmp/qa_cache），
      否则会继续读取旧的 OCR 缓存。
      """
  ```
  已满足“写明重渲后需手动清缓存”的刚性要求。

### 1.6 测试纪律（通过，完全隔离外部慢速依赖）
- **核查结果**：8 个测试全部纯净运行，零网络、零外部模型加载、零 Node/Remotion 调用。
- **测试构成**：
  1. `test_text_at_finds_box_inside`（几何内含）
  2. `test_text_at_converts_box_to_xywh`（坐标格式转换）
  3. `test_text_at_rejects_outside`（几何外拒）
  4. `test_text_at_tolerates_small_pad`（25px 边界容差）
  5. `test_text_at_returns_scores`（置信度保留）
  6. `test_ocr_result_json_roundtrip`（序列化往返）
  7. `test_assert_box_format_detects_invalid`（格式异常报错）
  8. `test_ocr_cached_reads_cache`（缓存命中短路分支，使用虚拟路径验证不调用 OCR）
  无任何偷偷进行的真实 OCR 或端到端运行。

### 1.7 全局单例（通过）
- **核查结果**：
  - `load_ocr` 采用模块级 `_OCR`，并做延迟导入（`from paddleocr import PaddleOCR` 放置在函数内部），确保只在首次识别时耗时 ~4.7s 加载，未被调用的模块（如跑测试集或只做数据检查时）不会产生开销。
  - 在当前单线程 CLI 场景下表现稳定，无并发隐患。

---

## 2. 代码质量检查

### 2.1 Python 3.9 兼容性
- 全部使用 `Optional[X]`、`Tuple[...]`、`List[...]`，没有 `X | None` 语法。
- 没有使用 `match-case` 等高版本语法。
- 完全兼容 Python 3.9.6。

### 2.2 错误处理
- `ocr_cached` 捕获 `(ValueError, KeyError)` 并优雅重算，防止损坏的 json 缓存文件导致流程崩溃。
- `render_frame` 使用 `check=True`，保证 Remotion CLI 抽帧失败时抛出 `CalledProcessError`。
- `_assert_box_format` 及时拦截不合规的坐标数组，避免下游所有槽位静默变空。

### 2.3 Docstring 完整性
- 模块头部明确写明了两大踩坑纪律（格式坑：`[x1,y1,x2,y2]`；空间坑：画布空间 vs 板面空间），传达清楚。

### 2.4 代码微瑕（Minor，不阻碍合入）
- `qa_v2/frames.py` 第 40-41 行：
  ```python
  from qa_v2.data import Episode, Slot
  from qa_v2.geometry import CANVAS, Rect
  ```
  其中 `Episode`、`Slot`、`CANVAS` 在 `frames.py` 中未被直接使用（仅使用了 `Rect` 做类型提示）。属于无害的冗余 import，可后续择机清理。

---

## 3. 结论

- **Spec 合规**：✅
- **代码质量**：Approved（质量优良，无 Critical / Important 问题，仅 1 处 Minor 级别无害 import 冗余）
