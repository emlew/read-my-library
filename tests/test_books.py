"""Data-integrity tests: catch typos and gaps in the curated dataset early."""

from mood_matcher.books import BOOKS, MOODS, TIME_OPTIONS, GENRES

REQUIRED_KEYS = {"id", "title", "author", "description", "moods", "genres", "reading_hours"}


def test_every_book_has_required_fields():
    for book in BOOKS:
        assert set(book) == REQUIRED_KEYS, book.get("title")


def test_book_ids_are_unique():
    ids = [book["id"] for book in BOOKS]
    assert len(ids) == len(set(ids))


def test_books_only_use_allowed_moods_and_genres():
    for book in BOOKS:
        assert set(book["moods"]) <= set(MOODS), book["title"]
        assert set(book["genres"]) <= set(GENRES), book["title"]


def test_reading_hours_are_positive_integers():
    for book in BOOKS:
        assert isinstance(book["reading_hours"], int) and book["reading_hours"] > 0


def test_every_option_matches_at_least_one_book():
    # Otherwise the UI would offer a choice that can never return results.
    used_moods = {mood for book in BOOKS for mood in book["moods"]}
    used_genres = {genre for book in BOOKS for genre in book["genres"]}
    assert used_moods == set(MOODS)
    assert used_genres == set(GENRES)


def test_shortest_time_option_has_books():
    evening_limit = TIME_OPTIONS["evening"]
    assert any(book["reading_hours"] <= evening_limit for book in BOOKS)
