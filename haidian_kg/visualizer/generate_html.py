"""
haidian_kg/visualizer/generate_html.py
海淀历史地名知识图谱离线交互式可视化看板生成器
读取 entities.json 数据，组装拓扑图元，输出单文件离线 HTML (index.html)。
包含 D3.js 力导向图、时空地层演进游标、实体分类过滤与考据证据抽屉。
"""
import json
import pathlib
from typing import Dict, List, Any


def generate_graph_data(entities_data: Dict[str, Any]) -> Dict[str, Any]:
    nodes = []
    links = []
    node_ids = set()

    # 1. 物理地物
    for feat in entities_data.get("physical_features", []):
        f_id = feat["id"]
        nodes.append({
            "id": f_id,
            "label": feat["label"],
            "group": "PhysicalFeature",
            "category": feat["feature_type"],
            "description": feat.get("description", ""),
            "coordinates": feat.get("coordinates"),
            "year": -1000,
        })
        node_ids.add(f_id)

    # 2. 建置实体
    for unit in entities_data.get("administrative_units", []):
        u_id = unit["id"]
        nodes.append({
            "id": u_id,
            "label": unit["label"],
            "group": "AdministrativeUnit",
            "category": unit["unit_type"],
            "description": unit.get("description", ""),
            "year": unit.get("valid_start_year") or 1400,
        })
        node_ids.add(u_id)

        if unit.get("located_at_feature_id") and unit["located_at_feature_id"] in node_ids:
            links.append({
                "source": u_id,
                "target": unit["located_at_feature_id"],
                "type": "locatedAt",
                "label": "地理坐落于",
            })

    # 3. 地名实体
    for top in entities_data.get("toponyms", []):
        t_id = top["id"]
        nodes.append({
            "id": t_id,
            "label": top["standard_form"],
            "group": "Toponym",
            "category": top["name_type"],
            "pinyin": top.get("phonetic_pinyin", ""),
            "year": 1200,
        })
        node_ids.add(t_id)

        if top.get("associated_unit_id") and top["associated_unit_id"] in node_ids:
            links.append({
                "source": top["associated_unit_id"],
                "target": t_id,
                "type": "namedAs",
                "label": "建制定名为",
            })

        if top.get("predecessor_toponym_id") and top["predecessor_toponym_id"] in node_ids:
            links.append({
                "source": top["predecessor_toponym_id"],
                "target": t_id,
                "type": "evolvedFrom",
                "label": "历史演变自",
            })

    # 4. 书证用例实体
    for att in entities_data.get("place_attestations", []):
        a_id = att["id"]
        yr = att.get("recorded_year") or 1500
        nodes.append({
            "id": a_id,
            "label": att["attested_name"],
            "group": "PlaceAttestation",
            "evidence_level": att["evidence_level"],
            "epistemic_status": att["epistemic_status"],
            "quote": att["quote"],
            "source_title": att["source_title"],
            "source_author": att.get("source_author", ""),
            "dynasty": att["dynasty"],
            "notes": att.get("notes", ""),
            "year": yr,
        })
        node_ids.add(a_id)

        if att["toponym_id"] in node_ids:
            links.append({
                "source": att["toponym_id"],
                "target": a_id,
                "type": "attestedIn",
                "label": "见载书证于",
            })

    # 5. 演变事件实体
    for evt in entities_data.get("evolution_events", []):
        e_id = evt["id"]
        yr = evt.get("occurred_year") or 1600
        nodes.append({
            "id": e_id,
            "label": evt["event_type"],
            "group": "EvolutionEvent",
            "category": evt["event_type"],
            "description": evt["description"],
            "dynasty": evt.get("dynasty", ""),
            "year": yr,
        })
        node_ids.add(e_id)

        if evt.get("source_toponym_id") and evt["source_toponym_id"] in node_ids:
            links.append({
                "source": evt["source_toponym_id"],
                "target": e_id,
                "type": "eventSource",
                "label": "演变前源",
            })
        if evt.get("target_toponym_id") and evt["target_toponym_id"] in node_ids:
            links.append({
                "source": e_id,
                "target": evt["target_toponym_id"],
                "type": "eventTarget",
                "label": "演变生成",
            })

    return {"nodes": nodes, "links": links}


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>海淀历史地名知识图谱 (HHTO) 交互式看板</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="./d3.v7.min.js"></script>
  <script>
    if (typeof d3 === 'undefined') {
      document.write('<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"><\\/script>');
    }
  </script>
  <style>
    :root {
      --bg: #0f141c;
      --panel-bg: rgba(22, 30, 44, 0.92);
      --border: #28374d;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --gold: #fbbf24;
      --purple: #c084fc;
      --green: #4ade80;
      --red: #f87171;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background: var(--bg);
      color: var(--text);
      overflow: hidden;
      height: 100vh;
      display: flex;
    }
    #main-container {
      flex: 1;
      height: 100vh;
      position: relative;
    }
    #graph-svg {
      width: 100%;
      height: 100%;
      cursor: grab;
    }
    #graph-svg:active { cursor: grabbing; }

    /* 控制顶栏 */
    .header-bar {
      position: absolute;
      top: 16px;
      left: 16px;
      background: var(--panel-bg);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 20px;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    .header-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--accent);
      letter-spacing: 0.5px;
    }
    .search-input {
      background: #111827;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 6px 12px;
      color: var(--text);
      font-size: 13px;
      width: 180px;
      outline: none;
    }
    .search-input:focus { border-color: var(--accent); }

    /* 底部时间轴浮动滑块 */
    .timeline-slider-card {
      position: absolute;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--panel-bg);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 24px;
      z-index: 10;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      width: 620px;
      box-shadow: 0 12px 32px rgba(0,0,0,0.6);
    }
    .timeline-labels {
      display: flex;
      justify-content: space-between;
      width: 100%;
      font-size: 11px;
      color: var(--text-muted);
    }
    .timeline-range {
      width: 100%;
      accent-color: var(--accent);
      cursor: pointer;
    }
    .timeline-current {
      font-size: 13px;
      font-weight: 500;
      color: var(--gold);
    }

    /* 右侧详情抽屉 */
    #sidebar-drawer {
      width: 380px;
      height: 100vh;
      background: var(--panel-bg);
      border-left: 1px solid var(--border);
      padding: 24px;
      overflow-y: auto;
      z-index: 20;
      display: flex;
      flex-direction: column;
      gap: 16px;
      box-shadow: -8px 0 32px rgba(0,0,0,0.5);
      transition: transform 0.3s ease;
    }
    .drawer-title {
      font-size: 20px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .badge-toponym { background: rgba(56, 189, 248, 0.2); color: var(--accent); }
    .badge-feature { background: rgba(74, 222, 128, 0.2); color: var(--green); }
    .badge-unit { background: rgba(192, 132, 252, 0.2); color: var(--purple); }
    .badge-attestation { background: rgba(251, 191, 36, 0.2); color: var(--gold); }
    .badge-event { background: rgba(248, 113, 113, 0.2); color: var(--red); }
    .badge-disproven { background: rgba(239, 68, 68, 0.3); color: #fca5a5; border: 1px solid #ef4444; }

    .drawer-section {
      background: #141c2b;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      font-size: 13px;
      line-height: 1.6;
    }
    .section-label {
      font-size: 11px;
      color: var(--text-muted);
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .quote-box {
      border-left: 3px solid var(--gold);
      padding-left: 10px;
      font-style: italic;
      color: #cbd5e1;
      margin-top: 6px;
    }

    /* 图例卡片 */
    .legend-card {
      position: absolute;
      bottom: 24px;
      left: 24px;
      background: var(--panel-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      z-index: 10;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-muted);
    }
    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
  </style>
</head>
<body>
  <div id="main-container">
    <div class="header-bar">
      <div class="header-title">🏛 海淀历史地名知识图谱 (HHTO)</div>
      <input type="text" class="search-input" id="search-box" placeholder="搜索地名 (如 六郎庄)...">
      <div style="font-size:12px; color:var(--text-muted);" id="stats-counter">统计加载中...</div>
    </div>

    <svg id="graph-svg"></svg>

    <div class="legend-card">
      <div class="legend-item"><div class="legend-dot" style="background:#38bdf8;"></div>地名称号实体 (Toponym)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#4ade80;"></div>物理地物环境 (PhysicalFeature)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#c084fc;"></div>建制制度单元 (AdministrativeUnit)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#fbbf24;"></div>史料书证用例 (Attestation)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#f87171;"></div>地名演变事件 (EvolutionEvent)</div>
    </div>

    <div class="timeline-slider-card">
      <div class="timeline-current" id="timeline-label">当前地层：全量历史时空 (先秦 — 当代)</div>
      <input type="range" class="timeline-range" id="time-slider" min="0" max="8" value="8" step="1">
      <div class="timeline-labels">
        <span>先秦</span>
        <span>唐</span>
        <span>辽金</span>
        <span>元</span>
        <span>明</span>
        <span>清初</span>
        <span>清盛</span>
        <span>民国</span>
        <span>当代</span>
      </div>
    </div>
  </div>

  <div id="sidebar-drawer">
    <div class="drawer-title">
      <span id="detail-name">点击节点检视详情</span>
      <span class="badge" id="detail-badge">HHTO</span>
    </div>
    <div class="drawer-section">
      <div class="section-label">实体类别与定义</div>
      <div id="detail-type" style="color:var(--accent);">请在左侧力导向图中选择任意节点</div>
    </div>
    <div class="drawer-section" id="detail-quote-section" style="display:none;">
      <div class="section-label">史料书证原始引文</div>
      <div class="quote-box" id="detail-quote"></div>
      <div style="font-size:11px; color:var(--text-muted); margin-top:6px;" id="detail-source"></div>
    </div>
    <div class="drawer-section">
      <div class="section-label">考据与时空背景</div>
      <div id="detail-desc" style="color:#cbd5e1;">知识图谱包含实体、属性、书证与演变因果链。</div>
    </div>
    <div class="drawer-section" id="detail-evidence-section" style="display:none;">
      <div class="section-label">认识论确证状态与证据分层</div>
      <div id="detail-level" style="font-weight:600; color:var(--gold);"></div>
    </div>
  </div>

  <script>
    const graphData = GRAPH_DATA_PLACEHOLDER;

    const ERA_MILESTONES = [
      { name: "先秦 / 汉代 (蓟城原野)", maxYear: -200 },
      { name: "唐代 (羁縻带州 705)", maxYear: 900 },
      { name: "辽金时期 (大觉寺/温泉 1150)", maxYear: 1234 },
      { name: "元代 (王恽海店/郭守敬 1260-1292)", maxYear: 1367 },
      { name: "明代 (卫所军屯/万寿寺 1368-1643)", maxYear: 1643 },
      { name: "清代前期 (畅春园/八旗营 1644-1735)", maxYear: 1735 },
      { name: "清代鼎盛 (大有庄/苏州街 1750-1860)", maxYear: 1860 },
      { name: "清末民初 (京西图/清华 1861-1948)", maxYear: 1948 },
      { name: "现代与当代 (科学城/高新区 1949-至今)", maxYear: 2026 }
    ];

    document.getElementById("stats-counter").innerText =
      `实体数: ${graphData.nodes.length} | 关联边: ${graphData.links.length}`;

    const width = window.innerWidth - 380;
    const height = window.innerHeight;

    const svg = d3.select("#graph-svg")
      .attr("viewBox", [0, 0, width, height]);

    const gContainer = svg.append("g");

    // 缩放
    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on("zoom", (e) => gContainer.attr("transform", e.transform));
    svg.call(zoom);

    // 颜色比例尺
    const colorMap = {
      Toponym: "#38bdf8",
      PhysicalFeature: "#4ade80",
      AdministrativeUnit: "#c084fc",
      PlaceAttestation: "#fbbf24",
      EvolutionEvent: "#f87171"
    };

    // 力导向仿真
    const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(d => {
        if (d.type === "evolvedFrom") return 70;
        if (d.type === "attestedIn") return 50;
        return 90;
      }))
      .force("charge", d3.forceManyBody().strength(-220))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(22));

    // 箭头定义
    svg.append("defs").selectAll("marker")
      .data(["evolvedFrom", "namedAs", "locatedAt", "attestedIn", "eventTarget"])
      .join("marker")
      .attr("id", d => `arrow-${d}`)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 18)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("fill", d => d === "evolvedFrom" ? "#c084fc" : "#64748b")
      .attr("d", "M0,-5L10,0L0,5");

    // 边
    const link = gContainer.append("g")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(graphData.links)
      .join("line")
      .attr("stroke", d => d.type === "evolvedFrom" ? "#c084fc" : (d.type === "attestedIn" ? "#fbbf24" : "#475569"))
      .attr("stroke-width", d => d.type === "evolvedFrom" ? 2.5 : 1.2)
      .attr("stroke-dasharray", d => d.type === "attestedIn" ? "3,3" : "none")
      .attr("marker-end", d => `url(#arrow-${d.type})`);

    // 节点
    const node = gContainer.append("g")
      .selectAll("g")
      .data(graphData.nodes)
      .join("g")
      .call(d3.drag()
        .on("start", (e, d) => {
          if (!e.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end", (e, d) => {
          if (!e.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        }));

    node.append("circle")
      .attr("r", d => d.group === "Toponym" ? 10 : (d.group === "PlaceAttestation" ? 6 : 8))
      .attr("fill", d => {
        if (d.epistemic_status === "DISPROVEN") return "#ef4444";
        return colorMap[d.group] || "#94a3b8";
      })
      .attr("stroke", "#0f172a")
      .attr("stroke-width", 2);

    node.append("text")
      .text(d => d.label)
      .attr("x", 12)
      .attr("y", 4)
      .attr("fill", "#cbd5e1")
      .attr("font-size", "11px")
      .style("pointer-events", "none");

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // 节点点击事件
    node.on("click", (e, d) => {
      document.getElementById("detail-name").innerText = d.label;
      const badge = document.getElementById("detail-badge");
      badge.className = `badge badge-${d.group.toLowerCase()}`;
      if (d.epistemic_status === "DISPROVEN") badge.className = "badge badge-disproven";
      badge.innerText = d.group;

      document.getElementById("detail-type").innerText = `${d.group} (${d.category || d.pinyin || ''})`;

      const quoteSec = document.getElementById("detail-quote-section");
      if (d.quote) {
        quoteSec.style.display = "block";
        document.getElementById("detail-quote").innerText = `“${d.quote}”`;
        document.getElementById("detail-source").innerText = `出处: ${d.source_title} (${d.dynasty || ''})`;
      } else {
        quoteSec.style.display = "none";
      }

      document.getElementById("detail-desc").innerText = d.description || d.notes || "实体关联已建立";

      const evSec = document.getElementById("detail-evidence-section");
      if (d.evidence_level) {
        evSec.style.display = "block";
        document.getElementById("detail-level").innerText =
          `${d.evidence_level} [${d.epistemic_status}]`;
      } else {
        evSec.style.display = "none";
      }

      // 高亮邻接节点
      node.selectAll("circle").attr("opacity", n => (n === d ? 1 : 0.3));
      link.attr("opacity", l => (l.source.id === d.id || l.target.id === d.id ? 1 : 0.1));
    });

    // 背景点击取消高亮
    svg.on("click", (e) => {
      if (e.target.tagName === "svg") {
        node.selectAll("circle").attr("opacity", 1);
        link.attr("opacity", 0.6);
      }
    });

    // 搜索过滤
    document.getElementById("search-box").addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) {
        node.selectAll("circle").attr("opacity", 1);
        link.attr("opacity", 0.6);
        return;
      }
      node.selectAll("circle").attr("opacity", d => d.label.toLowerCase().includes(q) ? 1 : 0.1);
      link.attr("opacity", 0.1);
    });

    // 时间轴过滤
    const slider = document.getElementById("time-slider");
    slider.addEventListener("input", (e) => {
      const idx = parseInt(e.target.value);
      const milestone = ERA_MILESTONES[idx];
      document.getElementById("timeline-label").innerText = `当前地层：${milestone.name}`;

      node.style("display", d => d.year <= milestone.maxYear ? "block" : "none");
      link.style("display", l => {
        const sVisible = l.source.year <= milestone.maxYear;
        const tVisible = l.target.year <= milestone.maxYear;
        return sVisible && tVisible ? "block" : "none";
      });
    });
  </script>
</body>
</html>
"""


def main():
    entities_path = pathlib.Path("haidian_kg/data/entities.json")
    if not entities_path.exists():
        from haidian_kg.extractor import HaidianCorpusExtractor
        HaidianCorpusExtractor.load_or_extract()

    with open(entities_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph_payload = generate_graph_data(data)

    html_content = HTML_TEMPLATE.replace("GRAPH_DATA_PLACEHOLDER", json.dumps(graph_payload, ensure_ascii=False))

    out_file = pathlib.Path("haidian_kg/visualizer/index.html")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated visualizer HTML at {out_file} (size: {len(html_content)} bytes)")
    print(f"Nodes: {len(graph_payload['nodes'])}, Links: {len(graph_payload['links'])}")


if __name__ == "__main__":
    main()
