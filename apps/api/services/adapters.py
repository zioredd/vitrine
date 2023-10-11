"""Thin facades delegating HTTP layer calls to domain packages."""
from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from vitrine_ai.recommender import find_similar_exhibitions, recommend_pacing_adjustments
from vitrine_catalog.repository import CatalogRepository
from vitrine_core.editorial import assess_booking_risks, compute_release_windows
from vitrine_core.intelligence import (
    build_command_center,
    build_decision_report,
    build_intelligence_report,
)
from vitrine_core.scoring import composite_vitrine_score, rank_normalize
from vitrine_crowd.narrative import arc_completeness, relationship_web, theme_clusters
from vitrine_enterprise.program import (
    BudgetLine,
    BudgetOffice,
    ComplianceCheck,
    ComplianceReport,
    ExecutiveProgram,
    Incident,
    IncidentResponse,
    build_board_pack,
)
from vitrine_events.store import EventStore
from vitrine_graph.graph import build_exhibition_graph, bfs, dijkstra, residency_tree
from vitrine_ingest.pipeline import parse_json_records, run_ingest_pipeline
from vitrine_mix.craft import build_craft_report, pacing_curve, wall_text_craft
from vitrine_parser.query import compile_filter, parse_query, tokenize
from vitrine_pipeline.runner import StageRunner
from vitrine_rebalance.routing import dijkstra_min_fee
from vitrine_rules.engine import run_rules
from vitrine_scheduler.cron import CronSchedule
from vitrine_sync.merkle import reconcile
from vitrine_types.models import JobStatus
from vitrine_worker.orchestrator import WorkerOrchestrator

from common.serialize import to_jsonable


@dataclass
class CatalogFacade:
    repository: CatalogRepository

    def list_exhibitions(self) -> list[dict[str, Any]]:
        return [ex.model_dump(mode="json") for ex in self.repository.load_all()]

    def get_exhibition(self, exhibition_id: str) -> dict[str, Any]:
        exhibition = self.repository.get_by_id(exhibition_id)
        if exhibition is None:
            return {}
        return exhibition.model_dump(mode="json")

    def list_tags(self) -> list[dict[str, Any]]:
        counts: Counter[str] = Counter()
        for exhibition in self.repository.load_all():
            for tag in exhibition.tags:
                counts[tag.label] += 1
        return [{"label": label, "count": count} for label, count in counts.most_common()]

    def format_spectrum(self) -> list[dict[str, Any]]:
        counts: Counter[str] = Counter()
        for exhibition in self.repository.load_all():
            if exhibition.genre:
                counts[exhibition.genre] += 1
            if exhibition.venue and exhibition.venue.format:
                counts[exhibition.venue.format] += 1
        return [{"label": label, "count": count} for label, count in counts.most_common()]


@dataclass
class MixFacade:
    repository: CatalogRepository

    def pacing(self, set_id: str) -> dict[str, Any]:
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None:
            return {}
        return to_jsonable(
            {
                "set_id": set_id,
                "curve": pacing_curve(exhibition.all_artworks()),
                "report": build_craft_report(exhibition),
            }
        )

    def dialogue(self, set_id: str) -> dict[str, Any]:
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None:
            return {}
        artworks = exhibition.all_artworks()
        return {
            "set_id": set_id,
            "wall_text_score": wall_text_craft(artworks),
            "avg_wall_text_ratio": round(
                sum(a.wall_text_ratio for a in artworks) / len(artworks), 3
            )
            if artworks
            else 0.0,
        }


@dataclass
class CrowdFacade:
    repository: CatalogRepository

    def arc(self, set_id: str) -> dict[str, Any]:
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None:
            return {}
        return to_jsonable(arc_completeness(exhibition))

    def web(self, set_id: str) -> dict[str, Any]:
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None:
            return {}
        return to_jsonable(relationship_web(exhibition))

    def theme_clusters(self) -> list[dict[str, Any]]:
        clusters: list[dict[str, Any]] = []
        for exhibition in self.repository.load_all():
            for cluster in theme_clusters(exhibition):
                clusters.append(
                    {
                        "exhibition_id": exhibition.id,
                        **to_jsonable(cluster),
                    }
                )
        return clusters


