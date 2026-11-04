"""Entry point for Vercel, which looks for a Flask object named `app` in app.py."""

from mood_matcher import create_app

app = create_app()
