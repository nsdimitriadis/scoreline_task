from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException

from app.core.gw_index import build_all_indices
from app.core.player_directory import PlayerSummary, build_player_directory, search_players
from app.core.timeseries import build_total_points_timeseries_by_code
from app.data.fplcache_io import iter_snapshots
from app.models.api import (
    PlayerSearchResponse,
    TimeSeriesResponse,
)

app = FastAPI(title="fpl-cache-api")

PLAYER_DIRECTORY: Optional[dict[int, PlayerSummary]] = None
GW_INDICES: Optional[dict[str, dict[int, Path]]] = None


@app.on_event("startup")
def _startup_build_caches() -> None:
    """
    Build GW indices and a simple player directory once at startup.
    Reference snapshot: latest available overall.
    """
    global PLAYER_DIRECTORY, GW_INDICES
    try:
        snaps = iter_snapshots()
        if not snaps:
            return
        GW_INDICES = build_all_indices(snaps)
        ref_snapshot = snaps[-1][1]
        PLAYER_DIRECTORY = build_player_directory(ref_snapshot)
    except Exception:
        return


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> Dict[str, str]:
    return {"service": "fpl-cache-api"}


@app.get("/players/search", response_model=PlayerSearchResponse)
def players_search(q: str, limit: int = 10) -> Dict[str, object]:
    if PLAYER_DIRECTORY is None:
        raise HTTPException(
            status_code=500,
            detail="Player directory not built. Ensure cache is fetched and restart the server.",
        )
    results = search_players(PLAYER_DIRECTORY, q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@lru_cache(maxsize=512)
def _timeseries_cached(player_code: int) -> Dict[str, object]:
    if GW_INDICES is None:
        raise HTTPException(
            status_code=500,
            detail="GW indices not built. Ensure cache is fetched and restart the server.",
        )
    return build_total_points_timeseries_by_code(player_code, GW_INDICES)


@app.get("/players/{player_code}/timeseries", response_model=TimeSeriesResponse)
def player_timeseries(player_code: int) -> Dict[str, object]:
    # Optional fast 404 if directory is present and code not found
    if PLAYER_DIRECTORY is not None and player_code not in PLAYER_DIRECTORY:
        raise HTTPException(status_code=404, detail="Player code not found")

    ts = _timeseries_cached(player_code)
    has_any = any(pt["value"] is not None for pt in ts.get("points", []))
    if not has_any:
        raise HTTPException(status_code=404, detail="No data for given player code")
    return ts


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
