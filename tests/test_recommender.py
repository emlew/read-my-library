"""Unit tests for the recommendation rules, using a tiny dataset we control."""

import copy

import pytest

from mood_matcher.books import BOOKS
from mood_matcher.recommender import recommend


def make_book(id, title, moods, genres, hours):
    return {
        "id": id,
        "title": title,
        "author": "Test Author",
        "description": "Test description.",
        "moods": moods,
        "genres": genres,
        "reading_hours": hours,
    }


@pytest.fixture
def books():
    return [
        make_book(1, "Mood and Genre", ["cozy"], ["fantasy"], 5),
        make_book(2, "Mood Only", ["cozy"], ["mystery"], 5),
        make_book(3, "Genre Only", ["suspenseful"], ["fantasy"], 5),
        make_book(4, "No Match", ["suspenseful"], ["mystery"], 5),
        make_book(5, "Very Long Cozy Fantasy", ["cozy"], ["fantasy"], 20),
    ]


def titles(results):
    return [r["book"]["title"] for r in results]


def test_ranks_mood_and_genre_above_mood_above_genre(books):
    results = recommend(books, "cozy", "fantasy", "weekend")
    assert titles(results) == ["Mood and Genre", "Mood Only", "Genre Only"]
    assert [r["score"] for r in results] == [3, 2, 1]


def test_excludes_books_with_no_match(books):
    results = recommend(books, "cozy", "fantasy", "week")
    assert "No Match" not in titles(results)


def test_excludes_books_that_do_not_fit_time(books):
    results = recommend(books, "cozy", "fantasy", "weekend")
    assert "Very Long Cozy Fantasy" not in titles(results)


def test_week_has_no_time_limit(books):
    results = recommend(books, "cozy", "fantasy", "week")
    assert "Very Long Cozy Fantasy" in titles(results)


def test_book_exactly_at_time_limit_is_included():
    books = [make_book(1, "Three Hours", ["cozy"], ["fantasy"], 3)]
    assert titles(recommend(books, "cozy", "fantasy", "evening")) == ["Three Hours"]


def test_ties_break_by_shorter_reading_time_then_title():
    books = [
        make_book(1, "Zebra", ["cozy"], ["fantasy"], 4),
        make_book(2, "Long", ["cozy"], ["fantasy"], 8),
        make_book(3, "Apple", ["cozy"], ["fantasy"], 4),
    ]
    assert titles(recommend(books, "cozy", "fantasy", "weekend")) == ["Apple", "Zebra", "Long"]


def test_rationale_names_what_matched(books):
    results = recommend(books, "cozy", "fantasy", "weekend")
    by_title = {r["book"]["title"]: r["rationale"] for r in results}

    assert by_title["Mood and Genre"] == (
        "Matches your cozy mood and your fantasy genre. About 5 hours, fits your weekend."
    )
    assert by_title["Mood Only"].startswith("Matches your cozy mood.")
    assert by_title["Genre Only"].startswith("Matches your fantasy genre.")


def test_returns_empty_list_when_nothing_matches(books):
    assert recommend(books, "curious", "nonfiction", "week") == []


@pytest.mark.parametrize(
    "mood, genre, time",
    [
        ("grumpy", "fantasy", "weekend"),
        ("cozy", "cookbook", "weekend"),
        ("cozy", "fantasy", "month"),
        ("", "fantasy", "weekend"),
        ("Cozy", "fantasy", "weekend"),  # matching is case-sensitive
    ],
)
def test_invalid_preferences_raise_value_error(books, mood, genre, time):
    with pytest.raises(ValueError):
        recommend(books, mood, genre, time)


def test_does_not_modify_input(books):
    original = copy.deepcopy(books)
    recommend(books, "cozy", "fantasy", "weekend")
    assert books == original


def test_real_dataset_results_follow_the_rules():
    # Smoke test with the real catalog. Checks the rules, not specific titles,
    # so editing the catalog doesn't break it.
    results = recommend(BOOKS, "cozy", "fantasy", "weekend")
    assert results
    assert all(r["book"]["reading_hours"] <= 10 for r in results)
    assert all(r["score"] > 0 for r in results)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
