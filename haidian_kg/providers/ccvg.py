"""
CCVG 本地镜像索引查询器（CcvgLocalIndex）
=========================================

加载 haidian_kg/data/ccvg/ccvg_index.json（由同目录 build_index.py 离线构建，
原始 CSV/KMZ 不入库），为闭包扩展引擎提供村志级离线查询：

  - query(name)  精确键命中返回行记录列表（简体/繁体/拼音/去通名核心键）；
    索引文件缺失或未命中一律返回空列表，绝不抛异常阻塞流水线。
  - resolve(name) 在 query 之上包装为 AuthorityMatchRecord（复用
    authority_resolver 的裁决记录类型，provider_id='ccvg'）。

许可证纪律：CCVG 官网声明供学者免费下载，但 D-Scholarship 权利声明为
Copyright Not Evaluated —— 对应 LicenseClass.METADATA_UNSPECIFIED，
本地仅作匹配留证，不再分发原始文件。
"""

import importlib.util
import json
from pathlib import Path
from typing import Dict, List, Optional

from haidian_kg.authority_resolver import (
    AuthorityMatchRecord,
    GeographicalGranularity,
    LicenseClass,
    MatchMethod,
)

_PROVIDER_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_PATH = _PROVIDER_ROOT / "data" / "ccvg" / "ccvg_index.json"
_DEFAULT_BUILDER_PATH = _PROVIDER_ROOT / "data" / "ccvg" / "build_index.py"

#: provider 标识（与 build_index 索引 meta.provider_id 一致）
PROVIDER_ID = "ccvg"


def _load_builder():
    """按路径惰性加载 build_index.py，仅复用其 s2t/t2s 繁简归一表；
    文件缺失时返回 None（查询退化为原样键匹配）。"""
    try:
        spec = importlib.util.spec_from_file_location(
            "ccvg_build_index", _DEFAULT_BUILDER_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except (OSError, AttributeError):
        return None


_builder = _load_builder()


class CcvgLocalIndex:
    """CCVG 村志倒排索引的离线加载与查询（外部网络波动的兜底层）。"""

    provider_id = PROVIDER_ID

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = Path(index_path) if index_path else DEFAULT_INDEX_PATH
        self.records: Dict[str, Dict] = {}
        self.inverted_index: Dict[str, List[str]] = {}
        self.meta: Dict = {}
        self._loaded = False

    # ------------------------------------------------------------------
    def load(self) -> "CcvgLocalIndex":
        """读取索引 JSON；文件缺失/损坏时保持空索引（不抛异常）。"""
        self._loaded = True
        try:
            with open(self.index_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return self
        self.records = data.get("records", {})
        self.inverted_index = data.get("inverted_index", {})
        self.meta = data.get("meta", {})
        return self

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    # ------------------------------------------------------------------
    def _candidate_keys(self, name: str) -> List[str]:
        keys = [name.strip()]
        if _builder is not None:
            try:
                keys.append(_builder.t2s(name.strip()))
            except Exception:
                pass
        seen, uniq = set(), []
        for k in keys:
            if k and k not in seen:
                seen.add(k)
                uniq.append(k)
        return uniq

    def query(self, name: str) -> List[Dict]:
        """按村名/村志题名/拼音/去通名核心精确查询，返回行记录列表。

        索引文件缺失、未加载或未命中 → 空列表（流水线不阻塞）。
        拼音键统一小写；繁体查询经 t2s 归一后再命中简体规范键。
        """
        self._ensure_loaded()
        if not name or not isinstance(name, str):
            return []
        for key in self._candidate_keys(name):
            for lowered in (key, key.lower()):
                codes = self.inverted_index.get(lowered)
                if codes:
                    return [self.records[c] for c in codes if c in self.records]
        return []

    # ------------------------------------------------------------------
    def to_match_record(self, row: Dict) -> AuthorityMatchRecord:
        """行记录 → AuthorityMatchRecord（供 AuthorityResolver 联合裁决）。"""
        name = row.get("village_name_cn") or row.get("gazetteer_title") or ""
        where = [p for p in (row.get("county_cn"), row.get("city_cn"),
                             row.get("province_cn")) if p]
        built = (self.meta.get("built_at") or "")[:10]
        return AuthorityMatchRecord(
            provider_id=self.provider_id,
            provider_record_id="ccvg:%s" % row.get("gazetteer_code", ""),
            matched_name=name,
            matched_uri=self.meta.get("sources", {}).get("item"),
            license_class=LicenseClass.METADATA_UNSPECIFIED,
            granularity=GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT,
            match_method=MatchMethod.LOCAL_MIRROR_INDEX,
            match_confidence="high",
            historical_years="pub %s" % row["pub_year"] if row.get("pub_year") else None,
            parent_jurisdiction=", ".join(where) or None,
            source_citation=(
                "Contemporary Chinese Village Gazetteer Data (CCVG), "
                "ULS East Asian Library, Univ. of Pittsburgh"
            ),
            is_reference_only=False,
            retrieved_at=built,
            raw_payload=row,
        )

    def resolve(self, name: str) -> List[AuthorityMatchRecord]:
        """查询并包装为裁决记录；空命中 → 空列表。"""
        return [self.to_match_record(row) for row in self.query(name)]
