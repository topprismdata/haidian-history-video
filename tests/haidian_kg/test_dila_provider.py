"""
测试 DILA Provider 原型 connector（全部 mock 网络层，不触外网）

契约要点（2026-10-02 实测，见 .superpowers/sdd/dila-api-findings.md）：
- 详情：getAuthorityData.php?type=place&id=PL...&jsoncallback=cb → JSONP
- 搜索：search.php?ml=词&isLikeSearch=1&isFurther=0 → HTML（fpr_div 块内含规范码）
- 失败纪律：网络/解析故障静默返回 None，绝不抛异常
"""
import urllib.error

import pytest

from haidian_kg.authority_resolver import (
    GeographicalGranularity,
    LicenseClass,
    MatchMethod,
)
from haidian_kg.providers.dila import DilaProvider, DILA_DATA_URL, DILA_SEARCH_URL

# ------------------------- 实测响应 fixture -------------------------
DUN_VILLAGE_JSONP = (
    'dilaConnectorProbe({"data1":{'
    '"authorityID":"PL000000010214","name":"遯村","dynasty":null,'
    '"long":"120.6467","lat":"31.1657","districtHistorical":null,'
    '"districtModern":"中國-江蘇省-蘇州市-吳江區",'
    '"note":"位吳江。蘇州府遯村報恩浮石通賢禪師，出住吳江之報恩上堂。（X82n1571_p0313c24）",'
    '"lang":"中文","shortAuthorityID":"PL10214","names":"",'
    '"pinyin":{"遯村":"dùn cūn"}}})'
)

SONG_MOUNTAIN_JSONP = (
    'cb({"data1":{"authorityID":"PL000000023253","name":"嵩山","dynasty":"慣用名",'
    '"long":"113.003188","lat":"34.519744",'
    '"districtModern":"中國-河南省-鄭州市-登封市","note":"中嶽。","lang":"中文",'
    '"names":"嵩高山,中嶽,外方","pinyin":{}}})'
)

SEARCH_HIT_HTML = (
    '<html><body>'
    "<a href='search.php?code=PL000000000083'>側欄示例（不在 fpr_div 內，不得誤提取）</a>"
    '<div id="" class="fpr_div">  <span><span class=\'HL\'>遯村</span>(dùn cūn)</span>'
    "規範碼：PL000000010214 規範碼短碼：PL10214"
    "舊規範碼：CN0320584A06AA(僅供參考請勿使用)"
    "</div></body></html>"
)

SEARCH_MULTI_HIT_HTML = (
    '<html><body>'
    '<div id="" class="fpr_div"> <span class=\'HL\'>遯村</span>規範碼：PL000000010214</div>'
    '<div id="" class="fpr_div"> <span class=\'HL\'>大范村</span>規範碼：PL000000021579</div>'
    '</body></html>'
)

SEARCH_ZERO_HIT_HTML = "<html><body><div>檢索無結果</div></body></html>"


def _install_routes(monkeypatch, provider: DilaProvider, routes: dict) -> list:
    """按 URL 前缀路由的假网络层；返回捕获到的请求 URL 列表。"""
    captured = []

    def fake_http_get(url: str):
        captured.append(url)
        for prefix, body in routes.items():
            if url.startswith(prefix):
                return body
        raise AssertionError(f"意外请求：{url}")

    monkeypatch.setattr(provider, "_http_get", fake_http_get)
    return captured


def _new_provider() -> DilaProvider:
    return DilaProvider(min_interval_sec=0.0)


class TestFetchById:
    def test_maps_full_field_structure(self, monkeypatch):
        p = _new_provider()
        _install_routes(monkeypatch, p, {DILA_DATA_URL: DUN_VILLAGE_JSONP})

        rec = p.fetch_by_id("PL000000010214")

        assert rec is not None
        assert rec.provider_id == "dila"
        assert rec.provider_record_id == "PL000000010214"
        assert rec.matched_name == "遯村"
        assert rec.matched_uri == "https://authority.dila.edu.tw/place/search.php?code=PL000000010214"
        assert rec.license_class == LicenseClass.CC_BY_SA
        assert rec.granularity == GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT
        assert rec.match_method == MatchMethod.EXACT
        assert rec.match_confidence == "high"
        assert rec.historical_years is None                 # dynasty 为 null
        assert rec.parent_jurisdiction == "中國-江蘇省-蘇州市-吳江區"
        assert rec.source_citation == "X82n1571_p0313c24"   # note 末尾括注提取
        assert rec.is_reference_only is False
        assert rec.raw_payload["long"] == "120.6467"        # 坐标全量缓存于 raw_payload
        assert rec.raw_payload["lat"] == "31.1657"
        assert rec.raw_payload["pinyin"] == {"遯村": "dùn cūn"}

    def test_dynasty_field_carried_through(self, monkeypatch):
        p = _new_provider()
        _install_routes(monkeypatch, p, {DILA_DATA_URL: SONG_MOUNTAIN_JSONP})
        rec = p.fetch_by_id("PL000000023253")
        assert rec.historical_years == "慣用名"

    def test_short_code_expands_to_long_form(self, monkeypatch):
        p = _new_provider()
        captured = _install_routes(monkeypatch, p, {DILA_DATA_URL: DUN_VILLAGE_JSONP})
        rec = p.fetch_by_id("PL10214")
        assert rec is not None
        assert "id=PL000000010214" in captured[0]           # 请求用长码

    def test_malformed_ids_rejected_without_network(self, monkeypatch):
        p = _new_provider()
        captured = _install_routes(monkeypatch, p, {})      # 无路由：任何请求即断言失败
        assert p.fetch_by_id("BOGUS") is None
        assert p.fetch_by_id("PL123") is None               # 4 位短码非法
        assert p.fetch_by_id("PL0000000102145") is None     # 13 位非法
        assert p.fetch_by_id("") is None
        assert p.fetch_by_id(None) is None
        assert captured == []

    def test_null_and_empty_entries_return_none(self, monkeypatch):
        p = _new_provider()
        _install_routes(monkeypatch, p, {
            DILA_DATA_URL + "?type=place&id=PL000000010214": "cb(null)",
            DILA_DATA_URL + "?type=place&id=PL000000021579": 'cb({"data1":""})',  # 中研院授权子集
        })
        assert p.fetch_by_id("PL000000010214") is None
        assert p.fetch_by_id("PL000000021579") is None

    def test_garbage_body_returns_none(self, monkeypatch):
        p = _new_provider()
        _install_routes(monkeypatch, p, {DILA_DATA_URL: "<html>502 Bad Gateway</html>"})
        assert p.fetch_by_id("PL000000010214") is None

    def test_network_exception_swallowed_returns_none(self, monkeypatch):
        """真网络层异常路径：urlopen 抛 URLError 必须被吞掉，返回 None 不抛。"""

        def raise_urlopen(req, timeout=None):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(
            "haidian_kg.providers.dila.urllib.request.urlopen", raise_urlopen
        )
        p = _new_provider()
        assert p._http_get(f"{DILA_DATA_URL}?type=place&id=PL000000010214") is None
        assert p.fetch_by_id("PL000000010214") is None      # 全链路静默


