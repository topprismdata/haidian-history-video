"""
外部地名权威裁决器（Authority Federation Resolver）
==================================================

用于闭包扩展引擎（Closure Engine）的候选裁决层（Candidate Triage & Validation）。
多源异构架构：
  AuthorityResolver = TGAZ + DILA + CCTS_MHPNAME + MCGD

设计纪律（2026-10-02 外部核验定稿）：
1. 不以单一 TGAZ 为绝对裁决源（TGAZ 虽含 1820/1911 宛平县西大营等村镇，但偏向政区级；未命中不否决）。
2. DILA 为宗教/文献独立视角，包含真实村落（遯村、大范村）与寺庙山泉，CC BY-SA 3.0，允许本地镜像。
3. CCTS_MHPNAME（读史方舆纪要层 61,685 条明代县级以下地名：村、庄、店、寨、桥、闸、铺等）
   为非开放许可证，标为 REFERENCE_ONLY_UNLESS_LICENSED：仅用于匹配留证与 URI 记录，绝不全量复制入公开库。
4. MCGD（Aix-Marseille）提供近代外文转写与异名关联，用于异名消歧。
5. 外部网络波动不可阻塞闭包流水线；所有外部查询必须在 machine_observation 层带版本缓存。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import datetime


class LicenseClass(str, Enum):
    OPEN_DATA = "OPEN_DATA"                                    # 明确开放数据（CC0, ODbL 等）
    CC_BY_SA = "CC_BY_SA"                                      # CC BY-SA 3.0/4.0（如 DILA 自建子集）
    CC_BY_NC = "CC_BY_NC"                                      # CC BY-NC（如 CHGIS/TGAZ 学术免费）
    REFERENCE_ONLY_UNLESS_LICENSED = "REFERENCE_ONLY_UNLESS_LICENSED"  # 仅作匹配留证，严禁全量再发布（如 CCTS 纪要层）
    METADATA_UNSPECIFIED = "METADATA_UNSPECIFIED"              # 许可证未明确（如 MCGD Zenodo 元数据待核）


class GeographicalGranularity(str, Enum):
    PROVINCE_PREFECTURE = "PROVINCE_PREFECTURE"                # 省/府/道级
    COUNTY_LEVEL = "COUNTY_LEVEL"                              # 县/州级
    SUB_COUNTY_TOWN = "SUB_COUNTY_TOWN"                        # 县以下乡镇/市镇（如 TGAZ 1820/1911 ctype=cun zhen）
    MICRO_VILLAGE_SETTLEMENT = "MICRO_VILLAGE_SETTLEMENT"      # 村/庄/店/寨/桥/闸/寺等微观聚落与工程点


class MatchMethod(str, Enum):
    EXACT = "EXACT"                                            # 完全精准匹配
    PREFIX_LIKE = "PREFIX_LIKE"                                # 前缀 LIKE（如 TGAZ 搜索匹配）
    ALIAS_VARIANT = "ALIAS_VARIANT"                            # 异名/异体/西文转写匹配（如 MCGD/DILA）
    LOCAL_MIRROR_INDEX = "LOCAL_MIRROR_INDEX"                  # 本地镜像倒排索引
    MANUAL_CURATED = "MANUAL_CURATED"                          # 人工校定核实


@dataclass
class AuthorityMatchRecord:
    """单个外部权威源的单条匹配记录（可安全持久化入 machine_observation）"""
    provider_id: str                                           # 如 'tgaz', 'dila', 'ccts_mhpname', 'mcgd'
    provider_record_id: str                                    # 如 'hvd_141901', 'PL000000010214'
    matched_name: str                                          # 命中的名称
    matched_uri: Optional[str] = None                          # 外部规范 URI
    license_class: LicenseClass = LicenseClass.CC_BY_NC
    granularity: GeographicalGranularity = GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT
    match_method: MatchMethod = MatchMethod.EXACT
    match_confidence: str = "high"                             # high / mid / low
    historical_years: Optional[str] = None                     # 如 '1577 ~ 1911'
    parent_jurisdiction: Optional[str] = None                  # 如 '宛平县', '顺天府'
    source_citation: Optional[str] = None                      # 外部权威引用的文献（如《读史方舆纪要》卷十一）
    is_reference_only: bool = False                            # 是否受版权限制仅作外部比对留证
    retrieved_at: str = field(default_factory=lambda: datetime.date.today().isoformat())
    raw_payload: Optional[Dict] = None                         # 缓存的原始 JSON/dict 响应


@dataclass
class AuthorityResolutionResult:
    """候选假说经多源 AuthorityResolver 联合判定后的综合裁决结果"""
    query_name: str
    matches: List[AuthorityMatchRecord] = field(default_factory=list)
    consensus_confidence: str = "low"                          # high / mid / low
    has_micro_village_match: bool = False                      # 是否有村落/微观聚落级直接命中
    has_temple_religious_match: bool = False                   # 是否有寺庙/宗教圣地级命中（DILA 等）
    is_pure_modern_new_name: bool = False                      # 是否仅现代村志命中而历史源全无
    verdict_summary: str = ""

    def add_match(self, record: AuthorityMatchRecord) -> None:
        self.matches.append(record)
        if record.granularity == GeographicalGranularity.MICRO_VILLAGE_SETTLEMENT:
            self.has_micro_village_match = True
        if record.provider_id == "dila":
            self.has_temple_religious_match = True

        # 联合置信度判定：异源交叉（如 TGAZ 政区 + DILA/CCTS 微观）提升为 high
        providers = {m.provider_id for m in self.matches}
        if len(providers) >= 2 or any(m.match_confidence == "high" for m in self.matches):
            self.consensus_confidence = "high"
        elif len(providers) == 1:
            self.consensus_confidence = "mid"


class AuthorityResolver:
    """
    联合地名权威裁决器：管理多源 Provider，支持离线缓存优先与在线按需解析。
    遵循：
      - CCTS_MHPNAME 标记 is_reference_only=True
      - DILA 标记可本地镜像
      - TGAZ 前缀 LIKE 解析
    """

    def __init__(self, offline_cache: Optional[Dict[str, List[AuthorityMatchRecord]]] = None):
        self._cache: Dict[str, List[AuthorityMatchRecord]] = offline_cache or {}

    def register_cached_match(self, query_name: str, match: AuthorityMatchRecord) -> None:
        self._cache.setdefault(query_name, []).append(match)

    def resolve(self, candidate_name: str) -> AuthorityResolutionResult:
        """
        裁决给定候选地名字串。
        优先读取缓存；未命中时返回空匹配（不阻塞离线流水线）。
        """
        res = AuthorityResolutionResult(query_name=candidate_name)
        cached = self._cache.get(candidate_name, [])
        for m in cached:
            res.add_match(m)

        if not res.matches:
            res.consensus_confidence = "low"
            res.verdict_summary = f"未在多源权威库（TGAZ/DILA/CCTS/MCGD）命中；保留为本地发现待人工Triage"
        else:
            providers = ", ".join(sorted({m.provider_id for m in res.matches}))
            res.verdict_summary = f"在 {providers} 命中 {len(res.matches)} 条记录；综合置信度: {res.consensus_confidence}"

        return res
