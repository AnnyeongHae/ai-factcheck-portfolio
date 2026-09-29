/**
 * ==============================================================================
 * D3.js Force-Directed Citation Network Graph Component
 * ==============================================================================
 */

import { graphData, currentGraphType } from '../core/store.js';

let simulationRef = null;
let nodeSelection = null;
let linkSelection = null;

export function initCitationGraph() {
  if (typeof d3 === 'undefined') {
    console.warn('[CitationGraph] d3 library is not loaded');
    return;
  }
  const svg = d3.select("#techGraphSvg");
  const container = document.getElementById("graphView");
  if (!container || svg.empty()) return;

  const width = container.clientWidth || 1100;
  const height = 640;
  svg.selectAll("*").remove(); // Clean previous render if any
  svg.attr("viewBox", [-width / 2, -height / 2, width, height]);

  const g = svg.append("g");
  svg.call(d3.zoom().scaleExtent([0.2, 4.0]).on("zoom", (e) => g.attr("transform", e.transform)));

  const rawNodes = (window.graphData?.nodes?.length ? window.graphData.nodes : (graphData?.nodes || []));
  const rawLinks = (window.graphData?.links?.length ? window.graphData.links : (graphData?.links || []));
  // Create shallow clones so D3 mutation doesn't mutate immutable frozen objects
  const nodes = rawNodes.map(d => ({ ...d }));
  const links = rawLinks.map(d => ({ ...d }));

  if (nodes.length === 0) {
    console.info('[CitationGraph] No nodes found for citation graph.');
    return;
  }

  simulationRef = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-380))
    .force("center", d3.forceCenter(0, 0))
    .force("collision", d3.forceCollide().radius(d => (d.val || 15) + 14));

  linkSelection = g.append("g")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke", "rgba(0, 0, 0, 0.12)")
    .attr("stroke-width", 1.5);

  const nodeGroup = g.append("g")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended));

  function getNodeColor(d) {
    if (d.group === "language") return "#b45309";
    if (d.group === "technology") return "#047857";
    if (d.group === "organization") return "#4338ca";
    if (d.group === "person") return "#be185d";
    if (d.group === "paper") return "#c2410c";
    return "#111827";
  }

  nodeSelection = nodeGroup.append("circle")
    .attr("r", d => d.val || 15)
    .attr("fill", d => getNodeColor(d))
    .attr("stroke", "#ffffff")
    .attr("stroke-width", 2.5);

  nodeGroup.append("text")
    .text(d => d.name || d.id)
    .attr("x", 0)
    .attr("y", d => (d.val || 15) + 14)
    .attr("text-anchor", "middle")
    .attr("fill", "#111827")
    .attr("font-size", "11px")
    .attr("font-family", "Pretendard, Noto Sans SC, sans-serif")
    .attr("font-weight", "600");

  simulationRef.on("tick", () => {
    linkSelection
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    nodeGroup.attr("transform", d => `translate(${d.x},${d.y})`);
  });

  function dragstarted(event, d) {
    if (!event.active) simulationRef.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
  }
  function dragged(event, d) {
    d.fx = event.x; d.fy = event.y;
  }
  function dragended(event, d) {
    if (!event.active) simulationRef.alphaTarget(0);
    d.fx = null; d.fy = null;
  }
}

export function filterGraphGroup(group) {
  window.currentGraphType = group;
  document.querySelectorAll('.graph-group-btn').forEach(btn => {
    if (btn.dataset.group === group) {
      btn.classList.add('active', 'bg-ink-primary', 'text-white');
    } else {
      btn.classList.remove('active', 'bg-ink-primary', 'text-white');
    }
  });

  const nodes = (graphData && graphData.nodes) || (window.graphData && window.graphData.nodes) || [];

  if (nodeSelection) {
    nodeSelection.attr("opacity", d => (group === 'ALL' || d.group === group) ? 0.95 : 0.08);
  }
  if (linkSelection) {
    linkSelection.attr("opacity", l => {
      if (group === 'ALL') return 0.4;
      const s = typeof l.source === 'object' ? l.source : nodes.find(n => n.id === l.source);
      const t = typeof l.target === 'object' ? l.target : nodes.find(n => n.id === l.target);
      return (s && s.group === group) || (t && t.group === group) ? 0.8 : 0.04;
    });
  }
}
