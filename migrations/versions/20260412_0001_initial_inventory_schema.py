"""Create initial inventory schema.

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12 13:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260412_0001"
down_revision = None
branch_labels = None
depends_on = None


item_status_enum = sa.Enum(
    "in storage",
    "lent out",
    "broken",
    "retired/disposed",
    "lost",
    "under repair",
    name="itemstatus",
    native_enum=False,
    length=32,
)

audit_event_type_enum = sa.Enum(
    "item_created",
    "item_edited",
    "status_changed",
    "item_lent_out",
    "item_returned",
    name="auditeventtype",
    native_enum=False,
    length=32,
)


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=100), nullable=False),
        sa.Column("inventory_number", sa.String(length=120), nullable=False),
        sa.Column("hu_number", sa.String(length=120), nullable=False),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("brand_model", sa.String(length=200), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("warranty_end", sa.Date(), nullable=True),
        sa.Column("status", item_status_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_items")),
        sa.UniqueConstraint("inventory_number", name=op.f("uq_items_inventory_number")),
        sa.UniqueConstraint("hu_number", name=op.f("uq_items_hu_number")),
    )
    op.create_index("ix_items_hu_number", "items", ["hu_number"], unique=False)
    op.create_index("ix_items_inventory_number", "items", ["inventory_number"], unique=False)
    op.create_index("ix_items_item_type", "items", ["item_type"], unique=False)
    op.create_index("ix_items_serial_number", "items", ["serial_number"], unique=False)
    op.create_index("ix_items_status", "items", ["status"], unique=False)

    op.create_table(
        "audit_log_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("event_type", audit_event_type_enum, nullable=False),
        sa.Column(
            "event_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name=op.f("fk_audit_log_entries_item_id_items"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log_entries")),
    )
    op.create_index(
        "ix_audit_log_entries_event_type",
        "audit_log_entries",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_audit_log_entries_item_event_time",
        "audit_log_entries",
        ["item_id", "event_at"],
        unique=False,
    )

    op.create_table(
        "lending_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("borrower_name", sa.String(length=200), nullable=False),
        sa.Column("lent_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name=op.f("fk_lending_records_item_id_items"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lending_records")),
    )
    op.create_index("ix_lending_records_return_date", "lending_records", ["return_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lending_records_return_date", table_name="lending_records")
    op.drop_table("lending_records")
    op.drop_index("ix_audit_log_entries_item_event_time", table_name="audit_log_entries")
    op.drop_index("ix_audit_log_entries_event_type", table_name="audit_log_entries")
    op.drop_table("audit_log_entries")
    op.drop_index("ix_items_status", table_name="items")
    op.drop_index("ix_items_serial_number", table_name="items")
    op.drop_index("ix_items_item_type", table_name="items")
    op.drop_index("ix_items_inventory_number", table_name="items")
    op.drop_index("ix_items_hu_number", table_name="items")
    op.drop_table("items")
