import { useMemo, useState } from "react";

import type { GraphNode } from "../types";

type Props = {
  nodes: GraphNode[];
  onNavigateToNode: (node: GraphNode) => void;
};

export function GraphSearchBar({ nodes, onNavigateToNode }: Props) {
  const [q, setQ] = useState("");
  const picks = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return [];
    return nodes
      .filter((n) => (n.title ?? n.id).toLowerCase().includes(term))
      .slice(0, 8);
  }, [nodes, q]);

  return (
    <div className="graph-search">
      <input
        className="graph-search__input"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search nodes..."
        aria-label="Search graph nodes"
      />
      {picks.length ? (
        <ul className="graph-search__results" role="listbox">
          {picks.map((n) => (
            <li key={n.id}>
              <button
                type="button"
                className="graph-search__pick"
                onClick={() => {
                  onNavigateToNode(n);
                  setQ("");
                }}
              >
                <span className="graph-search__pick-title">{n.title ?? n.id}</span>
                <span className="graph-search__pick-sub">{n.summary ?? "No summary"}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
