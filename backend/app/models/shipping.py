from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class ShippingSchedule(TimestampMixin, Base):
    __tablename__ = "shipping_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plants.id"), nullable=False
    )
    target_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    ship_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    assignments: Mapped[list["ShippingAssignment"]] = relationship(
        back_populates="schedule", lazy="selectin", cascade="all, delete-orphan"
    )


class ShippingAssignment(TimestampMixin, Base):
    __tablename__ = "shipping_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shipping_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    priority_order: Mapped[int] = mapped_column(Integer, nullable=False)

    schedule: Mapped["ShippingSchedule"] = relationship(back_populates="assignments")
