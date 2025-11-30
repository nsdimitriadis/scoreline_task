from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from app.data.fplcache_io import read_snapshot
from app.models.fpl import BootstrapStatic


def build_total_points_timeseries_by_code(
    player_code: int,
    gw_indices: Dict[str, Dict[int, Path]],
) -> Dict[str, object]:
    """
    Build a per-gameweek time series using provided GW indices.
    Always output all GWs; if player is missing, value and delta are None.
    """
    points: List[Dict[str, object]] = []
    player_name: Optional[str] = None

    for season in sorted(gw_indices.keys()):
        gw_to_path = gw_indices[season]
        prev_value: Optional[int] = None
        for gw in sorted(gw_to_path.keys()):
            p = gw_to_path[gw]
            raw = read_snapshot(p)
            data = BootstrapStatic.model_validate(raw)

            value: Optional[int] = None
            for el in data.elements:
                if el.code == player_code:
                    if player_name is None:
                        player_name = el.web_name
                    value = el.total_points
                    break

            if prev_value is None:
                delta: Optional[int] = value
            else:
                delta = None if (value is None) else (value - prev_value)
            prev_value = value

            points.append(
                {
                    "season": season,
                    "gw": gw,
                    "value": value,
                    "delta": delta,
                }
            )

    return {
        "player_code": player_code,
        "player_name": player_name,
        "stat": "total_points",
        "points": points,
    }
