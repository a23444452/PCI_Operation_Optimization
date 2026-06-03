from datetime import date

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Defect(TimestampMixin, Base):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    sheet_id: Mapped[str] = mapped_column(String(50), nullable=False)
    line_id: Mapped[str] = mapped_column(String(50), nullable=False)
    x_position: Mapped[float] = mapped_column(Float, nullable=False)
    y_position: Mapped[float] = mapped_column(Float, nullable=False)
    loss_code: Mapped[str] = mapped_column(String(20), nullable=False)
    lis_defect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    defect_size: Mapped[float] = mapped_column(Float, nullable=False)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
