# Vitrine Submission

Vitrine is an exhibition and gallery curation intelligence platform. Curators use Vitrine to score exhibitions, analyze visitor pacing and narrative tension across rooms and artworks, audit provenance signals, and plan editorial release windows.

## Product

Vitrine models exhibitions as curated experiences with:

- **Rooms and artworks** with telemetry: dwell time, intensity, narrative tension, wall-text ratio
- **Visitor signals** with provenance (source, URL, confidence, rank)
- **Artwork relationship graphs** for narrative and spatial analysis
- **Vitrine Score** composite scoring with freshness decay and editorial analytics

## Monorepo packages

Twenty domain packages live under `packages/`:

| Package | Purpose |
|---------|---------|
| `types` | Shared Pydantic models |
| `core` | Scoring, intelligence, editorial, analytics |
| `catalog` | Repository over rich seed exhibition profiles |
| `mix` | Craft analytics: pacing, energy, wall-text dialogue |
| `crowd` | Narrative structure: webs, arcs, theme clusters |
| `graph` | BFS, Dijkstra, residency trees |
| `parser` | Filter query lexer + AST compiler |
| `rebalance` | Bellman-Ford, min-fee routing, greedy planner |
| `sync` | Merkle reconciliation |
| `events` | Append-only store with vector clocks |
| `queue` | Binary heap + job state machine |
| `scheduler` | Cron expansion and next-run |
| `retry` | Exponential backoff + dead-letter queue |
| `pipeline` | Multi-stage decode/normalize/diff runner |
| `worker` | Orchestrator with rate limiting and DLQ |
| `ingest` | CSV/JSON parsers, normalizers, validators |
| `rules` | Pluggable data-quality rule engine |
| `ops` | Policy engine, circuit breaker, audit chain |
| `enterprise` | Executive program, budget, compliance, board pack |
| `ai` | Heuristic exhibition recommender |

## Development

Install packages in dependency order (types first):

```bash
pip install -e packages/types
pip install -e packages/core
pip install -e packages/catalog
# ... remaining packages
pytest
```

Generate seed catalog (~48 exhibitions, 5000+ lines):

```bash
python scripts/generate_vitrine_seed_profiles.py
```

## Architecture

HTTP handlers (future API layer) delegate to packages. Business logic lives in domain packages, not route files. Seed data is generated reproducibly via script for a production-like fixture corpus.
