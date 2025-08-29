# Test Player Data Fixtures

This directory contains JSON fixtures used exclusively for continuous integration tests.

The `test_players.json` fixture seeds the SQLite database with a minimal set of
player records so the Django homepage can render without reaching out to the
external NBA API. Only the fields required for template rendering are included
and the data is intentionally lightweight.

These fixtures should not be used for production or development databases.
