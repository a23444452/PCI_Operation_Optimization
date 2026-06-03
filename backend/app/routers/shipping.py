from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.batch import Batch
from app.models.plant import Plant
from app.models.shipping import ShippingAssignment, ShippingSchedule
from app.models.user import User
from app.schemas.common import ok
from app.schemas.shipping import AssignmentItem, RecalculateRequest, ScheduleItem
from app.services.shipping_service import run_fifo_assignment

router = APIRouter(prefix="/api/v1/shipping", tags=["shipping"])


@router.get("/schedules")
def list_schedules(
    plant_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(ShippingSchedule)
    if plant_id:
        query = query.filter(ShippingSchedule.plant_id == plant_id)
    schedules = query.order_by(ShippingSchedule.ship_date.desc()).all()

    results = []
    for s in schedules:
        assignments = (
            db.query(ShippingAssignment)
            .filter(ShippingAssignment.schedule_id == s.id)
            .all()
        )
        # Sum assigned qty
        assigned_qty = 0
        for a in assignments:
            batch = db.query(Batch).filter(Batch.crate_id == a.crate_id).first()
            if batch:
                assigned_qty += batch.in_qty or 0

        plant = db.query(Plant).filter(Plant.id == s.plant_id).first()
        results.append(
            ScheduleItem(
                id=s.id,
                plant_id=s.plant_id,
                plant_name=plant.name if plant else None,
                target_qty=s.target_qty,
                ship_date=s.ship_date,
                source_file=s.source_file,
                assigned_qty=assigned_qty,
                assignment_count=len(assignments),
            ).model_dump()
        )

    return ok(results)


@router.get("/schedules/{schedule_id}/assignments")
def get_assignments(
    schedule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    schedule = (
        db.query(ShippingSchedule)
        .filter(ShippingSchedule.id == schedule_id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    assignments = (
        db.query(ShippingAssignment)
        .filter(ShippingAssignment.schedule_id == schedule_id)
        .order_by(ShippingAssignment.priority_order.asc())
        .all()
    )

    results = []
    for a in assignments:
        batch = db.query(Batch).filter(Batch.crate_id == a.crate_id).first()
        results.append(
            AssignmentItem(
                id=a.id,
                crate_id=a.crate_id,
                priority_order=a.priority_order,
                in_qty=batch.in_qty if batch else None,
                cut_lot_end_date=batch.cut_lot_end_date if batch else None,
            ).model_dump()
        )

    return ok(results)


@router.post("/recalculate")
def recalculate(
    body: RecalculateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    schedule = (
        db.query(ShippingSchedule)
        .filter(ShippingSchedule.id == body.schedule_id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    count = run_fifo_assignment(db, body.schedule_id)
    return ok({"message": f"Recalculated: {count} crates assigned"})
