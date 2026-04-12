from werkzeug.security import check_password_hash, generate_password_hash

from lendbase import create_app
from lendbase.config import TestingConfig as AppTestingConfig
from lendbase.db import Base, db_session, get_engine
from lendbase.models import AdminUser


def create_test_app():
    app = create_app(AppTestingConfig())
    with app.app_context():
        Base.metadata.create_all(bind=get_engine(app))
    return app


def test_setup_admin_page_is_available_before_admin_exists():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/setup/admin")

    assert response.status_code == 200
    assert b"Create the shared admin account" in response.data


def test_setup_admin_creates_account_and_logs_in():
    app = create_test_app()

    with app.test_client() as client:
        response = client.post(
            "/setup/admin",
            data={
                "username": "admin",
                "password": "very-secure-pass",
                "password_confirm": "very-secure-pass",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"Admin account created." in response.data
    assert b"Signed in as" in response.data
    assert b"admin" in response.data


def test_root_redirects_to_setup_before_admin_exists():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 302
    assert "/login?next=/" in response.headers["Location"]


def test_login_and_logout_flow_after_bootstrap():
    app = create_test_app()

    with app.app_context():
        db_session.add(
            AdminUser(username="admin", password_hash=generate_password_hash("very-secure-pass"))
        )
        db_session.commit()

    with app.test_client() as client:
        bad_login = client.post("/login", data={"username": "admin", "password": "wrong-password"})
        assert bad_login.status_code == 400

        login_response = client.post(
            "/login",
            data={"username": "admin", "password": "very-secure-pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200
        assert b"Logged in successfully." in login_response.data

        logout_response = client.post("/logout", follow_redirects=True)
        assert logout_response.status_code == 200
        assert b"Logged out." in logout_response.data


def test_setup_admin_is_disabled_after_first_admin_exists():
    app = create_test_app()

    with app.test_client() as client:
        client.post(
            "/setup/admin",
            data={
                "username": "admin",
                "password": "very-secure-pass",
                "password_confirm": "very-secure-pass",
            },
        )
        client.post("/logout")
        response = client.get("/setup/admin", follow_redirects=True)

    assert response.status_code == 200
    assert b"Admin user already configured. Please log in." in response.data


def test_reset_admin_password_command_updates_hash():
    app = create_test_app()

    with app.app_context():
        db_session.add(
            AdminUser(username="admin", password_hash=generate_password_hash("old-password-123"))
        )
        db_session.commit()

    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["reset-admin-password", "--username", "admin"],
        input="new-password-456\nnew-password-456\n",
    )

    assert result.exit_code == 0
    assert "Password updated for admin user 'admin'." in result.output

    with app.app_context():
        admin_user = db_session.query(AdminUser).filter_by(username="admin").one()
        assert check_password_hash(admin_user.password_hash, "new-password-456")


def test_reset_admin_password_command_fails_for_missing_user():
    app = create_test_app()

    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["reset-admin-password", "--username", "missing-admin"],
        input="new-password-456\nnew-password-456\n",
    )

    assert result.exit_code != 0
    assert "Admin user 'missing-admin' was not found." in result.output
