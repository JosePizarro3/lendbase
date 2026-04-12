# Schema Extension Guide

This document explains how to extend the item schema safely so the Flask app,
database, and UI stay in sync.

## Where the schema lives

Core item fields are defined in:

- [src/lendbase/models.py](../src/lendbase/models.py)

The current CRUD flow uses:

- [src/lendbase/inventory.py](../src/lendbase/inventory.py)
- [src/lendbase/templates/inventory/form.html](../src/lendbase/templates/inventory/form.html)
- [src/lendbase/templates/inventory/detail.html](../src/lendbase/templates/inventory/detail.html)
- [src/lendbase/templates/inventory/list.html](../src/lendbase/templates/inventory/list.html)

Database migrations live in:

- [migrations/versions](../migrations/versions)

## Decide whether a new field belongs in the schema

Add a real field when:

- the value appears on many items
- the value should be validated
- the value should be searchable, filterable, or exported later

Use `notes` when:

- the data is irregular
- it comes from trailing one-off spreadsheet columns
- it is free-form context rather than structured metadata

## Steps to add a new field

1. Update the SQLAlchemy model

Add the field to `Item` in [src/lendbase/models.py](../src/lendbase/models.py).

Example:

```python
storage_location: Mapped[str | None] = mapped_column(String(120))
```

2. Create a migration

Add a new Alembic migration under [migrations/versions](../migrations/versions).

Example:

```python
def upgrade() -> None:
    op.add_column("items", sa.Column("storage_location", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("items", "storage_location")
```

Apply it locally:

```cmd
uv run alembic upgrade head
```

3. Update the Flask CRUD flow

In [src/lendbase/inventory.py](../src/lendbase/inventory.py), update:

- `build_item_form_data`
- `validate_item_form`
- `apply_item_form`
- `serialize_item_snapshot`

If the field is optional, make sure missing values are safely turned into empty strings
for the form layer.

4. Update the templates

Add the field to:

- [src/lendbase/templates/inventory/form.html](../src/lendbase/templates/inventory/form.html)
- [src/lendbase/templates/inventory/detail.html](../src/lendbase/templates/inventory/detail.html)

Add it to the list page only if it is useful for overview scanning:

- [src/lendbase/templates/inventory/list.html](../src/lendbase/templates/inventory/list.html)

5. Update tests

Adjust or add tests in:

- [tests/test_inventory.py](../tests/test_inventory.py)
- [tests/test_migrations.py](../tests/test_migrations.py)

At minimum, verify:

- item creation accepts the field
- item edit preserves and updates the field
- the migration creates the new column

6. Update documentation

If the field affects setup or usage, update:

- [README.md](../README.md)

If it affects longer-term product or implementation direction, update:

- [VIBE_NOTES.md](../VIBE_NOTES.md)

## Verification checklist

After extending the schema, run:

```cmd
uv run alembic upgrade head
uv run ruff check .
uv run pytest -p no:cacheprovider
uv run pre-commit run --all-files
```

Then manually verify:

1. Open `/items/new`
2. Create an item using the new field
3. Open the detail page
4. Edit the item and confirm the value persists

## Common pitfalls

- Updating the model without a migration leaves the database behind
- Updating the migration without the form/template code leaves the field unreachable in the UI
- Optional values may be `None`, so form helpers must coerce them safely
- Renames should use a dedicated migration so existing local rows are preserved

## Rule of thumb for this project

Repeated structured Excel columns are good candidates for real fields.
Trailing comments, mixed-purpose notes, and sheet-specific exceptions should usually
stay in `notes` until a later workflow clearly needs more structure.
