"""
tests/haidian_kg/test_holdout_eval.py
=====================================

Holdout 评估器单测：评分函数边界（零预测/零真值/全对/全错）、
金标提取（最长匹配/变体字形/反恒真负控制）、五指标闸门逻辑、
漏检/误报归因分类、以及「评分路径零 expansion 依赖」纪律钉死。

纪律：本文件禁真调 PaddleOCR / 网络（评估器本身是纯文本管线，
无此类依赖；本注释钉死未来也不许引入）。
"""
import inspect
import json
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.evaluation import holdout_eval as HE
from haidian_kg.evaluation.holdout_eval import (
    GoldMention, NameRegistry, PredOcc,
    norm_eval, strip_annotation, build_name_registry, extract_gold_mentions,
    locate_span, match_segment, compute_metrics, gate_check,
    attribute_miss, attribute_fp, load_segments, evaluate, soft_forms_from_registry,
)


# ---------------------------------------------------------------------------
# 夹具：迷你注册表（独立于 calibration 模块，便于边界受控）
# ---------------------------------------------------------------------------

def mini_registry():
    # 键 = 归一形（真值层契约）；挖掘器停用词「圆明园」照收（反恒真负控制）
    forms = {
        "大有庄": {"ent_dyz"},
        "青龙桥镇": {"ent_qlq"},
        "青龙桥": {"ent_qlq"},
        "圆明园": {"ent_ymp"},
        "中官村": {"ent_zgc"},          # 原形「中官邨」经独立变体表归一
        "万寿山": {"ent_wss"},
        "董四墓": {"ent_dsm"},
        "昆明湖": {"ent_kmh"},
        "清水院": {"ent_qsy"},
        "外火器营": {"ent_whq"},
        "蓝靛厂": {"ent_ldc"},
    }
    display = {f: f for f in forms}
    return NameRegistry(forms, display)


def gm(seg, start, form, ents=("ent_x",)):
    return GoldMention(segment_id=seg, start=start, end=start + len(form),
                       surface=form, normalized_form=form,
                       entity_ids=tuple(ents), display_form=form)


def po(seg, start, form, conf="mid", method="suffix_scan", occ_id="occ1"):
    return PredOcc(segment_id=seg, start=start, end=start + len(form),
                   surface=form, normalized_form=form, confidence=conf,
                   method=method, occ_id=occ_id)


# ---------------------------------------------------------------------------
# 真值层
# ---------------------------------------------------------------------------

class TestTruthLayer:
    def test_variant_table_is_length_preserving(self):
        s = "中官邨与中关村"
        assert len(norm_eval(s)) == len(s)
        assert norm_eval("中官邨") == "中官村"

    def test_strip_annotation(self):
        assert strip_annotation("高梁桥（元代石闸桥；三山五园名录2024纠偏字形木字底）") == "高梁桥"
        assert strip_annotation("大有庄") == "大有庄"
        assert strip_annotation("外火器营营房（蓝靛厂）") == "外火器营营房"

    def test_registry_from_calibration_modules(self):
        reg = build_name_registry()
        assert "大有庄" in reg.form_map
        assert "苏州街" in reg.form_map
        # script_variants 异体「中官邨」经归一入表（键为归一形「中官村」）
        assert "中官村" in reg.form_map
        assert "ent_zhongguancun" in reg.entities_of("中官村")
        assert reg.entities_of("大有庄") == {"ent_dayouzhuang"}
        # 别名挂对实体：青龙桥（别名）→ 青龙桥镇实体
        assert "ent_qinglongqiao" in reg.entities_of("青龙桥")

    def test_gold_longest_match_wins(self):
        text = "青龙桥镇商旅云集"
        golds = extract_gold_mentions(text, "seg1", mini_registry())
        assert [g.normalized_form for g in golds] == ["青龙桥镇"]
        assert (golds[0].start, golds[0].end) == (0, 4)
        assert golds[0].surface == "青龙桥镇"

    def test_gold_variant_glyph_maps_to_raw_span(self):
        text = "迁驻中官邨北"
        golds = extract_gold_mentions(text, "seg1", mini_registry())
        assert len(golds) == 1
        assert golds[0].surface == "中官邨", "surface 必须是原文逐字"
        assert (golds[0].start, golds[0].end) == (2, 5)

    def test_gold_not_filtered_by_miner_stopwords__anti_tautology(self):
        """负控制：圆明园在挖掘器停用词表里，真值照样产出金标。

        若金标构造复用了挖掘器词表，此用例的 gold 会消失——
        那样 recall 会虚高，评估器恒真。"""
        golds = extract_gold_mentions("圆明园护军营房", "seg1", mini_registry())
        assert any(g.normalized_form == "圆明园" for g in golds)

    def test_gold_repeated_form_two_mentions(self):
        golds = extract_gold_mentions("大有庄与大有庄西", "seg1", mini_registry())
        assert [g.start for g in golds] == [0, 4]


