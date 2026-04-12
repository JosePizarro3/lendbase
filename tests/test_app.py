from lendbase import create_app
from lendbase.config import TestingConfig as AppTestingConfig
from lendbase.db import get_engine, resolve_database_url
from lendbase.qr import make_qr_png, make_qr_svg


def test_homepage_requires_authentication():
    app = create_app(AppTestingConfig())

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 302
    assert "/login?next=/" in response.headers["Location"]


def test_health_endpoint_returns_ok_status():
    app = create_app(AppTestingConfig())

    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {
        "status": "ok",
        "app": "lendbase",
        "database_url": "sqlite:///:memory:",
    }


def test_database_engine_is_initialized():
    app = create_app(AppTestingConfig())

    with app.app_context():
        engine = get_engine(app)

    assert str(engine.url) == "sqlite:///:memory:"


def test_relative_sqlite_database_url_uses_instance_path(tmp_path):
    resolved = resolve_database_url("sqlite:///lendbase-dev.db", str(tmp_path))

    assert resolved == f"sqlite:///{tmp_path.as_posix()}/lendbase-dev.db"


def test_legacy_instance_relative_sqlite_database_url_is_resolved_from_project_root(tmp_path):
    instance_path = tmp_path / "instance"
    resolved = resolve_database_url("sqlite:///instance/lendbase-dev.db", str(instance_path))

    assert resolved == f"sqlite:///{tmp_path.as_posix()}/instance/lendbase-dev.db"


def test_make_qr_svg_returns_svg_content():
    svg = make_qr_svg("http://localhost/items/1")

    assert svg.startswith("<?xml")
    assert "<svg" in svg


def test_make_qr_png_returns_png_content():
    png = make_qr_png("http://localhost/items/1")

    assert png.startswith(b"\x89PNG\r\n\x1a\n")
