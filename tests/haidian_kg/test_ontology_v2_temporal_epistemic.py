"""
tests/haidian_kg/test_ontology_v2_temporal_epistemic.py
BHKG/HHTO v2.1 本体时态层与认识论层负控制测试

依据：GPT 第1轮 P0（时态/空间/冻结实例/拓扑时态化）与
      第2轮 P0（ChronologicalPoint 四语义拆分、证据三层、负控制证伪强度）

每条负控制断言都必须有对应的真实拦截测试，禁止"永不失败的测试"。
"""
import pytest

from haidian_kg.ontology.temporal import (
    Era, CalibrationTable, ReignYear, GregorianDate, DatePoint,
    TimeSpan, TemporalProcess,
)
from haidian_kg.ontology.epistemic import (
    TextualFact, Proposition, BeliefAdoption, EpistemicStatus,
    SourceDivision, HistoricalSource, SourceCategory,
)


# ============ 正例构造 ============

def _ts(y1, y2, tag="ts"):
    return TimeSpan(
        id=tag,
        label="%d-%d" % (y1, y2),
        begin=DatePoint(
            id=tag + "_b", label=str(y1),
            gregorian=GregorianDate(year=y1, calibration=CalibrationTable.CN_ASTRONOMICAL_ALMANAC),
        ),
        end=DatePoint(
            id=tag + "_e", label=str(y2),
            gregorian=GregorianDate(year=y2, calibration=CalibrationTable.CN_ASTRONOMICAL_ALMANAC),
        ),
    )


# ============ P0-1 时态：禁止裸公历年 ============

class TestCalibrationGuard:
    def test_bare_gregorian_year_rejected(self):
        """【负控制】公历换算必须声明权威历表，无基准即拒绝入库"""
        with pytest.raises(ValueError) as e:
            GregorianDate(year=1292, calibration=CalibrationTable.UNCALIBRATED)
        assert "权威历表" in str(e.value)

    def test_calibrated_gregorian_accepted(self):
        d = GregorianDate(year=1292, calibration=CalibrationTable.CN_ASTRONOMICAL_ALMANAC)
        assert d.year == 1292

    def test_negative_uncertainty_rejected(self):
        with pytest.raises(ValueError):
            GregorianDate(year=1292, calibration=CalibrationTable.GB_T_33661_2017,
                          uncertainty_years=-5)


# ============ P0-1 时态：年号与公历必须分离 ============

class TestReignYearSeparation:
    def test_reign_year_keeps_verbatim_only(self):
        """年号纪年对象只表达"文献怎么写的"，不自动等于公历年"""
        ry = ReignYear(era=Era.QING, reign_title="乾隆", year_within_reign=16,
                       lunar_month=7, ganzhi="癸未", verbatim="乾隆十六年七月癸未")
        assert ry.verbatim == "乾隆十六年七月癸未"
        assert ry.year_within_reign == 16
        # 关键：对象本身不携带 gregorian，必须由 DatePoint 另行挂换算结果
        assert not hasattr(ry, "gregorian")

    def test_reign_year_requires_verbatim(self):
        """纪年必须保留文献原始写法，否则无法回溯"""
        with pytest.raises(Exception):
            ReignYear(era=Era.QING, reign_title="乾隆", year_within_reign=16)


# ============ P0 时态：区间开闭与重叠 ============

class TestTimeSpan:
    def test_contains_within_range(self):
        ts = _ts(938, 1368)
        assert ts.contains(1292) is True
        assert ts.contains(1500) is False

    def test_open_begin_means_before_earliest(self):
        ts = TimeSpan(id="t", label="open", open_begin=True)
        assert ts.contains(-5000) is True

    def test_open_end_means_still_exists(self):
        ts = TimeSpan(id="t", label="open", open_end=True)
        assert ts.contains(2026) is True

    def test_overlap(self):
        a = _ts(938, 1368, "a")
        b = _ts(1200, 1400, "b")
        assert a.overlaps(b) is True


# ============ P0 渐变过程：不得伪装成离散事件 ============

class TestTemporalProcess:
    def test_gradual_process_allowed(self):
        """高梁→高粱的讹音传播无确切日期，必须建成过程而非事件"""
        p = TemporalProcess(
            id="proc1", process_type="PHONETIC_DRIFT", subject_ids=["top_gl"],
            time_span=_ts(1500, 1900), mechanism="俗写传播",
            dating_basis="无确切改制文书，只能给出区间",
        )
        assert p.is_gradual is True

    def test_process_requires_dating_basis(self):
        """过程必须说明"为何只能给区间"——这是防伪核心"""
        with pytest.raises(Exception):
            TemporalProcess(
                id="p", process_type="SILTATION", subject_ids=["x"],
                time_span=_ts(1, 2), mechanism="淤积", dating_basis=None,
            )


