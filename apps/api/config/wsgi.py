"""WSGI config for Vitrine API."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
packages_dir = root / "packages"
if packages_dir.is_dir() and str(packages_dir) not in sys.path:
    sys.path.insert(0, str(packages_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
