from datetime import date

from pydantic import BaseModel


class AnalysisDataPoint(BaseModel):
    tank_id: int
    tank_name: str | None = None
    crate_id: str | None
    date: date
    value: float | None


class ItemInfo(BaseModel):
    id: int
    name: str
    display_name: str | None


class TankInfo(BaseModel):
    id: int
    name: str
    code: str
