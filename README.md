![Scoreline celebration](scoreline_celebration.png)

# Scoreline Take-Home Assignment

Yes, this is me celebrating my first ever goal with Scoreline's Jeresey. It might not even be my last.

I really enjoyed working with football data!

Thank you for giving me the opportunity!

NOTE: I tried to keep this README file as small as possible happy to discuss more.

## Table of Contents

- [How to run the project](#how-to-run-the-project)
- [Flow (high level)](#flow-high-level)
- [Testing & Checks](#testing--checks)
- [Which stat I chose and why](#which-stat-i-chose-and-why)
- [How I constructed the time series](#how-i-constructed-the-time-series)
- [Assumptions & Ambiguities](#assumptions--ambiguities)
- [What I'd improve with more time](#what-id-improve-with-more-time)

## How to run the project
### Requirements
- Python 3.11
- uv
- git
- xz (CLI)
- make

### Steps
```bash
cd scoreline_task
make
```
Open http://127.0.0.1:8000/docs#/

## Testing & Checks
- Run unit tests:
  ```bash
  make test
  ```
- Run lint + format checks (Ruff):
  ```bash
  make check
  ```

### Usage example
Search (Use any part of the name. I used "sal"):

```bash
curl "http://127.0.0.1:8000/players/search?q=sal"
```

Response:

```json
{"query":"sal","count":2,"results":[{"code":462424,"id":6,"web_name":"Saliba"},{"code":118748,"id":381,"web_name":"M.Salah"}]}
```

Time series (use Salah's code 118748):

```bash
curl "http://127.0.0.1:8000/players/118748/timeseries"
```

Response (truncated example):

```json
{"player_code":118748,"player_name":"Salah","stat":"total_points","points":[{"season":"2023-24","gw":1,"value":5,"delta":5},{"season":"2023-24","gw":2,"value":10,"delta":5},{"season":"2023-24","gw":3,
.
.
.
"value":334,"delta":2},{"season":"2024-25","gw":38,"value":344,"delta":10}]}
```

## Flow (high level)
1. `make fetch` pulls a sparse copy of `Randdalf/fplcache` into `vendor/fplcache/` with compressed snapshots under `vendor/fplcache/cache/`.
2. On API startup:
   - Scan snapshots and build a GW index per season (`gw -> snapshot path`) using `events[].deadline_time`.
   - Load the latest snapshot to build a lightweight player directory used by the search endpoint.
3. `GET /players/search?q=...` searches the in-memory directory and returns matching `player_code`s.
4. `GET /players/{player_code}/timeseries` reads the preselected per-GW snapshots, extracts `total_points`, computes per-GW deltas, and returns the series (responses cached in-memory).

## Which stat I chose and why

I chose `total_points` as the single player stat for the time series because it’s the most direct, universally interpretable performance metric in FPL, and it’s available for every player in every bootstrap-static snapshot. It’s also cumulative, which makes it ideal for this dataset: by sampling one snapshot per gameweek and taking a simple difference between consecutive gameweeks, we can derive a clean per-GW “points gained” (`delta`) while keeping the underlying series stable and easy to validate.

## How I constructed the time series
I keep it simple: one snapshot per gameweek, then basic maths.

- I scan `vendor/fplcache/cache/YYYY/MM/DD/HHMM.json.xz`.
- For each season (2023–24, 2024–25), I pick the last snapshot before the next GW deadline.
- This way I capture the latest status for each gameweek.
- For each chosen snapshot I grab the player by `code` and read `total_points` (cumulative).
- Per GW: delta = current - previous (first GW: delta = value; if missing: delta = None).

Tiny example:
- GW1: value 7 → delta 7
- GW2: value 10 → delta 3

## Assumptions & Ambiguities
- Snapshots vs gameweeks: point-in-time `bootstrap-static`, not final GW tables.
- GW boundaries:
  - start = deadline(GW i)
  - end = deadline(GW i+1)
  - GW38 ends at season end
- Snapshot selection:
  - pick latest snapshot within GW window
- Cross-season identity:
  - track by `player_code` (stable)
  - `id` may change; `web_name` isn’t unique
- Storage choice: 
    - I compute the time series on-demand and cache results in-memory, rather than precomputing into DuckDB/SQLite, to keep the solution lightweight and aligned with the 2-hour scope
    - this also makes caching a meaningful optimisation for repeated queries.

## What I'd improve with more time

With more time, I’d take this further in a few practical directions:
- Precompute + DuckDB/SQLite: one table {season, gw, player_code, value, delta}; API becomes simple SQL reads; no repeated .xz/JSON.
- More tests: unit tests for snapshot selection; delta correctness (missing values, season boundaries).
- API tests: smoke tests for 200/404; tiny integration test that boots the app and exercises the happy path.
- Observability: structured logs, request timing, cache hit/miss metrics.
- If this were exposed publicly, I’d add authentication and basic rate limiting (429 Too Many Requests) to protect the heavier endpoints and prevent abuse.
