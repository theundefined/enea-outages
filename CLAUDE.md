# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`enea-outages` is a small Python library + CLI that scrapes the Enea Operator website
(`wylaczenia.operator.enea.pl`) for planned and unplanned power outage notices. There is no
official API — the client fetches HTML and parses it with BeautifulSoup, including
Polish-language date strings (e.g. `"8 grudnia 2025 r. w godz. 08:00 - 16:00"`).

## Commands

The project is managed with `hatch`, but a `venv/` with dev dependencies already exists at the
repo root, so `pytest`/`ruff`/`mypy` can also be invoked directly.

```bash
# Setup (hatch-managed env)
hatch env create dev

# Lint
hatch run dev:lint          # ruff check .

# Test with coverage
hatch run dev:cov           # pytest --cov-report=term-missing --cov-report=xml --cov=src

# Plain test run
hatch run dev:test          # pytest

# Run a single test (via venv, faster iteration)
venv/bin/pytest tests/test_client.py::test_parse_planned_date_format

# Type check
venv/bin/mypy src
```

CI (`.github/workflows/ci.yml`) runs `hatch run dev:lint` then `hatch run dev:cov` on Python
3.10–3.14 for every push/PR to `main`. Match that before considering work done.

## Architecture

Everything lives in `src/enea_outages/` as three files:

- **`models.py`** — `OutageType` enum (`PLANNED = "unpl"`, `UNPLANNED = "awarie"`, values are the
  site's `page` query param) and the `Outage` dataclass (`region`, `description`, `start_time`,
  `end_time`; times are `datetime | None`).
- **`client.py`** — `EneaOutagesClient`, the only client (an async variant existed previously and
  was removed to keep the library simple — do not reintroduce it without being asked).
  - Holds a persistent `httpx.Client` (`self._client`, default `timeout=DEFAULT_TIMEOUT` = 10s)
    created in `__init__` for connection reuse. Supports `with EneaOutagesClient() as client:` /
    `client.close()` to release the pool; the CLI uses the context-manager form.
  - `_fetch_raw_html(region, outage_type)` calls `self._client.get(...)` against
    `BASE_URL = "https://wylaczenia.operator.enea.pl/index.php"` with `page`/`oddzial` params.
  - `_parse_outage_block(block)` pulls region/description/date text out of one
    `<div class="unpl block info">` and builds an `Outage`.
  - `_parse_date_formats(date_info)` regex-parses two distinct Polish date formats — one for
    planned outages (`"... w godz. HH:MM - HH:MM"`, yields both start and end time) and one for
    unplanned outages (`"... do godziny HH:MM"`, yields only an end time, start is `None`). Month
    names are resolved via `MONTH_MAP` (Polish genitive month names → int). Unrecognized formats
    raise `ValueError`.
  - `get_outages_for_region()` fetches + parses all outage blocks on a page; parse failures for
    individual blocks are caught and logged via `logging.getLogger(__name__)` at `WARNING` (not
    printed — this is a library, so callers control visibility by configuring logging).
  - `get_outages_for_address()` is a client-side substring filter (case-insensitive) over
    `get_outages_for_region()` results — it does not hit a different endpoint.
  - `get_available_regions()` scrapes the `<select id="oddzial">` options from the planned-outages
    page (region lists are identical across page types, so one fixed request is used).
- **`cli.py`** — `argparse`-based CLI (`enea-outages` console script, entry point defined in
  `pyproject.toml`), a thin wrapper around `EneaOutagesClient`. Errors are caught broadly and
  printed rather than raised, since this is a terminal-facing tool.

`__init__.py` re-exports `EneaOutagesClient` and `Outage`, and derives `__version__` via
`importlib.metadata` (falls back to `"0.0.0-dev"` when not installed).

The package ships a `py.typed` marker (PEP 561) so downstream type checkers pick up its type
hints — keep it when touching packaging config. There is no `requirements.txt`; `pyproject.toml`
is the single source of truth for dependencies.

### Testing approach

`tests/test_client.py` uses `pytest-httpx` to mock HTTP responses and static HTML fixtures
(`SAMPLE_UNPLANNED_BLOCK`, `SAMPLE_PLANNED_BLOCK`, `SAMPLE_HTML_PAGE_WITH_REGIONS`) rather than
hitting the live site. When changing HTML parsing logic, update these fixtures to match the real
site's markup structure if it has changed, and add a fixture for any new date format encountered.

### Versioning and releases

Version is **dynamic**, derived from git tags via `hatch-vcs` — it is never hand-edited in
`pyproject.toml`. Releases are cut with `./release.sh [major|minor|patch|vX.Y.Z]`, which requires
a clean working tree on `main`, tags, and pushes; the tag push triggers the `publish` job in CI,
which builds with `hatch build` and publishes to PyPI via Trusted Publishing (OIDC, no stored
token).

### Note on `PROJECT_STATE.md`

This file predates the removal of `AsyncEneaOutagesClient` and still references it — treat
`src/enea_outages/client.py` as the source of truth over that document.
