import logging
from datetime import date, datetime, timezone

from app.database import SessionLocal
from app.models.batch import Batch
from app.models.defect import Defect
from app.models.etl_job import EtlJob

logger = logging.getLogger(__name__)

DEFECT_QUERY = """
SELECT
    batch_id,
    sheet_id,
    line_id,
    x_position,
    y_position,
    loss_code,
    lis_defect_type,
    defect_size
FROM defect_detail
WHERE batch_id = :batch_id
"""


def run_defect_sync():
    """Sync defect data from Oracle PPDA for recently synced batches."""
    job = EtlJob(
        job_type="defect_sync",
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db = SessionLocal()
    try:
        db.add(job)
        db.commit()

        today = date.today()
        batch_ids = [
            row[0]
            for row in db.query(Batch.batch_id)
            .filter(Batch.etl_date == today)
            .distinct()
            .all()
        ]

        from app.etl.connections import get_oracle_connection

        count = 0
        with get_oracle_connection() as conn:
            cursor = conn.cursor()
            for batch_id in batch_ids:
                cursor.execute(DEFECT_QUERY, {"batch_id": batch_id})
                rows = cursor.fetchall()
                for row in rows:
                    db.add(
                        Defect(
                            batch_id=row[0],
                            sheet_id=row[1],
                            line_id=row[2],
                            x_position=row[3],
                            y_position=row[4],
                            loss_code=row[5],
                            lis_defect_type=row[6],
                            defect_size=row[7],
                            etl_date=today,
                        )
                    )
                    count += 1
                # Commit per batch to avoid huge transactions
                db.commit()

        job.status = "completed"
        job.finished_at = datetime.now(timezone.utc)
        job.records_count = count
        db.commit()
        logger.info("defect_sync completed: %d records", count)

    except Exception as exc:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_msg = str(exc)[:500]
        db.commit()
        logger.error("defect_sync failed: %s", exc)
    finally:
        db.close()