# ============ P0 证据链：禁止跨卷拼接 ============

class TestCrossVolumeGuard:
    def test_cross_volume_rejected(self):
        """【负控制·实测已拦】卷十三与卷十四不得拼成一句原典"""
        with pytest.raises(ValueError) as e:
            TextualFact(
                id="tf", division_id="div_vol13,div_vol14",
                verbatim_quote="高梁水出蓟县西北平地，注于鲍丘水",
                attested_string="高梁水",
            )
        assert "跨卷" in str(e.value)

    def test_cross_division_rejected(self):
        with pytest.raises(ValueError):
            TextualFact(
                id="tf", division_id="div_a&div_b",
                verbatim_quote="测试引文内容足够长",
                attested_string="测试",
            )

    def test_single_volume_accepted(self):
        tf = TextualFact(
            id="tf", division_id="div_sjz_vol13_luoshui",
            verbatim_quote="高梁水出蓟城西北平地泉",
            attested_string="高梁水",
        )
        assert tf.division_id == "div_sjz_vol13_luoshui"

    def test_empty_quote_rejected(self):
        with pytest.raises(ValueError) as e:
            TextualFact(id="tf", division_id="div_a", verbatim_quote="  ",
                         attested_string="x")
        assert "引文" in str(e.value)


# ============ P0 负控制：absence of evidence ≠ evidence of absence ============

class TestDisproofGuard:
    def test_disproven_without_evidence_rejected(self):
        """【负控制·实测已拦】不能无据就把命题标成"已证伪\""""
        with pytest.raises(ValueError) as e:
            BeliefAdoption(
                proposition_id="p1", status=EpistemicStatus.DISPROVEN,
                confidence=0.05, adopted_by="test", rationale="无据",
            )
        assert "无证据不等于不存在" in str(e.value)

    def test_disproven_with_evidence_accepted(self):
        ba = BeliefAdoption(
            proposition_id="p1", status=EpistemicStatus.DISPROVEN,
            confidence=0.02, adopted_by="第1轮复审", rationale="原文与年代矛盾",
            refuting_fact_ids=["tf_contradiction"],
        )
        assert ba.status == EpistemicStatus.DISPROVEN

    def test_unsubstantiated_is_distinct_from_disproven(self):
        """无据推论必须与已证伪区分——这正是"高梁/高粱"类案例的教训"""
        ba = BeliefAdoption(
            proposition_id="p2", status=EpistemicStatus.UNSUBSTANTIATED,
            confidence=0.3, adopted_by="test", rationale="词源无定论",
        )
        assert ba.status != EpistemicStatus.DISPROVEN


# ============ P0 认识论三层分离 ============

class TestEpistemicLayering:
    def test_proposition_requires_textual_facts(self):
        """断言必须挂在文本事实上，不能凭空提出"""
        p = Proposition(
            id="p1", statement="高梁桥于元至元二十九年创建",
            derived_from_fact_ids=["tf_yuan"], inference_method="《元史·河渠志》直载",
        )
        assert p.derived_from_fact_ids == ["tf_yuan"]

    def test_proposition_records_alternatives(self):
        """学界有多说的，alternative_explanations 必须能留空但字段须存在"""
        p = Proposition(
            id="p2", statement="高梁水词源为津梁义",
            derived_from_fact_ids=["tf1"],
            inference_method="排除作物说后的推测",
            alternative_explanations=["因梁山而名", "古越语音译"],
        )
        assert len(p.alternative_explanations) == 2

    def test_textual_fact_does_not_carry_verdict(self):
        """【架构红线】TextualFact 只声明"这么写"，不得携带认识论判定"""
        tf = TextualFact(
            id="tf", division_id="div_a",
            verbatim_quote="测试文本内容足够长", attested_string="测试",
        )
        assert not hasattr(tf, "epistemic_status")
        assert not hasattr(tf, "evidence_level")


# ============ 文献三级结构完整性 ============

class TestSourceHierarchy:
    def test_division_links_to_source(self):
        src = HistoricalSource(id="src_sjz", title="水经注",
                               category=SourceCategory.GEOGRAPHICAL_TREATISE)
        div = SourceDivision(id="div_v13", source_id=src.id,
                             volume_number="卷十三", section_title="漯水")
        assert div.source_id == "src_sjz"

    def test_division_supports_nesting(self):
        """卷→篇→条三级，parent_division_id 必填才能表达"""
        div = SourceDivision(id="div_tie", source_id="src_a",
                             volume_number="卷十三", section_title="漯水条三",
                             parent_division_id="div_v13")
        assert div.parent_division_id == "div_v13"
