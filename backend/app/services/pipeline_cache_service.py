import json
import logging
from datetime import datetime, timezone

import pandas as pd

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pipeline_cache import PipelineCache
from app.services.pipeline_service import run_offload_pipeline

logger = logging.getLogger(__name__)


def _normalize_plants_key(plants: list[str]) -> str:
    return ",".join(sorted(plants))


def get_cached_pipeline(db: Session, start: str, end: str, plants: list[str]) -> dict | None:
    cache = (
        db.query(PipelineCache)
        .filter(
            PipelineCache.query_start == start,
            PipelineCache.query_end == end,
            PipelineCache.plants == _normalize_plants_key(plants),
            PipelineCache.status == "completed",
        )
        .order_by(PipelineCache.created_at.desc())
        .first()
    )
    if not cache:
        return None
    result = json.loads(cache.result_json)
    result["_cache_meta"] = {
        "cached": True,
        "cached_at": cache.created_at.isoformat(),
        "triggered_by": cache.triggered_by,
    }
    return result


def save_pipeline_cache(
    db: Session,
    start: str,
    end: str,
    plants: list[str],
    result: dict,
    triggered_by: str,
    error_msg: str | None = None,
) -> PipelineCache:
    status = "completed" if error_msg is None else "failed"
    cache = PipelineCache(
        query_start=start,
        query_end=end,
        plants=_normalize_plants_key(plants),
        result_json=json.dumps(result, ensure_ascii=False, default=str) if result else "{}",
        status=status,
        triggered_by=triggered_by,
        error_msg=error_msg,
    )
    db.add(cache)
    db.commit()
    db.refresh(cache)
    return cache


def invalidate_cache(db: Session, start: str, end: str) -> int:
    count = (
        db.query(PipelineCache)
        .filter(
            PipelineCache.query_start == start,
            PipelineCache.query_end == end,
        )
        .delete()
    )
    db.commit()
    logger.info("Invalidated %d cache entries for %s ~ %s", count, start, end)
    return count


def run_and_cache_pipeline(
    start: str,
    end: str,
    plants: list[str],
    triggered_by: str,
    max_batches: int = 0,
) -> dict:
    db = SessionLocal()
    try:
        logger.info("Running pipeline for cache: %s ~ %s, plants=%s", start, end, plants)
        result = run_offload_pipeline(start, end, max_batches=max_batches, plant_filter=plants)
        save_pipeline_cache(db, start, end, plants, result, triggered_by)
        logger.info("Pipeline cached successfully: %s ~ %s", start, end)
        return result
    except Exception as e:
        logger.exception("Pipeline failed for cache: %s ~ %s", start, end)
        save_pipeline_cache(db, start, end, plants, {}, triggered_by, error_msg=str(e)[:500])
        raise
    finally:
        db.close()
