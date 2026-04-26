import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import { forceCenter, forceCollide } from "d3-force";
import { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { BIRTH_TOTAL_MS, birthVisual } from "../graphBirth";
import { QUERY_PULSE_TOTAL_MS, queryPulseScale } from "../graphQueryPulse";
import type { GraphData, GraphLink, GraphNode } from "../types";
import { linkKey, neighborSets, nodeRadius } from "../graphUtils";

type Props = {
  data: GraphData;
  width: number;
  height: number;
  selectedId: string | null;
  onSelectNode: (node: GraphNode | null) => void;
  queryUsedIds: Set<string>;
  queryUpdatedId: string | null;
  reheatToken: number;
  birthEpoch: number;
  birthNodeIds: readonly string[];
  queryPulseEpoch: number;
  queryPulseIds: readonly string[];
  focusCameraRequest: { nodeId: string; nonce: number } | null;
};

function Inner({
  data,
  width,
  height,
  selectedId,
  onSelectNode,
  queryUsedIds,
  queryUpdatedId,
  reheatToken,
  birthEpoch,
  birthNodeIds,
  queryPulseEpoch,
  queryPulseIds,
  focusCameraRequest,
}: Props) {
  const fgRef = useRef<ForceGraphMethods<GraphNode, GraphLink> | undefined>(undefined);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const fittedRef = useRef(false);
  const birthStartsRef = useRef<Map<string, number>>(new Map());
  const pulseStartsRef = useRef<Map<string, number>>(new Map());
  const [, setBirthActive] = useState(false);
  const [, setPulseActive] = useState(false);

  const dimmingFocusId = queryUsedIds.size || queryUpdatedId ? null : selectedId;
  const { nodes: focusNeighbors, linkKeys } = useMemo(() => neighborSets(data, dimmingFocusId), [data, dimmingFocusId]);
  const { nodes: hoverNeighbors } = useMemo(() => neighborSets(data, hoverId), [data, hoverId]);
  const maxDegree = useMemo(() => Math.max(1, ...data.nodes.map((n) => n.__deg ?? 0)), [data.nodes]);

  useEffect(() => {
    fittedRef.current = false;
  }, [data.nodes.length, data.links.length]);

  useLayoutEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    const charge = fg.d3Force("charge") as { strength?: (v: number) => void } | undefined;
    charge?.strength?.(-120);
    const link = fg.d3Force("link") as { distance?: (v: number) => void } | undefined;
    link?.distance?.(90);
    fg.d3Force("center", forceCenter(0, 0).strength(0.06));
    fg.d3Force(
      "collide",
      forceCollide<GraphNode>()
        .radius((n) => {
          const degree = n.__deg ?? 0;
          const prominence = Math.pow(degree / maxDegree, 0.8);
          const prominenceBoost = 1 + prominence * 0.28;
          return nodeRadius(n, 3.2) * prominenceBoost + 20;
        })
        .strength(0.72),
    );
  }, [data.nodes.length, data.links.length, width, height, maxDegree]);

  useEffect(() => {
    fgRef.current?.d3ReheatSimulation();
  }, [reheatToken]);

  useEffect(() => {
    if (!birthEpoch || !birthNodeIds.length) return;
    const now = performance.now();
    birthStartsRef.current.clear();
    for (const id of birthNodeIds) birthStartsRef.current.set(id, now);
    setBirthActive(true);
    const t = window.setTimeout(() => {
      birthStartsRef.current.clear();
      setBirthActive(false);
    }, BIRTH_TOTAL_MS + 100);
    return () => window.clearTimeout(t);
  }, [birthEpoch, birthNodeIds]);

  useEffect(() => {
    if (!queryPulseEpoch || !queryPulseIds.length) return;
    const now = performance.now();
    pulseStartsRef.current.clear();
    for (const id of queryPulseIds) pulseStartsRef.current.set(id, now);
    setPulseActive(true);
    const t = window.setTimeout(() => {
      pulseStartsRef.current.clear();
      setPulseActive(false);
    }, QUERY_PULSE_TOTAL_MS + 100);
    return () => window.clearTimeout(t);
  }, [queryPulseEpoch, queryPulseIds]);

  useEffect(() => {
    if (!focusCameraRequest) return;
    const node = data.nodes.find((n) => n.id === focusCameraRequest.nodeId);
    if (!node || node.x === undefined || node.y === undefined) return;
    fgRef.current?.centerAt(node.x, node.y, 950);
    fgRef.current?.zoom(1.58, 950);
  }, [focusCameraRequest, data.nodes]);

  const nodeColor = useCallback(
    (n: GraphNode) => {
      if (!dimmingFocusId || focusNeighbors.has(n.id)) return n.color ?? "#84ccff";
      return "rgba(100,110,140,0.38)";
    },
    [dimmingFocusId, focusNeighbors],
  );

  const linkColor = useCallback(
    (l: GraphLink) => {
      const s = typeof l.source === "string" ? l.source : l.source.id;
      const t = typeof l.target === "string" ? l.target : l.target.id;
      if (!dimmingFocusId) return "rgba(145,160,190,0.28)";
      return linkKeys.has(linkKey(s, t)) ? "rgba(186,198,255,0.58)" : "rgba(120,135,160,0.14)";
    },
    [dimmingFocusId, linkKeys],
  );

  const nodeVal = useCallback((n: GraphNode) => {
    let v = nodeRadius(n, 3.2);
    const degree = n.__deg ?? 0;
    const prominence = Math.pow(degree / maxDegree, 0.8);
    v *= 1 + prominence * 0.28;
    const t = performance.now() * 0.001;
    const seed = Array.from(n.id).reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    // Subtle perpetual breathing to make nodes feel alive.
    v *= 1 + Math.sin(t * 1.2 + seed * 0.03) * 0.035;
    const b = birthStartsRef.current.get(n.id);
    if (b !== undefined) v *= birthVisual(performance.now() - b).scale;
    const p = pulseStartsRef.current.get(n.id);
    if (p !== undefined) v *= queryPulseScale(performance.now() - p);
    if (selectedId === n.id) v *= 1.12;
    if (hoverId === n.id) v *= 1.08;
    return v;
  }, [selectedId, hoverId, maxDegree]);

  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    if (node.x === undefined || node.y === undefined) return;
    const t = performance.now() * 0.001;
    const seed = Array.from(node.id).reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    const isHoverCore = hoverId === node.id;
    const isHoverNeighbor = !!hoverId && hoverNeighbors.has(node.id);
    const jiggleAmp = isHoverCore ? 4.8 : isHoverNeighbor ? 3.4 : 1.9;
    const fx = Math.cos(t * 0.65 + seed * 0.017) * jiggleAmp * 0.7;
    const fy = Math.sin(t * 0.8 + seed * 0.021) * jiggleAmp;
    const radius = nodeVal(node);
    const x = node.x + fx;
    const y = node.y + fy;
    const selected = selectedId === node.id;
    const hovered = hoverId === node.id;
    const intensity = selected ? 0.44 : hovered ? 0.3 : 0.2;

    // Outer atmospheric halo.
    ctx.save();
    ctx.globalAlpha = intensity;
    ctx.fillStyle = "rgba(76, 214, 255, 0.45)";
    ctx.beginPath();
    ctx.arc(x, y, radius + 4.6, 0, 2 * Math.PI);
    ctx.fill();
    ctx.restore();

    // Inner halo ring.
    ctx.save();
    ctx.strokeStyle = selected ? "rgba(224, 247, 255, 0.82)" : "rgba(162, 226, 246, 0.58)";
    ctx.lineWidth = (selected ? 1.35 : 1) / globalScale;
    ctx.beginPath();
    ctx.arc(x, y, radius + 1.8, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.restore();

    if (selectedId === node.id || hoverId === node.id) {
      ctx.save();
      ctx.strokeStyle = "rgba(236, 241, 255, 0.65)";
      ctx.lineWidth = 1.1 / globalScale;
      ctx.beginPath();
      ctx.arc(x, y, radius + 2.1, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.restore();
    }

    const isFocused = selected || hovered;
    const shouldRenderLabel = isFocused || globalScale >= 1.15 || (node.__deg ?? 0) >= Math.max(2, Math.round(maxDegree * 0.45));
    if (!shouldRenderLabel) return;
    const label = (node.title?.trim() || node.id).slice(0, 42);
    const fontSize = (isFocused ? 11.8 : 9.8) / Math.max(0.85, globalScale * 0.95);
    const textY = y + radius + (isFocused ? 11.5 : 10.2) / globalScale;
    ctx.save();
    ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const textWidth = ctx.measureText(label).width;
    const padX = 5.5 / globalScale;
    const padY = 2.8 / globalScale;
    const bgHeight = fontSize + padY * 2;
    const bgWidth = textWidth + padX * 2;
    ctx.fillStyle = isFocused ? "rgba(6, 14, 28, 0.82)" : "rgba(7, 14, 27, 0.62)";
    ctx.strokeStyle = isFocused ? "rgba(124, 230, 255, 0.52)" : "rgba(113, 173, 187, 0.35)";
    ctx.lineWidth = 0.9 / globalScale;
    ctx.beginPath();
    ctx.roundRect(x - bgWidth / 2, textY, bgWidth, bgHeight, 5 / globalScale);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = isFocused ? "rgba(229, 249, 255, 0.98)" : "rgba(203, 233, 243, 0.92)";
    ctx.fillText(label, x, textY + padY);
    ctx.restore();
  }, [hoverId, hoverNeighbors, maxDegree, nodeVal, selectedId]);

  return (
    <div className="graph-wrap graph-wrap--animated">
      <ForceGraph2D
        ref={fgRef}
        width={width}
        height={height}
        graphData={data}
        nodeId="id"
        backgroundColor="rgba(0,0,0,0)"
        nodeColor={nodeColor}
        nodeVal={nodeVal}
        linkColor={linkColor}
        linkWidth={0.55}
        linkDirectionalParticles={0.55}
        linkDirectionalParticleWidth={0.8}
        nodeCanvasObjectMode={() => "after"}
        nodeCanvasObject={nodeCanvasObject}
        autoPauseRedraw={false}
        cooldownTicks={320}
        cooldownTime={4500}
        d3AlphaMin={0.01}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.4}
        onNodeHover={(node) => setHoverId(node?.id ?? null)}
        onNodeClick={(node) => onSelectNode(node as GraphNode)}
        onBackgroundClick={() => onSelectNode(null)}
        onEngineStop={() => {
          if (!fittedRef.current && data.nodes.length > 0) {
            fittedRef.current = true;
            fgRef.current?.zoomToFit(900, 72);
          }
        }}
      />
    </div>
  );
}

export const KnowledgeGraph = memo(Inner);