class TestFetchByName:
    def test_search_then_fetch_pipeline(self, monkeypatch):
        p = _new_provider()
        captured = _install_routes(monkeypatch, p, {
            DILA_SEARCH_URL: SEARCH_HIT_HTML,
            DILA_DATA_URL: DUN_VILLAGE_JSONP,
        })
        records = p.fetch_by_name("遯村")
        assert records is not None and len(records) == 1
        assert records[0].matched_name == "遯村"
        assert any("ml=%E9%81%AF%E6%9D%91&isLikeSearch=1" in u for u in captured)
        assert any("isFurther=0" in u for u in captured)

    def test_extraction_scoped_to_fpr_blocks(self, monkeypatch):
        """侧栏 PL 码不得污染结果（实测搜索壳页侧栏含大量示例 PL 链接）。"""
        p = _new_provider()
        _install_routes(monkeypatch, p, {
            DILA_SEARCH_URL: SEARCH_HIT_HTML,
            DILA_DATA_URL: DUN_VILLAGE_JSONP,
        })
        captured_ids = []
        orig = p.fetch_by_id

        def spy(aid):
            captured_ids.append(aid)
            return orig(aid)

        monkeypatch.setattr(p, "fetch_by_id", spy)
        p.fetch_by_name("遯村")
        assert captured_ids == ["PL000000010214"]           # 侧栏 PL000000000083 未混入

    def test_max_results_caps_detail_fetches(self, monkeypatch):
        p = _new_provider()
        _install_routes(monkeypatch, p, {
            DILA_SEARCH_URL: SEARCH_MULTI_HIT_HTML,
            DILA_DATA_URL: DUN_VILLAGE_JSONP,
        })
        records = p.fetch_by_name("村", max_results=1)
        assert records is not None and len(records) == 1

    def test_api_unlicensed_subset_entries_skipped(self, monkeypatch):
        """搜索命中但 id 详情接口不覆盖（中研院授权子集）→ 逐条跳过。"""
        p = _new_provider()
        _install_routes(monkeypatch, p, {
            DILA_SEARCH_URL: SEARCH_MULTI_HIT_HTML,
            DILA_DATA_URL: 'cb({"data1":""})',              # 两个 id 都不返回数据
        })
        assert p.fetch_by_name("村") == []

    def test_zero_hits_returns_empty_list(self, monkeypatch):
        p = _new_provider()
        _install_routes(monkeypatch, p, {DILA_SEARCH_URL: SEARCH_ZERO_HIT_HTML})
        assert p.fetch_by_name("Qubernetes-Zzz") == []

    def test_search_network_failure_returns_none(self, monkeypatch):
        p = _new_provider()
        monkeypatch.setattr(p, "_http_get", lambda url: None)
        assert p.fetch_by_name("遯村") is None              # 传输层失败 ≠ 零命中

    def test_empty_name_rejected_without_network(self, monkeypatch):
        p = _new_provider()
        captured = _install_routes(monkeypatch, p, {})
        assert p.fetch_by_name("") is None
        assert p.fetch_by_name("   ") is None
        assert captured == []


class TestJsonpParsing:
    def test_bare_json_accepted(self):
        assert DilaProvider._strip_jsonp('{"a":1}') == {"a": 1}

    def test_jsonp_wrapper_stripped(self):
        assert DilaProvider._strip_jsonp("abc123({\"a\":1});") == {"a": 1}

    def test_garbage_returns_none(self):
        assert DilaProvider._strip_jsonp("") is None
        assert DilaProvider._strip_jsonp("<html>err</html>") is None
        assert DilaProvider._strip_jsonp("cb([1,2])") is None   # 非 dict


class TestIdNormalization:
    def test_lowercase_normalized(self):
        assert DilaProvider._normalize_authority_id("pl000000010214") == "PL000000010214"

    def test_short_code_zero_padded(self):
        assert DilaProvider._normalize_authority_id("PL21579") == "PL000000021579"

    def test_invalid_forms_return_none(self):
        assert DilaProvider._normalize_authority_id("CN0320584A06AA") is None  # 舊規範碼不收
        assert DilaProvider._normalize_authority_id(10214) is None