@dataclass
class IntelligenceFacade:
    repository: CatalogRepository
    worker: WorkerOrchestrator

    def report(self) -> dict[str, Any]:
        exhibitions = self.repository.load_all()
        return to_jsonable(build_intelligence_report(exhibitions, alerts=[]))

    def command_center(self) -> dict[str, Any]:
        exhibitions = self.repository.load_all()
        pending = self.worker.queue.pending_count()
        return to_jsonable(build_command_center(exhibitions, pending_jobs=pending))

    def editorial_decision_report(self) -> dict[str, Any]:
        exhibitions = self.repository.load_all()
        if not exhibitions:
            return {}
        risks = assess_booking_risks(exhibitions)
        top = max(exhibitions, key=lambda ex: ex.vitrine_score or 0.0)
        risk_score = next((r.risk_score for r in risks if r.exhibition_id == top.id), 0.0)
        return to_jsonable(build_decision_report(top, booking_risk=risk_score))


@dataclass
class EditorialFacade:
    repository: CatalogRepository

    def risks(self) -> list[dict[str, Any]]:
        return to_jsonable(assess_booking_risks(self.repository.load_all()))

    def publication_windows(self) -> list[dict[str, Any]]:
        return to_jsonable(compute_release_windows(self.repository.load_all()))

    def signals(self) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []
        for exhibition in self.repository.load_all():
            for signal in exhibition.signals:
                signals.append(
                    {
                        "exhibition_id": exhibition.id,
                        "signal": signal.model_dump(mode="json"),
                    }
                )
        return signals


@dataclass
class EnterpriseFacade:
    repository: CatalogRepository

    def program(self) -> dict[str, Any]:
        exhibitions = self.repository.load_all()
        residencies = Counter(ex.residency for ex in exhibitions if ex.residency)
        programs = [
            ExecutiveProgram(
                name=residency,
                sponsor="Vitrine Foundation",
                exhibitions=[ex.id for ex in exhibitions if ex.residency == residency],
                budget_allocated=250_000.0,
                budget_spent=180_000.0,
            )
            for residency, _ in residencies.most_common()
        ]
        return to_jsonable(programs)

    def budget(self) -> dict[str, Any]:
        office = BudgetOffice(
            fiscal_year=2026,
            lines=[
                BudgetLine(category="curation", planned=120_000, actual=118_500),
                BudgetLine(category="installation", planned=80_000, actual=92_000),
                BudgetLine(category="marketing", planned=45_000, actual=41_000),
            ],
        )
        return to_jsonable(office)

    def board_pack(self) -> dict[str, Any]:
        exhibitions = self.repository.load_all()
        residencies = Counter(ex.residency for ex in exhibitions if ex.residency)
        programs = [
            ExecutiveProgram(
                name=residency,
                sponsor="Vitrine Foundation",
                exhibitions=[ex.id for ex in exhibitions if ex.residency == residency],
                budget_allocated=250_000.0,
                budget_spent=180_000.0,
            )
            for residency, _ in residencies.most_common()
        ]
        compliance = ComplianceReport(
            checks=[
                ComplianceCheck(regulation="GDPR", passed=True),
                ComplianceCheck(regulation="Accessibility", passed=True),
            ]
        )
        incidents = IncidentResponse(
            incidents=[
                Incident(
                    id="inc-001",
                    severity="medium",
                    summary="HVAC fluctuation in gallery B",
                    opened_on=datetime.now(timezone.utc).date(),
                )
            ]
        )
        return to_jsonable(build_board_pack(exhibitions, programs, compliance, incidents))

    def compliance(self) -> dict[str, Any]:
        report = ComplianceReport(
            checks=[
                ComplianceCheck(regulation="GDPR", passed=True),
                ComplianceCheck(regulation="Provenance SLA", passed=True),
                ComplianceCheck(regulation="Insurance", passed=False, notes="renewal pending"),
            ]
        )
        return to_jsonable(report)

    def incidents(self) -> dict[str, Any]:
        response = IncidentResponse(
            incidents=[
                Incident(
                    id="inc-001",
                    severity="medium",
                    summary="Climate control alert",
                    opened_on=datetime.now(timezone.utc).date(),
                )
            ]
        )
        return to_jsonable(response)


