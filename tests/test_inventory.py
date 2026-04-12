from lendbase import create_app
from lendbase.config import TestingConfig as AppTestingConfig
from lendbase.db import Base, db_session, get_engine
from lendbase.models import AdminUser, AuditEventType, Item, ItemStatus
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
