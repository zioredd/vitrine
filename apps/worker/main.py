"""Optional Celery-style worker entry using vitrine_worker orchestrator."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_paths() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    packages_dir = repo_root / "packages"
    api_dir = repo_root / "apps" / "api"
    for path in (packages_dir, api_dir):
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
    for package in packages_dir.glob("*/src"):
        src = str(package)
        if src not in sys.path:
            sys.path.insert(0, src)


def main(argv: list[str] | None = None) -> int:
    _ensure_paths()

    parser = argparse.ArgumentParser(description="Vitrine background worker")
    parser.add_argument("--once", action="store_true", help="Process one batch then exit")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between polls")
    args = parser.parse_args(argv)

    from services.container import create_service_container

    container = create_service_container()

    if args.once:
        container.worker.run_once()
    else:
        container.worker.run(poll_interval=args.poll_interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
