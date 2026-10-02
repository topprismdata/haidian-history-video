"""
DILA 地名規範資料库 Provider（原型 connector）
=============================================

数据源：https://authority.dila.edu.tw/（法鼓文理学院 DDBC 地名规范资料库）

真实 API 契约（2026-10-02 实测，详见 .superpowers/sdd/dila-api-findings.md）：
1. 详情（JSONP，仅覆盖 DILA 自修纂 ~18,000 筆）：
   GET https://authority.dila.edu.tw/webwidget/getAuthorityData.php
       ?type=place&id=<AuthorityID>&jsoncallback=<cb>
   → `<cb>({"data1":{authorityID,name,dynasty,long,lat,districtModern,note,...}})`
   未命中/参数无效 → `<cb>(null)` 或 `<cb>({"data1":""})`。
2. 名称搜索（服务端渲染 HTML）：
   GET https://authority.dila.edu.tw/place/search.php?ml=<词>&isLikeSearch=1&isFurther=0
   → HTML，命中条目在 `class="fpr_div"` 块内，含規範碼 PLxxxxxxxxxxxx。

许可证纪律（与 authority_resolver.py 设计纪律一致）：
- API/下载仅提供 DILA 自修纂子集（CC BY-SA 3.0，允许本地镜像）→ LicenseClass.CC_BY_SA。
- 在线搜索界面另含中研院 CCTS 授权的 ~40,000 筆：这些条目名称搜索可命中，
  但 id 详情接口不返回数据（fetch_by_id 得 None），连接器自然不会将其复制入库。

失败纪律：任何网络/解析故障一律返回 None，绝不抛异常阻塞闭包流水线。
"""

import json
import re
import time
import urllib.parse
import urllib.request
from typing import List, Optional

from haidian_kg.authority_resolver import (
    AuthorityMatchRecord,
    GeographicalGranularity,
    LicenseClass,
    MatchMethod,
)

DILA_DATA_URL = "https://authority.dila.edu.tw/webwidget/getAuthorityData.php"
DILA_SEARCH_URL = "https://authority.dila.edu.tw/place/search.php"

# 长规范码 PL + 12 位数字；短码 PL + 5 位数字（如 PL10214 = PL000000010214）
_LONG_ID_RE = re.compile(r"^PL\d{12}$")
_SHORT_ID_RE = re.compile(r"^PL(\d{5})$")
# 只在 fpr_div 命中块内提取规范码（页面侧栏/工具区也可能出现 PL 码，必须定界）
_AUTHORITY_ID_IN_HTML_RE = re.compile(r"PL\d{12}")
_FPR_BLOCK_SPLIT_RE = re.compile(r'class="fpr_div"')
# note 末尾的文献出处括注，如 （X82n1571_p0313c24）
_TRAILING_CITATION_RE = re.compile(r"[（(]([^（）()]{4,80})[）)]\s*$")

_REQUEST_TIMEOUT_SEC = 10.0
_USER_AGENT = "haidian-kg-closure/0.1 (prototype DILA connector; polite throttle)"


