import os
from typing import Union

# Resolve project root from this file location (utils/.. -> repo root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load_markdown(*path_parts: Union[str, os.PathLike]) -> str:
    """Load a markdown file relative to the project root.

    Usage: load_markdown('markdown', 'scenarios.md')
    Returns the file contents, or a short placeholder message on error.
    """
    try:
        path = os.path.join(PROJECT_ROOT, *path_parts)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as exc:
        return f"[Content unavailable: {os.path.join(*path_parts)} — {exc}]"
