"""Recommendation logic. Pure Python: no Flask, no database.

Rules:
1. Drop books that don't fit the reader's available time.
2. Score the rest: +2 if the mood matches, +1 if the genre matches.
3. Drop books that score 0, then sort by score (high first),
   reading time (short first), and title.
"""

from mood_matcher.books import GENRES, MOODS, TIME_OPTIONS

MOOD_WEIGHT = 2
GENRE_WEIGHT = 1


def validate_preferences(mood: str, genre: str, time: str) -> None:
    """Raise ValueError if any preference isn't an allowed value."""
    if mood not in MOODS:
        raise ValueError(f"Unknown mood: {mood!r}")
    if genre not in GENRES:
        raise ValueError(f"Unknown genre: {genre!r}")
    if time not in TIME_OPTIONS:
        raise ValueError(f"Unknown time: {time!r}")


def fits_time(book: dict, time: str) -> bool:
    max_hours = TIME_OPTIONS[time]
    return max_hours is None or book["reading_hours"] <= max_hours


def score_book(book: dict, mood: str, genre: str) -> int:
    score = 0
    if mood in book["moods"]:
        score += MOOD_WEIGHT
    if genre in book["genres"]:
        score += GENRE_WEIGHT
    return score


def build_rationale(book: dict, mood: str, genre: str, time: str) -> str:
    matches = []
    if mood in book["moods"]:
        matches.append(f"your {mood} mood")
    if genre in book["genres"]:
        matches.append(f"your {genre} genre")

    hours = book["reading_hours"]
    hour_word = "hour" if hours == 1 else "hours"
    return f"Matches {' and '.join(matches)}. About {hours} {hour_word}, fits your {time}."


def recommend(books: list[dict], mood: str, genre: str, time: str) -> list[dict]:
    """Return matching books, best first, each with a score and rationale."""
    validate_preferences(mood, genre, time)

    results = []
    for book in books:
        if not fits_time(book, time):
            continue
        score = score_book(book, mood, genre)
        if score == 0:
            continue
        results.append({
            "book": book,
            "score": score,
            "rationale": build_rationale(book, mood, genre, time),
        })

    # Sort key is a tuple: Python compares it item by item.
    # -score puts the highest score first while the rest sort ascending.
    results.sort(key=lambda r: (-r["score"], r["book"]["reading_hours"], r["book"]["title"]))
    return results
