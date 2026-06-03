import logging
from datetime import date, datetime, timezone

from app.database import SessionLocal
from app.models.batch import Batch
from app.models.etl_job import EtlJob

logger = logging.getLogger(__name__)

BATCH_QUERY = """
SELECT
    batch_id,
    crate_id,
    in_qty,
    cut_lot_end_date
FROM dbo.v_batch_info
WHERE cut_lot_end_date >= DATEADD(day, -30, GETDATE())
"""


def run_batch_sync():
    """Sync recent batches from MESDW to local PostgreSQL."""
    job = EtlJob(
        job_type="batch_sync",
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db = SessionLocal()
    try:
        db.add(job)
        db.commit()

        from app.etl.connections import get_mssql_connection

        with get_mssql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(BATCH_QUERY)
            rows = cursor.fetchall()

        count = 0
        today = date.today()
        for row in rows:
            existing = (
                db.query(Batch)
                .filter(Batch.batch_id == row[0], Batch.crate_id == row[1])
                .first()
            )
            if existing:
                existing.in_qty = row[2]
                existing.cut_lot_end_date = row[3]
                existing.etl_date = today
            else:
                db.add(
                    Batch(
                        batch_id=row[0],
                        crate_id=row[1],
                        in_qty=row[2],
                        cut_lot_end_date=row[3],
                        etl_date=today,
                    )
                )
            count += 1

        db.commit()

        job.status = "completed"
        job.finished_at = datetime.now(timezone.utc)
        job.records_count = count
        db.commit()
        logger.info("batch_sync completed: %d records", count)

    except Exception as exc:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_msg = str(exc)[:500]
        db.commit()
        logger.error("batch_sync failed: %s", exc)
    finally:
        db.close()
