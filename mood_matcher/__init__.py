"""Reading Mood Matcher: a small Flask app that recommends books by mood."""
import os
from pathlib import Path

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from mood_matcher import db
from mood_matcher.routes import bp

# Static files live in public/static so Vercel's CDN can serve them;
# locally, Flask serves the same folder at the same /static/... URLs.
STATIC_FOLDER = Path(__file__).parent.parent / "public" / "static"

def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    return jsonify(error=e.description), e.code


def create_app(test_config: dict | None = None) -> Flask:
    """App factory: build and configure a new Flask app.

    Tests call this with their own config so each test gets a fresh app.
    """
    app = Flask(__name__, static_folder=STATIC_FOLDER)
    if os.environ.get("VERCEL"):
        # Vercel sets VERCEL=1. Its file system is read-only except /tmp,
        # which is temporary, so the reading list resets now and then.
        app.config["DATABASE"] = "/tmp/mood_matcher.sqlite"
    else:
        # instance/ holds local files that aren't code, like the database.
        app.config["DATABASE"] = str(Path(app.instance_path) / "mood_matcher.sqlite")
    if test_config:
        app.config.update(test_config)

    app.errorhandler(HTTPException)(handle_http_exception)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    app.register_blueprint(bp)
    return app
