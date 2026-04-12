from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lendbase.db import Base


class ItemStatus(str, enum.Enum):
    IN_STORAGE = "in storage"
    LENT_OUT = "lent out"
    BROKEN = "broken"
    RETIRED = "retired/disposed"
    LOST = "lost"
    UNDER_REPAIR = "under repair"


class AuditEventType(str, enum.Enum):
    ITEM_CREATED = "item_created"
    ITEM_EDITED = "item_edited"
    STATUS_CHANGED = "status_changed"
    ITEM_LENT_OUT = "item_lent_out"
    ITEM_RETURNED = "item_returned"


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_inventory_number", "inventory_number"),
        Index("ix_items_hu_number", "hu_number"),
        Index("ix_items_serial_number", "serial_number"),
        Index("ix_items_item_type", "item_type"),
        Index("ix_items_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type: Mapped[str] = mapped_column(String(100), nullable=False)
    inventory_number: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    hu_number: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    serial_number: Mapped[str | None] = mapped_column(String(200))
    brand_model: Mapped[str | None] = mapped_column(String(200))
    purchase_date: Mapped[date | None] = mapped_column(Date())
    warranty_end: Mapped[date | None] = mapped_column(Date())
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, native_enum=False, length=32),
        nullable=False,
        default=ItemStatus.IN_STORAGE,
    )
    notes: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    lending_records: Mapped[list["LendingRecord"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="desc(LendingRecord.lent_date)",
    )
    audit_entries: Mapped[list["AuditLogEntry"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="desc(AuditLogEntry.event_at)"
    )


class LendingRecord(Base):
    __tablename__ = "lending_records"
    __table_args__ = (Index("ix_lending_records_return_date", "return_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    borrower_name: Mapped[str] = mapped_column(String(200), nullable=False)
    lent_date: Mapped[date] = mapped_column(Date(), nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date())
    comments: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    item: Mapped[Item] = relationship(back_populates="lending_records")


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"
    __table_args__ = (
        Index("ix_audit_log_entries_item_event_time", "item_id", "event_at"),
        Index("ix_audit_log_entries_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, native_enum=False, length=32),
        nullable=False,
    )
    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON())

    item: Mapped[Item] = relationship(back_populates="audit_entries")
