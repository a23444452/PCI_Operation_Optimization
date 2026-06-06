from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class PipelineCache(TimestampMixin, Base):
    __tablename__ = "pipeline_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_start: Mapped[str] = mapped_column(String(30), nullable=False)
    query_end: Mapped[str] = mapped_column(String(30), nullable=False)
    plants: Mapped[str] = mapped_column(String(100), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
