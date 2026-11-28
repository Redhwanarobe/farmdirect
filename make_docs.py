"""Build HTML documentation for FarmDirect with pdoc."""

import os
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import pdoc  # noqa: E402

pdoc.pdoc("accounts", "farms", "visits", "bulk", "core", output_directory=Path("docs"))
print("Docs ready: open docs/index.html")
