from __future__ import annotations

import csv
from datetime import date
from io import StringIO

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import and_, or_, select

from lendbase.auth import login_required
from lendbase.db import db_session
from lendbase.models import AuditEventType, AuditLogEntry, Item, ItemStatus, LendingRecord
from lendbase.qr import make_qr_png, make_qr_svg

inventory = Blueprint("inventory", __name__)


def parse_optional_date(raw_value: str) -> date | None:
    value = raw_value.strip()
    if not value:
        return None
    return date.fromisoformat(value)


def serialize_item_snapshot(item: Item) -> dict[str, str | None]:
    return {
        "item_type": item.item_type,
        "service_tag": item.service_tag,
        "hu_number": item.hu_number,
        "serial_number": item.serial_number,
        "brand_model": item.brand_model,
        "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
        "warranty_end": item.warranty_end.isoformat() if item.warranty_end else None,
        "status": item.status.value,
        "notes": item.notes,
    }


def build_item_form_data(form_data) -> dict[str, str]:
    def get_text(name: str, default: str = "") -> str:
        value = form_data.get(name, default)
        if value is None:
            return default
        return str(value).strip()

    return {
        "item_type": get_text("item_type"),
        "service_tag": get_text("service_tag"),
        "hu_number": get_text("hu_number"),
        "serial_number": get_text("serial_number"),
        "brand_model": get_text("brand_model"),
        "purchase_date": get_text("purchase_date"),
        "warranty_end": get_text("warranty_end"),
        "status": get_text("status", ItemStatus.IN_STORAGE.value),
        "notes": get_text("notes"),
    }


def validate_item_form(form_data: dict[str, str], current_item_id: int | None = None) -> list[str]:
    errors: list[str] = []

    if not form_data["item_type"]:
        errors.append("Item type is required.")
    if not form_data["service_tag"]:
        errors.append("Service tag is required.")
    if not form_data["hu_number"]:
        errors.append("HU number is required.")

    try:
        ItemStatus(form_data["status"])
    except ValueError:
        errors.append("Status is invalid.")

    for field_name in ("purchase_date", "warranty_end"):
        try:
            parse_optional_date(form_data[field_name])
        except ValueError:
            errors.append(f"{field_name.replace('_', ' ').title()} must use YYYY-MM-DD format.")

    uniqueness_filters = or_(
        Item.service_tag == form_data["service_tag"],
        Item.hu_number == form_data["hu_number"],
    )
    existing_items = db_session.scalars(select(Item).where(uniqueness_filters)).all()
    for existing_item in existing_items:
        if current_item_id is not None and existing_item.id == current_item_id:
            continue
        if existing_item.service_tag == form_data["service_tag"]:
            errors.append("Service tag must be unique.")
        if existing_item.hu_number == form_data["hu_number"]:
            errors.append("HU number must be unique.")

    return errors


def apply_item_form(item: Item, form_data: dict[str, str]) -> None:
    item.item_type = form_data["item_type"]
    item.service_tag = form_data["service_tag"]
    item.hu_number = form_data["hu_number"]
    item.serial_number = form_data["serial_number"] or None
    item.brand_model = form_data["brand_model"] or None
    item.purchase_date = parse_optional_date(form_data["purchase_date"])
    item.warranty_end = parse_optional_date(form_data["warranty_end"])
    item.status = ItemStatus(form_data["status"])
    item.notes = form_data["notes"] or None


def create_audit_entry(
    item: Item, event_type: AuditEventType, message: str, details: dict | None
) -> None:
    db_session.add(
        AuditLogEntry(item=item, event_type=event_type, message=message, details=details or None)
    )


def create_status_change_entry(
    item: Item, before_status: ItemStatus, after_status: ItemStatus
) -> None:
    if before_status == after_status:
        return
    create_audit_entry(
        item,
        AuditEventType.STATUS_CHANGED,
        f"Status changed from {before_status.value} to {after_status.value}.",
        {"before_status": before_status.value, "after_status": after_status.value},
    )


