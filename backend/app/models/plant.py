from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Plant(TimestampMixin, Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criteria: Mapped[list["PlantCriteria"]] = relationship(
        back_populates="plant", lazy="selectin", cascade="all, delete-orphan"
    )


class PlantCriteria(TimestampMixin, Base):
    __tablename__ = "plant_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    defect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    min_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    operator: Mapped[str] = mapped_column(String(5), default="<", nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    plant: Mapped["Plant"] = relationship(back_populates="criteria")


class OffloadSelection(TimestampMixin, Base):
    __tablename__ = "offload_selections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False)
    plant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plants.id"), nullable=False
    )
    selected_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="selected", nullable=False)
    is_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
