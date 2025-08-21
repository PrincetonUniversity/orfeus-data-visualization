import os
import re
from typing import Union, Optional

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


def extract_first_h1(markdown_text: str, fallback: Optional[str] = None) -> str:
    """Return the first level-1 heading text from markdown.

    Recognizes lines starting with a single '# ' (not '##'), trims trailing hashes and whitespace.
    If none found, returns the provided fallback or an empty string.
    """
    try:
        for line in markdown_text.splitlines():
            m = re.match(r"^#\s+(.+?)\s*#*\s*$", line)
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return fallback or ""
