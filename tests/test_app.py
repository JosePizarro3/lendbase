from lendbase import create_app
from lendbase.config import TestingConfig as AppTestingConfig


def test_homepage_loads():
    app = create_app(AppTestingConfig())

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert b"lendbase" in response.data


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
