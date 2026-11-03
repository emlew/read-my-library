"""API tests: check HTTP status codes and JSON shape, not the ranking rules."""

import pytest

from mood_matcher.books import BOOKS, GENRES, MOODS, TIME_OPTIONS

URL = "/api/recommendations"
VALID = {"mood": "cozy", "genre": "fantasy", "time": "weekend"}


def test_valid_request_returns_ranked_results(client):
    response = client.get(URL, query_string=VALID)

    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["count"] == len(data["results"]) > 0

    first = data["results"][0]
    assert set(first) == {"book", "score", "rationale"}
    scores = [r["score"] for r in data["results"]]
    assert scores == sorted(scores, reverse=True)


def test_no_matches_returns_200_with_empty_list(client):
    # No nostalgic or romance book fits in an evening.
    params = {"mood": "nostalgic", "genre": "romance", "time": "evening"}
    response = client.get(URL, query_string=params)

    assert response.status_code == 200
    assert response.get_json() == {"results": [], "count": 0}


@pytest.mark.parametrize("missing", ["mood", "genre", "time"])
def test_missing_parameter_returns_400(client, missing):
    params = {k: v for k, v in VALID.items() if k != missing}
    response = client.get(URL, query_string=params)

    assert response.status_code == 400
    assert missing in response.get_json()["error"]


def test_missing_all_parameters_lists_each_one(client):
    response = client.get(URL)

    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing required parameter(s): mood, genre, time"


def test_empty_parameter_counts_as_missing(client):
    response = client.get(URL, query_string={**VALID, "mood": ""})

    assert response.status_code == 400
    assert "mood" in response.get_json()["error"]


@pytest.mark.parametrize(
    "field, bad_value",
    [("mood", "grumpy"), ("genre", "cookbook"), ("time", "month")],
)
def test_invalid_value_returns_400(client, field, bad_value):
    response = client.get(URL, query_string={**VALID, field: bad_value})

    assert response.status_code == 400
    assert bad_value in response.get_json()["error"]


def test_post_is_not_allowed(client):
    response = client.post(URL, json=VALID)
    assert response.status_code == 405


def test_index_page_renders_every_option(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for value in (*MOODS, *GENRES, *TIME_OPTIONS):
        assert f'value="{value}"' in html


def test_books_endpoint_returns_whole_catalog_sorted_by_title(client):
    response = client.get("/api/books")

    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == len(BOOKS)
    titles = [book["title"].lower() for book in data["books"]]
    assert titles == sorted(titles)
