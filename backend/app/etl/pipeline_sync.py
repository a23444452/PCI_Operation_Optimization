import logging
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models.plant import Plant
from app.services.pipeline_cache_service import run_and_cache_pipeline

logger = logging.getLogger(__name__)


def run_pipeline_sync():
    """Daily scheduled job: cache pipeline results for previous day 7:00 ~ today 7:00."""
    now = datetime.now()
    today_7am = now.replace(hour=7, minute=0, second=0, microsecond=0)
    yesterday_7am = today_7am - timedelta(days=1)

    start = yesterday_7am.strftime("%Y-%m-%d %H:%M")
    end = today_7am.strftime("%Y-%m-%d %H:%M")

    db = SessionLocal()
    try:
        plants = [p.code for p in db.query(Plant).filter(Plant.is_active == True).all()]
    finally:
        db.close()

    if not plants:
        logger.warning("No active plants found, skipping pipeline sync")
        return

    logger.info("Pipeline sync started: %s ~ %s, plants=%s", start, end, plants)
    run_and_cache_pipeline(start, end, plants, triggered_by="scheduler", max_batches=0)
    logger.info("Pipeline sync completed: %s ~ %s", start, end)
