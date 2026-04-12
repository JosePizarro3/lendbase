from __future__ import annotations

from pathlib import Path

from flask import Flask
from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata


db_session = scoped_session(
    sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False)
)


def resolve_database_url(database_url: str, instance_path: str) -> str:
    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database not in (None, "", ":memory:"):
        db_path = Path(url.database)
        if not db_path.is_absolute():
            resolved_path = Path(instance_path) / db_path
            return f"sqlite:///{resolved_path.as_posix()}"
    return database_url


def ensure_database_parent(database_url: str) -> None:
    url = make_url(database_url)
    if url.drivername.startswith("sqlite") and url.database not in (None, "", ":memory:"):
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def create_db_engine(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def init_db(app: Flask) -> None:
    resolved_url = resolve_database_url(app.config["DATABASE_URL"], app.instance_path)
    ensure_database_parent(resolved_url)

    engine = create_db_engine(resolved_url)
    db_session.configure(bind=engine)

    app.config["DATABASE_URL_RESOLVED"] = resolved_url
    app.extensions["lendbase_db"] = {"engine": engine, "session": db_session}
    app.teardown_appcontext(shutdown_session)


def shutdown_session(_exception: BaseException | None = None) -> None:
    db_session.remove()


def get_engine(app: Flask) -> Engine:
    return app.extensions["lendbase_db"]["engine"]
