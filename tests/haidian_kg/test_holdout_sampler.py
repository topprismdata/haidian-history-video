"""
tests/haidian_kg/test_holdout_sampler.py
Holdout 基准抽样器测试（spec §5.3：冻结框架必须在接入《日下旧闻考》前可复现）

验收核心：
1. 固定种子两次运行输出字节级一致（可复现 = 可冻结）
2. JSONL 逐行可解析、schema 完整、段 id 唯一
3. 抽样只读 corpus/（冻结纪律：抽样器不许碰语料）
4. 分层轴（朝代/文献类型/繁简/地名类型）与篇卷号抽取的边界行为
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.evaluation import holdout_sampler as hs

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "haidian_kg" / "corpus"


# ---------------------------------------------------------------------------
# 真实语料：可复现与 JSONL 契约
# ---------------------------------------------------------------------------

def test_fixed_seed_two_runs_identical():
    records_a, report_a = hs.sample_holdout(str(CORPUS_DIR))
    records_b, report_b = hs.sample_holdout(str(CORPUS_DIR))
    assert hs.dumps_jsonl(records_a) == hs.dumps_jsonl(records_b)
    assert report_a == report_b


def test_jsonl_lines_parseable_and_schema_complete():
    records, report = hs.sample_holdout(str(CORPUS_DIR))
    lines = hs.dumps_jsonl(records).splitlines()
    assert len(lines) == len(records) > 0
    seen_ids = set()
    required = {"segment_id", "source_file", "line_start", "line_end",
                "heading_path", "text", "strata", "rxjwkc_cue_scope",
                "rxjwkc_juan", "text_sha1", "n_chars"}
    for line in lines:
        rec = json.loads(line)  # 每行都必须是合法 JSON
        assert required <= set(rec)
        assert rec["text"].strip()
        assert rec["line_end"] >= rec["line_start"]
        assert rec["n_chars"] == len(rec["text"])
        assert rec["text_sha1"] == hashlib.sha1(
            rec["text"].encode("utf-8")).hexdigest()
        assert set(rec["strata"]) == {"dynasty", "doc_type", "script",
                                      "toponym_type"}
        assert rec["rxjwkc_cue_scope"] in ("direct", "section", "file")
        assert rec["rxjwkc_juan"] == sorted(set(rec["rxjwkc_juan"]))
        seen_ids.add(rec["segment_id"])
    assert len(seen_ids) == len(records)  # 段 id 唯一（重复段会毁掉金标）


def test_frame_never_exceeds_universe_and_counts_consistent():
    records, report = hs.sample_holdout(str(CORPUS_DIR))
    assert report["universe_segments_total"] >= report["frame_segments_total"]
    assert report["sampled"] == min(report["n_requested"],
                                    report["frame_segments_total"])
    assert report["frame_shortfall"] == max(
        0, report["n_requested"] - report["frame_segments_total"])
    assert sum(report["strata_sampled"].values()) == report["sampled"]


def test_corpus_is_read_only():
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(CORPUS_DIR.glob("era*.md"))}
    hs.sample_holdout(str(CORPUS_DIR))
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(CORPUS_DIR.glob("era*.md"))}
    assert before == after


def test_cli_deterministic_bytes(tmp_path):
    out_a = tmp_path / "a.jsonl"
    out_b = tmp_path / "b.jsonl"
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT))
    for out in (out_a, out_b):
        proc = subprocess.run(
            [sys.executable, "-m", "haidian_kg.evaluation.holdout_sampler",
             "--out", str(out)],
            cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
    assert out_a.read_bytes() == out_b.read_bytes()
    for line in out_a.read_text(encoding="utf-8").splitlines():
        json.loads(line)


# ---------------------------------------------------------------------------
# 合成语料：分段 / 相关性 / 分层的确定性边界
# ---------------------------------------------------------------------------

SYNTHETIC_NO_PREAMBLE = """# 合成时代考据长编 (Era X: 公元1年 — 公元2年)

## 1. 某主题

### 1.1 直接引用节
- **文献出处**：《日下旧闻考》卷一百零一引《析津志》
- **清水院**（今大觉寺）：
  - 金章宗行宫与避暑水院；

