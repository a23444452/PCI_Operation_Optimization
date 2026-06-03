from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Batch(TimestampMixin, Base):
    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint("batch_id", "crate_id", name="uq_batch_crate"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    crate_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    in_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    cut_lot_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
