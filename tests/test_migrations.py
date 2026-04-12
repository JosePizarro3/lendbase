from pathlib import Path

from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy import create_engine, inspect


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_creates_expected_tables(tmp_path):
    database_path = tmp_path / "lendbase-migration-test.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)

    upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) >= {
        "alembic_version",
        "admin_users",
        "items",
        "lending_records",
        "audit_log_entries",
    }
    item_columns = {column["name"] for column in inspector.get_columns("items")}
    assert "service_tag" in item_columns
    assert "inventory_number" not in item_columns
