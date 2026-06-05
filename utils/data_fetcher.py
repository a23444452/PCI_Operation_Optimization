"""High-level data fetching: combines connection + query."""
import pandas as pd

from utils.db_connections import get_PPDA, get_MESDW, get_cube
from utils.sql_queries import (
    build_in_clause,
    BATCH_CRATE_SQL,
    build_batch_crate_query,
    build_crate_audit_query,
    build_defect_query,
    build_cube_query,
)


# Oracle IN-list 上限 (1000)，建議 500 以保險
DEFECT_BATCH_SIZE = 500


def _chunked(lst, n):
    """切分 list（避免超過 Oracle IN 上限）"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def fetch_crate_resume(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Build the master 'crate resume' table.

    Parameters
    ----------
    start_date : optional, e.g. "2025-06-03"
    end_date : optional, e.g. "2025-06-04"
    If both provided, uses explicit date range. Otherwise uses default (last 1.5 days).
    """
    if start_date and end_date:
        sql = build_batch_crate_query(start_date, end_date)
    else:
        sql = BATCH_CRATE_SQL
    df = get_MESDW(sql)
    df = df.dropna(subset=["crate_id"])
    df = df.drop_duplicates(subset=["crate_id", "batch_id"], keep="first")
    
    if df.empty:
        return df
    
    crate_ids = df["crate_id"].unique().tolist()
    audit_long = get_PPDA(build_crate_audit_query(build_in_clause(crate_ids)))
    
    audit_wide = (
        audit_long.pivot_table(
            index="crate_id",
            columns="itm_name",
            values="itm_value1",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"QUANTITY": "in_qty"})
    )
    
    for col in ["START_TIME", "END_TIME"]:
        if col in audit_wide.columns:
            audit_wide[col] = pd.to_datetime(
                audit_wide[col], format="%Y%m%d%H%M%S", errors="coerce"
            )
    if "in_qty" in audit_wide.columns:
        audit_wide["in_qty"] = pd.to_numeric(audit_wide["in_qty"], errors="coerce")
    
    return df.merge(audit_wide, on="crate_id", how="inner")


def fetch_defects_per_batch(batch_ids: list, 
                            batch_size: int = DEFECT_BATCH_SIZE,
                            verbose: bool = True) -> pd.DataFrame:
    """
    Fetch defect data using IN clause in chunks (much faster than one-by-one).
    
    Parameters
    ----------
    batch_ids : list of BATCH_IDs to query
    batch_size : how many BATCH_IDs per query (max 1000 by Oracle limit)
    """
    if not batch_ids:
        return pd.DataFrame()
    
    chunks = list(_chunked(batch_ids, batch_size))
    total_chunks = len(chunks)
    results = []
    
    for i, chunk in enumerate(chunks, 1):
        if verbose:
            print(f"  [Chunk {i}/{total_chunks}] Querying {len(chunk)} batch_ids...", end=" ")
        try:
            sql = build_defect_query(chunk)
            df = get_PPDA(sql)
            df = df.dropna(subset=["loss_code"])
            results.append(df)
            if verbose:
                print(f"→ {len(df)} rows")
        except Exception as e:
            print(f"FAILED: {repr(e)[:200]}")
    
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


def fetch_cube_data(crate_ids: list) -> pd.DataFrame:
    """Run MDX query for the given crate_ids."""
    if not crate_ids:
        return pd.DataFrame()
    return get_cube(build_cube_query(crate_ids))