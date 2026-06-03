import logging
from contextlib import contextmanager

import oracledb
import pyodbc

from app.config import settings

logger = logging.getLogger(__name__)


@contextmanager
def get_oracle_connection():
    """Connect to Oracle PPDA database."""
    conn = None
    try:
        conn = oracledb.connect(settings.ppda_conn)
        yield conn
    except Exception as exc:
        logger.error("Oracle connection failed: %s", exc)
        raise
    finally:
        if conn:
            conn.close()


@contextmanager
def get_mssql_connection():
    """Connect to MSSQL MESDW database."""
    conn = None
    try:
        conn = pyodbc.connect(settings.mesdw_conn)
        yield conn
    except Exception as exc:
        logger.error("MSSQL connection failed: %s", exc)
        raise
    finally:
        if conn:
            conn.close()
