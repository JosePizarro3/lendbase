from datetime import date

from lendbase import create_app
from lendbase.config import TestingConfig as AppTestingConfig
from lendbase.db import Base, db_session, get_engine
from lendbase.models import AdminUser, AuditEventType, Item, ItemStatus, LendingRecord
from werkzeug.security import generate_password_hash


def create_test_app():
    app = create_app(AppTestingConfig())
    with app.app_context():
        Base.metadata.create_all(bind=get_engine(app))
        db_session.add(
            AdminUser(username="admin", password_hash=generate_password_hash("very-secure-pass"))
        )
        db_session.commit()
    return app


def login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "very-secure-pass"},
        follow_redirects=True,
    )


def test_item_list_requires_authentication():
    app = create_test_app()

    with app.test_client() as client:
        response = client.get("/items")

    assert response.status_code == 302
    assert "/login?next=/items" in response.headers["Location"]


def test_create_item_flow():
    app = create_test_app()

    with app.test_client() as client:
        login(client)
        response = client.post(
            "/items/new",
            data={
                "item_type": "Laptop",
                "service_tag": "ST-001",
                "hu_number": "HU-001",
                "serial_number": "SER-001",
                "brand_model": "Dell Latitude 5420",
                "purchase_date": "2024-01-15",
                "warranty_end": "2027-01-15",
                "status": "in storage",
                "notes": "Migrated from spreadsheet comment column.",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"Item created." in response.data
    assert b"ST-001" in response.data

    with app.app_context():
        item = db_session.query(Item).filter_by(service_tag="ST-001").one()
        assert item.item_type == "Laptop"
        assert item.status == ItemStatus.IN_STORAGE
        assert item.audit_entries[-1].event_type == AuditEventType.ITEM_CREATED


def test_duplicate_identifiers_are_rejected():
    app = create_test_app()

    with app.app_context():
        db_session.add(
            Item(
                item_type="Monitor",
                service_tag="ST-001",
                hu_number="HU-001",
                status=ItemStatus.IN_STORAGE,
            )
        )
        db_session.commit()

    with app.test_client() as client:
        login(client)
        response = client.post(
            "/items/new",
            data={
                "item_type": "Keyboard",
                "service_tag": "ST-001",
                "hu_number": "HU-001",
                "status": "in storage",
            },
        )

    assert response.status_code == 400
    assert b"Service tag must be unique." in response.data
    assert b"HU number must be unique." in response.data


def test_edit_item_updates_fields_and_audit():
    app = create_test_app()

    with app.app_context():
        item = Item(
            item_type="Monitor",
            service_tag="ST-200",
            hu_number="HU-200",
            status=ItemStatus.IN_STORAGE,
        )
        db_session.add(item)
        db_session.commit()
        item_id = item.id

    with app.test_client() as client:
        login(client)
        response = client.post(
            f"/items/{item_id}/edit",
            data={
                "item_type": "Monitor",
                "service_tag": "ST-200",
                "hu_number": "HU-200",
                "serial_number": "SER-200",
                "brand_model": "Dell U2720Q",
                "purchase_date": "2024-02-01",
                "warranty_end": "2027-02-01",
                "status": "under repair",
                "notes": "Panel issue reported.",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"Item updated." in response.data
    assert b"under repair" in response.data

    with app.app_context():
        item = db_session.get(Item, item_id)
        assert item.serial_number == "SER-200"
        assert item.status == ItemStatus.UNDER_REPAIR
        assert item.audit_entries[-1].event_type == AuditEventType.ITEM_EDITED


def test_edit_item_form_loads_with_optional_empty_fields():
    app = create_test_app()

    with app.app_context():
        item = Item(
            item_type="Mouse",
            service_tag="ST-EMPTY",
            hu_number="HU-EMPTY",
            status=ItemStatus.IN_STORAGE,
        )
        db_session.add(item)
        db_session.commit()
        item_id = item.id

    with app.test_client() as client:
        login(client)
        response = client.get(f"/items/{item_id}/edit")

    assert response.status_code == 200
    assert b"Edit item" in response.data
    assert b"ST-EMPTY" in response.data


def test_delete_item_removes_it():
    app = create_test_app()

    with app.app_context():
        item = Item(
            item_type="Keyboard",
            service_tag="ST-DELETE",
            hu_number="HU-DELETE",
            status=ItemStatus.IN_STORAGE,
        )
        db_session.add(item)
        db_session.commit()
        item_id = item.id

    with app.test_client() as client:
        login(client)
        response = client.post(f"/items/{item_id}/delete", follow_redirects=True)

    assert response.status_code == 200
    assert b"Item deleted:" in response.data
    assert b"ST-DELETE" in response.data

    with app.app_context():
        assert db_session.get(Item, item_id) is None


def test_lend_item_creates_lending_record_and_updates_status():
    app = create_test_app()

    with app.app_context():
        item = Item(
            item_type="Laptop",
            service_tag="ST-LEND",
            hu_number="HU-LEND",
            status=ItemStatus.IN_STORAGE,
        )
        db_session.add(item)
        db_session.commit()
        item_id = item.id

    with app.test_client() as client:
        login(client)
        response = client.post(
            f"/items/{item_id}/lend",
            data={
                "borrower_name": "Alice Example",
                "lent_date": "2026-04-12",
                "comments": "Loaned for conference travel.",
            },
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"Item marked as lent out." in response.data
    assert b"Alice Example" in response.data

    with app.app_context():
        item = db_session.get(Item, item_id)
        assert item.status == ItemStatus.LENT_OUT
        lending_record = db_session.query(LendingRecord).filter_by(item_id=item_id).one()
        assert lending_record.borrower_name == "Alice Example"
        assert lending_record.comments == "Loaned for conference travel."
        assert item.audit_entries[-1].event_type == AuditEventType.ITEM_LENT_OUT


def test_return_item_closes_active_lending_record_and_resets_status():
    app = create_test_app()

    with app.app_context():
        item = Item(
            item_type="Monitor",
            service_tag="ST-RETURN",
            hu_number="HU-RETURN",
            status=ItemStatus.LENT_OUT,
        )
        db_session.add(item)
        db_session.flush()
        db_session.add(
            LendingRecord(
                item=item,
                borrower_name="Bob Example",
                lent_date=date(2026, 4, 10),
                comments="Desk setup",
            )
        )
        db_session.commit()
        item_id = item.id

    with app.test_client() as client:
        login(client)
        response = client.post(
            f"/items/{item_id}/return",
            data={"return_date": "2026-04-14"},
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert b"Item marked as returned." in response.data

    with app.app_context():
        item = db_session.get(Item, item_id)
        assert item.status == ItemStatus.IN_STORAGE
        lending_record = db_session.query(LendingRecord).filter_by(item_id=item_id).one()
        assert lending_record.return_date == date(2026, 4, 14)
        assert item.audit_entries[-1].event_type == AuditEventType.ITEM_RETURNED
