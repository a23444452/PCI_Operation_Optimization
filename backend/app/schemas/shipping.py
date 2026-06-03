from datetime import date

from pydantic import BaseModel


class ScheduleItem(BaseModel):
    id: int
    plant_id: int
    plant_name: str | None = None
    target_qty: int
    ship_date: date
    source_file: str | None
    assigned_qty: int = 0
    assignment_count: int = 0


class AssignmentItem(BaseModel):
    id: int
    crate_id: str
    priority_order: int
    in_qty: int | None = None
    cut_lot_end_date: date | None = None


class RecalculateRequest(BaseModel):
    schedule_id: int
