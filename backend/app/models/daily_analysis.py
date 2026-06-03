from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class DailyMl(TimestampMixin, Base):
    __tablename__ = "daily_ml"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tank_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tanks.id"), nullable=False
    )
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)


class DailyMsl(TimestampMixin, Base):
    __tablename__ = "daily_msl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tank_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tanks.id"), nullable=False
    )
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)


class DailyAttribute(TimestampMixin, Base):
    __tablename__ = "daily_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tank_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tanks.id"), nullable=False
    )
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
