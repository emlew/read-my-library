"""Reading-list queries. Every query uses ? placeholders, never string formatting."""

import sqlite3


def list_saved(db: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.execute("SELECT book_id, added_at FROM reading_list ORDER BY id").fetchall()


def add_book(db: sqlite3.Connection, book_id: int) -> bool:
    """Save a book. Return False if it was already saved."""
    try:
        db.execute("INSERT INTO reading_list (book_id) VALUES (?)", (book_id,))
        db.commit()
    except sqlite3.IntegrityError:  # UNIQUE constraint on book_id
        return False
    return True


def remove_book(db: sqlite3.Connection, book_id: int) -> bool:
    """Remove a book. Return False if it wasn't in the list."""
    cursor = db.execute("DELETE FROM reading_list WHERE book_id = ?", (book_id,))
    db.commit()
    return cursor.rowcount > 0
