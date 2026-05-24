# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShotGeek is a Django web application providing NBA player stats, career comparisons, shot charts, game logs, scores, and news. It fetches live data from the NBA API (`nba_api` package) and scrapes The Ringer for news.

## Commands

### Local development (SQLite)
```sh
source venv/bin/activate   # or: source myenv/bin/activate
# Set DEVELOPMENT=True in .env
python manage.py migrate
python manage.py runserver
```

### Docker (PostgreSQL)
```sh
docker compose up --build
docker compose exec web python manage.py migrate
```

### Run tests
```sh
pytest                                          # all tests
pytest NoseBleedSeat/tests/test_views.py        # single file
pytest NoseBleedSeat/tests/ -k "test_home"      # single test
```

Tests use `DJANGO_SETTINGS_MODULE=core.settings.development`, `--reuse-db`, `--no-migrations`, and `-x` (stop on first failure).

Test files:
- `NoseBleedSeat/tests/test_views.py` — homepage and HTMX view smoke tests
- `NoseBleedSeat/tests/test_archive.py` — `_build_archive_graph` unit tests (uses DB fixtures, no external calls)
- `NoseBleedSeat/tests/test_functions.py` — function-level tests (some hit the NBA API)
- `nba_stats/tests/test_import_box_scores.py` — `import_box_scores` command tests (mocks kagglehub)

Note: `test_functions.py::TestSearchTeamByName` references the legacy `insert_teams` command and `EasternConferenceTeams`/`WesternConferenceTeams` models — those tests should be removed or updated.

### Seed data (run on each deploy)
```sh
python manage.py populate_nba_data     # populate NBATeam and Player tables from static NBA API data (no HTTP calls)
python manage.py populate_player_data  # populate PlayerBio and Player.team via BallDontLie API (rate-limited, slow)
python manage.py import_box_scores     # download Kaggle CSV and populate SeasonStat, CareerStat, PlayerStats
```

`import_box_scores` is also scheduled to run daily via Heroku Scheduler to pick up new game data.

Note: `populate_player_data` only needs to re-run on deploy if player bios or team assignments have changed.

## Architecture

### Apps and responsibilities

| App | Responsibility |
|---|---|
| `NoseBleedSeat` | Homepage, player search/autocomplete, home-page player comparison widget, league leaders, word of the day |
| `nba_stats` | Player detail pages, career/season/rankings tables, graphs, game logs, shot charts, player comparison flow |
| `nba_teams` | Team pages, roster, history, retired numbers, standings |
| `nba_today` | Today's scores and box scores |
| `nba_news` | News feed scraped from The Ringer |
| `core` | Django project settings, root URL conf |

### Settings split

`core/settings/` has three files:
- `base.py` — shared settings, reads `.env` for `SECRET_KEY` and SmartProxy credentials
- `development.py` — `DEBUG=True`, SQLite locally, PostgreSQL when `DOCKER_ENV=True`
- `production.py` — production settings

`pytest.ini` points at `core.settings.development`.

### NBA API access pattern

All NBA API calls follow the same pattern across `functions.py` files:
- If `SMARTPROXY_USERNAME` / `SMARTPROXY_PASSWORD` env vars are set, calls go through SmartProxy (production).
- Otherwise, calls use a custom `NBA_HEADERS` dict to bypass rate limiting (development).

This `create_proxy_url()` helper exists in multiple `functions.py` files and in management commands.

### Session-based caching

Views avoid redundant API calls by storing player data in Django sessions:
- `player_page_info` — headshot, bio, full career stats dict (used across player detail sub-views)
- `player_compare_info` / `comparison_info` — player pair data for comparison flow
- `player1` / `player2` — names of the home-page comparison widget players (persisted across visits)

### Key models (`nba_stats`)

- `Player` — NBA player with `player_id` (PK), `bdl_id` (Ball Don't Lie), `image_url`, FK to `NBATeam`; `first_name`/`last_name` are generated/persisted DB fields
- `PlayerBio` — OneToOne with `Player`, biographical info
- `PlayerStats` — career per-game averages (PTS/REB/AST/BLK/STL), used for home-page radar chart
- `SeasonStat` / `CareerStat` — per-season and career totals populated by `import_box_scores` from Kaggle data
- `SeasonHigh`, `SeasonRanking`, `CareerAwards`, `LeagueLeaders` — supporting data

`NBATeam` (in `nba_teams`) is the authoritative team model. The older `EasternConferenceTeams` / `WesternConferenceTeams` models are legacy.

### Kaggle data pipeline

Historical box score data comes from the Kaggle dataset `eoinamoore/historical-nba-data-and-player-box-scores` (`PlayerStatistics.csv`). The `import_box_scores` management command:
1. Downloads the CSV via `kagglehub` (uses local cache if available)
2. Groups game rows by player + season + game type
3. Upserts `SeasonStat` (season totals), `CareerStat` (career totals), and `PlayerStats` (career per-game averages for Regular Season)

Views in `NoseBleedSeat` query `SeasonStat` and `PlayerStats` directly — no pandas or in-memory DataFrames at request time.

Requires `KAGGLE_USERNAME` and `KAGGLE_KEY` env vars in production.

### HTMX partials

Several views render into `templates/partials/` for HTMX lazy-loading:
- `player_awards` — triggered from player detail page
- `player_bio` — triggered from player detail page
- `league_leaders` — triggered from homepage
- `career_awards_player1/2` — triggered from homepage comparison widget
- `player_auto_complete` — live search suggestions

### Per-game stat computation

PPG, RPG, APG, BLKPG, STLPG are not stored — they are computed in views by dividing career/season totals by `GP`. This pattern repeats in `nba_stats/views.py` across `player_details`, `regular_season`, `post_season`, and `compare_profiles`.

### Static files

WhiteNoise serves static files. `STATIC_ROOT = staticfiles/`; run `python manage.py collectstatic` before deploying.
