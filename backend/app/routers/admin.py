from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role
from app.models.etl_job import EtlJob
from app.models.user import User
from app.schemas.common import ok

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/etl-status")
def get_etl_status(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Get recent ETL job statuses."""
    jobs = (
        db.query(EtlJob)
        .order_by(EtlJob.started_at.desc())
        .limit(50)
        .all()
    )
    return ok([
        {
            "id": j.id,
            "job_type": j.job_type,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            "status": j.status,
            "records_count": j.records_count,
            "error_msg": j.error_msg,
        }
        for j in jobs
    ])


@router.post("/etl/trigger/{job_type}")
def trigger_etl(
    job_type: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Manually trigger an ETL job."""
    valid_types = {"batch_sync", "defect_sync", "cube_sync", "shipping_import"}
    if job_type not in valid_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid job type. Valid: {valid_types}"
        )

    from app.etl.batch_sync import run_batch_sync
    from app.etl.cube_sync import run_cube_sync
    from app.etl.defect_sync import run_defect_sync
    from app.etl.shipping_import import run_shipping_import

    job_map = {
        "batch_sync": run_batch_sync,
        "defect_sync": run_defect_sync,
        "cube_sync": run_cube_sync,
        "shipping_import": run_shipping_import,
    }

    # Run synchronously for now (could use background task in future)
    job_map[job_type]()
    return ok({"message": f"ETL job '{job_type}' triggered"})
