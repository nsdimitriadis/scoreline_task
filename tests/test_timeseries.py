from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from app.core import timeseries
from app.core.timeseries import build_total_points_timeseries_by_code


def test_build_total_points_timeseries_by_code_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    # Prepare fake snapshots for two seasons and a few GWs
    a, b, c = Path("/snap/a"), Path("/snap/b"), Path("/snap/c")
    gw_indices = {
        "2023-24": {1: a, 2: b},
        "2024-25": {1: c},
    }

    def fake_read_snapshot(p: Path) -> Dict[str, Any]:
        if p is a:
            return {
                "events": [],
                "elements": [{"id": 1, "code": 123, "web_name": "Alpha", "total_points": 10}],
            }
        if p is b:
            return {
                "events": [],
                "elements": [{"id": 1, "code": 123, "web_name": "Alpha", "total_points": 12}],
            }
        if p is c:
            return {
                "events": [],
                "elements": [{"id": 1, "code": 123, "web_name": "Alpha", "total_points": 5}],
            }
        return {"events": [], "elements": []}

    monkeypatch.setattr(timeseries, "read_snapshot", fake_read_snapshot)

    out = build_total_points_timeseries_by_code(123, gw_indices)
    assert out["player_code"] == 123
    assert out["player_name"] == "Alpha"
    pts = out["points"]
    # 3 points: two in 2023-24, one in 2024-25
    assert len(pts) == 3
    assert pts[0] == {"season": "2023-24", "gw": 1, "value": 10, "delta": 10}
    assert pts[1] == {"season": "2023-24", "gw": 2, "value": 12, "delta": 2}
    # delta resets per season
    assert pts[2] == {"season": "2024-25", "gw": 1, "value": 5, "delta": 5}


def test_build_total_points_timeseries_by_code_missing_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    a, b = Path("/snap/a"), Path("/snap/b")
    gw_indices = {"2023-24": {1: a, 2: b}}

    def fake_read_snapshot(_p: Path) -> Dict[str, Any]:
        return {
            "events": [],
            "elements": [{"id": 1, "code": 999, "web_name": "Other", "total_points": 42}],
        }

    monkeypatch.setattr(timeseries, "read_snapshot", fake_read_snapshot)

    out = build_total_points_timeseries_by_code(123, gw_indices)
    pts = out["points"]
    # Player absent: always None values and deltas
    assert pts == [
        {"season": "2023-24", "gw": 1, "value": None, "delta": None},
        {"season": "2023-24", "gw": 2, "value": None, "delta": None},
    ]
    assert out["player_name"] is None
