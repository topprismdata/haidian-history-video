## Task 4: Finding 与报告输出

**Files:**
- Create: `qa_v2/report.py`
- Create: `tests/test_report.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `class Finding: layer: str; page: Optional[int]; slot: Optional[str]; level: str; code: str; message: str; detail: Optional[dict]`
    - `level ∈ {"fail", "warn", "skip", "info"}`
  - `def summarize(findings: List[Finding]) -> Dict[str, int]` —— 各 level 计数
  - `def render_text(findings: List[Finding], ep: str) -> str` —— 终端可读
  - `def render_json(findings: List[Finding], ep: str) -> str`

- [ ] **Step 1: 写失败的测试**

`tests/test_report.py`：

```python
from qa_v2.report import Finding, summarize, render_text, render_json


def test_summarize_counts_by_level():
    fs = [
        Finding("L1", 3, "r1_flag", "fail", "SLOT_MISSING_IN_TEXT", "文案没填"),
        Finding("L4", 3, "r1_total", "fail", "NUMBER_MISMATCH", "1485≠1486"),
        Finding("L4", 3, "r2_dir", "warn", "NUMBER_UNKNOWN", "归一失败率高"),
        Finding("L6", 5, "evidence_tag", "skip", "NO_NAMES", "专名表缺"),
    ]
    assert summarize(fs) == {"fail": 2, "warn": 1, "skip": 1, "info": 0}


def test_render_text_mentions_ep_and_counts():
    fs = [Finding("L1", 1, "title", "fail", "X", "坏了")]
    out = render_text(fs, "shucun")
    assert "shucun" in out
    assert "fail" in out
    assert "坏了" in out


def test_render_text_empty_says_pass():
    assert "通过" in render_text([], "shucun")


def test_render_json_roundtrips():
    import json as _json
    fs = [Finding("L1", 1, "title", "fail", "X", "坏了", {"a": 1})]
    got = _json.loads(render_json(fs, "shucun"))
    assert got["episode"] == "shucun"
    assert got["summary"]["fail"] == 1
    assert got["findings"][0]["slot"] == "title"
    assert got["findings"][0]["detail"] == {"a": 1}


def test_finding_defaults():
    f = Finding("L1", 1, "title", "fail", "X", "m")
    assert f.detail is None
    assert f.slot == "title"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_report.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.report'`

- [ ] **Step 3: 写最小实现**

`qa_v2/report.py`：

```python
"""验收结论的表示与输出。

level 语义（只有 fail 阻塞退出码，见 spec §10.2）：
  fail —— 违反判据，必须修
  warn —— 可疑但可能是判据过严，不阻塞
  skip —— 该判据因缺前置数据未执行（如专名表未维护），**不算通过**
  info —— 补充信息
"""
import json
from typing import Dict, List, Optional

LEVELS = ("fail", "warn", "skip", "info")


class Finding(object):
    __slots__ = ("layer", "page", "slot", "level", "code", "message", "detail")

    def __init__(self, layer, page, slot, level, code, message,
                 detail=None):
        assert level in LEVELS, "未知 level: %r" % level
        self.layer = layer
        self.page = page
        self.slot = slot
        self.level = level
        self.code = code
        self.message = message
        self.detail = detail

    def to_dict(self):
        return {
            "layer": self.layer, "page": self.page, "slot": self.slot,
            "level": self.level, "code": self.code, "message": self.message,
            "detail": self.detail,
        }

    def __repr__(self):
        return "Finding(%s, p%s, %s, %s, %s)" % (
            self.layer, self.page, self.slot, self.level, self.code)


def summarize(findings):
    out = dict((lv, 0) for lv in LEVELS)
    for f in findings:
        out[f.level] += 1
    return out


_ICON = {"fail": "✗", "warn": "⚠", "skip": "–", "info": "·"}


def render_text(findings, ep):
    s = summarize(findings)
    lines = ["=== %s ===" % ep]
    if not findings:
        lines.append("  全部通过，无发现")
    else:
        order = {"fail": 0, "warn": 1, "skip": 2, "info": 3}
        for f in sorted(findings, key=lambda x: (
                order.get(x.level, 9), x.layer, x.page or 0)):
            where = "P%s" % f.page if f.page else "-"
            slot = f.slot or "-"
            lines.append("  %s [%s] %s/%s  %s" % (
                _ICON.get(f.level, "?"), f.level, where, slot, f.message))
            if f.detail:
                for k, v in sorted(f.detail.items()):
                    lines.append("        %s=%s" % (k, v))
    tail = "  -> fail %d / warn %d / skip %d / info %d" % (
        s["fail"], s["warn"], s["skip"], s["info"])
    lines.append(tail)
    lines.append("  判定：" + ("不通过" if s["fail"] else "通过"))
    return "\n".join(lines)


def render_json(findings, ep):
    return json.dumps(
        {"episode": ep, "summary": summarize(findings),
         "findings": [f.to_dict() for f in findings]},
        ensure_ascii=False, indent=1)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_report.py -v`
Expected: PASS —— 6 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/report.py tests/test_report.py
git commit -m "feat(qa): Finding 与报告输出

level 四级，只有 fail 阻塞退出码（历史集 warn 噪声不应淹没真问题）。
skip 表示判据因缺前置数据未执行，不等于通过 —— 专名表缺失时必须显式 skip。"
```

---

