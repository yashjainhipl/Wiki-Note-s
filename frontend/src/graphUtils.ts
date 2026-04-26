import type { GraphData, GraphLink, GraphNode } from "./types";

export function groupColor(group?: string, bright = false): string {
  const g = (group || "default").toLowerCase();
  let hash = 0;
  for (let i = 0; i < g.length; i += 1) hash = (hash << 5) - hash + g.charCodeAt(i);
  const hue = Math.abs(hash) % 360;
  const sat = bright ? 74 : 62;
  const light = bright ? 66 : 54;
  return `hsl(${hue} ${sat}% ${light}%)`;
}

export function linkKey(a: string, b: string): string {
  return a < b ? `${a}::${b}` : `${b}::${a}`;
}

export function nodeRadius(node: GraphNode, base = 3.2): number {
  const degree = node.__deg ?? 0;
  return base + Math.sqrt(degree + 1) * 0.75;
}

export function prepareGraphData(raw: GraphData, opts?: { snapshot?: Map<string, { x: number; y: number }>; maxLinksPerNode?: number }): GraphData {
  const maxLinksPerNode = opts?.maxLinksPerNode ?? 16;
  const nodes = raw.nodes.map((n) => ({ ...n }));
  const idSet = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const degree = new Map<string, number>();
  const perNodeLinkCount = new Map<string, number>();
  const links: GraphLink[] = [];

  for (const link of raw.links) {
    const source = typeof link.source === "string" ? link.source : link.source.id;
    const target = typeof link.target === "string" ? link.target : link.target.id;
    if (!idSet.has(source) || !idSet.has(target) || source === target) continue;
    const key = linkKey(source, target);
    if (seen.has(key)) continue;
    const sCount = perNodeLinkCount.get(source) ?? 0;
    const tCount = perNodeLinkCount.get(target) ?? 0;
    if (sCount >= maxLinksPerNode || tCount >= maxLinksPerNode) continue;
    seen.add(key);
    perNodeLinkCount.set(source, sCount + 1);
    perNodeLinkCount.set(target, tCount + 1);
    degree.set(source, (degree.get(source) ?? 0) + 1);
    degree.set(target, (degree.get(target) ?? 0) + 1);
    links.push({ source, target });
  }

  const snapshot = opts?.snapshot;
  for (const node of nodes) {
    node.__deg = degree.get(node.id) ?? 0;
    if (!node.color) node.color = groupColor(node.group);
    const snap = snapshot?.get(node.id);
    if (snap) {
      node.x = snap.x;
      node.y = snap.y;
    }
  }

  return { nodes, links };
}

export function neighborSets(data: GraphData, nodeId: string | null): { nodes: Set<string>; linkKeys: Set<string> } {
  const n = new Set<string>();
  const l = new Set<string>();
  if (!nodeId) return { nodes: n, linkKeys: l };
  n.add(nodeId);
  for (const link of data.links) {
    const s = typeof link.source === "string" ? link.source : link.source.id;
    const t = typeof link.target === "string" ? link.target : link.target.id;
    if (s === nodeId || t === nodeId) {
      n.add(s);
      n.add(t);
      l.add(linkKey(s, t));
    }
  }
  return { nodes: n, linkKeys: l };
}