# ---------------------------------------------------------------------------
# 匹配
# ---------------------------------------------------------------------------

class TestMatching:
    def test_tp_requires_form_and_span(self):
        golds = [gm("s", 10, "大有庄")]
        preds = [po("s", 0, "大有庄")]      # 同形异位：span 不含 → FP+FN
        tps, fps, fns = match_segment(golds, preds)
        assert tps == [] and len(fps) == 1 and len(fns) == 1

    def test_tp_span_containment_both_directions(self):
        # gold [0,3) 含于 pred [0,4)：相互包含成立（文档 containment 语义）
        golds = [gm("s", 0, "大有庄")]
        preds = [PredOcc(segment_id="s", start=0, end=4, surface="大有庄区",
                         normalized_form="大有庄", confidence="mid",
                         method="suffix_scan", occ_id="o1")]
        tps, fps, fns = match_segment(golds, preds)
        assert len(tps) == 1 and fps == [] and fns == []

    def test_full_correct(self):
        golds = [gm("s", 0, "大有庄"), gm("s", 5, "青龙桥")]
        preds = [po("s", 0, "大有庄"), po("s", 5, "青龙桥")]
        tps, fps, fns = match_segment(golds, preds)
        assert len(tps) == 2 and fps == [] and fns == []

    def test_all_wrong_forms(self):
        golds = [gm("s", 0, "大有庄")]
        preds = [po("s", 0, "青龙桥")]
        tps, fps, fns = match_segment(golds, preds)
        assert tps == [] and len(fps) == 1 and len(fns) == 1

    def test_locate_span(self):
        text = "驻跸圆明园，圆明园大拓"
        assert locate_span(text, "圆明园") == (2, 5)
        assert locate_span(text, "无此词") is None


# ---------------------------------------------------------------------------
# 五指标与闸门
# ---------------------------------------------------------------------------

