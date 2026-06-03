from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.plant import OffloadSelection, Plant
from app.models.user import User
from app.schemas.common import ok
from app.schemas.offload import (
    CrateEvaluation,
    OffloadSelectionItem,
    PlantItem,
    SelectCratesRequest,
)
from app.services.offload_service import evaluate_crates

router = APIRouter(prefix="/api/v1/offload", tags=["offload"])


@router.get("/plants")
def list_plants(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plants = db.query(Plant).filter(Plant.is_active == True).all()
    return ok([PlantItem(id=p.id, name=p.name, code=p.code).model_dump() for p in plants])


@router.get("/crates")
def get_crates(
    plant_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    results = evaluate_crates(db, plant_id)
    return ok([CrateEvaluation(**r).model_dump() for r in results])


@router.post("/select")
def select_crates(
    body: SelectCratesRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    results = evaluate_crates(db, body.plant_id)
    non_compliant_ids = {r["crate_id"] for r in results if not r["is_compliant"]}

    selected_non_compliant = [cid for cid in body.crate_ids if cid in non_compliant_ids]

    if selected_non_compliant and not user.has_permission("offload_override"):
        raise HTTPException(
            status_code=403,
            detail="Permission 'offload_override' required to select non-compliant crates",
        )

    for crate_id in body.crate_ids:
        is_override = crate_id in non_compliant_ids
        selection = OffloadSelection(
            crate_id=crate_id,
            plant_id=body.plant_id,
            selected_by=user.id,
            status="selected",
            is_override=is_override,
        )
        db.add(selection)

    db.commit()
    return ok({"message": f"{len(body.crate_ids)} crates selected"})


@router.get("/selections")
def get_selections(
    plant_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(OffloadSelection)
    if plant_id:
        query = query.filter(OffloadSelection.plant_id == plant_id)
    selections = query.all()
    return ok([
        OffloadSelectionItem(
            id=s.id,
            crate_id=s.crate_id,
            plant_id=s.plant_id,
            status=s.status,
            is_override=s.is_override,
        ).model_dump()
        for s in selections
    ])
