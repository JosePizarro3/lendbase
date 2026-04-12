from __future__ import annotations

from functools import wraps

import click
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash

from lendbase.db import db_session
from lendbase.models import AdminUser

auth = Blueprint("auth", __name__)


def validate_password_rules(password: str, password_confirm: str) -> list[str]:
    errors: list[str] = []
    if len(password) < 12:
        errors.append("Password must be at least 12 characters long.")
    if password != password_confirm:
        errors.append("Password confirmation does not match.")
    return errors


def admin_exists() -> bool:
    return db_session.query(AdminUser.id).first() is not None


def get_current_admin() -> AdminUser | None:
    admin_id = session.get("admin_user_id")
    if admin_id is None:
        return None
    return db_session.get(AdminUser, admin_id)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.admin_user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


@auth.before_app_request
def load_logged_in_admin() -> None:
    g.admin_user = get_current_admin()


@auth.get("/login")
def login():
    if not admin_exists():
        return redirect(url_for("auth.setup_admin"))
    if g.admin_user is not None:
        return redirect(url_for("web.home"))
    return render_template("auth/login.html")


@auth.post("/login")
def login_post():
    if not admin_exists():
        return redirect(url_for("auth.setup_admin"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    admin_user = db_session.query(AdminUser).filter(AdminUser.username == username).one_or_none()
    if admin_user is None or not check_password_hash(admin_user.password_hash, password):
        flash("Invalid username or password.", "error")
        return render_template("auth/login.html", entered_username=username), 400

    session.clear()
    session["admin_user_id"] = admin_user.id
    flash("Logged in successfully.", "success")
    next_url = request.args.get("next") or url_for("web.home")
    return redirect(next_url)


@auth.route("/setup/admin", methods=["GET", "POST"])
def setup_admin():
    if admin_exists():
        flash("Admin user already configured. Please log in.", "info")
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        return render_template("auth/setup_admin.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    errors: list[str] = []
    if not username:
        errors.append("Username is required.")
    errors.extend(validate_password_rules(password, password_confirm))

    if errors:
        for error in errors:
            flash(error, "error")
        return render_template("auth/setup_admin.html", entered_username=username), 400

    admin_user = AdminUser(username=username, password_hash=generate_password_hash(password))
    db_session.add(admin_user)
    db_session.commit()

    session.clear()
    session["admin_user_id"] = admin_user.id
    flash("Admin account created.", "success")
    return redirect(url_for("web.home"))


@auth.post("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))


@click.command("reset-admin-password")
@click.option("--username", required=True, help="Admin username to update.")
@click.password_option(
    "--password",
    confirmation_prompt=True,
    prompt=True,
    help="New password for the admin user.",
)
@with_appcontext
def reset_admin_password_command(username: str, password: str) -> None:
    if len(password) < 12:
        raise click.ClickException("Password must be at least 12 characters long.")

    admin_user = db_session.query(AdminUser).filter(AdminUser.username == username).one_or_none()
    if admin_user is None:
        raise click.ClickException(f"Admin user '{username}' was not found.")

    admin_user.password_hash = generate_password_hash(password)
    db_session.commit()
    click.echo(f"Password updated for admin user '{username}'.")
