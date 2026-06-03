from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.batch import Batch
from app.models.cube_msl import CubeMsl
from app.models.defect import Defect
from app.models.plant import OffloadSelection
from app.models.user import User
from app.schemas.common import ok

router = APIRouter(prefix="/api/v1/coa", tags=["coa"])


@router.get("/data")
def get_coa_data(
    plant_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get COA data for selected offload crates.

    Returns defect ratios + MSL data for all confirmed selections.
    """
    query = db.query(OffloadSelection).filter(OffloadSelection.status == "selected")
    if plant_id:
        query = query.filter(OffloadSelection.plant_id == plant_id)
    selections = query.all()

    results = []
    for sel in selections:
        batch = db.query(Batch).filter(Batch.crate_id == sel.crate_id).first()
        if not batch:
            continue

        in_qty = batch.in_qty or 0

        # Get defect summary
        defects = (
            db.query(Defect.lis_defect_type, func.count(Defect.id))
            .filter(Defect.batch_id == batch.batch_id)
            .group_by(Defect.lis_defect_type)
            .all()
        )
        defect_ratios = {}
        for dtype, cnt in defects:
            if dtype and in_qty > 0:
                defect_ratios[dtype] = round(cnt / in_qty, 6)

        # Get MSL data
        msl_data = (
            db.query(CubeMsl.defect_item, CubeMsl.value)
            .filter(CubeMsl.crate_id == sel.crate_id)
            .all()
        )
        msl = {item: val for item, val in msl_data if item}

        results.append({
            "crate_id": sel.crate_id,
            "batch_id": batch.batch_id,
            "in_qty": in_qty,
            "cut_lot_end_date": batch.cut_lot_end_date.isoformat() if batch.cut_lot_end_date else None,
            "defect_ratios": defect_ratios,
            "msl": msl,
            "is_override": sel.is_override,
        })

    return ok(results)


@router.get("/export")
def export_coa(
    plant_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export COA data as Excel file."""
    import io

    from openpyxl import Workbook

    query = db.query(OffloadSelection).filter(OffloadSelection.status == "selected")
    if plant_id:
        query = query.filter(OffloadSelection.plant_id == plant_id)
    selections = query.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "COA Report"
    ws.append(["Crate ID", "Batch ID", "In Qty", "Cut Lot End Date", "Override"])

    for sel in selections:
        batch = db.query(Batch).filter(Batch.crate_id == sel.crate_id).first()
        ws.append([
            sel.crate_id,
            batch.batch_id if batch else "",
            batch.in_qty if batch else 0,
            str(batch.cut_lot_end_date) if batch and batch.cut_lot_end_date else "",
            "Yes" if sel.is_override else "No",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=coa_report.xlsx"},
    )