@dataclass
class GraphFacade:
    repository: CatalogRepository

    def shortest_path(self, set_id: str, target: str | None) -> dict[str, Any]:
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None or not target:
            return {"path": [], "cost": None}
        graph = build_exhibition_graph(exhibition)
        path, cost = dijkstra(graph, set_id if set_id in graph.adjacency else next(iter(graph.adjacency), set_id), target)
        if not path and graph.adjacency:
            start = next(iter(graph.adjacency))
            path, cost = dijkstra(graph, start, target)
        return {"path": path, "cost": cost}

    def traverse(self, set_id: str, depth: int = 3) -> dict[str, Any]:
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None:
            return {"visited": []}
        graph = build_exhibition_graph(exhibition)
        start = next(iter(graph.adjacency), set_id)
        visited = bfs(graph, start)[:depth]
        return {"visited": visited, "depth": depth}

    def residency_tree(self) -> dict[str, Any]:
        exhibitions = self.repository.load_all()
        residencies = sorted({ex.residency for ex in exhibitions if ex.residency})
        if not residencies:
            return {}
        tree = residency_tree(exhibitions, residencies[0])
        return to_jsonable(tree)


@dataclass
class ParserFacade:
    def tokenize(self, expression: str) -> dict[str, Any]:
        tokens = tokenize(expression)
        return {
            "tokens": [
                {"kind": token.kind.name, "value": token.value, "pos": token.pos}
                for token in tokens
            ]
        }

    def parse(self, expression: str) -> dict[str, Any]:
        return {"ast": to_jsonable(parse_query(expression))}

    def compile(self, ast_or_expression: Any) -> dict[str, Any]:
        if isinstance(ast_or_expression, str):
            ast = parse_query(ast_or_expression)
        elif isinstance(ast_or_expression, dict):
            from vitrine_parser.query import FilterNode

            ast = FilterNode(**ast_or_expression)
        else:
            ast = ast_or_expression
        return {"query": compile_filter(ast)}


