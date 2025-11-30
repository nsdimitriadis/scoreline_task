from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    deadline_time: Optional[datetime] = None

    @field_validator("deadline_time")
    @classmethod
    def ensure_utc(cls, value: Optional[datetime]) -> Optional[datetime]:
        """
        Ensure parsed datetimes are timezone-aware (UTC). If the source is naive,
        assume UTC; if it has a tzinfo, normalize to UTC.
        """
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Element(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    code: int
    web_name: str
    total_points: int


class BootstrapStatic(BaseModel):
    model_config = ConfigDict(extra="ignore")

    events: List[Event]
    elements: List[Element]
