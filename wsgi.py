"""WSGI entrypoint for Gunicorn.
Exposes `server` (the underlying Flask app) for gunicorn to run.
"""

from app import app as dash_app  # dash.Dash instance
# Import the layout/callbacks module so it sets dash_app.layout and registers callbacks
import dash_layout_main_run  # noqa: F401

# Gunicorn expects a WSGI callable; use the underlying Flask server
server = dash_app.server

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8055, debug=False)
