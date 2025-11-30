from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app.data.fplcache_io import read_snapshot
from app.models.fpl import BootstrapStatic


@dataclass(frozen=True)
class PlayerSummary:
    code: int
    id: int
    web_name: str
    web_name_lower: str


def build_player_directory(snapshot_path: Path) -> Dict[int, PlayerSummary]:
    """
    Build a simple dictionary keyed by player 'code' from a single snapshot.
    """
    raw = read_snapshot(snapshot_path)
    data = BootstrapStatic.model_validate(raw)
    directory: Dict[int, PlayerSummary] = {}
    for el in data.elements:
        directory[el.code] = PlayerSummary(
            code=el.code,
            id=el.id,
            web_name=el.web_name,
            web_name_lower=el.web_name.lower(),
        )
    return directory


def search_players(
    directory: Dict[int, PlayerSummary], q: str, limit: int = 10
) -> List[Dict[str, object]]:
    """
    Case-insensitive substring search on web_name; startswith matches first.
    """
    needle = q.lower()
    matches = [p for p in directory.values() if needle in p.web_name_lower]
    matches.sort(key=lambda p: (0 if p.web_name_lower.startswith(needle) else 1, p.web_name_lower))
    results = [
        {"code": p.code, "id": p.id, "web_name": p.web_name} for p in matches[: max(0, limit)]
    ]
    return results
