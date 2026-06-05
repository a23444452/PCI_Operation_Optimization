"""Database connection helpers."""
import sys
import sqlalchemy
import pandas as pd
import oracledb

from config import PPDA_CONN, MESDW_CONN, CUBE_CONN, ADOMD_DLL_PATH

ORACLE_CLIENT_DIR = r"C:\oracle64\product\12.1.0\Client_x64\BIN"

try:
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
except Exception:
    pass


def get_PPDA(query: str) -> pd.DataFrame:
    """Run a query against the PPDA Oracle DB."""
    engine = sqlalchemy.create_engine(PPDA_CONN)
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
    sys.path.append(ADOMD_DLL_PATH)
    import clr
    clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
    from pyadomd import Pyadomd

    with Pyadomd(CUBE_CONN) as conn:
        with conn.cursor().execute(mdx_query) as cur:
            rows = cur.fetchall()
            cols = [c.name for c in cur.description]
    return pd.DataFrame(rows, columns=cols)