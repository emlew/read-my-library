"""Shared pytest fixtures. pytest loads this file automatically."""

import pytest

from mood_matcher import create_app


@pytest.fixture
def db_path(tmp_path):
    # tmp_path is a built-in fixture: a fresh temporary folder for each test.
    return str(tmp_path / "test.sqlite")


@pytest.fixture
def app(db_path):
    return create_app({"TESTING": True, "DATABASE": db_path})


@pytest.fixture
def client(app):
    # A fake browser: sends requests to the app without running a server.
    return app.test_client()
