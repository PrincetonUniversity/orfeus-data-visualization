from __future__ import annotations

from typing import Tuple, Optional, Any

try:
    import dropbox  # type: ignore
except Exception:  # dropbox may not be installed in some envs
    dropbox = None  # type: ignore

from .config import SETTINGS


def get_dropbox() -> Tuple[Optional[Any], bool]:
    """Create a Dropbox client from env/config if possible.

    Returns (dbx, has_dropbox)
    """
    # In stub mode, never use Dropbox
    if getattr(SETTINGS, "stub_mode", False):
        return None, False

    if dropbox is None:
        return None, False

    if not (SETTINGS.app_key and SETTINGS.app_secret and SETTINGS.refresh_token):
        return None, False

    try:
        client = dropbox.Dropbox(
            app_key=SETTINGS.app_key,
            app_secret=SETTINGS.app_secret,
            oauth2_refresh_token=SETTINGS.refresh_token,
        )
        return client, True
    except Exception:
        return None, False
