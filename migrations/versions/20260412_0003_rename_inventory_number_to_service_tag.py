"""Rename inventory number to service tag.

Revision ID: 20260412_0003
Revises: 20260412_0002
Create Date: 2026-04-12 16:20:00
"""

from __future__ import annotations

from alembic import op


revision = "20260412_0003"
down_revision = "20260412_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("items", "inventory_number", new_column_name="service_tag")
    op.drop_index("ix_items_inventory_number", table_name="items")
    op.create_index("ix_items_service_tag", "items", ["service_tag"], unique=False)


def downgrade() -> None:
    op.alter_column("items", "service_tag", new_column_name="inventory_number")
    op.drop_index("ix_items_service_tag", table_name="items")
    op.create_index("ix_items_inventory_number", "items", ["inventory_number"], unique=False)
