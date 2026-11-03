"""SQLite connection handling: one connection per request, closed automatically."""

import sqlite3
from pathlib import Path

from flask import Flask, current_app, g

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db() -> sqlite3.Connection:
    # g is per-request storage, so repeated calls in one request reuse a connection.
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts: row["book_id"]
    return g.db


def close_db(exception: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    get_db().executescript(SCHEMA_PATH.read_text())


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)  # runs at the end of every request
    with app.app_context():
        init_db()
