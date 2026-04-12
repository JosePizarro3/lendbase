from __future__ import annotations

from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import or_, select

from lendbase.auth import login_required
from lendbase.db import db_session
from lendbase.models import AuditEventType, AuditLogEntry, Item, ItemStatus

inventory = Blueprint("inventory", __name__)


def parse_optional_date(raw_value: str) -> date | None:
    value = raw_value.strip()
    if not value:
        return None
    return date.fromisoformat(value)


def serialize_item_snapshot(item: Item) -> dict[str, str | None]:
    return {
        "item_type": item.item_type,
        "inventory_number": item.inventory_number,
        "hu_number": item.hu_number,
        "serial_number": item.serial_number,
        "brand_model": item.brand_model,
        "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
        "warranty_end": item.warranty_end.isoformat() if item.warranty_end else None,
        "status": item.status.value,
        "notes": item.notes,
    }


def build_item_form_data(form_data) -> dict[str, str]:
    return {
        "item_type": form_data.get("item_type", "").strip(),
        "inventory_number": form_data.get("inventory_number", "").strip(),
        "hu_number": form_data.get("hu_number", "").strip(),
        "serial_number": form_data.get("serial_number", "").strip(),
        "brand_model": form_data.get("brand_model", "").strip(),
        "purchase_date": form_data.get("purchase_date", "").strip(),
        "warranty_end": form_data.get("warranty_end", "").strip(),
        "status": form_data.get("status", ItemStatus.IN_STORAGE.value).strip(),
        "notes": form_data.get("notes", "").strip(),
    }


def validate_item_form(form_data: dict[str, str], current_item_id: int | None = None) -> list[str]:
    errors: list[str] = []

    if not form_data["item_type"]:
        errors.append("Item type is required.")
    if not form_data["inventory_number"]:
        errors.append("Inventory number is required.")
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
        Item.inventory_number == form_data["inventory_number"],
        Item.hu_number == form_data["hu_number"],
    )
    existing_items = db_session.scalars(select(Item).where(uniqueness_filters)).all()
    for existing_item in existing_items:
        if current_item_id is not None and existing_item.id == current_item_id:
            continue
        if existing_item.inventory_number == form_data["inventory_number"]:
            errors.append("Inventory number must be unique.")
        if existing_item.hu_number == form_data["hu_number"]:
            errors.append("HU number must be unique.")

    return errors


def apply_item_form(item: Item, form_data: dict[str, str]) -> None:
    item.item_type = form_data["item_type"]
    item.inventory_number = form_data["inventory_number"]
    item.hu_number = form_data["hu_number"]
    item.serial_number = form_data["serial_number"] or None
    item.brand_model = form_data["brand_model"] or None
    item.purchase_date = parse_optional_date(form_data["purchase_date"])
    item.warranty_end = parse_optional_date(form_data["warranty_end"])
    item.status = ItemStatus(form_data["status"])
    item.notes = form_data["notes"] or None


def create_audit_entry(item: Item, event_type: AuditEventType, message: str, details: dict | None) -> None:
    db_session.add(
        AuditLogEntry(item=item, event_type=event_type, message=message, details=details or None)
    )


def get_item_or_404(item_id: int) -> Item:
    item = db_session.get(Item, item_id)
    if item is None:
        abort(404)
    return item


@inventory.get("/items")
@login_required
def item_list():
    items = db_session.scalars(select(Item).order_by(Item.updated_at.desc(), Item.id.desc())).all()
    return render_template("inventory/list.html", items=items)


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
    return render_template("inventory/detail.html", item=item)


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
    apply_item_form(item, form_data)
    after_snapshot = serialize_item_snapshot(item)
    create_audit_entry(
        item,
        AuditEventType.ITEM_EDITED,
        "Item edited.",
        {"before": before_snapshot, "after": after_snapshot},
    )
    db_session.commit()
    flash("Item updated.", "success")
    return redirect(url_for("inventory.item_detail", item_id=item.id))
