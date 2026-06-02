"""Database connection helpers."""
import sys
import sqlalchemy
import pandas as pd

from config import PPDA_CONN, MESDW_CONN, CUBE_CONN, ADOMD_DLL_PATH


def get_PPDA(query: str) -> pd.DataFrame:
    """Run a query against the PPDA Oracle DB."""
    engine = sqlalchemy.create_engine(PPDA_CONN, thick_mode=True)
    try:
        with engine.connect() as conn:
            return pd.read_sql_query(query, conn)
    finally:
        engine.dispose()


def get_MESDW(query: str) -> pd.DataFrame:
    """Run a query against the MESDW SQL Server."""
    engine = sqlalchemy.create_engine(MESDW_CONN)
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    finally:
        engine.dispose()


def get_cube(mdx_query: str) -> pd.DataFrame:
    """Run an MDX query against the SSAS cube."""
    # Lazy import: load DLL only when needed
    sys.path.append(ADOMD_DLL_PATH)
    import clr
    clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
    from pyadomd import Pyadomd

    with Pyadomd(CUBE_CONN) as conn:
        with conn.cursor().execute(mdx_query) as cur:
            rows = cur.fetchall()
            cols = [c.name for c in cur.description]
    return pd.DataFrame(rows, columns=cols)