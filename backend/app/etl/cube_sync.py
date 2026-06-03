import logging
from datetime import date, datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app.models.cube_msl import CubeMsl
from app.models.etl_job import EtlJob

logger = logging.getLogger(__name__)

MDX_QUERY = """
SELECT
    {[Measures].[Value]} ON COLUMNS,
    NON EMPTY {
        [Crate].[Crate ID].Members *
        [Gen].[Gen].Members *
        [Defect Item].[Item Name].Members
    } ON ROWS
FROM [MSL_Cube]
"""


def _query_cube() -> list[tuple]:
    """Execute MDX query against SSAS cube using ADOMD.NET via pythonnet."""
    import clr

    clr.AddReference(settings.adomd_dll_path)
    from Microsoft.AnalysisServices.AdomdClient import AdomdCommand, AdomdConnection

    conn = AdomdConnection(settings.cube_conn)
    conn.Open()
    try:
        cmd = AdomdCommand(MDX_QUERY, conn)
        reader = cmd.ExecuteReader()
        results = []
        while reader.Read():
            crate_id = str(reader[0]) if reader[0] else None
            gen = str(reader[1]) if reader[1] else None
            defect_item = str(reader[2]) if reader[2] else None
            value = float(reader[3]) if reader[3] else None
            if crate_id:
                results.append((crate_id, gen, defect_item, value))
        reader.Close()
        return results
    finally:
        conn.Close()


def run_cube_sync():
    """Sync MSL data from SSAS Cube to local PostgreSQL."""
    job = EtlJob(
        job_type="cube_sync",
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db = SessionLocal()
    try:
        db.add(job)
        db.commit()

        if not settings.cube_conn:
            job.status = "skipped"
            job.finished_at = datetime.now(timezone.utc)
            job.error_msg = "cube_conn not configured"
            db.commit()
            logger.warning("cube_sync skipped: cube_conn not configured")
            return

        rows = _query_cube()
        today = date.today()

        # Delete today's data and re-insert (full refresh for the day)
        db.query(CubeMsl).filter(CubeMsl.etl_date == today).delete()
        db.commit()

        for crate_id, gen, defect_item, value in rows:
            db.add(
                CubeMsl(
                    crate_id=crate_id,
                    gen=gen,
                    defect_item=defect_item,
                    value=value,
                    etl_date=today,
                )
            )

        db.commit()

        job.status = "completed"
        job.finished_at = datetime.now(timezone.utc)
        job.records_count = len(rows)
        db.commit()
        logger.info("cube_sync completed: %d records", len(rows))

    except Exception as exc:
        job.status = "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.error_msg = str(exc)[:500]
        db.commit()
        logger.error("cube_sync failed: %s", exc)
    finally:
        db.close()
