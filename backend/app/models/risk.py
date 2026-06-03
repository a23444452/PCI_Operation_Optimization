from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class RiskRule(TimestampMixin, Base):
    __tablename__ = "risk_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    conditions_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class RiskAssessment(TimestampMixin, Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crate_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("risk_rules.id"), nullable=False
    )
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
