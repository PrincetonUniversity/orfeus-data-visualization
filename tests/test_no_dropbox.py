"""Dropbox is not a reliable data source; the app must read data only from data/."""
from __future__ import annotations

from pathlib import Path

from conftest import REPO_ROOT

CHECKED_SUFFIXES = {".py", ".txt", ".yml", ".yaml", ".toml", ".cfg"}
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "tests"}


def _source_files() -> list[Path]:
    files = []
    for p in REPO_ROOT.rglob("*"):
        if p.is_file() and p.suffix in CHECKED_SUFFIXES and not (SKIP_DIRS & set(p.relative_to(REPO_ROOT).parts)):
            files.append(p)
    return files


def test_source_files_found() -> None:
    # Guard against the scan silently checking nothing.
    names = {p.name for p in _source_files()}
    assert {"app.py", "requirements.txt", "lmps.py"} <= names


def test_no_dropbox_references() -> None:
    offenders = [
        str(p.relative_to(REPO_ROOT))
        for p in _source_files()
        if "dropbox" in p.read_text(encoding="utf-8", errors="replace").lower()
    ]
    assert offenders == [], f"Dropbox still referenced in: {offenders}"


def test_dropbox_client_module_removed() -> None:
    assert not (REPO_ROOT / "utils" / "dropbox_client.py").exists()
