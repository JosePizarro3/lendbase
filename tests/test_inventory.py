from datetime import date

from lendbase import create_app
from lendbase.config import TestingConfig as AppTestingConfig
from lendbase.db import Base, db_session, get_engine
from lendbase.models import (
    AdminUser,
    AuditEventType,
    AuditLogEntry,
    Item,
    ItemStatus,
    LendingRecord,
)
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


def test_home_page_shows_inventory_summary_and_home_navigation():
    app = create_test_app()

    with app.app_context():
        db_session.add_all(
            [
                Item(
                    item_type="Laptop",
                    service_tag="ST-HOME-1",
                    hu_number="HU-HOME-1",
                    status=ItemStatus.IN_STORAGE,
                ),
                Item(
                    item_type="Monitor",
                    service_tag="ST-HOME-2",
                    hu_number="HU-HOME-2",
                    status=ItemStatus.LENT_OUT,
                ),
                Item(
                    item_type="Dock",
                    service_tag="ST-HOME-3",
                    hu_number="HU-HOME-3",
                    status=ItemStatus.UNDER_REPAIR,
                ),
            ]
        )
        db_session.commit()

    with app.test_client() as client:
        login(client)
        response = client.get("/")

    assert response.status_code == 200
    assert b"Home" in response.data
    assert b"Total items" in response.data
    assert b"Currently lent out" in response.data
    assert b"Need attention" in response.data
    assert b"Open items" in response.data


def test_item_list_search_and_filter_work():
    app = create_test_app()

    with app.app_context():
        db_session.add_all(
            [
                Item(
                    item_type="Laptop",
                    service_tag="ST-FILTER-1",
                    hu_number="HU-FILTER-1",
                    serial_number="SER-A",
                    status=ItemStatus.IN_STORAGE,
                ),
                Item(
                    item_type="Monitor",
                    service_tag="ST-FILTER-2",
                    hu_number="HU-FILTER-2",
                    serial_number="SER-B",
                    status=ItemStatus.LENT_OUT,
                ),
            ]
        )
        db_session.commit()

    with app.test_client() as client:
        login(client)
        response = client.get("/items?query=SER-B&status=lent+out")

    assert response.status_code == 200
    assert b"ST-FILTER-2" in response.data
    assert b"ST-FILTER-1" not in response.data


def test_item_list_lent_out_view_only_shows_lent_items():
    app = create_test_app()

    with app.app_context():
        db_session.add_all(
            [
                Item(
                    item_type="Docking station",
                    service_tag="ST-VIEW-1",
                    hu_number="HU-VIEW-1",
                    status=ItemStatus.IN_STORAGE,
                ),
                Item(
                    item_type="Webcam",
                    service_tag="ST-VIEW-2",
                    hu_number="HU-VIEW-2",
                    status=ItemStatus.LENT_OUT,
                ),
            ]
        )
        db_session.commit()

    with app.test_client() as client:
        login(client)
        response = client.get("/items?view=lent_out")

    assert response.status_code == 200
    assert b"ST-VIEW-2" in response.data
    assert b"ST-VIEW-1" not in response.data


def test_item_export_returns_csv_for_filtered_items():
    app = create_test_app()

    with app.app_context():
        db_session.add_all(
            [
                Item(
                    item_type="Keyboard",
                    service_tag="ST-CSV-1",
                    hu_number="HU-CSV-1",
                    serial_number="CSV-ONE",
                    status=ItemStatus.IN_STORAGE,
                ),
                Item(
                    item_type="Keyboard",
                    service_tag="ST-CSV-2",
                    hu_number="HU-CSV-2",
                    serial_number="CSV-TWO",
                    status=ItemStatus.LENT_OUT,
                ),
            ]
        )
        db_session.commit()

    with app.test_client() as client:
        login(client)
        response = client.get("/items/export?query=CSV-TWO")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert response.headers["Content-Disposition"] == 'attachment; filename="lendbase-items.csv"'
    assert b"ST-CSV-2" in response.data
    assert b"ST-CSV-1" not in response.data


def test_item_detail_shows_qr_target_url_and_download_options():
    app = create_test_app()

    with app.app_context():
        item = Item(
            item_type="Laptop",
            service_tag="ST-QR",
            hu_number="HU-QR",
            status=ItemStatus.IN_STORAGE,
        )
        db_session.add(item)
        db_session.commit()
        item_id = item.id

    with app.test_client() as client:
        login(client)
        detail_response = client.get(f"/items/{item_id}")
        qr_response = client.get(f"/items/{item_id}/qr.svg")
        qr_png_response = client.get(f"/items/{item_id}/qr.png")

    assert detail_response.status_code == 200
    assert b"http://localhost/items/" in detail_response.data
    assert b"Usage notes" not in detail_response.data
    assert b"Download SVG" in detail_response.data
    assert b"Download PNG" in detail_response.data
    assert qr_response.status_code == 200
    assert qr_response.mimetype == "image/svg+xml"
    assert b"<svg" in qr_response.data
    assert qr_png_response.status_code == 200
    assert qr_png_response.mimetype == "image/png"
    assert qr_png_response.headers["Content-Disposition"] == 'attachment; filename="st-qr-qr.png"'
    assert qr_png_response.data.startswith(b"\x89PNG\r\n\x1a\n")


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
        event_types = [entry.event_type for entry in item.audit_entries]
        assert AuditEventType.ITEM_EDITED in event_types
        assert AuditEventType.STATUS_CHANGED in event_types


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
        event_types = [entry.event_type for entry in item.audit_entries]
        assert AuditEventType.ITEM_LENT_OUT in event_types
        assert AuditEventType.STATUS_CHANGED in event_types


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
        event_types = [entry.event_type for entry in item.audit_entries]
        assert AuditEventType.ITEM_RETURNED in event_types
        assert AuditEventType.STATUS_CHANGED in event_types


def test_item_detail_shows_audit_history_details():
    app = create_test_app()

    with app.app_context():
        item = Item(
            item_type="Laptop",
            service_tag="ST-HISTORY",
            hu_number="HU-HISTORY",
            status=ItemStatus.IN_STORAGE,
        )
        db_session.add(item)
        db_session.flush()
        db_session.add(
            AuditLogEntry(
                item=item,
                event_type=AuditEventType.ITEM_EDITED,
                message="Item edited.",
                details={
                    "before": {"brand_model": "Old Model", "notes": None},
                    "after": {"brand_model": "New Model", "notes": "Updated note"},
                },
            )
        )
        db_session.commit()
        item_id = item.id

    with app.test_client() as client:
        login(client)
        response = client.get(f"/items/{item_id}")

    assert response.status_code == 200
    assert b"Item edited." in response.data
    assert b"brand model: Old Model -&gt; New Model" in response.data
    assert b"notes: - -&gt; Updated note" in response.data
