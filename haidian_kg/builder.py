"""
haidian_kg/builder.py
海淀历史地名 RDF 知识图谱构建器与 Turtle 序列化引擎
读取 schema 与 entities.json 数据，构建符合 OWL 2/RDFS 语义规范的全量时空知识图谱。
"""
import pathlib
from typing import Optional
import rdflib
from rdflib import Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
from haidian_kg.extractor import HaidianCorpusExtractor, HaidianDataset


HHTO = rdflib.Namespace("http://history.haidian.gov.cn/ontology/")
HD = rdflib.Namespace("http://history.haidian.gov.cn/resource/")


class HaidianKGBuilder:
    """海淀历史地名知识图谱构建与导出器"""

    def __init__(self, dataset: Optional[HaidianDataset] = None):
        self.dataset = dataset or HaidianCorpusExtractor.load_or_extract()
        self.graph = rdflib.Graph()
        self._bind_namespaces()

    def _bind_namespaces(self):
        self.graph.bind("hhto", HHTO)
        self.graph.bind("hd", HD)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)

    def build_graph(self) -> rdflib.Graph:
        """从实体数据集构建全量 RDF 三元组图谱"""
        # 1. 加载核心本体模式定义
        ontology_file = pathlib.Path("haidian_kg/ontology/haidian_ontology.ttl")
        if ontology_file.exists():
            self.graph.parse(str(ontology_file), format="turtle")

        # 2. 构建物理空间地物 (Physical Features)
        for feat in self.dataset.physical_features:
            feat_uri = HD[feat.id]
            # 基础类型与具体地物类型
            self.graph.add((feat_uri, RDF.type, HHTO.PhysicalFeature))
            if hasattr(HHTO, feat.feature_type):
                self.graph.add((feat_uri, RDF.type, getattr(HHTO, feat.feature_type)))
            self.graph.add((feat_uri, RDFS.label, Literal(feat.label, lang="zh")))
            if feat.description:
                self.graph.add((feat_uri, RDFS.comment, Literal(feat.description, lang="zh")))
            if feat.coordinates:
                coord_str = f"{feat.coordinates[0]},{feat.coordinates[1]}"
                self.graph.add((feat_uri, HHTO.coordinatesWGS84, Literal(coord_str, datatype=XSD.string)))

        # 3. 构建建置制度实体 (Administrative Units)
        for unit in self.dataset.administrative_units:
            unit_uri = HD[unit.id]
            self.graph.add((unit_uri, RDF.type, HHTO.AdministrativeUnit))
            if hasattr(HHTO, unit.unit_type):
                self.graph.add((unit_uri, RDF.type, getattr(HHTO, unit.unit_type)))
            self.graph.add((unit_uri, RDFS.label, Literal(unit.label, lang="zh")))
            if unit.description:
                self.graph.add((unit_uri, RDFS.comment, Literal(unit.description, lang="zh")))
            if unit.located_at_feature_id:
                feat_uri = HD[unit.located_at_feature_id]
                self.graph.add((unit_uri, HHTO.locatedAtFeature, feat_uri))
            if unit.valid_start_year is not None:
                self.graph.add((unit_uri, HHTO.validTimeStart, Literal(unit.valid_start_year, datatype=XSD.integer)))
            if unit.valid_end_year is not None:
                self.graph.add((unit_uri, HHTO.validTimeEnd, Literal(unit.valid_end_year, datatype=XSD.integer)))

        # 4. 构建地名称号实体 (Toponyms)
        for top in self.dataset.toponyms:
            top_uri = HD[top.id]
            self.graph.add((top_uri, RDF.type, HHTO.Toponym))
            self.graph.add((top_uri, RDFS.label, Literal(top.standard_form, lang="zh")))
            self.graph.add((top_uri, HHTO.standardForm, Literal(top.standard_form, datatype=XSD.string)))
            if top.phonetic_pinyin:
                self.graph.add((top_uri, HHTO.phoneticPinyin, Literal(top.phonetic_pinyin, datatype=XSD.string)))
            if top.associated_unit_id:
                unit_uri = HD[top.associated_unit_id]
                self.graph.add((unit_uri, HHTO.namedAs, top_uri))
            if top.predecessor_toponym_id:
                pred_uri = HD[top.predecessor_toponym_id]
                self.graph.add((top_uri, HHTO.evolvedFrom, pred_uri))

        # 5. 构建史料书证用例实体 (Place Attestations)
        for att in self.dataset.place_attestations:
            att_uri = HD[att.id]
            top_uri = HD[att.toponym_id]

            self.graph.add((att_uri, RDF.type, HHTO.PlaceAttestation))
            self.graph.add((att_uri, RDFS.label, Literal(att.attested_name, lang="zh")))
            self.graph.add((top_uri, HHTO.attestedIn, att_uri))

            # 书证详细属性
            self.graph.add((att_uri, HHTO.originalQuote, Literal(att.quote, lang="zh")))
            self.graph.add((att_uri, HHTO.evidenceLevel, Literal(att.evidence_level.value, datatype=XSD.string)))
            self.graph.add((att_uri, HHTO.epistemicStatus, Literal(att.epistemic_status.value, datatype=XSD.string)))
            self.graph.add((att_uri, RDFS.comment, Literal(f"断代: {att.dynasty} | 来源: 《{att.source_title}》", lang="zh")))

            if att.recorded_year is not None:
                self.graph.add((att_uri, HHTO.recordedYear, Literal(att.recorded_year, datatype=XSD.integer)))
            if att.notes:
                self.graph.add((att_uri, HHTO.epistemicNotes, Literal(att.notes, lang="zh")))

        # 6. 构建地名演变事件 (Toponym Evolution Events)
        for evt in self.dataset.evolution_events:
            evt_uri = HD[evt.id]
            self.graph.add((evt_uri, RDF.type, HHTO.ToponymEvolutionEvent))
            if hasattr(HHTO, evt.event_type):
                self.graph.add((evt_uri, RDF.type, getattr(HHTO, evt.event_type)))
            self.graph.add((evt_uri, RDFS.label, Literal(evt.description, lang="zh")))

            target_uri = HD[evt.target_toponym_id]
            self.graph.add((evt_uri, HHTO.targetToponym, target_uri))
            self.graph.add((target_uri, HHTO.evolutionTriggeredBy, evt_uri))

            if evt.source_toponym_id:
                src_uri = HD[evt.source_toponym_id]
                self.graph.add((evt_uri, HHTO.sourceToponym, src_uri))
                # 建立前后演变关系
                self.graph.add((target_uri, HHTO.evolvedFrom, src_uri))

            if evt.occurred_year is not None:
                self.graph.add((evt_uri, HHTO.recordedYear, Literal(evt.occurred_year, datatype=XSD.integer)))
            if evt.triggering_person:
                self.graph.add((evt_uri, HHTO.triggeringPerson, Literal(evt.triggering_person, lang="zh")))

        # 7. 构建争议假说 (Competing Hypotheses)
        for hypo in self.dataset.competing_hypotheses:
            hypo_uri = HD[hypo.id]
            top_uri = HD[hypo.toponym_id]
            self.graph.add((hypo_uri, RDF.type, HHTO.CompetingHypothesis))
            self.graph.add((hypo_uri, RDFS.label, Literal(hypo.hypothesis_title, lang="zh")))
            self.graph.add((hypo_uri, RDFS.comment, Literal(hypo.claim_summary, lang="zh")))
            self.graph.add((top_uri, HHTO.hasHypothesis, hypo_uri))
            self.graph.add((hypo_uri, HHTO.epistemicStatus, Literal(hypo.confidence_status.value, datatype=XSD.string)))

            for s_id in hypo.supported_by_attestation_ids:
                self.graph.add((hypo_uri, HHTO.supportedBy, HD[s_id]))
            for d_id in hypo.disproven_by_attestation_ids:
                self.graph.add((hypo_uri, HHTO.disprovenBy, HD[d_id]))

        return self.graph

    def export_turtle(self, output_path: pathlib.Path):
        """将完整知识图谱导出为标准 Turtle 文件"""
        if len(self.graph) == 0:
            self.build_graph()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph.serialize(destination=str(output_path), format="turtle")


if __name__ == "__main__":
    builder = HaidianKGBuilder()
    g = builder.build_graph()
    out = pathlib.Path("haidian_kg/data/haidian_kg.ttl")
    builder.export_turtle(out)
    print(f"Exported Haidian KG to {out} with {len(g)} triples.")
