"""
haidian_kg/query.py
海淀历史地名知识图谱查询与沿革推理引擎
融合 rdflib SPARQL 查询与 NetworkX 有向图算法，
实现地名生命周期回溯、断代时空切片检索、证据链溯源与假说真伪研判。
"""
import pathlib
from typing import List, Dict, Any, Optional
import rdflib
from rdflib.namespace import RDF, RDFS
import networkx as nx

HHTO = rdflib.Namespace("http://history.haidian.gov.cn/ontology/")
HD = rdflib.Namespace("http://history.haidian.gov.cn/resource/")


class KGQueryEngine:
    """历史地名时空图谱查询与推理引擎"""

    def __init__(self, ttl_path: Optional[pathlib.Path] = None):
        self.ttl_path = ttl_path or pathlib.Path("haidian_kg/data/haidian_kg.ttl")
        self.graph = rdflib.Graph()
        self._load_graph()
        self.evolution_graph = nx.DiGraph()
        self._build_evolution_network()

    def _load_graph(self):
        if not self.ttl_path.exists():
            from haidian_kg.builder import HaidianKGBuilder
            builder = HaidianKGBuilder()
            builder.export_turtle(self.ttl_path)
        self.graph.parse(str(self.ttl_path), format="turtle")

    def _build_evolution_network(self):
        """构建地名演变拓扑网络 (Predecessor -> Successor)"""
        # 从 evolvedFrom 边构建有向图: (target, evolvedFrom, source) => source -> target
        for target, _, source in self.graph.triples((None, HHTO.evolvedFrom, None)):
            src_str = str(source)
            tgt_str = str(target)
            src_label = self._get_label(source)
            tgt_label = self._get_label(target)
            self.evolution_graph.add_edge(src_str, tgt_str)
            self.evolution_graph.nodes[src_str]["label"] = src_label
            self.evolution_graph.nodes[tgt_str]["label"] = tgt_label

        # 确保所有地名实体即使无演变也有节点
        for top in self.graph.subjects(RDF.type, HHTO.Toponym):
            top_str = str(top)
            if top_str not in self.evolution_graph:
                self.evolution_graph.add_node(top_str, label=self._get_label(top))

    def _get_label(self, uri: rdflib.URIRef) -> str:
        for _, _, l in self.graph.triples((uri, RDFS.label, None)):
            return str(l)
        return uri.split("/")[-1]

    def _find_toponym_uri_by_label(self, label: str) -> Optional[str]:
        for node, data in self.evolution_graph.nodes(data=True):
            if data.get("label") == label:
                return node
        # 模糊匹配
        for node, data in self.evolution_graph.nodes(data=True):
            if label in data.get("label", ""):
                return node
        return None

    def trace_evolution(self, toponym_label: str) -> List[Dict[str, Any]]:
        """
        全生命周期演变溯源：
        从指定地名向前回溯至最原始前身，再沿演变链正向推演至终态。
        返回有序的演变节点链列表。
        """
        current_uri = self._find_toponym_uri_by_label(toponym_label)
        if not current_uri:
            return []

        # 1. 寻找该实体所在的弱连通分支所有前身与后继
        # 逆向追溯最古老根节点 (In-degree == 0)
        ancestors = set()
        queue = [current_uri]
        while queue:
            curr = queue.pop(0)
            ancestors.add(curr)
            preds = list(self.evolution_graph.predecessors(curr))
            for p in preds:
                if p not in ancestors:
                    queue.append(p)

        # 找到入度为0的根节点
        roots = [n for n in ancestors if self.evolution_graph.in_degree(n) == 0]
        root = roots[0] if roots else current_uri

        # 2. 从根节点沿拓扑排序生成演变序列
        visited = []
        q = [root]
        while q:
            curr = q.pop(0)
            if curr not in visited:
                visited.append(curr)
                successors = list(self.evolution_graph.successors(curr))
                q.extend(successors)

        return [{"uri": u, "label": self.evolution_graph.nodes[u].get("label", u)} for u in visited]

    def query_by_period(self, dynasty_keyword: str) -> List[Dict[str, Any]]:
        """按朝代关键词（如‘元’、‘明’、‘清’）检索在此断代记录的所有书证凭证"""
        results = []
        for att in self.graph.subjects(RDF.type, HHTO.PlaceAttestation):
            # 检查断代描述或记录年份
            comment = ""
            for _, _, c in self.graph.triples((att, RDFS.comment, None)):
                comment = str(c)
            if dynasty_keyword in comment:
                name = ""
                for _, _, n in self.graph.triples((att, RDFS.label, None)):
                    name = str(n)
                quote = ""
                for _, _, q in self.graph.triples((att, HHTO.originalQuote, None)):
                    quote = str(q)
                level = ""
                for _, _, l in self.graph.triples((att, HHTO.evidenceLevel, None)):
                    level = str(l)
                results.append({
                    "attestation_uri": str(att),
                    "attested_name": name,
                    "quote": quote,
                    "evidence_level": level,
                    "dynasty_info": comment,
                })
        return results

    def get_attestations(self, toponym_label: str) -> List[Dict[str, Any]]:
        """获取指定地名（及同族系前身/后继）挂接的全部文献书证与证据层级"""
        # 获取同族系全部地名
        lineage = self.trace_evolution(toponym_label)
        target_uris = {h["uri"] for h in lineage} if lineage else set()
        target_uri = self._find_toponym_uri_by_label(toponym_label)
        if target_uri:
            target_uris.add(target_uri)

        results = []
        for t_uri in target_uris:
            t_ref = rdflib.URIRef(t_uri)
            for _, _, att in self.graph.triples((t_ref, HHTO.attestedIn, None)):
                name = ""
                for _, _, n in self.graph.triples((att, RDFS.label, None)):
                    name = str(n)
                quote = ""
                for _, _, q in self.graph.triples((att, HHTO.originalQuote, None)):
                    quote = str(q)
                level = ""
                for _, _, l in self.graph.triples((att, HHTO.evidenceLevel, None)):
                    level = str(l)
                status = ""
                for _, _, s in self.graph.triples((att, HHTO.epistemicStatus, None)):
                    status = str(s)
                results.append({
                    "toponym_uri": t_uri,
                    "attestation_uri": str(att),
                    "attested_name": name,
                    "quote": quote,
                    "evidence_level": level,
                    "epistemic_status": status,
                })
        return results

    def find_contested_hypotheses(self) -> List[Dict[str, Any]]:
        """检出全区学术争议假说 (CONTESTED 状态)"""
        results = []
        for hypo in self.graph.subjects(RDF.type, HHTO.CompetingHypothesis):
            status = ""
            for _, _, s in self.graph.triples((hypo, HHTO.epistemicStatus, None)):
                status = str(s)
            if "CONTESTED" in status:
                title = ""
                for _, _, t in self.graph.triples((hypo, RDFS.label, None)):
                    title = str(t)
                summary = ""
                for _, _, sm in self.graph.triples((hypo, RDFS.comment, None)):
                    summary = str(sm)
                results.append({
                    "hypothesis_uri": str(hypo),
                    "title": title,
                    "claim_summary": summary,
                    "status": status,
                })
        return results

    def find_disproven_myths(self) -> List[Dict[str, Any]]:
        """检出全区已被证伪的伪说与负控制断言 (DISPROVEN 状态)"""
        results = []
        # 1. 来自假说实体
        for hypo in self.graph.subjects(RDF.type, HHTO.CompetingHypothesis):
            status = ""
            for _, _, s in self.graph.triples((hypo, HHTO.epistemicStatus, None)):
                status = str(s)
            if "DISPROVEN" in status:
                title = ""
                for _, _, t in self.graph.triples((hypo, RDFS.label, None)):
                    title = str(t)
                summary = ""
                for _, _, sm in self.graph.triples((hypo, RDFS.comment, None)):
                    summary = str(sm)
                results.append({
                    "uri": str(hypo),
                    "title": title,
                    "claim_summary": summary,
                    "type": "Hypothesis",
                })
        # 2. 来自书证实体
        for att in self.graph.subjects(RDF.type, HHTO.PlaceAttestation):
            status = ""
            for _, _, s in self.graph.triples((att, HHTO.epistemicStatus, None)):
                status = str(s)
            if "DISPROVEN" in status:
                name = ""
                for _, _, n in self.graph.triples((att, RDFS.label, None)):
                    name = str(n)
                quote = ""
                for _, _, q in self.graph.triples((att, HHTO.originalQuote, None)):
                    quote = str(q)
                results.append({
                    "uri": str(att),
                    "title": name,
                    "claim_summary": quote,
                    "type": "Attestation",
                })
        return results


if __name__ == "__main__":
    engine = KGQueryEngine()
    print("--- 演变谱系追踪 (六郎庄) ---")
    print(engine.trace_evolution("六郎庄"))
    print("\n--- 元代书证 ---")
    print(len(engine.query_by_period("元")))
    print("\n--- 争议假说 ---")
    print(engine.find_contested_hypotheses())
    print("\n--- 已证伪伪说 ---")
    print(engine.find_disproven_myths())
