from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, render_template
from sqlalchemy import func, select

from lendbase.auth import login_required
from lendbase.db import db_session
from lendbase.models import Item, ItemStatus

web = Blueprint("web", __name__)


@web.get("/")
@login_required
def home():
    summary = {
        "total_items": db_session.scalar(select(func.count()).select_from(Item)) or 0,
        "lent_out_items": db_session.scalar(
            select(func.count()).select_from(Item).where(Item.status == ItemStatus.LENT_OUT)
        )
        or 0,
        "attention_items": db_session.scalar(
            select(func.count())
            .select_from(Item)
            .where(Item.status.in_([ItemStatus.BROKEN, ItemStatus.LOST, ItemStatus.UNDER_REPAIR]))
        )
        or 0,
    }
    return render_template(
        "home.html",
        app_name=current_app.config["APP_NAME"],
        environment=current_app.config.get("ENVIRONMENT_NAME", "development"),
        app_base_url=current_app.config["APP_BASE_URL"],
        admin_username=g.admin_user.username,
        summary=summary,
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
