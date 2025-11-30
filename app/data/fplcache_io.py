from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


FPLCACHE_DIR: Path = Path(os.getenv("FPLCACHE_DIR", "vendor/fplcache"))
CACHE_ROOT: Path = FPLCACHE_DIR / "cache"


def list_snapshot_files() -> List[Path]:
    """
    Find all snapshot files in the cache tree.
    Returns a list of paths matching '*.json.xz' under CACHE_ROOT.
    """
    if not CACHE_ROOT.exists():
        raise FileNotFoundError(
            f"FPL cache not found at {CACHE_ROOT}. Run `make fetch` or set FPLCACHE_DIR."
        )
    return [p for p in CACHE_ROOT.rglob("*.json.xz") if p.is_file()]


def parse_snapshot_datetime(path: Path) -> datetime:
    """
    Parse .../cache/{year}/{month}/{day}/{HHMM}.json.xz into a UTC datetime.
    Minimal checks: filename suffix and 4-digit HHMM; datetime enforces ranges/dates.
    """
    parts = path.parts
    if len(parts) < 4:
        raise ValueError(f"Invalid snapshot path depth (expected >= 4): {path}")
    try:
        year_str, month_str, day_str = parts[-4], parts[-3], parts[-2]
    except Exception:
        raise ValueError(f"Invalid snapshot path structure: {path}") from None

    suffix = ".json.xz"
    name = path.name
    if not name.endswith(suffix):
        raise ValueError(f"Snapshot filename must end with '{suffix}': {path}")
    hhmm = name[:-len(suffix)]
    if len(hhmm) != 4 or not hhmm.isdigit():
        raise ValueError(f"Snapshot time must be exactly 4 digits HHMM: {path}")

    try:
        return datetime(
            int(year_str),
            int(month_str),
            int(day_str),
            int(hhmm[:2]),
            int(hhmm[2:]),
            tzinfo=timezone.utc,
        )
    except ValueError as e:
        raise ValueError(f"Invalid snapshot date/time in {path}: {e}") from None


def iter_snapshots() -> List[Tuple[datetime, Path]]:
    """
    Return a list of (timestamp, path) tuples for all snapshots,
    sorted by timestamp ascending.
    """
    pairs: List[Tuple[datetime, Path]] = []
    for p in list_snapshot_files():
        ts = parse_snapshot_datetime(p)
        pairs.append((ts, p))
    pairs.sort(key=lambda x: x[0])
    return pairs


def read_snapshot(path: Path) -> Dict:
    """
    Read a single JSON snapshot stored as .json.xz compressed file.
    """
    try:
        # Lazy import to avoid _lzma missing at interpreter build time
        import lzma  # type: ignore

        with lzma.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (ModuleNotFoundError, ImportError):
        # Fallback to external xz utility
        try:
            result = subprocess.run(
                ["xz", "-dc", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "xz executable not found. Install with `brew install xz` on macOS "
                "or `sudo apt-get install xz-utils` on Linux."
            ) from exc
        return json.loads(result.stdout)


