from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template

web = Blueprint("web", __name__)


@web.get("/")
def home():
    return render_template(
        "home.html",
        app_name=current_app.config["APP_NAME"],
        environment=current_app.config.get("ENVIRONMENT_NAME", "development"),
        app_base_url=current_app.config["APP_BASE_URL"],
    )


@web.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "app": current_app.config["APP_NAME"],
            "database_url": current_app.config["SQLALCHEMY_DATABASE_URI"],
        }
    )
