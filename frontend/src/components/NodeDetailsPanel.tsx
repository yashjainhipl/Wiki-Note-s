import type { GraphData, GraphNode } from "../types";

type Props = {
  graphData: GraphData;
  node: GraphNode | null;
  onClose: () => void;
  onNavigateToNode: (node: GraphNode) => void;
};

export function NodeDetailsPanel({ graphData, node, onClose, onNavigateToNode }: Props) {
  return (
    <aside className="details-panel">
      <div className="details-panel__header">
        <h3 className="details-panel__title">Active Focus</h3>
        <button type="button" className="details-panel__close" onClick={onClose} aria-label="Close node details">
          ×
        </button>
      </div>
      <div className="details-panel__body">
        {!node ? (
          <p className="details-panel__empty">Select a node to inspect temporal metadata and related concepts.</p>
        ) : (
          <article className="node-card">
            <h2 className="node-card__title">{node.title ?? node.id}</h2>
            <p className="node-card__summary">{node.summary ?? "No summary available."}</p>

            <section className="node-card__section">
              <h4>Key points</h4>
              <ul>
                {(node.key_points ?? []).slice(0, 6).map((kp) => (
                  <li key={kp}>{kp}</li>
                ))}
              </ul>
            </section>

            <section className="node-card__section">
              <h4>Tags</h4>
              <div className="node-card__tags">
                {(node.tags ?? []).map((tag) => (
                  <span className="tag-pill" key={tag}>
                    {tag}
                  </span>
                ))}
              </div>
            </section>

            <section className="node-card__section">
              <h4>Related</h4>
              <ul className="node-card__related">
                {(node.related ?? []).map((rid) => {
                  const next = graphData.nodes.find((n) => n.id === rid || n.title === rid);
                  if (!next) return null;
                  return (
                    <li key={next.id}>
                      <button className="node-card__related-btn" onClick={() => onNavigateToNode(next)}>
                        {next.title ?? next.id}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          </article>
        )}
      </div>
    </aside>
  );
}
