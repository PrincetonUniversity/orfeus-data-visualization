from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # Dropbox
    app_key: str | None
    app_secret: str | None
    refresh_token: str | None
    # Maps
    mapbox_token: str | None
    mapbox_style: str | None
    # App
    port: int
    stub_mode: bool
    # Paths
    root_dir: Path
    pgscen_dir: Path


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def load_settings() -> Settings:
    # utils/.. -> repo root
    root_dir = Path(__file__).resolve().parents[1]

    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

    mapbox_token = os.getenv("MAPBOX_TOKEN") or os.getenv("DASH_MAPBOX_TOKEN")
    mapbox_style = os.getenv("MAPBOX_STYLE")

    port = _env_int("PORT", 8055)
    stub_mode = os.getenv("STUB_MODE", "0").strip() in ("1", "true", "True", "yes", "on")

    pgscen_dir = Path(os.getenv("ORFEUS_PGSCEN_DIR", str(root_dir / "data" / "PGscen_Scenarios")))

    # Auto-enable stub mode if critical data is missing in the mounted /app/data directory
    if not stub_mode:
        data_dir = root_dir / "data"
        critical = [
            data_dir / "Vatic_Grids" / "Texas-7k" / "TX_Data" / "SourceData" / "bus.csv",
        ]
        try:
            if any(not p.exists() for p in critical):
                stub_mode = True
        except Exception:
            # If any error occurs checking files, stay in non-stub unless explicitly set
            pass

    return Settings(
        app_key=app_key,
        app_secret=app_secret,
        refresh_token=refresh_token,
        mapbox_token=mapbox_token,
        mapbox_style=mapbox_style,
        port=port,
    stub_mode=stub_mode,
        root_dir=root_dir,
        pgscen_dir=pgscen_dir,
    )


SETTINGS: Settings = load_settings()
