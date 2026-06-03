import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    if not settings.etl_enabled:
        logger.info("ETL scheduler disabled (etl_enabled=False)")
        return

    from app.etl.batch_sync import run_batch_sync
    from app.etl.defect_sync import run_defect_sync
    from app.etl.cube_sync import run_cube_sync
    from app.etl.shipping_import import run_shipping_import

    scheduler.add_job(run_batch_sync, CronTrigger(hour=6, minute=0), id="batch_sync")
    scheduler.add_job(run_defect_sync, CronTrigger(hour=6, minute=15), id="defect_sync")
    scheduler.add_job(run_cube_sync, CronTrigger(hour=6, minute=30), id="cube_sync")
    scheduler.add_job(run_shipping_import, CronTrigger(hour=6, minute=45), id="shipping_import")

    scheduler.start()
    logger.info("ETL scheduler started with 4 daily jobs at 06:00-06:45")