def build_audit_history_entries(item: Item) -> list[dict[str, object]]:
    history_entries: list[dict[str, object]] = []

    for entry in item.audit_entries:
        detail_lines: list[str] = []
        details = entry.details or {}

        if entry.event_type == AuditEventType.ITEM_EDITED:
            before = details.get("before") or {}
            after = details.get("after") or {}
            for field_name, after_value in after.items():
                before_value = before.get(field_name)
                if before_value != after_value:
                    detail_lines.append(
                        f"{field_name.replace('_', ' ')}: {before_value or '-'} -> {after_value or '-'}"
                    )
        elif entry.event_type == AuditEventType.ITEM_CREATED:
            after = details.get("after") or {}
            for field_name, value in after.items():
                if value:
                    detail_lines.append(f"{field_name.replace('_', ' ')}: {value}")
        elif entry.event_type == AuditEventType.STATUS_CHANGED:
            detail_lines.append(
                f"{details.get('before_status', '-')} -> {details.get('after_status', '-')}"
            )
        elif entry.event_type == AuditEventType.ITEM_LENT_OUT:
            detail_lines.extend(
                [
                    f"borrower name: {details.get('borrower_name', '-')}",
                    f"lent date: {details.get('lent_date', '-')}",
                ]
            )
            if details.get("comments"):
                detail_lines.append(f"comments: {details['comments']}")
        elif entry.event_type == AuditEventType.ITEM_RETURNED:
            detail_lines.extend(
                [
                    f"borrower name: {details.get('borrower_name', '-')}",
                    f"return date: {details.get('return_date', '-')}",
                ]
            )

        history_entries.append(
            {
                "timestamp": entry.event_at,
                "event_type": entry.event_type.value,
                "message": entry.message,
                "detail_lines": detail_lines,
            }
        )

    return history_entries


def get_item_or_404(item_id: int) -> Item:
    item = db_session.get(Item, item_id)
    if item is None:
        abort(404)
    return item


def get_active_lending_record(item: Item) -> LendingRecord | None:
    for lending_record in item.lending_records:
        if lending_record.return_date is None:
            return lending_record
    return None


def build_lending_form_data(form_data) -> dict[str, str]:
    def get_text(name: str, default: str = "") -> str:
        value = form_data.get(name, default)
        if value is None:
            return default
        return str(value).strip()

    return {
        "borrower_name": get_text("borrower_name"),
        "lent_date": get_text("lent_date", date.today().isoformat()),
        "comments": get_text("comments"),
    }


def build_return_form_data(form_data) -> dict[str, str]:
    def get_text(name: str, default: str = "") -> str:
        value = form_data.get(name, default)
        if value is None:
            return default
        return str(value).strip()

    return {"return_date": get_text("return_date", date.today().isoformat())}


def build_list_filters(args) -> dict[str, str]:
    return {
        "query": args.get("query", "").strip(),
        "item_type": args.get("item_type", "").strip(),
        "status": args.get("status", "").strip(),
        "view": args.get("view", "").strip(),
    }


def build_item_list_query(filters: dict[str, str]):
    conditions = []

    if filters["query"]:
        search_term = f"%{filters['query']}%"
        conditions.append(
            or_(
                Item.service_tag.ilike(search_term),
                Item.hu_number.ilike(search_term),
                Item.serial_number.ilike(search_term),
            )
        )

    if filters["item_type"]:
        conditions.append(Item.item_type == filters["item_type"])

    if filters["status"]:
        try:
            conditions.append(Item.status == ItemStatus(filters["status"]))
        except ValueError:
            pass

    if filters["view"] == "lent_out":
        conditions.append(Item.status == ItemStatus.LENT_OUT)

    query = select(Item)
    if conditions:
        query = query.where(and_(*conditions))
    return query.order_by(Item.updated_at.desc(), Item.id.desc())


def get_distinct_item_types() -> list[str]:
    return list(
        db_session.scalars(select(Item.item_type).distinct().order_by(Item.item_type.asc())).all()
    )


