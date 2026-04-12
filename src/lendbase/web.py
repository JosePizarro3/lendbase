from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, render_template

from lendbase.auth import login_required

web = Blueprint("web", __name__)


@web.get("/")
@login_required
def home():
    return render_template(
        "home.html",
        app_name=current_app.config["APP_NAME"],
        environment=current_app.config.get("ENVIRONMENT_NAME", "development"),
        app_base_url=current_app.config["APP_BASE_URL"],
        admin_username=g.admin_user.username,
    )


@web.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "app": current_app.config["APP_NAME"],
            "database_url": current_app.config["DATABASE_URL_RESOLVED"],
        }
    )