class TestMetrics:
    def counts(self, tp=0, fp=0, fn=0, tp_high=0, n_high=0):
        return {"tp": tp, "fp": fp, "fn": fn, "tp_high": tp_high, "n_high": n_high}

    def test_zero_prediction(self):
        m = compute_metrics(self.counts(tp=0, fp=0, fn=3), 2, 0, 0, 0)
        assert m["mention_precision"] is None
        assert m["mention_recall"] == 0.0

    def test_zero_gold(self):
        m = compute_metrics(self.counts(tp=0, fp=4, fn=0), 0, 0, 0, 4)
        assert m["mention_precision"] == 0.0
        assert m["mention_recall"] is None

    def test_all_correct(self):
        m = compute_metrics(self.counts(tp=5, fp=0, fn=0, tp_high=2, n_high=2),
                            3, 0, 0, 7)
        assert m["mention_precision"] == 1.0
        assert m["mention_recall"] == 1.0
        assert m["mention_f1"] == 1.0
        assert m["high_conf_precision"] == 1.0
        assert m["duplication_rate"] == 0.0
        assert m["collision_rate"] == 0.0

    def test_all_wrong(self):
        m = compute_metrics(self.counts(tp=0, fp=3, fn=4), 2, 0, 0, 0)
        assert m["mention_precision"] == 0.0
        assert m["mention_recall"] == 0.0
        assert m["mention_f1"] is None, "P=R=0 时 F1 无定义，必须显式 None"

    def test_duplication_and_collision_molecules(self):
        m = compute_metrics(self.counts(tp=4, fp=1, fn=1),
                            gold_entity_total=10, dup_entities=2,
                            collision_hyps=1, hyp_total=25)
        assert m["duplication_rate"] == pytest.approx(0.2)
        assert m["collision_rate"] == pytest.approx(0.04)

    def test_gate_none_never_passes(self):
        m = compute_metrics(self.counts(tp=0, fp=0, fn=0), 0, 0, 0, 0)
        rows = gate_check(m)
        assert all(r["pass"] is False for r in rows), "无分母 = 证据不足，不放行"

    def test_gate_threshold_directions(self):
        m = compute_metrics(self.counts(tp=90, fp=10, fn=10, tp_high=19, n_high=20),
                            20, 1, 0, 50)
        rows = {r["metric"]: r for r in gate_check(m)}
        assert rows["mention_precision"]["pass"] is True    # 0.90 == 阈值线，取等
        assert rows["mention_recall"]["pass"] is True       # 0.90
        assert rows["high_conf_precision"]["pass"] is True  # 0.95
        assert rows["duplication_rate"]["pass"] is True     # 0.05
        assert rows["collision_rate"]["pass"] is True       # 0.0

    def test_gate_collision_hard_zero(self):
        m = compute_metrics(self.counts(tp=9, fp=1, fn=1),
                            10, 0, 1, 50)
        rows = {r["metric"]: r for r in gate_check(m)}
        assert rows["collision_rate"]["pass"] is False, "collision=0 硬闸，>0 即不过"


# ---------------------------------------------------------------------------
# 假说层覆盖（duplication / collision 分子）
# ---------------------------------------------------------------------------

def fake_report(hyps):
    return SimpleNamespace(candidates_found=hyps)


def fake_hyp(form, occs):
    return SimpleNamespace(normalized_form=form, occurrences=occs)


def fake_occ(div, surface):
    return SimpleNamespace(division_id=div, surface_form=surface)


class TestHypothesisCoverage:
    def seg(self, sid, text):
        return {"segment_id": sid, "text": text}

    def test_duplication_two_hypotheses_one_entity(self):
        segs = [self.seg("s1", "青龙桥镇与青龙桥闸并列")]
        golds = {("s1"): extract_gold_mentions(
            segs[0]["text"], "s1",
            NameRegistry({"青龙桥镇": {"e1"}, "青龙桥": {"e1"},
                          "青龙桥闸": {"e1"}}, {}))}
        rep = fake_report([fake_hyp("青龙桥镇", [fake_occ("div_holdout_000", "青龙桥镇")]),
                           fake_hyp("青龙桥", [fake_occ("div_holdout_000", "青龙桥")])])
        reg = NameRegistry({"青龙桥镇": {"e1"}, "青龙桥": {"e1"}}, {})
        dup, coll, _ = HE.hypothesis_coverage(rep, segs, golds, reg)
        assert dup == {"e1"}, "同实体被 ≥2 假说覆盖 → duplication"
        assert coll == set()

    def test_collision_one_hypothesis_two_entities(self):
        segs = [self.seg("s1", "西城闸旧址犹存")]
        reg = NameRegistry({"西城闸": {"e_gate_a", "e_gate_b"}}, {})
        golds = {"s1": extract_gold_mentions(segs[0]["text"], "s1", reg)}
        rep = fake_report([fake_hyp("西城闸", [fake_occ("div_holdout_000", "西城闸")])])
        dup, coll, detail = HE.hypothesis_coverage(rep, segs, golds, reg)
        assert coll and len(coll) == 1, "一假说覆盖两个 gold 实体 → collision"
        assert dup == set()


# ---------------------------------------------------------------------------
# 归因
# ---------------------------------------------------------------------------

