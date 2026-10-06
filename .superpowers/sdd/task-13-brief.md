## Task 13: 统一入口与 CLI

**Files:**
- Create: `qa_v2/run.py`
- Create: `tests/test_run.py`
- Modify: `qa_all.py`（改为薄壳，转调 `qa_v2/run.py`）

**Interfaces:**
- Consumes: 全部 check 模块
- Produces:
  - `run_episode(ep: str, use_ocr: bool = False, full: bool = False) -> List[Finding]`
  - `main(argv: List[str]) -> int` —— 返回退出码（0=通过，1=有 fail）
  - `COMPOSITION_OVERRIDES = {"shucun": "ShucunCourse", ...}` —— 集名 → Composition id

- [ ] **Step 1: 写失败的测试**

`tests/test_run.py`：

```python
import json
import pathlib

from qa_v2.run import parse_args, exit_code, COMPOSITION_OVERRIDES


def test_parse_args_defaults():
    a = parse_args(["shucun"])
    assert a.episodes == ["shucun"]
    assert a.use_ocr is False
    assert a.full is False
    assert a.as_json is False


def test_parse_args_flags():
    a = parse_args(["shucun", "--ocr", "--full", "--json"])
    assert a.use_ocr and a.full and a.as_json


def test_parse_args_multiple_episodes():
    a = parse_args(["shucun", "dazhongsi"])
    assert a.episodes == ["shucun", "dazhongsi"]


def test_exit_code_zero_when_no_fail():
    from qa_v2.report import Finding
    assert exit_code([Finding("L1", 1, "a", "warn", "X", "m")]) == 0
    assert exit_code([Finding("L1", 1, "a", "skip", "X", "m")]) == 0


def test_exit_code_one_on_fail():
    from qa_v2.report import Finding
    assert exit_code([Finding("L1", 1, "a", "fail", "X", "m")]) == 1


def test_composition_overrides_covers_shucun():
    assert COMPOSITION_OVERRIDES["shucun"] == "ShucunCourse"


def test_composition_overrides_covers_all_registered_episodes():
    """集名 → Composition 映射必须完整，且不是 capitalize() 的结果。

    `gaoliangqiao`.capitalize() → `Gaoliangqiao`，但实际注册名是
    `GaoLiangQiaoCourse`；靠拼名字会在旧集上直接报「Composition 不存在」。
    """
    assert set(COMPOSITION_OVERRIDES) >= {
        "yimuyuan", "niangniangfu", "xisanqi", "gaoliangqiao",
        "dazhongsi", "landianchang", "shucun",
    }
    for ep, comp in COMPOSITION_OVERRIDES.items():
        assert comp.endswith("Course")
        assert comp != "%sCourse" % ep.capitalize() or ep in (
            "shucun", "dazhongsi", "xisanqi", "yimuyuan", "niangniangfu",
            "landianchang",
        ), "%s 的映射是 capitalize() 拼的，需人工确认" % ep
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_run.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.run'`

- [ ] **Step 3: 写最小实现**

`qa_v2/run.py`：

