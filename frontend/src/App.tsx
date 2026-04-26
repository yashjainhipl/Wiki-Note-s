import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type MouseEvent } from "react";

import "./App.css";
import { api } from "./api";
import { GraphSearchBar } from "./components/GraphSearchBar";
import { IngestModal } from "./components/IngestModal";
import { KnowledgeGraph } from "./components/KnowledgeGraph";
import { NodeDetailsPanel } from "./components/NodeDetailsPanel";
import { QueryBar } from "./components/QueryBar";
import { Sidebar } from "./components/Sidebar";
import { prepareGraphData } from "./graphUtils";
import type { GraphData, GraphNode, HealthLintResponse, QueryResponse, RefactorResponse, StatsResponse } from "./types";

const emptyGraph = (): GraphData => ({ nodes: [], links: [] });

export default function App() {
  const [graphData, setGraphData] = useState<GraphData>(() => prepareGraphData(emptyGraph()));
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [graphLoading, setGraphLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [graphError, setGraphError] = useState<string | null>(null);

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [detailsPanelOpen, setDetailsPanelOpen] = useState(true);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryAnswerEpoch, setQueryAnswerEpoch] = useState(0);
  const [queryPulseEpoch, setQueryPulseEpoch] = useState(0);
  const [queryPulseIds, setQueryPulseIds] = useState<readonly string[]>([]);
  const [reheatToken, setReheatToken] = useState(0);
  const [ingestOpen, setIngestOpen] = useState(false);
  const [ingestBusy, setIngestBusy] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [birthEpoch, setBirthEpoch] = useState(0);
  const [birthNodeIds, setBirthNodeIds] = useState<string[]>([]);
  const [refactorLoading, setRefactorLoading] = useState(false);
  const [refactorError, setRefactorError] = useState<string | null>(null);
  const [refactorResult, setRefactorResult] = useState<RefactorResponse | null>(null);
  const [healthLintLoading, setHealthLintLoading] = useState(false);
  const [healthLintError, setHealthLintError] = useState<string | null>(null);
  const [healthLintResult, setHealthLintResult] = useState<HealthLintResponse | null>(null);
  const [queryHistory, setQueryHistory] = useState<string[]>([]);
  const [canvasInteractive, setCanvasInteractive] = useState(false);
  const [canvasGlow, setCanvasGlow] = useState({ x: 50, y: 40 });

  const graphAreaRef = useRef<HTMLDivElement>(null);
  const [graphSize, setGraphSize] = useState({ w: 800, h: 500 });
  const focusCameraNonceRef = useRef(0);
  const [focusCameraRequest, setFocusCameraRequest] = useState<{ nodeId: string; nonce: number } | null>(null);
  const layoutSnapshotRef = useRef<Map<string, { x: number; y: number }>>(new Map());

  const queryUsedIds = useMemo(() => new Set(queryResult?.used_nodes ?? []), [queryResult?.used_nodes]);
  const queryUpdatedId = queryResult?.updated_node ?? null;

  const captureLayout = useCallback(() => {
    for (const n of graphData.nodes) {
      if (typeof n.x === "number" && typeof n.y === "number") {
        layoutSnapshotRef.current.set(n.id, { x: n.x, y: n.y });
      }
    }
  }, [graphData.nodes]);

  const refreshGraph = useCallback(async (preserve = false) => {
    setGraphLoading(true);
    setGraphError(null);
    try {
      const g = await api.graph();
      const prepared = prepareGraphData(g, {
        snapshot: preserve ? layoutSnapshotRef.current : undefined,
        maxLinksPerNode: 14,
      });
      setGraphData(prepared);
      setReheatToken((x) => x + 1);
    } catch (err) {
      setGraphError((err as Error).message);
    } finally {
      setGraphLoading(false);
    }
  }, []);

  const refreshStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      setStats(await api.stats());
    } catch {
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshGraph(false);
    void refreshStats();
  }, [refreshGraph, refreshStats]);

  useEffect(() => {
    void (async () => {
      try {
        const latest = await api.getLatestHealthLint();
        if (latest?.report) setHealthLintResult(latest);
      } catch {
        // Ignore optional health-lint fetch failures at startup.
      }
    })();
  }, []);

  useEffect(() => {
    const el = graphAreaRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setGraphSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setGraphSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  const bumpFocus = useCallback((nodeId: string) => {
    focusCameraNonceRef.current += 1;
    setFocusCameraRequest({ nodeId, nonce: focusCameraNonceRef.current });
  }, []);

  const navigateToNode = useCallback((node: GraphNode) => {
    setDetailsPanelOpen(true);
    setSelectedNode(node);
    bumpFocus(node.id);
  }, [bumpFocus]);

  const handleSelectNode = useCallback((node: GraphNode | null) => {
    if (node) setDetailsPanelOpen(true);
    setSelectedNode(node);
  }, []);

  const handleQuery = useCallback(async (text: string) => {
    setQueryError(null);
    setQueryLoading(true);
    captureLayout();
    try {
      const body = await api.query(text);
      setQueryResult(body);
      setQueryAnswerEpoch((x) => x + 1);
      setQueryHistory((h) => [text, ...h.filter((x) => x !== text)].slice(0, 5));
      await refreshGraph(true);
      await refreshStats();
      const pulseIds = [...new Set([...body.used_nodes, ...(body.updated_node ? [body.updated_node] : [])])];
      setQueryPulseIds(pulseIds);
      setQueryPulseEpoch((x) => x + 1);
      if (body.updated_node) {
        setBirthNodeIds([body.updated_node]);
        setBirthEpoch((x) => x + 1);
      }
    } catch (err) {
      setQueryError((err as Error).message);
      throw err;
    } finally {
      setQueryLoading(false);
    }
  }, [captureLayout, refreshGraph, refreshStats]);

  const handleRefactor = useCallback(async () => {
    setRefactorLoading(true);
    setRefactorError(null);
    try {
      const out = await api.refactor();
      setRefactorResult(out);
      captureLayout();
      await refreshGraph(true);
      await refreshStats();
    } catch (err) {
      setRefactorError((err as Error).message);
    } finally {
      setRefactorLoading(false);
    }
  }, [captureLayout, refreshGraph, refreshStats]);

  const handleHealthLint = useCallback(async () => {
    setHealthLintLoading(true);
    setHealthLintError(null);
    try {
      const out = await api.runHealthLint();
      setHealthLintResult(out);
    } catch (err) {
      setHealthLintError((err as Error).message);
    } finally {
      setHealthLintLoading(false);
    }
  }, []);

  const handleIngestFiles = useCallback(async (files: File[], generate: boolean) => {
    setIngestError(null);
    setIngestBusy(true);
    setIngestStatus("Uploading source files...");
    try {
      const payload = await api.uploadBatch(files);
      if (generate && payload.successes.length) {
        setIngestStatus("Generating knowledge nodes...");
        const generated = await api.generateFromRaw(payload.successes.map((x) => x.raw_note));
        if (generated.errors.length) {
          throw new Error(generated.errors[0]);
        }
      }
      if (payload.errors.length) {
        throw new Error(payload.errors[0].error);
      }
      setIngestStatus("Syncing graph and stats...");
      captureLayout();
      await refreshGraph(true);
      await refreshStats();
      const before = new Set(graphData.nodes.map((n) => n.id));
      const next = (await api.graph()).nodes.map((n) => n.id).filter((id) => !before.has(id));
      if (next.length) {
        setBirthNodeIds(next);
        setBirthEpoch((x) => x + 1);
      }
      return `Ingested ${payload.successes.length} file(s).`;
    } catch (err) {
      const msg = (err as Error).message || "Ingest failed.";
      setIngestError(msg);
      throw err;
    } finally {
      setIngestBusy(false);
      setIngestStatus(null);
    }
  }, [captureLayout, graphData.nodes, refreshGraph, refreshStats]);

  const handleIngestText = useCallback(async (text: string, generate: boolean) => {
    setIngestError(null);
    setIngestBusy(true);
    setIngestStatus("Saving note...");
    try {
      const payload = await api.ingestText(text);
      if (generate) {
        setIngestStatus("Generating knowledge node...");
        const generated = await api.generateFromRaw([payload.raw_note]);
        if (generated.errors.length) {
          throw new Error(generated.errors[0]);
        }
      }
      setIngestStatus("Syncing graph and stats...");
      captureLayout();
      await refreshGraph(true);
      await refreshStats();
      return "Text ingested";
    } catch (err) {
      const msg = (err as Error).message || "Ingest failed.";
      setIngestError(msg);
      throw err;
    } finally {
      setIngestBusy(false);
      setIngestStatus(null);
    }
  }, [captureLayout, refreshGraph, refreshStats]);

  const resolveNodeByTitle = useCallback((title: string) => graphData.nodes.find((n) => n.title === title || n.id === title) ?? null, [graphData.nodes]);

  const showGraph = graphSize.w > 0 && graphSize.h > 0;
  const handleCanvasMove = useCallback((ev: MouseEvent<HTMLDivElement>) => {
    const rect = ev.currentTarget.getBoundingClientRect();
    const x = ((ev.clientX - rect.left) / Math.max(1, rect.width)) * 100;
    const y = ((ev.clientY - rect.top) / Math.max(1, rect.height)) * 100;
    setCanvasGlow({ x, y });
  }, []);
  const canvasStyle = useMemo(
    () =>
      ({
        "--canvas-glow-x": `${canvasGlow.x.toFixed(2)}%`,
        "--canvas-glow-y": `${canvasGlow.y.toFixed(2)}%`,
      }) as CSSProperties,
    [canvasGlow.x, canvasGlow.y],
  );

  return (
    <div className={`app${detailsPanelOpen ? "" : " app--details-closed"}`}>
      <Sidebar
        stats={stats}
        loading={statsLoading}
        onPickTitle={(title) => {
          const n = resolveNodeByTitle(title);
          if (n) navigateToNode(n);
        }}
        onAddNote={() => {
          setIngestError(null);
          setIngestOpen(true);
        }}
        onRefactor={() => void handleRefactor()}
        onHealthLint={() => void handleHealthLint()}
        refactorLoading={refactorLoading}
        refactorError={refactorError}
        refactorResult={refactorResult}
        healthLintLoading={healthLintLoading}
        healthLintError={healthLintError}
        healthLintResult={healthLintResult}
      />

      <main className="app__main">
        <header className="app__header">
          <div className="app__header-lead app__header-card">
            <h1 className="app__title">Wiki Notes</h1>
            <p className="app__subtitle">Connected knowledge workspace</p>
          </div>
          <section className="app__header-telemetry app__header-card" aria-label="Project telemetry">
            {statsLoading && !stats ? (
              <div className="skeleton skeleton--stats" />
            ) : stats ? (
              <div className="app__header-telemetry-row">
                <span className="app__header-telemetry-title">Project telemetry</span>
                <span className="app__header-metric"><strong>{stats.total_nodes}</strong> Nodes</span>
                <span className="app__header-metric"><strong>{stats.total_edges}</strong> Edges</span>
              </div>
            ) : (
              <p className="sidebar__muted">No stats yet.</p>
            )}
          </section>
          <div className="app__header-search">
            <GraphSearchBar nodes={graphData.nodes} onNavigateToNode={navigateToNode} />
          </div>
          <div className="app__header-status">{graphLoading ? <span className="badge badge--pulse">Syncing...</span> : null}</div>
        </header>

        <div
          className={`app__canvas${canvasInteractive ? " app__canvas--active" : ""}`}
          ref={graphAreaRef}
          style={canvasStyle}
          onMouseMove={handleCanvasMove}
          onMouseEnter={() => setCanvasInteractive(true)}
          onMouseLeave={() => setCanvasInteractive(false)}
        >
          {graphError ? <div className="app__error">{graphError}</div> : null}
          {!graphLoading && !graphData.nodes.length && !graphError ? (
            <div className="app__empty app__empty--brain">
              <p className="app__empty-message">Your second brain is empty. Add knowledge to begin.</p>
              <button type="button" className="app__empty-cta" onClick={() => setIngestOpen(true)}>
                Add Knowledge
              </button>
            </div>
          ) : null}
          {showGraph && graphData.nodes.length ? (
            <KnowledgeGraph
              data={graphData}
              width={graphSize.w}
              height={graphSize.h}
              selectedId={selectedNode?.id ?? null}
              onSelectNode={handleSelectNode}
              queryUsedIds={queryUsedIds}
              queryUpdatedId={queryUpdatedId}
              reheatToken={reheatToken}
              birthEpoch={birthEpoch}
              birthNodeIds={birthNodeIds}
              queryPulseEpoch={queryPulseEpoch}
              queryPulseIds={queryPulseIds}
              focusCameraRequest={focusCameraRequest}
            />
          ) : null}
        </div>

        <div className="app__bottom">
          <QueryBar
            answer={queryResult?.answer ?? null}
            loading={queryLoading}
            error={queryError}
            answerEpoch={queryAnswerEpoch}
            queryHistory={queryHistory}
            onReplayHistory={(q) => void handleQuery(q)}
            onSubmit={handleQuery}
            onDismissError={() => setQueryError(null)}
          />
        </div>
      </main>

      {detailsPanelOpen ? (
        <NodeDetailsPanel
          graphData={graphData}
          node={selectedNode}
          onClose={() => {
            setSelectedNode(null);
            setDetailsPanelOpen(false);
          }}
          onNavigateToNode={navigateToNode}
        />
      ) : null}

      <IngestModal
        open={ingestOpen}
        busy={ingestBusy}
        statusText={ingestStatus}
        error={ingestError}
        onClose={() => {
          if (ingestBusy) return;
          setIngestOpen(false);
          setIngestError(null);
        }}
        onSubmitFiles={handleIngestFiles}
        onSubmitText={handleIngestText}
      />
    </div>
  );
}
