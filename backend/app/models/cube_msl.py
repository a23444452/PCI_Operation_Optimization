from datetime import date

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class CubeMsl(TimestampMixin, Base):
    __tablename__ = "cube_msl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crate_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    gen: Mapped[str] = mapped_column(String(20), nullable=False)
    defect_item: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
