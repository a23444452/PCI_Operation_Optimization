import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from app.config import settings
from app.database import SessionLocal
from app.models.etl_job import EtlJob
from app.models.plant import Plant
from app.models.shipping import ShippingSchedule

logger = logging.getLogger(__name__)


def _find_new_files(folder: str) -> list[Path]:
    """Find Excel files modified today in the shipping folder."""
    today = date.today()
    files = []
    folder_path = Path(folder)
    if not folder_path.exists():
        logger.warning("Shipping folder does not exist: %s", folder)
        return []

    for f in folder_path.glob("*.xlsx"):
        mtime = datetime.fromtimestamp(os.path.getmtime(f)).date()
        if mtime >= today:
            files.append(f)
    return files


def run_shipping_import():
    """Import shipping schedule from Excel files in shared folder."""
    job = EtlJob(
        job_type="shipping_import",
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db = SessionLocal()
    try:
        db.add(job)
        db.commit()

        if not settings.shipping_folder:
            job.status = "skipped"
            job.finished_at = datetime.now(timezone.utc)
            job.error_msg = "shipping_folder not configured"
            db.commit()
            logger.warning("shipping_import skipped: shipping_folder not configured")
            return

        files = _find_new_files(settings.shipping_folder)
        if not files:
            job.status = "completed"
            job.finished_at = datetime.now(timezone.utc)
            job.records_count = 0
            job.error_msg = "No new files found"
            db.commit()
            logger.info("shipping_import: no new files")
            return

        # Build plant code -> id mapping
        plants = {p.code: p.id for p in db.query(Plant).all()}

        count = 0
        for file_path in files:
            df = pd.read_excel(file_path)
            # Expected columns: plant_code, target_qty, ship_date
            required_cols = {"plant_code", "target_qty", "ship_date"}
            if not required_cols.issubset(set(df.columns)):
                logger.warning("Skipping %s: missing required columns", file_path.name)
                continue

            for _, row in df.iterrows():
                plant_code = str(row["plant_code"]).strip()
                plant_id = plants.get(plant_code)
                if plant_id is None:
                    logger.warning("Unknown plant code: %s", plant_code)
                    continue

                ship_date = pd.to_datetime(row["ship_date"]).date()
                target_qty = int(row["target_qty"])

                # Upsert: check if schedule exists for this plant + date
                existing = (
                    db.query(ShippingSchedule)
                    .filter(
                        ShippingSchedule.plant_id == plant_id,
                        ShippingSchedule.ship_date == ship_date,
                    )
                    .first()
                )
                if existing:
                    existing.target_qty = target_qty
                    existing.source_file = file_path.name
                else:
                    db.add(
                        ShippingSchedule(
                            plant_id=plant_id,
                            target_qty=target_qty,
                            ship_date=ship_date,
                            source_file=file_path.name,
                        )
                    )
                count += 1

            db.commit()

        job.status = "completed"
        job.finished_at = datetime.now(timezone.utc)
        job.records_count = count
        db.commit()
        logger.info("shipping_import completed: %d records from %d files", count, len(files))

    except Exception as exc:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_msg = str(exc)[:500]
        db.commit()
        logger.error("shipping_import failed: %s", exc)
    finally:
        db.close()