class TestAttribution:
    def test_miss_same_form_elsewhere(self):
        g = gm("s", 10, "大有庄")
        preds = [po("s", 0, "大有庄")]
        cls, _ = attribute_miss(g, preds, "大有庄与大有庄")
        assert cls == "same-form-elsewhere"

    def test_miss_erosion(self):
        g = gm("s", 0, "青龙桥镇")
        preds = [po("s", 0, "青龙桥")]
        cls, why = attribute_miss(g, preds, "青龙桥镇商旅云集")
        assert cls == "erosion"
        assert "青龙桥" in why

    def test_miss_stopword_suppressed(self):
        # v4 后噪声判定与 _is_noise 同义（整词成员）：旗制复合词仍整词在表
        g = gm("s", 1, "圆明园八旗")
        cls, why = attribute_miss(g, [], "驻圆明园八旗")
        assert cls == "stopword-suppressed"
        assert "圆明园八旗" in why

    def test_miss_noise_keyword(self):
        # 内嵌实体：圆明园 被右侧 营-通道拖进 圆明园护军营 复合词，职官关键词拦
        g = gm("s", 0, "圆明园")
        cls, why = attribute_miss(g, [], "圆明园护军营驻防")
        assert cls == "noise-keyword"
        assert "护军" in why

    def test_miss_suffix_and_cue_missing(self):
        g = gm("s", 3, "董四墓")
        text = "今香山董四墓附近"
        cls, why = attribute_miss(g, [], text)
        assert cls == "suffix-and-cue-missing", "「墓」非收录后缀且无线索词"

    def test_miss_cue_window_narrow(self):
        g = gm("s", 2, "清水院")
        text = "寺曰清水院"
        cls, _ = attribute_miss(g, [], text)
        assert cls == "cue-window-narrow", "「院」非收录后缀，仅曰窗可达"

    def test_miss_walkback_overrun(self):
        g = gm("s", 10, "长春园")
        text = "圣皇太后六十寿辰拓建长春园"
        cls, why = attribute_miss(g, [], text)
        assert cls == "walkback-overrun"
        assert "6" in why

    def test_miss_walkback_too_short(self):
        # 有 是停用边界字：回溯只剩「庄」1 字，不满足 ≥2 字下限
        g = gm("s", 4, "大有庄")
        text = "乾隆赐名大有庄"
        cls, why = attribute_miss(g, [], text)
        assert cls == "walkback-too-short"
        assert "有" in why

    def test_fp_erosion(self):
        g = gm("s", 0, "青龙桥镇")
        p = po("s", 0, "青龙桥")
        cls, _ = attribute_fp(p, [g], mini_registry(), set())
        assert cls == "erosion"

    def test_fp_paren_note_fragment(self):
        p = po("s", 2, "树村西")
        cls, why = attribute_fp(p, [], mini_registry(), {"树村西"})
        assert cls == "paren-note-fragment"
        assert "树村西" in why

    def test_fp_boundary_splice(self):
        p = po("s", 0, "今海淀温泉")
        cls, why = attribute_fp(p, [], mini_registry(), set())
        assert cls == "boundary-splice"
        assert "今" in why

    def test_fp_markdown_prefix_bleed(self):
        p = po("s", 0, "- **万泉")
        cls, why = attribute_fp(p, [], mini_registry(), set())
        assert cls == "markdown-prefix-bleed"
        assert "句读" in why or "记号" in why

    def test_fp_kb_coverage_gap(self):
        p = po("s", 0, "清水院")
        reg = NameRegistry({"大有庄": {"e1"}}, {"大有庄": "大有庄"})
        cls, _ = attribute_fp(p, [], reg, set())
        assert cls == "kb-coverage-gap"

    def test_soft_forms_extracted_from_parens(self):
        reg = NameRegistry({}, {"k": "外火器营营房（蓝靛厂）"})
        soft = soft_forms_from_registry(reg)
        assert "蓝靛厂" in soft


