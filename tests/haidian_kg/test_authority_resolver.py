"""
测试 AuthorityResolver 多源外部地名权威裁决器
"""
import pytest
from haidian_kg.authority_resolver import (
    AuthorityResolver,
    AuthorityMatchRecord,
    LicenseClass,
    GeographicalGranularity,
    MatchMethod,
)


class TestAuthorityResolver:
    def test_empty_resolver_unblocks_pipeline(self):
        resolver = AuthorityResolver()
        res = resolver.resolve("树村")
        assert res.consensus_confidence == "low"
        assert res.matches == []
        assert "保留为本地发现" in res.verdict_summary

    def test_dila_micro_match_sets_flags(self):
        resolver = AuthorityResolver()
        rec = AuthorityMatchRecord(
            provider_id="dila",
            provider_record_id="PL000000010214",
            matched_name="遯村",
            matched_uri="https://authority.dila.edu.tw/place/search.php?code=PL000000010214",
            license_class=LicenseClass.CC_BY_SA,
            granularity=GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT,
            match_method=MatchMethod.EXACT,
            match_confidence="high",
        )
        resolver.register_cached_match("遯村", rec)
        res = resolver.resolve("遯村")
        assert res.consensus_confidence == "high"
        assert res.has_micro_village_match is True
        assert res.has_temple_religious_match is True
        assert len(res.matches) == 1

    def test_ccts_reference_only_discipline(self):
        resolver = AuthorityResolver()
        rec = AuthorityMatchRecord(
            provider_id="ccts_mhpname",
            provider_record_id="mhp_1582_0912",
            matched_name="万寿寺",
            license_class=LicenseClass.REFERENCE_ONLY_UNLESS_LICENSED,
            granularity=GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT,
            is_reference_only=True,
            source_citation="《读史方舆纪要》卷十一顺天府宛平县",
        )
        resolver.register_cached_match("万寿寺", rec)
        res = resolver.resolve("万寿寺")
        assert res.matches[0].is_reference_only is True
        assert res.matches[0].license_class == LicenseClass.REFERENCE_ONLY_UNLESS_LICENSED

    def test_multi_provider_consensus_boosts_confidence(self):
        resolver = AuthorityResolver()
        # Provider 1: TGAZ county-level
        rec1 = AuthorityMatchRecord(
            provider_id="tgaz",
            provider_record_id="hvd_141901",
            matched_name="万寿寺",
            granularity=GeographicalGranularity.SUB_COUNTY_TOWN,
            match_confidence="mid",
        )
        # Provider 2: DILA religious micro
        rec2 = AuthorityMatchRecord(
            provider_id="dila",
            provider_record_id="PL_WANSHOU",
            matched_name="万寿寺",
            granularity=GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT,
            match_confidence="mid",
        )
        resolver.register_cached_match("万寿寺", rec1)
        resolver.register_cached_match("万寿寺", rec2)
        res = resolver.resolve("万寿寺")
        # 异源联合提升为 high
        assert res.consensus_confidence == "high"
        assert len(res.matches) == 2
        assert "dila, tgaz" in res.verdict_summary
