import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.plant import OffloadSelection
from app.models.shipping import ShippingAssignment, ShippingSchedule

logger = logging.getLogger(__name__)


def run_fifo_assignment(db: Session, schedule_id: int) -> int:
    """Run FIFO assignment for a specific shipping schedule.

    Returns the number of crates assigned.
    """
    schedule = (
        db.query(ShippingSchedule)
        .filter(ShippingSchedule.id == schedule_id)
        .first()
    )
    if not schedule:
        return 0

    # Clear existing assignments for this schedule
    db.query(ShippingAssignment).filter(
        ShippingAssignment.schedule_id == schedule_id
    ).delete()
    db.flush()

    cutoff_date = schedule.ship_date - timedelta(days=3)

    # Get already assigned crate_ids (to other schedules)
    assigned_crate_ids = {
        row[0]
        for row in db.query(ShippingAssignment.crate_id).all()
    }

    # Get offload-selected crate_ids for this plant
    selected_crate_ids = {
        row[0]
        for row in db.query(OffloadSelection.crate_id)
        .filter(
            OffloadSelection.plant_id == schedule.plant_id,
            OffloadSelection.status == "selected",
        )
        .all()
    }

    # Build eligible crates query
    query = (
        db.query(Batch)
        .filter(
            Batch.crate_id.in_(selected_crate_ids) if selected_crate_ids else False,
            Batch.cut_lot_end_date <= cutoff_date,
            Batch.cut_lot_end_date.isnot(None),
            Batch.crate_id.isnot(None),
        )
        .order_by(Batch.cut_lot_end_date.asc(), Batch.crate_id.asc())
    )

    if assigned_crate_ids:
        query = query.filter(Batch.crate_id.notin_(assigned_crate_ids))

    eligible_crates = query.all()

    # FIFO: accumulate until target reached
    accumulated_qty = 0
    count = 0
    for crate in eligible_crates:
        if accumulated_qty >= schedule.target_qty:
            break

        assignment = ShippingAssignment(
            schedule_id=schedule_id,
            crate_id=crate.crate_id,
            priority_order=count + 1,
        )
        db.add(assignment)
        accumulated_qty += crate.in_qty or 0
        count += 1

    db.commit()
    logger.info(
        "FIFO assignment for schedule %d: %d crates, %d qty (target: %d)",
        schedule_id,
        count,
        accumulated_qty,
        schedule.target_qty,
    )
    return count