# ---------------------------------------------------------------------------
# 端到端（迷你段 + 真引擎 + 真评分；无网络无 OCR）
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_load_segments_rejects_drift(self, tmp_path):
        seg = {"segment_id": "x.md:L1-L1", "text": "大有庄考", "text_sha1": "0" * 40}
        p = tmp_path / "holdout.jsonl"
        p.write_text(json.dumps(seg, ensure_ascii=False), encoding="utf-8")
        with pytest.raises(ValueError, match="漂移"):
            load_segments(str(p))
        import hashlib
        seg["text_sha1"] = hashlib.sha1("大有庄考".encode("utf-8")).hexdigest()
        p.write_text(json.dumps(seg, ensure_ascii=False), encoding="utf-8")
        assert len(load_segments(str(p))) == 1

    def test_mini_evaluate_structure(self):
        sha = __import__("hashlib").sha1
        segs = [
            {"segment_id": "mini.md:L1-L1", "text": "乾隆赐名大有庄",
             "text_sha1": sha("乾隆赐名大有庄".encode("utf-8")).hexdigest()},
            {"segment_id": "mini.md:L2-L2", "text": "外火器营迁驻蓝靛厂",
             "text_sha1": sha("外火器营迁驻蓝靛厂".encode("utf-8")).hexdigest()},
        ]
        reg = mini_registry()
        res = evaluate(segs, reg)
        assert set(res["metrics"]) >= {
            "mention_precision", "mention_recall", "high_conf_precision",
            "duplication_rate", "collision_rate"}
        assert res["n_segments"] == 2
        assert len(res["per_segment"]) == 2
        # 大有庄段：真引擎实际收不到（赐名 + 有 是回溯边界字，庄只剩 1 字），
        # 金标 1 → FN，且归因必须是 walkback-too-short
        s1 = res["per_segment"][0]
        assert s1["n_gold"] == 1 and s1["tp"] == 0
        assert res["false_negatives"][0]["class"] == "walkback-too-short"
        # 营房段：suffix_scan 双命中（外火器营/蓝靛厂）→ 2 TP
        s2 = res["per_segment"][1]
        assert s2["n_gold"] == 2
        assert s2["tp"] == 2, "专名+通名结构（营/厂）双命中必须进 TP"
        # 每条 FN/FP 必须带归因类别
        for row in res["false_negatives"] + res["false_positives"]:
            assert row["class"] and row["why"]
        assert res["metrics"]["gold_entity_total"] == 3

    def test_pred_spans_point_into_text(self):
        sha = __import__("hashlib").sha1
        text = "外火器营迁驻蓝靛厂"
        segs = [{"segment_id": "m.md:L1-L1", "text": text,
                 "text_sha1": sha(text.encode("utf-8")).hexdigest()}]
        preds, _ = HE.run_engine(segs)
        got = preds["m.md:L1-L1"]
        assert got, "suffix_scan 必须产出预测"
        for p in got:
            assert text[p.start:p.end] == p.surface, (
                "span 恢复必须逐字落回原文")


# ---------------------------------------------------------------------------
# 纪律钉死：评分路径零 expansion 依赖（反恒真）
# ---------------------------------------------------------------------------

class TestIndependenceDiscipline:
    SCORING_FUNCS = (
        build_name_registry, extract_gold_mentions, match_segment,
        compute_metrics, gate_check, norm_eval, strip_annotation,
        locate_span, HE.NameRegistry, HE.GoldMention,
    )

    def test_scoring_path_never_mentions_expansion(self):
        for fn in self.SCORING_FUNCS:
            src = inspect.getsource(fn)
            assert "expansion" not in src, (
                "%s 的源码引用了挖掘器模块——真值/评分与挖掘器必须隔离" % fn)

    def test_variant_table_not_shared_with_miner(self):
        from haidian_kg import expansion
        assert HE._VARIANT_MAP.keys().isdisjoint(
            expansion._TRAD_TO_SIMP.keys()), (
            "评估器变体表与挖掘器繁简表必须零共享键（独立维护）")

    def test_module_top_level_imports_expandable_only_for_adapter(self):
        """模块顶层只许 import 引擎入口相关，不许 import expansion。"""
        import ast
        src_path = inspect.getsourcefile(HE)
        with open(src_path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        top_imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_imports.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_imports.append(node.module)
        assert not any("expansion" in m for m in top_imports), (
            "顶层 import 出现 expansion：评分路径被污染")
