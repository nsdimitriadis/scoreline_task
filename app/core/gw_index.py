from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from app.data.fplcache_io import parse_snapshot_datetime, read_snapshot
from app.models.fpl import BootstrapStatic


@dataclass(frozen=True)
class SeasonWindow:
    """
    UTC-bounded window for a Premier League season.

    bootstrap-static is a point-in-time snapshot; we approximate per-gameweek values
    by sampling one snapshot at the end of each GW using the next GW deadline as the boundary.
    """
    name: str
    start: datetime  # inclusive
    end: datetime    # exclusive


UTC = timezone.utc

SEASON_2023_24 = SeasonWindow(
    "2023-24",
    datetime(2023, 8, 1, 0, 0, tzinfo=UTC),
    datetime(2024, 7, 1, 0, 0, tzinfo=UTC),
)
SEASON_2024_25 = SeasonWindow(
    "2024-25",
    datetime(2024, 8, 1, 0, 0, tzinfo=UTC),
    datetime(2025, 7, 1, 0, 0, tzinfo=UTC),
)


def build_gw_snapshot_index(
    season: SeasonWindow,
    snapshots: List[Tuple[datetime, Path]],
) -> Dict[int, Path]:
    """
    Build an index selecting one snapshot per gameweek for the given season.

    Algorithm:
    - Filter snapshots to season window [start, end)
    - Read earliest snapshot in the window and validate via BootstrapStatic.model_validate(raw)
    - From events, keep those with non-null deadline_time; sort by id
    - For GW i (except last), pick the latest snapshot with ts < deadline_time(next_gw)
    - For last GW, pick the last snapshot within the season window
    - Include only GWs where a snapshot was found
    """
    window_snaps = [(ts, p) for ts, p in snapshots if season.start <= ts < season.end]
    if not window_snaps:
        return {}
    window_snaps.sort(key=lambda x: x[0])

    # Load earliest snapshot to extract events metadata
    first_ts, first_path = window_snaps[0]
    raw = read_snapshot(first_path)
    bootstrap = BootstrapStatic.model_validate(raw)

    events = [e for e in bootstrap.events if e.deadline_time is not None]
    if not events:
        return {}
    events.sort(key=lambda e: e.id)

    index: Dict[int, Path] = {}

    # For each GW except the last:
    # Prefer the latest snapshot strictly before the next GW's deadline
    for i in range(len(events) - 1):
        gw = events[i]
        next_gw = events[i + 1]
        next_deadline = next_gw.deadline_time
        if next_deadline is None:
            continue
        # Find latest snapshot with ts < next_deadline
        latest_before: Optional[Path] = None
        for ts, p in window_snaps:
            if ts < next_deadline:
                latest_before = p
            else:
                break
        if latest_before is not None:
            index[gw.id] = latest_before

    # For the last GW, choose the last snapshot in the season window
    last_gw = events[-1]
    index[last_gw.id] = window_snaps[-1][1]

    return index


def build_all_indices(
    snapshots: List[Tuple[datetime, Path]],
) -> Dict[str, Dict[int, Path]]:
    """
    Build indices for both seasons:
      { "2023-24": {gw_id: Path, ...}, "2024-25": {...} }
    """
    return {
        SEASON_2023_24.name: build_gw_snapshot_index(SEASON_2023_24, snapshots),
        SEASON_2024_25.name: build_gw_snapshot_index(SEASON_2024_25, snapshots),
    }


def describe_index(index: Dict[int, Path]) -> Dict[str, object]:
    """
    Return a brief summary:
      - gw_count
      - min_gw / max_gw
      - first/last mapped snapshot timestamps (UTC; derived from path)
    """
    if not index:
        return {
            "gw_count": 0,
            "min_gw": None,
            "max_gw": None,
            "first_snapshot_ts": None,
            "last_snapshot_ts": None,
        }

    gw_ids = sorted(index.keys())
    mapped_paths = [index[i] for i in gw_ids]
    mapped_ts = [parse_snapshot_datetime(p) for p in mapped_paths]
    mapped_ts.sort()
    return {
        "gw_count": len(gw_ids),
        "min_gw": gw_ids[0],
        "max_gw": gw_ids[-1],
        "first_snapshot_ts": mapped_ts[0],
        "last_snapshot_ts": mapped_ts[-1],
    }


