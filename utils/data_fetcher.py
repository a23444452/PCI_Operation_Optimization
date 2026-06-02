"""High-level data fetchers — combines connection + query + retry."""
import pandas as pd

from utils.db_connections import get_PPDA, get_MESDW, get_cube
from utils.sql_queries import (
    BATCH_CRATE_QTY_SQL,
    build_defect_query,
    build_cube_query,
)


def fetch_batch_crate_qty() -> pd.DataFrame:
    """Get batch / crate / qty from MESDW (for the past 1~2 days)."""
    df = get_MESDW(BATCH_CRATE_QTY_SQL)
    df = df.dropna(subset=["crate_id"]).drop_duplicates()
    return df


def fetch_defects_per_batch(batch_ids: list, verbose: bool = True) -> pd.DataFrame:
    """
    Loop through every batch_id and run the defect query.
    Single-batch query is much faster + safer than IN list.
    """
    results = []
    total = len(batch_ids)
    
    for i, batch in enumerate(batch_ids, 1):
        if verbose:
            print(f"[{i}/{total}] Querying {batch}...", end=" ")
        try:
            df = get_PPDA(build_defect_query(batch))
            df = df.dropna(subset=["loss_code"])
            results.append(df)
            if verbose:
                print(f"→ {len(df)} rows")
        except Exception as e:
            print(f"FAILED: {repr(e)[:200]}")
    
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


def fetch_cube_data(crate_ids: list) -> pd.DataFrame:
    """Run the MDX query for the given crates."""
    if not crate_ids:
        return pd.DataFrame()
    return get_cube(build_cube_query(crate_ids))