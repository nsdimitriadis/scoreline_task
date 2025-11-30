from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PlayerSearchItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: int
    id: int
    web_name: str


class PlayerSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    count: int
    results: List[PlayerSearchItem]


class TimeSeriesPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season: str
    gw: int
    value: Optional[int]
    delta: Optional[int]


class TimeSeriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_code: int
    player_name: Optional[str]
    stat: str
    points: List[TimeSeriesPoint]
