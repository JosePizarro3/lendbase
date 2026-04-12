from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from lendbase.config import BaseConfig, get_config
from lendbase.db import init_db
from lendbase.web import web


def create_app(config: BaseConfig | None = None) -> Flask:
    load_dotenv()

    project_root = Path(__file__).resolve().parents[2]
    app = Flask(
        __name__,
        instance_path=str(project_root / "instance"),
        instance_relative_config=True,
    )
    app_config = config or get_config()
    app.config.update(app_config.as_flask_config())

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    init_db(app)
    app.register_blueprint(web)

    return app
