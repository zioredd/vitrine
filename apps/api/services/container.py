"""Service container wiring domain packages to a shared catalog repository."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vitrine_catalog.repository import CatalogRepository
from vitrine_events.store import EventStore
from vitrine_worker.orchestrator import WorkerOrchestrator

from services.adapters import (
    AIFacade,
    CatalogFacade,
    CrowdFacade,
    EditorialFacade,
    EnterpriseFacade,
    GraphFacade,
    IngestFacade,
    IntelligenceFacade,
    MixFacade,
    ParserFacade,
    PipelineFacade,
    QueueFacade,
    RebalanceFacade,
    RetryFacade,
    RulesFacade,
    SchedulerFacade,
    SyncFacade,
    WorkerFacade,
)


@dataclass
class ServiceContainer:
    """Holds wired domain services backed by one catalog repository."""

    catalog: CatalogFacade
    mix: MixFacade
    crowd: CrowdFacade
    intelligence: IntelligenceFacade
    editorial: EditorialFacade
    enterprise: EnterpriseFacade
    graph: GraphFacade
    parser: ParserFacade
    pipeline: PipelineFacade
    worker: WorkerFacade
    queue: QueueFacade
    scheduler: SchedulerFacade
    retry: RetryFacade
    ingest: IngestFacade
    rules: RulesFacade
    sync: SyncFacade
    rebalance: RebalanceFacade
    ai: AIFacade
    events: EventStore
    orchestrator: WorkerOrchestrator


_container: ServiceContainer | None = None


def create_service_container() -> ServiceContainer:
    """Instantiate all domain services with a shared catalog repository."""
    repository = CatalogRepository.from_seed()
    events = EventStore()
    orchestrator = WorkerOrchestrator(event_store=events)

    worker_facade = WorkerFacade(repository=repository, worker=orchestrator)

    return ServiceContainer(
        catalog=CatalogFacade(repository=repository),
        mix=MixFacade(repository=repository),
        crowd=CrowdFacade(repository=repository),
        intelligence=IntelligenceFacade(repository=repository, worker=orchestrator),
        editorial=EditorialFacade(repository=repository),
        enterprise=EnterpriseFacade(repository=repository),
        graph=GraphFacade(repository=repository),
        parser=ParserFacade(),
        pipeline=PipelineFacade(repository=repository, events=events),
        worker=worker_facade,
        queue=QueueFacade(worker=orchestrator),
        scheduler=SchedulerFacade(),
        retry=RetryFacade(worker=orchestrator),
        ingest=IngestFacade(repository=repository),
        rules=RulesFacade(repository=repository),
        sync=SyncFacade(repository=repository),
        rebalance=RebalanceFacade(repository=repository),
        ai=AIFacade(repository=repository),
        events=events,
        orchestrator=orchestrator,
    )


def get_container() -> ServiceContainer:
    """Return the process-wide service container singleton."""
    global _container
    if _container is None:
        _container = create_service_container()
    return _container


def reset_container() -> None:
    """Clear the singleton (used in tests)."""
    global _container
    _container = None
