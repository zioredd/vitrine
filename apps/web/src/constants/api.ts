/** Canonical Vitrine API paths — all prefixed with /v1 */
export const API = {
  // Catalog
  WEAVE: "/v1/weave",
  SET_DETAIL: (id: string) => `/v1/sets/${id}`,
  TAGS: "/v1/tags",
  FORMAT_SPECTRUM: "/v1/format-spectrum",

  // Craft (mix)
  CRAFT_PACING: (id: string) => `/v1/sets/${id}/craft/pacing`,
  CRAFT_DIALOGUE: (id: string) => `/v1/sets/${id}/craft/dialogue`,

  // Crowd / narrative
  NARRATIVE_ARC: (id: string) => `/v1/sets/${id}/narrative/arc`,
  NARRATIVE_WEB: (id: string) => `/v1/sets/${id}/narrative/web`,
  THEME_CLUSTERS: "/v1/themes/clusters",

  // Intelligence
  INTELLIGENCE: "/v1/intelligence",
  COMMAND_CENTER: "/v1/command-center",
  EDITORIAL_DECISION_REPORT: "/v1/editorial-decision-report",

  // Editorial
  RISKS: "/v1/risks",
  PUBLICATION_WINDOWS: "/v1/publication-windows",
  EDITORIAL_SIGNALS: "/v1/editorial-signals",

  // Enterprise
  ENTERPRISE_PROGRAM: "/v1/enterprise/program",
  ENTERPRISE_BUDGET: "/v1/enterprise/budget",
  ENTERPRISE_BOARD_PACK: "/v1/enterprise/board-pack",

  // Graph
  GRAPH_PATH: (id: string) => `/v1/graph/sets/${id}/path`,
  GRAPH_TRAVERSE: (id: string) => `/v1/graph/sets/${id}/traverse`,
  GRAPH_RESIDENCY_TREE: "/v1/graph/residency-tree",

  // Parser
  PARSER_TOKENIZE: "/v1/parser/tokenize",
  PARSER_PARSE: "/v1/parser/parse",
  PARSER_COMPILE: "/v1/parser/compile",

  // Pipeline
  PIPELINE_RUN: "/v1/pipeline/run",

  // Concurrency
  CONCURRENCY_BATCH_SCORE: "/v1/concurrency/batch-score",
  CONCURRENCY_INGEST: "/v1/concurrency/ingest",

  // Queue
  QUEUE_JOBS: "/v1/queue/jobs",
  QUEUE_SCHEDULE: "/v1/schedule",
  QUEUE_DEAD_LETTER: "/v1/queue/dead-letter",
  QUEUE_REPLAY: "/v1/queue/replay",

  // Ingest
  INGEST_SNAPSHOT: "/v1/ingest/snapshot",

  // Rules
  RULES_REPORT: "/v1/rules/report",

  // Sync / Rebalance
  SYNC_RECONCILE: "/v1/sync/reconcile",
  REBALANCE_ROUTE: "/v1/rebalance/route",

  // AI
  AI_RECOMMEND: "/v1/ai/recommend",
  AI_SIMILAR: "/v1/ai/similar",
} as const;

export const DEFAULT_SET_ID = "ex-001";

export const API_PATHS = Object.values(API).flatMap((v) =>
  typeof v === "function" ? [] : [v],
);
