"""Reading-list API tests. Each test gets its own empty temporary database."""

import pytest

from mood_matcher import create_app
from mood_matcher.books import BOOKS_BY_ID

URL = "/api/reading-list"


def saved_ids(client):
    return [item["book"]["id"] for item in client.get(URL).get_json()["items"]]


def test_starts_empty(client):
    response = client.get(URL)
    assert response.status_code == 200
    assert response.get_json() == {"items": [], "count": 0}


def test_add_book_returns_201_and_appears_in_list(client):
    response = client.post(URL, json={"book_id": 3})

    assert response.status_code == 201
    assert response.get_json()["book"] == BOOKS_BY_ID[3]

    items = client.get(URL).get_json()["items"]
    assert [item["book"]["id"] for item in items] == [3]
    assert items[0]["added_at"]  # set by the database default


def test_list_keeps_insertion_order(client):
    for book_id in (7, 2, 15):
        client.post(URL, json={"book_id": book_id})
    assert saved_ids(client) == [7, 2, 15]


def test_duplicate_add_returns_409(client):
    client.post(URL, json={"book_id": 3})
    response = client.post(URL, json={"book_id": 3})

    assert response.status_code == 409
    assert "already" in response.get_json()["error"]
    assert saved_ids(client) == [3]


def test_unknown_book_returns_404(client):
    response = client.post(URL, json={"book_id": 999})
    assert response.status_code == 404
    assert saved_ids(client) == []


@pytest.mark.parametrize(
    "body",
    [
        {},                    # missing book_id
        {"book_id": "3"},      # string, not int
        {"book_id": 3.0},      # float
        {"book_id": True},     # bool is technically an int in Python
        {"book_id": None},
        [3],                   # JSON, but not an object
    ],
)
def test_invalid_json_body_returns_400(client, body):
    response = client.post(URL, json=body)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_non_json_body_returns_400(client):
    response = client.post(URL, data="book_id=3")  # form data, not JSON
    assert response.status_code == 400


def test_delete_returns_204_and_removes_book(client):
    client.post(URL, json={"book_id": 3})
    client.post(URL, json={"book_id": 5})

    response = client.delete(f"{URL}/3")

    assert response.status_code == 204
    assert response.data == b""
    assert saved_ids(client) == [5]


def test_delete_book_not_in_list_returns_404(client):
    response = client.delete(f"{URL}/3")
    assert response.status_code == 404


def test_can_re_add_after_removing(client):
    client.post(URL, json={"book_id": 3})
    client.delete(f"{URL}/3")
    assert client.post(URL, json={"book_id": 3}).status_code == 201


def test_data_persists_across_app_restarts(db_path):
    # Two separate app instances sharing one database file simulate a restart.
    first = create_app({"TESTING": True, "DATABASE": db_path}).test_client()
    first.post(URL, json={"book_id": 3})

    second = create_app({"TESTING": True, "DATABASE": db_path}).test_client()
    assert saved_ids(second) == [3]
