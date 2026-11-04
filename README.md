# Reading Mood Matcher

A small Flask web app that recommends books based on your mood, preferred genre, and how much time you have to read. You can browse a curated catalog of 100 books, get ranked recommendations with an explanation for each one, and keep a reading list that persists across restarts.

Built with Python, Flask, SQLite, and vanilla JavaScript. No external APIs and no build step.

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # Flask + pytest
```

`requirements.txt` lists only what the app needs at runtime (Flask); that is what Vercel installs.

## Run

```bash
flask --app mood_matcher run --debug
```

Open http://127.0.0.1:5000. The SQLite database is created automatically at `instance/mood_matcher.sqlite` on first run. Delete that file to reset the reading list.

## Test

```bash
pytest          # all tests
pytest -v       # one line per test
```

Tests use a fresh temporary database each time, so they never touch your real reading list.

## Deploy (Vercel)

The app deploys to Vercel's free Hobby plan with no configuration file:

1. Sign in at [vercel.com](https://vercel.com) with GitHub.
2. **Add New → Project**, import this repository, and click **Deploy**. Vercel detects Flask and finds `app` in `app.py`.
3. Every push to the main branch redeploys automatically; other branches get preview URLs.

How it runs there:

- The Flask app becomes a single serverless function that starts on demand.
- Files in `public/` (the JS and CSS) are served directly from Vercel's CDN at the same `/static/...` URLs Flask uses locally.
- **The reading list is temporary on Vercel.** Its file system is read-only apart from `/tmp`, so the app stores SQLite there when the `VERCEL` environment variable is set. `/tmp` is cleared when an instance shuts down and isn't shared between instances, so saved books disappear from time to time. Recommendations and browsing are unaffected. Persistent storage would need a hosted database such as Postgres.

## Project structure

```
app.py                # entry point: app = create_app() (used by Vercel)
public/static/        # app.js, style.css (served by Vercel's CDN in production)
mood_matcher/
├── __init__.py       # create_app(): the app factory
├── books.py          # curated catalog + allowed moods, genres, and time options
├── recommender.py    # recommendation rules (pure Python, no Flask)
├── routes.py         # page + JSON API routes (HTTP only)
├── db.py             # one SQLite connection per request; creates the table on startup
├── reading_list.py   # the reading-list SQL queries
├── schema.sql        # reading_list table definition
└── templates/index.html
tests/
├── conftest.py               # app + client fixtures, temp database
├── test_books.py             # catalog integrity (valid tags, unique ids, coverage)
├── test_recommender.py       # scoring, filtering, sorting, validation
├── test_api.py               # recommendations + books endpoints, page render
└── test_reading_list_api.py  # save / list / remove, persistence
```

## How recommendations work

Given a **mood**, a **genre**, and an **available time** (evening ≤ 3h, weekend ≤ 10h, week = any length):

1. **Filter on time.** Drop any book whose estimated reading time is longer than the time available.
2. **Score.** +2 if the book has the chosen mood, +1 if it has the chosen genre. Mood weighs more because it is the main idea of the app.
3. **Drop zero scores**, then sort by score (highest first), reading time (shortest first), then title.
4. **Explain.** Each result gets a short reason built from what matched, e.g. *"Matches your cozy mood and your fantasy genre. About 5 hours, fits your weekend."*

An empty result is a valid answer (200 with an empty list), and the UI suggests trying a different combination.

## API

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/api/books` | 200, whole catalog A to Z | — |
| GET | `/api/recommendations?mood=&genre=&time=` | 200, ranked results (may be empty) | 400 missing or invalid parameter |
| GET | `/api/reading-list` | 200, saved books, oldest first | — |
| POST | `/api/reading-list` with body `{"book_id": 3}` | 201 | 400 invalid body, 404 unknown book, 409 already saved |
| DELETE | `/api/reading-list/<book_id>` | 204 | 404 not in list |

Errors always return JSON in the form `{"error": "message"}`.

## Key technical decisions

- **The recommender is separate from Flask.** `recommend()` takes a list of books and returns a list of results. It can be tested with a tiny hand-built dataset, and routes only translate between HTTP and Python.
- **The catalog lives in Python; only the reading list is in SQLite.** The books are fixed data that ships with the code. The reading list is the only data users change, so it is the only data that needs a database.
- **Built-in `sqlite3` instead of an ORM.** Plain SQL with `?` placeholders keeps queries visible and prevents SQL injection without an extra dependency.
- **The database prevents duplicates.** `book_id` is `UNIQUE`, and the insert catches `IntegrityError`. Checking first and then inserting could let two quick clicks both succeed.
- **Validation happens in two layers.** The route checks that parameters are present (an HTTP concern). The recommender checks that values are allowed (a domain rule) and raises `ValueError`, which the route turns into a 400. Dropdowns are also `required` in the browser, but that is only a convenience; the server is the real check.
- **One vocabulary for everything.** `MOODS`, `GENRES`, and `TIME_OPTIONS` in `books.py` fill the dropdowns, drive validation, and are checked against the catalog by tests, so they cannot drift apart.
- **An app factory (`create_app`).** Each test builds its own app pointed at a temporary database.
- **Safe rendering in the browser.** Book data is inserted with `textContent`, never `innerHTML`, so catalog text cannot inject HTML or scripts.

## Limitations and next steps

- **The reading list doesn't persist on Vercel** (see Deploy). It does persist when run locally.
- **Single shared reading list.** There are no user accounts, so everyone using the app shares one list. Adding users would mean a `user_id` column and authentication.
- **Exact tag matching.** A book either has a mood or it doesn't. Weighted tags or similarity scoring would give finer rankings.
- **Linear scan.** Each request scores every book. That is instant for 100 books. For thousands of books, the catalog would move into SQLite with indexed tag tables, filtering on time and tags in SQL.
- **Estimated reading times** are approximate (about 45 pages per hour).
- **The frontend has no automated tests.** The API it calls is covered; browser tests (e.g. Playwright) would be the next layer.