### 1.2 无引用节
- **某村**在城西二十里，与书证无关；

## 2. 负控制判据（无三级标题）

1. **某传说**严禁写入正史事实链；
   - 必须标记为民间传说；
"""

SYNTHETIC_WITH_PREAMBLE = """# 合成时代考据长编 (Era Y: 公元3年 — 公元4年)

> 整理原则：以清乾隆《日下旧闻考》为核心信史凭证。

## 1. 某主题

### 1.1 无直接引用节
- **某村**在城西二十里；
"""


@pytest.fixture()
def synthetic_corpus(tmp_path):
    (tmp_path / "eraX_synthetic.md").write_text(
        SYNTHETIC_NO_PREAMBLE, encoding="utf-8")
    (tmp_path / "eraY_synthetic.md").write_text(
        SYNTHETIC_WITH_PREAMBLE, encoding="utf-8")
    return str(tmp_path)


def test_segmentation_bullet_with_nested_lines(synthetic_corpus):
    segs = hs.parse_segments(
        (Path(synthetic_corpus) / "eraX_synthetic.md").read_text(
            encoding="utf-8").split("\n"),
        "eraX_synthetic.md")
    by_id = {s.segment_id: s for s in segs}
    # 顶层 bullet + 嵌套续行必须并成一段（标注单元自洽）
    merged = [s for s in segs if s.text.startswith("- **清水院**")]
    assert len(merged) == 1
    assert "金章宗行宫" in merged[0].text
    assert " > " in merged[0].heading_path  # 标题路径可追溯
    # ## 下无 ### 的负控制段不能被整节丢弃
    assert any("某传说" in s.text for s in segs)


def test_relevance_direct_section_file_none(synthetic_corpus):
    frame, _ = hs.load_frame(synthetic_corpus)
    scope = {s.segment_id: sc for s, sc, _ in frame}
    direct = [sid for sid, sc in scope.items() if sc == "direct"]
    # eraX §1.1：出处 bullet 是 direct，兄弟段（清水院）继承 section
    assert len(direct) == 1 and direct[0].startswith("eraX_synthetic.md")
    siblings = [sid for sid, sc in scope.items() if sc == "section"]
    assert len(siblings) == 1 and siblings[0].startswith("eraX_synthetic.md")
    # eraX 无文件前导引用块：§1.2 与书证无关的段 = none
    unrelated = [sc for (s, sc, _) in frame if "某村" in s.text
                 and s.source_file == "eraX_synthetic.md"]
    assert unrelated == ["none"]
    # none 作用域段不得进入抽样结果（冻结总体只含书证相关段）
    records, _ = hs.sample_holdout(synthetic_corpus, n=120)
    assert all(r["rxjwkc_cue_scope"] != "none" for r in records)
    assert not any(r["source_file"] == "eraX_synthetic.md"
                   and "某村" in r["text"] for r in records)
    # eraY 文件前导引用块提及书名 ⇒ 无节级线索的段落在 file 作用域内
    file_scoped = [(s, sc) for (s, sc, _) in frame
                   if sc == "file" and s.source_file == "eraY_synthetic.md"]
    assert len(file_scoped) == 1 and "某村" in file_scoped[0][0].text


def test_dynasty_mapping_from_filename():
    assert hs.dynasty_of("era4_liao_jin.md") == "辽金"
    assert hs.dynasty_of("era7_qing.md") == "清"
    assert hs.dynasty_of("era8_9_modern.md") == "近现代"
    assert hs.dynasty_of("era0_prehistoric.md") == "史前"


def test_doc_type_takes_strongest_level():
    assert hs.doc_type_of(["2", "1"]) == "L1_考古实物"  # Level 1 + Level 2 取 L1
    assert hs.doc_type_of([]) == "unattributed"
    assert hs.doc_type_of(["5"]) == "L5_民间传说"


def test_script_axis_trad_simp_mixed():
    assert hs.script_of("護軍校護軍等官房") == "trad"
    assert hs.script_of("护军校护军等官房") == "simp"
    assert hs.script_of("护军校駐樹村") == "mixed"
    assert hs.script_of("海淀西山") == "simp"  # 中性字 → simp 兜底


def test_toponym_type_by_earliest_suffix():
    assert hs.toponym_type_of("树村西边驻营") == "settlement"  # 村 先于 营
    assert hs.toponym_type_of("广源闸节制水量") == "hydraulic"
    assert hs.toponym_type_of("畅春园与万寿山") == "garden"
    assert hs.toponym_type_of("碧云庵重修") == "temple"
    assert hs.toponym_type_of("外火器营营房四千间") == "military"
    assert hs.toponym_type_of("万寿山瓮山泊") == "landscape"
    assert hs.toponym_type_of("无通名形状的段落") == "none"


def test_allocate_floor_and_cap():
    # 非空层数 ≤ n：每层保底 1
    alloc = hs.allocate({"a": 1, "b": 3}, 120)
    assert alloc == {"a": 1, "b": 3}  # 总体不足 → 全收
    # 层数 > n：比例分配，总量恰好 n
    alloc = hs.allocate({("k%d" % i): 10 for i in range(30)}, 5)
    assert sum(alloc.values()) == 5
    assert all(v >= 0 for v in alloc.values())
    # 配额不超过各层总体
    alloc = hs.allocate({"a": 2, "b": 8}, 5)
    assert sum(alloc.values()) == 5 and alloc["a"] <= 2


def test_sample_with_small_n_is_unique_subset():
    records, report = hs.sample_holdout(str(CORPUS_DIR), n=5, seed=20261002)
    assert len(records) == 5
    assert report["frame_shortfall"] == 0
    ids = [r["segment_id"] for r in records]
    assert len(set(ids)) == 5
    universe_keys = set(report["strata_universe"])
    for r in records:
        assert hs.strata_key(r["strata"]) in universe_keys


# ---------------------------------------------------------------------------
# 篇卷号抽取：窗口截断回归 + 区间/变体边界
# ---------------------------------------------------------------------------

def test_juan_extraction_edges():
    cases = [
        ("《日下旧闻考》卷一百零一引《明一统志》", [101]),
        ("《日下旧闻考》卷九十八记外火器营迁驻蓝靛厂", [98]),
        ("清乾隆《日下旧闻考》（卷七十六至卷一百零四）为核心凭证", [76, 104]),
        ("《日下旧闻考》卷72引《八旗册》", [72]),
        ("《日下旧聞考》卷第九十八", [98]),
        ("《日下旧闻考》卷七十六至一百零四", [76, 104]),
        ("与日下旧闻考无关的文本", []),
        ("《日下旧闻考》", []),
        ("见《日下旧闻考》卷99、又见《宛署杂记》卷3", [99]),
    ]
    for text, want in cases:
        assert hs.extract_rxjwkc_juan(text) == want, text


def test_juan_extraction_no_window_truncation():
    """回归：窗口边界曾把「一百零一」截成「一百」→ 假卷号 100。"""
    base = "《日下旧闻考》卷一百零一引《明一统志》《析津志》"
    doubled = base + "\n" + base
    assert hs.extract_rxjwkc_juan(doubled) == [101]


def test_chinese_num_rejects_malformed():
    assert hs.chinese_num_to_int("九十八") == 98
    assert hs.chinese_num_to_int("104") == 104
    assert hs.chinese_num_to_int("一百零四") == 104
    assert hs.chinese_num_to_int("七十六") == 76
    assert hs.chinese_num_to_int("十") == 10
    assert hs.chinese_num_to_int("百x") is None  # 畸形 token 恒 None，不猜


def test_real_frame_juan_values_are_plausible():
    """真实语料的卷号必须落在《日下旧闻考》160 卷范围内，且与长编
    已知引用一致（95/98/103/104/106 + 前导区间 76-104）。
    2026-10-04 考订：水院卷次 101→106、钓鱼台 96→95（QUARANTINE.md
    Q-004/Q-005）；96/101 现仅存于考订批注引录的旧误文，不作断言。"""
    records, _ = hs.sample_holdout(str(CORPUS_DIR))
    all_juans = set()
    for r in records:
        all_juans.update(r["rxjwkc_juan"])
    assert all_juans and all(1 <= j <= 160 for j in all_juans)
    assert {95, 98, 103, 104, 76, 106} <= all_juans