```python
"""统一入口：跑一集的七层验收。

    python3 -m qa_v2.run shucun            # L1/L2/L3/L5/L6（快，~2s/页）
    python3 -m qa_v2.run shucun --ocr      # 加 L4（~2min/页，8 页约 2 分钟）
    python3 -m qa_v2.run shucun --full     # 全开
    python3 -m qa_v2.run shucun --json     # 机读输出

只有 fail 阻塞退出码（spec §10.2）：历史集的 warn 噪声不应淹没真问题。
"""
import argparse
import pathlib
import sys
from typing import Dict, List

from qa_v2.checks_content import check_l4a, check_l4b, check_l4c, load_names
from qa_v2.checks_data import check_l1, check_l2
from qa_v2.checks_render import (
    check_l3, check_l5, check_l6, assert_negative_control,
)
from qa_v2.data import load_episode
from qa_v2.frames import ocr_cached, render_frame
from qa_v2.report import Finding, render_json, render_text

ROOT = pathlib.Path("/tmp/chemistry-video")
FRAME_DIR = pathlib.Path("/tmp/qa_frames")

# 集名 → Composition id（Remotion 注册名是驼峰）
COMPOSITION_OVERRIDES = {
    "yimuyuan": "YimuyuanCourse",
    "niangniangfu": "NiangniangfuCourse",
    "xisanqi": "XisanqiCourse",
    "gaoliangqiao": "GaoLiangQiaoCourse",
    "dazhongsi": "DazhongsiCourse",
    "landianchang": "LandianchangCourse",
    "shucun": "ShucunCourse",
}


def _frame_for(ep, page, use_ocr):
    """抽该页终态帧。--ocr 时顺带跑 OCR 并缓存。"""
    out = FRAME_DIR / ep.name
    out.mkdir(parents=True, exist_ok=True)
    png = out / ("p%02d.png" % page.number)
    if not png.exists():
        render_frame(COMPOSITION_OVERRIDES[ep.name],
                     ep.final_frame(page.number), png)
    if use_ocr:
        return png, ocr_cached(ep, page.number, png)
    return png, None


def run_episode(name, use_ocr=False, full=False):
    """跑一集的全部适用层，返回 findings。"""
    ep = load_episode(name)
    findings = []

    # L1 / L2：纯数据
    findings += check_l1(ep)
    findings += check_l2(ep)

    names = load_names()
    ocr_by_page = {}
    for page in ep.pages:
        try:
            png, ocr = _frame_for(name, page, use_ocr)
        except Exception as exc:                      # 抽帧/OCR 失败
            findings.append(Finding(
                "L3", page.number, None, "fail", "RENDER_FAILED",
                "抽帧或 OCR 失败：%s" % exc))
            continue

        findings += check_l5(page, png)
        findings += check_l6(page, png)

        if ocr is None:
            continue
        ocr_by_page[page.number] = ocr
        findings += check_l3(page, ocr)
        if use_ocr:
            findings += check_l4a(page, ocr)
            findings += check_l4b(page, ocr, names)
            # 负控制：证明 L3/L4 不是恒真
            missed = assert_negative_control(page, ocr)
            if missed:
                findings.append(Finding(
                    "L3", page.number, None, "fail", "NEGATIVE_CONTROL_FAIL",
                    "负控制失败：%d 个槽位平移后仍判有文本，判据恒真"
                    % missed))
    if use_ocr:
        findings += check_l4c(ep, ocr_by_page)
    return findings


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="qa_v2.run", description="七层验收")
    p.add_argument("episodes", nargs="+")
    p.add_argument("--ocr", action="store_true",
                   help="开启 L4 内容闭环（慢，约 2 分钟/集）")
    p.add_argument("--full", action="store_true",
                   help="等价于 --ocr，并额外提示运行字幕验收")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="输出 JSON")
    return p.parse_args(argv)


def exit_code(findings):
    from qa_v2.report import summarize
    return 1 if summarize(findings).get("fail") else 0


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    rc = 0
    for name in args.episodes:
        if name not in COMPOSITION_OVERRIDES:
            print("未知集 %s，可选 %s" % (name, list(COMPOSITION_OVERRIDES)))
            rc = 1
            continue
        findings = run_episode(name, use_ocr=(args.ocr or args.full),
                              full=args.full)
        print(render_json(findings, name) if args.as_json
              else render_text(findings, name))
        if exit_code(findings):
            rc = 1
    if args.full:
        print("\n提示：字幕/音频验收请另跑 "
              "/tmp/.asr-venv/bin/python "
              "/Volumes/macstudio/video-projects/scripts/verify_subtitles_asr.py")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_run.py -v`
Expected: PASS —— 5 passed

- [ ] **Step 5: 端到端验证（E11 快档）**

Run: `cd /tmp/chemistry-video && python3 -m qa_v2.run shucun`
Expected:
```
=== shucun ===
  → fail 0 / warn 0 / skip 0 / info 0
  判定：通过
```

若有 fail，逐条修；**不要调松阈值来让它过**。

- [ ] **Step 6: 提交**

```bash
cd /tmp/chemistry-video
git add qa_v2/run.py tests/test_run.py
git commit -m "feat(qa): 统一入口与 CLI

python3 -m qa_v2.run <集> [--ocr] [--full] [--json]
默认快档（~2s/页），--ocr 开内容闭环（~2min/集）。
只有 fail 阻塞退出码。"
```

- [ ] **Step 7: qa_all.py 改薄壳**

保持历史命令 `python3 qa_all.py shucun` 可用：

```python
#!/usr/bin/env python3
"""qa_all.py — 保留为薄壳，转调 qa.run。

新的七层验收在 qa_v2/ 包里（见 docs/superpowers/specs/2026-10-01-qa-v2-design.md）。
本文件保留只为兼容历史命令；新代码请加到 qa_v2/ 下。

用法：
    python3 qa_all.py shucun          # 等价 python3 -m qa_v2.run shucun
    python3 qa_all.py shucun --ocr    # 开启内容闭环
"""
import sys

from qa_v2.run import main, COMPOSITION_OVERRIDES

if __name__ == "__main__":
    sys.exit(main())
```

Run: `cd /tmp/chemistry-video && python3 qa_all.py shucun && echo "薄壳可用"`

- [ ] **Step 8: 提交薄壳**

```bash
cd /tmp/chemistry-video
git add qa_all.py
git commit -m "refactor(qa): qa_all.py 改薄壳，转调 qa.run

保留历史命令可用性；新判据加到 qa/ 包下。"
```

---

