"""HTTP routes. These handle requests and responses; the matching rules live in recommender.py."""

from flask import Blueprint, jsonify, render_template, request

from mood_matcher import reading_list
from mood_matcher.books import BOOKS, BOOKS_BY_ID, GENRES, MOODS, TIME_OPTIONS
from mood_matcher.db import get_db
from mood_matcher.recommender import recommend

bp = Blueprint("main", __name__)

REQUIRED_PARAMS = ("mood", "genre", "time")


@bp.get("/")
def index():
    # Dropdown options come from the same constants the API validates against.
    return render_template("index.html", moods=MOODS, genres=GENRES, time_options=TIME_OPTIONS)


@bp.get("/api/books")
def get_books():
    books = sorted(BOOKS, key=lambda book: book["title"].lower())
    return jsonify(books=books, count=len(books))


@bp.get("/api/recommendations")
def get_recommendations():
    # request.args holds the query string, e.g. ?mood=cozy&genre=fantasy&time=weekend
    missing = [name for name in REQUIRED_PARAMS if not request.args.get(name)]
    if missing:
        return jsonify(error=f"Missing required parameter(s): {', '.join(missing)}"), 400

    try:
        results = recommend(
            BOOKS,
            mood=request.args["mood"],
            genre=request.args["genre"],
            time=request.args["time"],
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400

    return jsonify(results=results, count=len(results))


@bp.get("/api/reading-list")
def get_reading_list():
    items = [
        {"book": BOOKS_BY_ID[row["book_id"]], "added_at": row["added_at"]}
        for row in reading_list.list_saved(get_db())
        if row["book_id"] in BOOKS_BY_ID  # skip books removed from the catalog
    ]
    return jsonify(items=items, count=len(items))


@bp.post("/api/reading-list")
def add_to_reading_list():
    # silent=True returns None instead of raising when the body isn't valid JSON.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Request body must be a JSON object like {\"book_id\": 1}"), 400

    book_id = data.get("book_id")
    # bool is a subclass of int in Python, so True would otherwise pass as 1.
    if not isinstance(book_id, int) or isinstance(book_id, bool):
        return jsonify(error="book_id must be an integer"), 400

    book = BOOKS_BY_ID.get(book_id)
    if book is None:
        return jsonify(error=f"No book with id {book_id}"), 404

    if not reading_list.add_book(get_db(), book_id):
        return jsonify(error=f"{book['title']} is already in your reading list"), 409

    return jsonify(book=book), 201


@bp.delete("/api/reading-list/<int:book_id>")
def remove_from_reading_list(book_id: int):
    book = BOOKS_BY_ID.get(book_id)
    if book is None:
        return jsonify(error=f"No book with id {book_id}"), 404

    if not reading_list.remove_book(get_db(), book_id):
        return jsonify(error=f"Book {book_id} is not in your reading list"), 404
    return "", 204  # success, no response body
