export type WikiAction = "updated" | "created" | "skipped";

export type RecentNode = {
  title: string;
  filename: string;
  created_at: string;
  updated_at: string;
  tags: string[];
};

export type TopTag = {
  tag: string;
  count: number;
};

export type StatsResponse = {
  total_nodes: number;
  total_edges: number;
  recent_nodes: RecentNode[];
  top_tags: TopTag[];
};

export type GraphNode = {
  id: string;
  title?: string;
  summary?: string;
  tags?: string[];
  key_points?: string[];
  source_notes?: string[];
  related?: string[];
  group?: string;
  color?: string;
  x?: number;
  y?: number;
  __deg?: number;
};

export type GraphLink = {
  source: string | GraphNode;
  target: string | GraphNode;
};

export type GraphData = {
  nodes: GraphNode[];
  links: GraphLink[];
};

export type QueryResponse = {
  answer: string;
  used_nodes: string[];
  updated_node: string | null;
  confidence_score: number;
  wiki_action: WikiAction;
  wiki_file: string | null;
};

export type RefactorResponse = {
  merged_groups: string[][];
  pages_merged: number;
  pages_updated: number;
  pages_rewritten: number;
  errors: string[];
};

export type HealthLintCounts = {
  contradictions: number;
  stale_claims: number;
  orphans: number;
  missing_pages: number;
  missing_cross_refs: number;
  data_gaps_web_search: number;
};

export type HealthLintAction = {
  action: string;
  severity: string;
  effort: string;
  rationale: string;
};

export type HealthLintReport = {
  generated_at: string;
  pages_analyzed: number;
  model: string;
  version: string;
  contradictions: unknown[];
  stale_claims: unknown[];
  orphans: unknown[];
  missing_pages: unknown[];
  missing_cross_refs: unknown[];
  data_gaps_web_search: unknown[];
  next_actions: HealthLintAction[];
  errors: string[];
};

export type HealthLintResponse = {
  report_path: string | null;
  report: HealthLintReport | null;
  counts: Partial<HealthLintCounts>;
  next_actions?: HealthLintAction[];
};
