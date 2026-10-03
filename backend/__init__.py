from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from .db import Database
from .routes import api
from .storage import LocalStorageAdapter

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(PROJECT_ROOT / "frontend" / "dist"),
        static_url_path="",
    )
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dietly-local-demo-secret-change-me"),
        DATABASE_PATH=os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "dietplanner.sqlite3")),
        UPLOAD_DIR=os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "data" / "uploads")),
        MAX_CONTENT_LENGTH=4 * 1024 * 1024,
        TESTING=False,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    database = Database(app.config["DATABASE_PATH"])
    database.init_db()
    app.extensions["db"] = database
    app.extensions["storage"] = LocalStorageAdapter(app.config["UPLOAD_DIR"])

    app.config.update(
        SESSION_COOKIE_NAME="dietly_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
    )
    app.register_blueprint(api, url_prefix="/api")

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": "File or request is too large."}), 413

    @app.get("/manus-routes.json")
    def route_manifest():
        public_manifest = PROJECT_ROOT / "public" / "manus-routes.json"
        if public_manifest.exists():
            return send_from_directory(public_manifest.parent, public_manifest.name)
        return jsonify({"routes": []})

    @app.get("/favicon.svg")
    def favicon():
        return send_from_directory(PROJECT_ROOT / "public", "favicon.svg")

    @app.get("/logo.svg")
    def logo():
        return send_from_directory(PROJECT_ROOT / "public", "logo.svg")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def spa(path: str):
        if path.startswith("api/"):
            return jsonify({"error": "Not found."}), 404
        static_root = Path(app.static_folder or "")
        candidate = static_root / path
        if path and candidate.is_file():
            return send_from_directory(static_root, path)
        index = static_root / "index.html"
        if index.exists():
            return send_from_directory(static_root, "index.html")
        return jsonify(
            {
                "service": "dietly-planner",
                "message": "Build the frontend with npm run build or use the Vite dev server.",
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
