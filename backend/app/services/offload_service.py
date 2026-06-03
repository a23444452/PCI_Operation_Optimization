from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.defect import Defect
from app.models.plant import PlantCriteria


def evaluate_crates(db: Session, plant_id: int) -> list[dict]:
    """Evaluate available crates against plant criteria.

    For each crate:
    1. Get total sheet count from batches (in_qty)
    2. Count defects grouped by lis_defect_type
    3. Compute ratio = defect_count / in_qty
    4. Compare ratio against each criterion's threshold
    """
    criteria = (
        db.query(PlantCriteria)
        .filter(PlantCriteria.plant_id == plant_id, PlantCriteria.is_active == True)
        .all()
    )

    if not criteria:
        return []

    crates = (
        db.query(Batch.crate_id, Batch.batch_id, Batch.in_qty, Batch.cut_lot_end_date)
        .filter(Batch.crate_id.isnot(None))
        .distinct(Batch.crate_id)
        .all()
    )

    results = []
    for crate in crates:
        crate_id = crate[0]
        batch_id = crate[1]
        in_qty = crate[2] or 0

        if in_qty == 0:
            continue

        defect_counts = (
            db.query(Defect.lis_defect_type, func.count(Defect.id))
            .filter(Defect.batch_id == batch_id)
            .group_by(Defect.lis_defect_type)
            .all()
        )

        defect_map = {dtype: cnt for dtype, cnt in defect_counts if dtype}
        defect_ratios = {dtype: cnt / in_qty for dtype, cnt in defect_map.items()}

        is_compliant = True
        failed = []
        for c in criteria:
            ratio = defect_ratios.get(c.defect_type, 0.0)

            if c.min_size is not None:
                sized_count = (
                    db.query(func.count(Defect.id))
                    .filter(
                        Defect.batch_id == batch_id,
                        Defect.lis_defect_type == c.defect_type,
                        Defect.defect_size >= c.min_size,
                    )
                    .scalar()
                )
                ratio = (sized_count or 0) / in_qty

            if c.operator == "<" and ratio >= c.threshold:
                is_compliant = False
                failed.append(c.defect_type)
            elif c.operator == "<=" and ratio > c.threshold:
                is_compliant = False
                failed.append(c.defect_type)
            elif c.operator == ">" and ratio <= c.threshold:
                is_compliant = False
                failed.append(c.defect_type)

        results.append({
            "crate_id": crate_id,
            "batch_id": batch_id,
            "in_qty": in_qty,
            "cut_lot_end_date": crate[3],
            "defect_ratios": defect_ratios,
            "is_compliant": is_compliant,
            "failed_criteria": failed,
        })

    return results
