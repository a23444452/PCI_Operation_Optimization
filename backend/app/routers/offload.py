import logging

from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.services.pipeline_cache_service import (
    get_cached_pipeline,
    invalidate_cache,
    save_pipeline_cache,
)
from app.services.pipeline_service import run_offload_pipeline

logger = logging.getLogger(__name__)

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


@router.get("/pipeline")
def run_pipeline_endpoint(
    start_date: str = Query(..., description="Start date, e.g. 2025-06-03"),
    end_date: str = Query(..., description="End date, e.g. 2025-06-04"),
    max_batches: int = Query(20, description="Limit batch count for defect query (0=all, default 20 for fast preview)"),
    plants: str = Query("", description="Comma-separated plant prefixes to filter specs, e.g. 'HF,BJ'. Empty=all"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return pipeline results, using cache when available."""
    plant_list = [p.strip() for p in plants.split(",") if p.strip()] if plants else []

    cached = get_cached_pipeline(db, start_date, end_date, plant_list)
    if cached:
        return ok(cached)

    try:
        results = run_offload_pipeline(start_date, end_date, max_batches=max_batches, plant_filter=plant_list)
        save_pipeline_cache(db, start_date, end_date, plant_list, results, triggered_by="manual")
        results["_cache_meta"] = {"cached": False}
        return ok(results)
    except Exception as exc:
        logger.exception("Pipeline execution failed")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(exc)}")


@router.post("/pipeline/refresh")
def refresh_pipeline(
    start_date: str = Query(..., description="Start date"),
    end_date: str = Query(..., description="End date"),
    plants: str = Query("", description="Comma-separated plant prefixes"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Invalidate cache and re-run pipeline for the given date range."""
    plant_list = [p.strip() for p in plants.split(",") if p.strip()] if plants else []

    invalidate_cache(db, start_date, end_date)

    try:
        results = run_offload_pipeline(start_date, end_date, max_batches=0, plant_filter=plant_list)
        save_pipeline_cache(db, start_date, end_date, plant_list, results, triggered_by="manual")
        results["_cache_meta"] = {"cached": False}
        return ok(results)
    except Exception as exc:
        logger.exception("Pipeline refresh failed")
        raise HTTPException(status_code=500, detail=f"Pipeline refresh failed: {str(exc)}")
