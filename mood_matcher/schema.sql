-- IF NOT EXISTS makes this safe to run on every startup without losing data.
CREATE TABLE IF NOT EXISTS reading_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,      -- insertion order
    book_id INTEGER NOT NULL UNIQUE,           -- UNIQUE blocks duplicate saves
    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