class DilaProvider:
    """DILA 地名规范库只读 connector 原型。

    - fetch_by_id(authority_id) -> Optional[AuthorityMatchRecord]
    - fetch_by_name(name, max_results) -> Optional[List[AuthorityMatchRecord]]
      （搜索请求本身失败 → None；成功但零命中 → []）

    网络层经 _http_get 注入，单元测试 monkeypatch 该方法即可，不触外网。
    """

    provider_id = "dila"

    def __init__(
        self,
        data_url: str = DILA_DATA_URL,
        search_url: str = DILA_SEARCH_URL,
        min_interval_sec: float = 1.2,
        timeout_sec: float = _REQUEST_TIMEOUT_SEC,
    ):
        self.data_url = data_url
        self.search_url = search_url
        self.min_interval_sec = min_interval_sec
        self.timeout_sec = timeout_sec
        self._last_request_at: float = 0.0

    # ------------------------------------------------------------------ 网络层
    def _throttle(self) -> None:
        """礼貌节流：两次请求间隔不小于 min_interval_sec（未观测到官方限速，保守处理）。"""
        elapsed = time.monotonic() - self._last_request_at
        if self._last_request_at > 0 and elapsed < self.min_interval_sec:
            time.sleep(self.min_interval_sec - elapsed)
        self._last_request_at = time.monotonic()

    def _http_get(self, url: str) -> Optional[str]:
        """GET 并返回 UTF-8 文本；任何故障返回 None（外部故障不阻塞纪律）。"""
        try:
            self._throttle()
            req = urllib.request.Request(
                url,
                headers={"User-Agent": _USER_AGENT, "Accept": "*/*"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return None

    # ------------------------------------------------------------------ 解析层
    @staticmethod
    def _strip_jsonp(body: str) -> Optional[dict]:
        """剥离 JSONP 包装 `<cb>({...})`；裸 JSON 亦兼容。失败返回 None。"""
        if not body:
            return None
        text = body.strip()
        try:
            m = re.match(r"^[^(]*\((.*)\)\s*;?\s*$", text, flags=re.S)
            payload = m.group(1) if m else text
            data = json.loads(payload)
        except (ValueError, TypeError):
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _normalize_authority_id(authority_id: str) -> Optional[str]:
        """校验/归一规范码：长码原样；5 位短码补零展开；其余 None。"""
        if not isinstance(authority_id, str):
            return None
        aid = authority_id.strip().upper()
        if _LONG_ID_RE.match(aid):
            return aid
        m = _SHORT_ID_RE.match(aid)
        if m:
            return "PL" + m.group(1).zfill(12)
        return None

    @staticmethod
    def _entry_to_match(entry: dict) -> Optional[AuthorityMatchRecord]:
        """data1 条目 → AuthorityMatchRecord；缺 authorityID/name 视为无效。"""
        if not isinstance(entry, dict):
            return None
        aid = entry.get("authorityID")
        name = entry.get("name")
        if not aid or not name:
            return None

        note = entry.get("note") or ""
        citation = None
        m = _TRAILING_CITATION_RE.search(note)
        if m:
            citation = m.group(1)

        return AuthorityMatchRecord(
            provider_id="dila",
            provider_record_id=aid,
            matched_name=name,
            matched_uri=f"https://authority.dila.edu.tw/place/search.php?code={aid}",
            license_class=LicenseClass.CC_BY_SA,
            granularity=GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT,
            match_method=MatchMethod.EXACT,
            match_confidence="high",
            historical_years=entry.get("dynasty"),          # 朝代字段（可为 None/'慣用名'）
            parent_jurisdiction=entry.get("districtModern"),  # 现代行政区，如 中國-江蘇省-蘇州市-吳江區
            source_citation=citation,
            is_reference_only=False,
            raw_payload=entry,  # 含 long/lat/names/pinyin/shortAuthorityID 全量缓存
        )

    @staticmethod
    def _extract_hit_ids(search_html: str) -> List[str]:
        """从名称搜索 HTML 的 fpr_div 命中块内按出现顺序去重提取规范码。"""
        ids: List[str] = []
        for block in _FPR_BLOCK_SPLIT_RE.split(search_html)[1:]:
            for aid in _AUTHORITY_ID_IN_HTML_RE.findall(block):
                if aid not in ids:
                    ids.append(aid)
        return ids

    # ------------------------------------------------------------------ 公开 API
    def fetch_by_id(self, authority_id: str) -> Optional[AuthorityMatchRecord]:
        """按规范码取详情。任何失败（网络/格式/未命中/短码非法）返回 None。"""
        aid = self._normalize_authority_id(authority_id)
        if aid is None:
            return None
        url = (
            f"{self.data_url}?type=place&id={urllib.parse.quote(aid)}"
            f"&jsoncallback=dilaConnectorProbe"
        )
        body = self._http_get(url)
        if body is None:
            return None
        data = self._strip_jsonp(body)
        if not data:
            return None
        entry = data.get("data1")
        return self._entry_to_match(entry) if entry else None

    def fetch_by_name(
        self,
        name: str,
        max_results: int = 5,
    ) -> Optional[List[AuthorityMatchRecord]]:
        """按名称模糊搜索（isLikeSearch=1），再逐条取详情。

        返回 None 仅表示搜索请求本身失败（网络故障）；成功但零命中返回 []。
        命中的条目若属中研院授权子集（id 详情接口不覆盖），逐条得 None 后跳过。
        """
        if not name or not name.strip():
            return None
        url = (
            f"{self.search_url}?ml={urllib.parse.quote(name.strip())}"
            f"&isLikeSearch=1&isFurther=0"
        )
        html = self._http_get(url)
        if html is None:
            return None
        records: List[AuthorityMatchRecord] = []
        for aid in self._extract_hit_ids(html):
            if len(records) >= max_results:
                break
            rec = self.fetch_by_id(aid)
            if rec is not None:
                records.append(rec)
        return records


def default_provider() -> DilaProvider:
    """供闭包引擎按需取用的默认实例。"""
    return DilaProvider()