@dataclass
class PipelineFacade:
    repository: CatalogRepository
    events: EventStore

    def run(self, stages: list[str] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        runner = StageRunner()
        ctx = runner.run({"raw_records": (payload or {}).get("records", []), **(payload or {})})
        return {
            "stages_run": ctx.stages_run,
            "errors": ctx.errors,
            "data": to_jsonable(ctx.data),
        }


@dataclass
class WorkerFacade:
    repository: CatalogRepository
    worker: WorkerOrchestrator

    def batch_score(self, ids: list[str] | None) -> dict[str, Any]:
        exhibitions = self.repository.load_all()
        if ids:
            id_set = set(ids)
            exhibitions = [ex for ex in exhibitions if ex.id in id_set]
        raw_scores = [ex.vitrine_score or 50.0 for ex in exhibitions]
        normalized = rank_normalize(raw_scores) if raw_scores else []
        scores = []
        for exhibition, normalized_score in zip(exhibitions, normalized):
            signal_scores = [signal.score for signal in exhibition.signals]
            composite = composite_vitrine_score(
                signal_scores,
                craft_score=normalized_score,
                crowd_score=exhibition.crowd_score or 50.0,
            )
            scores.append({"id": exhibition.id, "score": round(composite, 2)})
        return {"scores": scores}

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        records = payload.get("records")
        if records is None and "body" in payload:
            records = parse_json_records(payload["body"])
        elif records is None:
            records = [payload]
        result = run_ingest_pipeline(records)
        return {
            "accepted": len(result.records),
            "deduped": result.deduped,
            "errors": to_jsonable(result.errors),
        }

    def run_once(self) -> None:
        self.worker.process_one()

    def run(self, poll_interval: float = 1.0) -> None:
        while True:
            processed = self.worker.process_one()
            if processed is None and self.worker.queue.pending_count() == 0:
                time.sleep(poll_interval)


@dataclass
class QueueFacade:
    worker: WorkerOrchestrator

    def list_jobs(self) -> list[dict[str, Any]]:
        pending = self.worker.queue.heap.peek()
        jobs = [pending.model_dump(mode="json")] if pending else []
        return jobs


@dataclass
class SchedulerFacade:
    schedules: list[CronSchedule] = field(
        default_factory=lambda: [CronSchedule.parse("0 * * * *")]
    )

    def list_schedules(self) -> list[dict[str, Any]]:
        return [{"expression": "0 * * * *", "description": "hourly catalog refresh"}]


@dataclass
class RetryFacade:
    worker: WorkerOrchestrator

    def dead_letter_queue(self) -> list[dict[str, Any]]:
        return [
            {
                "job_id": entry.job.id,
                "reason": entry.reason,
                "attempts": entry.dead_at_attempt,
            }
            for entry in self.worker.dlq.all()
        ]

    def replay(self, job_id: str | None) -> dict[str, Any]:
        if not job_id:
            return {"status": "missing_job_id"}
        for entry in self.worker.dlq.all():
            if entry.job.id == job_id:
                job = entry.job.model_copy(update={"status": JobStatus.PENDING, "attempts": 0})
                self.worker.queue.enqueue(job)
                return {"job_id": job_id, "status": "replayed"}
        return {"job_id": job_id, "status": "not_found"}


@dataclass
class IngestFacade:
    repository: CatalogRepository

    def ingest_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        records = snapshot.get("items") or snapshot.get("records") or [snapshot]
        result = run_ingest_pipeline(records)
        return {
            "imported": len(result.records),
            "deduped": result.deduped,
            "errors": to_jsonable(result.errors),
        }


@dataclass
class RulesFacade:
    repository: CatalogRepository

    def run_report(self) -> dict[str, Any]:
        result = run_rules(self.repository.load_all())
        return to_jsonable(result)


@dataclass
class SyncFacade:
    repository: CatalogRepository

    def reconcile(self, remote: dict[str, Any]) -> dict[str, Any]:
        local = {
            ex.id: ex.model_dump_json()
            for ex in self.repository.load_all()
        }
        remote_leaves = remote.get("leaves", remote)
        if isinstance(remote_leaves, dict):
            remote_map = {str(k): str(v) for k, v in remote_leaves.items()}
        else:
            remote_map = {}
        result = reconcile(local, remote_map)
        return to_jsonable(result)


@dataclass
class RebalanceFacade:
    repository: CatalogRepository
    path_cache: Any = field(default_factory=dict)

    def route(
        self,
        graph: dict[str, Any],
        source: str | None = None,
        target: str | None = None,
    ) -> dict[str, Any]:
        adjacency: dict[str, list[tuple[str, float, float]]] = {}
        for edge in graph.get("edges", []):
            adjacency.setdefault(edge["source"], []).append(
                (edge["target"], edge.get("weight", 1.0), edge.get("fee", 0.0))
            )
        if not source or not target:
            exhibitions = self.repository.load_all()
            if exhibitions:
                source = source or exhibitions[0].id
                target = target or exhibitions[-1].id
            else:
                return {"route": [], "fee": None}
        path, fee = dijkstra_min_fee(adjacency, source, target)
        return {"route": path, "fee": fee}


@dataclass
class AIFacade:
    repository: CatalogRepository

    def recommend(self, set_id: str | None) -> dict[str, Any]:
        if not set_id:
            return {"recommendations": []}
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None:
            return {"recommendations": []}
        return {"recommendations": recommend_pacing_adjustments(exhibition)}

    def similar(self, set_id: str | None) -> dict[str, Any]:
        if not set_id:
            return {"items": []}
        exhibition = self.repository.get_by_id(set_id)
        if exhibition is None:
            return {"items": []}
        matches = find_similar_exhibitions(exhibition, self.repository)
        return {"items": to_jsonable(matches)}
