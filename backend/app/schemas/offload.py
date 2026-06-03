from datetime import date

from pydantic import BaseModel


class PlantItem(BaseModel):
    id: int
    name: str
    code: str


class CriteriaItem(BaseModel):
    defect_type: str
    min_size: float | None
    operator: str
    threshold: float


class CrateEvaluation(BaseModel):
    crate_id: str
    batch_id: str
    in_qty: int | None
    cut_lot_end_date: date | None
    defect_ratios: dict[str, float]
    is_compliant: bool
    failed_criteria: list[str] = []


class SelectCratesRequest(BaseModel):
    plant_id: int
    crate_ids: list[str]


class OffloadSelectionItem(BaseModel):
    id: int
    crate_id: str
    plant_id: int
    status: str
    is_override: bool
