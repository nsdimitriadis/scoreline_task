from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.data.fplcache_io import parse_snapshot_datetime


def test_parse_snapshot_datetime_valid() -> None:
    p = Path("vendor/fplcache/cache/2024/3/9/0152.json.xz")
    dt = parse_snapshot_datetime(p)
    assert dt == datetime(2024, 3, 9, 1, 52, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "path",
    [
        Path("vendor/fplcache/cache/2024/03/09/152.json.xz"),  # not 4 digits
        Path("vendor/fplcache/cache/2024/03/09/abcd.json.xz"),  # not digits
        Path("vendor/fplcache/cache/2024/03/09/2400.json.xz"),  # hour out of range
        Path("vendor/fplcache/cache/2024/03/09/2360.json.xz"),  # minute out of range
        Path("vendor/fplcache/cache/2024/02/30/0100.json.xz"),  # invalid date
    ],
)
def test_parse_snapshot_datetime_invalid(path: Path) -> None:
    with pytest.raises(ValueError):
        parse_snapshot_datetime(path)


def test_parse_snapshot_datetime_bad_suffix() -> None:
    p = Path("vendor/fplcache/cache/2024/3/9/0152.json")
    with pytest.raises(ValueError):
        parse_snapshot_datetime(p)