def export_items_csv(items: list[Item]) -> Response:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "item_type",
            "service_tag",
            "hu_number",
            "serial_number",
            "brand_model",
            "purchase_date",
            "warranty_end",
            "status",
            "notes",
            "current_borrower",
            "lent_date",
            "return_date",
        ]
    )

    for item in items:
        active_lending_record = get_active_lending_record(item)
        latest_lending_record = item.lending_records[0] if item.lending_records else None
        writer.writerow(
            [
                item.item_type,
                item.service_tag,
                item.hu_number,
                item.serial_number or "",
                item.brand_model or "",
                item.purchase_date.isoformat() if item.purchase_date else "",
                item.warranty_end.isoformat() if item.warranty_end else "",
                item.status.value,
                item.notes or "",
                active_lending_record.borrower_name if active_lending_record else "",
                active_lending_record.lent_date.isoformat() if active_lending_record else "",
                latest_lending_record.return_date.isoformat()
                if latest_lending_record and latest_lending_record.return_date
                else "",
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="lendbase-items.csv"'},
    )


def build_item_detail_url(item: Item) -> str:
    return (
        f"{current_app.config['APP_BASE_URL']}{url_for('inventory.item_detail', item_id=item.id)}"
    )


def build_item_detail_context(
    item: Item,
    lending_form_data: dict[str, str] | None = None,
    return_form_data: dict[str, str] | None = None,
):
    return {
        "item": item,
        "item_detail_url": build_item_detail_url(item),
        "qr_svg_url": url_for("inventory.item_qr_svg", item_id=item.id),
        "qr_png_url": url_for("inventory.item_qr_png", item_id=item.id),
        "active_lending_record": get_active_lending_record(item),
        "lending_form_data": lending_form_data or build_lending_form_data({}),
        "return_form_data": return_form_data or build_return_form_data({}),
        "audit_history_entries": build_audit_history_entries(item),
    }


@inventory.get("/items")
@login_required
def item_list():
    filters = build_list_filters(request.args)
    items = db_session.scalars(build_item_list_query(filters)).all()
    return render_template(
        "inventory/list.html",
        items=items,
        filters=filters,
        item_type_options=get_distinct_item_types(),
        status_options=list(ItemStatus),
    )


@inventory.get("/items/export")
@login_required
def item_export():
    filters = build_list_filters(request.args)
    items = db_session.scalars(build_item_list_query(filters)).all()
    return export_items_csv(items)


@inventory.route("/items/new", methods=["GET", "POST"])
@login_required
def item_create():
    form_data = build_item_form_data(request.form if request.method == "POST" else {})
    if request.method == "GET":
        return render_template(
            "inventory/form.html",
            form_title="Add item",
            form_intro="Create a new inventory record using the core metadata from the equipment sheets.",
            submit_label="Create item",
            form_data=form_data,
            status_options=list(ItemStatus),
            item=None,
        )

    errors = validate_item_form(form_data)
    if errors:
        for error in errors:
            flash(error, "error")
        return (
            render_template(
                "inventory/form.html",
                form_title="Add item",
                form_intro="Create a new inventory record using the core metadata from the equipment sheets.",
                submit_label="Create item",
                form_data=form_data,
                status_options=list(ItemStatus),
                item=None,
            ),
            400,
        )

    item = Item()
    apply_item_form(item, form_data)
    db_session.add(item)
    db_session.flush()
    create_audit_entry(
        item,
        AuditEventType.ITEM_CREATED,
        "Item created.",
        {"after": serialize_item_snapshot(item)},
    )
    db_session.commit()
    flash("Item created.", "success")
    return redirect(url_for("inventory.item_detail", item_id=item.id))


@inventory.get("/items/<int:item_id>")
@login_required
def item_detail(item_id: int):
    item = get_item_or_404(item_id)
    return render_template("inventory/detail.html", **build_item_detail_context(item))


@inventory.get("/items/<int:item_id>/qr.svg")
@login_required
def item_qr_svg(item_id: int):
    item = get_item_or_404(item_id)
    svg = make_qr_svg(build_item_detail_url(item))
    return Response(svg, mimetype="image/svg+xml")


@inventory.get("/items/<int:item_id>/qr.png")
@login_required
def item_qr_png(item_id: int):
    item = get_item_or_404(item_id)
    png = make_qr_png(build_item_detail_url(item))
    filename = f"{item.service_tag.lower()}-qr.png"
    return Response(
        png,
        mimetype="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@inventory.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def item_edit(item_id: int):
    item = get_item_or_404(item_id)
    if request.method == "GET":
        form_data = build_item_form_data(serialize_item_snapshot(item))
        return render_template(
            "inventory/form.html",
            form_title="Edit item",
            form_intro="Update the core inventory metadata. Any extra sheet-specific remarks can stay in notes.",
            submit_label="Save changes",
            form_data=form_data,
            status_options=list(ItemStatus),
            item=item,
        )

    form_data = build_item_form_data(request.form)
    errors = validate_item_form(form_data, current_item_id=item.id)
    if errors:
        for error in errors:
            flash(error, "error")
        return (
            render_template(
                "inventory/form.html",
                form_title="Edit item",
                form_intro="Update the core inventory metadata. Any extra sheet-specific remarks can stay in notes.",
                submit_label="Save changes",
                form_data=form_data,
                status_options=list(ItemStatus),
                item=item,
            ),
            400,
        )

    before_snapshot = serialize_item_snapshot(item)
    previous_status = item.status
    apply_item_form(item, form_data)
    after_snapshot = serialize_item_snapshot(item)
    create_audit_entry(
        item,
        AuditEventType.ITEM_EDITED,
        "Item edited.",
        {"before": before_snapshot, "after": after_snapshot},
    )
    create_status_change_entry(item, previous_status, item.status)
    db_session.commit()
    flash("Item updated.", "success")
    return redirect(url_for("inventory.item_detail", item_id=item.id))


@inventory.post("/items/<int:item_id>/delete")
@login_required
def item_delete(item_id: int):
    item = get_item_or_404(item_id)
    item_label = f"{item.item_type} ({item.service_tag})"
    db_session.delete(item)
    db_session.commit()
    flash(f"Item deleted: {item_label}.", "success")
    return redirect(url_for("inventory.item_list"))


@inventory.post("/items/<int:item_id>/lend")
@login_required
def item_lend(item_id: int):
    item = get_item_or_404(item_id)
    active_lending_record = get_active_lending_record(item)
    form_data = build_lending_form_data(request.form)

    errors: list[str] = []
    if active_lending_record is not None:
        errors.append("Item is already lent out and must be returned before lending it again.")
    if not form_data["borrower_name"]:
        errors.append("Borrower name is required.")
    try:
        lent_date = date.fromisoformat(form_data["lent_date"])
    except ValueError:
        errors.append("Lent date must use YYYY-MM-DD format.")
        lent_date = None

    if errors:
        for error in errors:
            flash(error, "error")
        return (
            render_template(
                "inventory/detail.html",
                **build_item_detail_context(
                    item,
                    lending_form_data=form_data,
                    return_form_data=build_return_form_data({}),
                ),
            ),
            400,
        )

    lending_record = LendingRecord(
        item=item,
        borrower_name=form_data["borrower_name"],
        lent_date=lent_date,
        comments=form_data["comments"] or None,
    )
    previous_status = item.status
    item.status = ItemStatus.LENT_OUT
    db_session.add(lending_record)
    create_status_change_entry(item, previous_status, item.status)
    create_audit_entry(
        item,
        AuditEventType.ITEM_LENT_OUT,
        "Item lent out.",
        {
            "borrower_name": lending_record.borrower_name,
            "lent_date": lending_record.lent_date.isoformat(),
            "comments": lending_record.comments,
        },
    )
    db_session.commit()
    flash("Item marked as lent out.", "success")
    return redirect(url_for("inventory.item_detail", item_id=item.id))


@inventory.post("/items/<int:item_id>/return")
@login_required
def item_return(item_id: int):
    item = get_item_or_404(item_id)
    active_lending_record = get_active_lending_record(item)
    form_data = build_return_form_data(request.form)

    errors: list[str] = []
    if active_lending_record is None:
        errors.append("Item is not currently lent out.")
    try:
        return_date = date.fromisoformat(form_data["return_date"])
    except ValueError:
        errors.append("Return date must use YYYY-MM-DD format.")
        return_date = None

    if active_lending_record is not None and return_date is not None:
        if return_date < active_lending_record.lent_date:
            errors.append("Return date cannot be earlier than the lent date.")

    if errors:
        for error in errors:
            flash(error, "error")
        return (
            render_template(
                "inventory/detail.html",
                **build_item_detail_context(
                    item,
                    lending_form_data=build_lending_form_data({}),
                    return_form_data=form_data,
                ),
            ),
            400,
        )

    active_lending_record.return_date = return_date
    previous_status = item.status
    item.status = ItemStatus.IN_STORAGE
    create_status_change_entry(item, previous_status, item.status)
    create_audit_entry(
        item,
        AuditEventType.ITEM_RETURNED,
        "Item returned.",
        {
            "borrower_name": active_lending_record.borrower_name,
            "return_date": active_lending_record.return_date.isoformat(),
        },
    )
    db_session.commit()
    flash("Item marked as returned.", "success")
    return redirect(url_for("inventory.item_detail", item_id=item.id))
