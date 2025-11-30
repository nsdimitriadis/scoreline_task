from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from app.core import gw_index
from app.core.gw_index import SEASON_2023_24, build_gw_snapshot_index

UTC = timezone.utc


def _events_two_gws() -> Dict[str, Any]:
    # Minimal bootstrap with two gameweeks and deadlines
    return {
        "events": [
            {"id": 1, "deadline_time": "2023-08-11T18:30:00Z"},
            {"id": 2, "deadline_time": "2023-08-18T18:30:00Z"},
        ],
        "elements": [],  # not used here
    }


def test_build_gw_snapshot_index_selects_latest_before_next_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Patch read_snapshot in the module that uses it
    monkeypatch.setattr(gw_index, "read_snapshot", lambda _p: _events_two_gws())

    # Snapshots within season window
    p1 = Path("/snap/a")  # 2023-08-10 (early)
    p2 = Path("/snap/b")  # 2023-08-18 18:29 (latest before next deadline)
    p3 = Path("/snap/c")  # 2023-08-18 18:31 (after)
    p4 = Path("/snap/d")  # later in season, becomes GW2 selection (last in window)

    snaps: List[Tuple[datetime, Path]] = [
        (datetime(2023, 8, 10, 12, 0, tzinfo=UTC), p1),
        (datetime(2023, 8, 18, 18, 29, tzinfo=UTC), p2),
        (datetime(2023, 8, 18, 18, 31, tzinfo=UTC), p3),
        (datetime(2023, 8, 31, 0, 0, tzinfo=UTC), p4),
    ]

    idx = build_gw_snapshot_index(SEASON_2023_24, snaps)
    assert idx[1] == p2  # latest before next GW deadline
    assert idx[2] == p4  # last snapshot in window for final GW


def test_build_gw_snapshot_index_omits_gw_if_no_snapshot_before_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gw_index, "read_snapshot", lambda _p: _events_two_gws())
    # Only after-deadline snapshots for GW1 boundary, so GW1 should be omitted
    p_after = Path("/snap/after")
    snaps: List[Tuple[datetime, Path]] = [
        (datetime(2023, 8, 18, 18, 31, tzinfo=UTC), p_after),
    ]
    idx = build_gw_snapshot_index(SEASON_2023_24, snaps)
    assert 1 not in idx
