"""
Quality Attribute Pipeline.

Produces a wide quality table (per CRATE_ID) with:
  - Quality long-table pivot (thickness, MWRNG, BOW, CRI, MRV, etc.)
  - RET (sandwich method, by process)
  - B_CURVATURE (BC, sandwich + EG filters)

Output is independent from the receiver/general spec reports.
"""
import pandas as pd

from config import (
    QUALITY_LONG_TABLE, EDGE_GRAD_TABLE, PROCESS_CONFIG, ORACLE_IN_BATCH_SIZE,
    ATTR_REQUIRED_ITMS, ATTR_RENAME_MAP, ATTR_NUMERIC_COLUMNS,
    ATTR_REQUIRED_COLUMNS, ATTR_CUSTOMER_COLUMN_ORDER,
)
from utils.db_connections import get_PPDA
from utils.sql_queries import build_in_clause


# ============================================================
# Helpers
# ============================================================
def _chunk(items: list, size: int = ORACLE_IN_BATCH_SIZE) -> list:
    """Split a list into sub-lists of `size`."""
    return [items[i : i + size] for i in range(0, len(items), size)]


def _batched_query(sql_template: str, items: list,
                   placeholder: str = "{IN_LIST}") -> pd.DataFrame:
    """Run SQL template in batches over IN-list, then concat."""
    results = []
    for batch in _chunk(items):
        sql = sql_template.replace(placeholder, build_in_clause(batch))
        df = get_PPDA(sql)
        df.columns = [c.upper() for c in df.columns]
        results.append(df)
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


def _format_size(x):
    """e.g. '2640X2300X0.485mm' -> '2300X2640' (short × long)."""
    if pd.isna(x) or x is None:
        return None
    try:
        parts = str(x).upper().split("X")
        n1 = float(parts[0])
        n2 = float(parts[1])
        short_side, long_side = min(n1, n2), max(n1, n2)
        fmt = lambda n: str(int(n)) if n == int(n) else str(n)
        return f"{fmt(short_side)}X{fmt(long_side)}"
    except Exception:
        return x


# ============================================================
# Query 1: Quality wide table
# ============================================================
def query_quality_wide(crate_list: list, process: str) -> pd.DataFrame:
    """
    Long table -> pivot wide -> rename -> unit conversion -> fill missing.
    MRV col differs between MES (MAX_MRV) and Juno (MRV_TRANSMISSION_MAX).
    """
    mrv_orig = PROCESS_CONFIG[process]["mrv_col"]
    itm_in = build_in_clause(ATTR_REQUIRED_ITMS + [mrv_orig])
    rename_map = {**ATTR_RENAME_MAP, mrv_orig: "RET_MRV_MAX"}

    sql = f"""
        SELECT CRATE_ID, ITM_NAME, ITM_VALUE1
        FROM {QUALITY_LONG_TABLE}
        WHERE CRATE_ID IN ({{IN_LIST}})
          AND ITM_NAME IN ({itm_in})
    """
    long_df = _batched_query(sql, crate_list)
    if long_df.empty:
        return pd.DataFrame(columns=ATTR_REQUIRED_COLUMNS)

    # Long → wide
    long_df = long_df.dropna(subset=["ITM_VALUE1"]).copy()
    long_df["ITM_VALUE1"] = long_df["ITM_VALUE1"].astype(str).str.strip()
    long_df = long_df[long_df["ITM_VALUE1"] != ""]
    long_df = long_df.drop_duplicates(subset=["CRATE_ID", "ITM_NAME"], keep="last")

    wide = (
        long_df.pivot(index="CRATE_ID", columns="ITM_NAME", values="ITM_VALUE1")
               .reset_index()
    )
    wide.columns.name = None
    wide = wide.rename(columns=rename_map)

    # Unit conversions
    for col in ["BOW_RANGE", "BOW_RANGE_B", "FEELER_GAGE_MAX"]:
        if col in wide.columns:
            wide[col] = pd.to_numeric(wide[col], errors="coerce") / 1000

    for col in ["CRI_MAX_RNG", "CRI_MAX_ABSMAX"]:
        if col in wide.columns:
            wide[col] = pd.to_numeric(wide[col], errors="coerce").round(1)

    for col in ATTR_NUMERIC_COLUMNS:
        if col in wide.columns:
            wide[col] = pd.to_numeric(wide[col], errors="coerce")

    for col in ["START_TIME", "END_TIME"]:
        if col in wide.columns:
            wide[col] = pd.to_datetime(wide[col], format="%Y%m%d%H%M%S",
                                       errors="coerce")

    # Fill missing required columns
    for col in ATTR_REQUIRED_COLUMNS:
        if col not in wide.columns:
            wide[col] = None

    wide["CUT_SHEET_SIZE"] = wide["CUT_SHEET_SIZE"].apply(_format_size)
    return wide


# ============================================================
# Query 2: RET (sandwich method)
# ============================================================
def query_ret(crate_list: list, process: str) -> pd.DataFrame:
    cfg = PROCESS_CONFIG[process]
    stress_table, tank_col, time_col = cfg["stress_table"], cfg["tank_col"], cfg["time_col"]

    sql = f"""
        WITH CRATE_TIME AS (
            SELECT CRATE_ID, SUBSTR(CRATE_ID, 1, 4) AS TANK_ID,
                MAX(CASE WHEN ITM_NAME = 'START_TIME'
                    THEN TO_DATE(ITM_VALUE1, 'YYYYMMDDHH24MISS') END) AS START_TIME,
                MAX(CASE WHEN ITM_NAME = 'END_TIME'
                    THEN TO_DATE(ITM_VALUE1, 'YYYYMMDDHH24MISS') END) AS END_TIME
            FROM {QUALITY_LONG_TABLE}
            WHERE CRATE_ID IN ({{IN_LIST}})
              AND ITM_NAME IN ('START_TIME', 'END_TIME')
            GROUP BY CRATE_ID
        ),
        QC_IN AS (
            SELECT c.CRATE_ID, q.MAX_RETARDANCE
            FROM CRATE_TIME c
            JOIN {stress_table} q
              ON q.{tank_col} = c.TANK_ID
             AND q.{time_col} >= c.START_TIME
             AND q.{time_col} <= c.END_TIME
        ),
        QC_BEFORE AS (
            SELECT CRATE_ID, MAX_RETARDANCE FROM (
                SELECT c.CRATE_ID, q.MAX_RETARDANCE,
                    ROW_NUMBER() OVER (PARTITION BY c.CRATE_ID
                        ORDER BY c.START_TIME - q.{time_col}) AS RN
                FROM CRATE_TIME c
                JOIN {stress_table} q
                  ON q.{tank_col} = c.TANK_ID
                 AND q.{time_col} < c.START_TIME
            ) WHERE RN = 1
        ),
        QC_AFTER AS (
            SELECT CRATE_ID, MAX_RETARDANCE FROM (
                SELECT c.CRATE_ID, q.MAX_RETARDANCE,
                    ROW_NUMBER() OVER (PARTITION BY c.CRATE_ID
                        ORDER BY q.{time_col} - c.END_TIME) AS RN
                FROM CRATE_TIME c
                JOIN {stress_table} q
                  ON q.{tank_col} = c.TANK_ID
                 AND q.{time_col} > c.END_TIME
            ) WHERE RN = 1
        ),
        QC_ALL AS (
            SELECT * FROM QC_IN UNION ALL
            SELECT * FROM QC_BEFORE UNION ALL
            SELECT * FROM QC_AFTER
        )
        SELECT c.CRATE_ID, MAX(q.MAX_RETARDANCE) AS RET_INT_MAX
        FROM CRATE_TIME c
        LEFT JOIN QC_ALL q ON q.CRATE_ID = c.CRATE_ID
        GROUP BY c.CRATE_ID
    """
    df = _batched_query(sql, crate_list)
    if not df.empty:
        df["RET_INT_MAX"] = pd.to_numeric(df["RET_INT_MAX"], errors="coerce")
    return df


# ============================================================
# Query 3: B_CURVATURE
# ============================================================
def query_bc(crate_list: list) -> pd.DataFrame:
    """BC query (Side=B, Production, sample W/H >= 1350)."""
    sql = f"""
        WITH CRATE_TIME AS (
            SELECT CRATE_ID, SUBSTR(CRATE_ID, 1, 4) AS TANK_ID,
                MAX(CASE WHEN ITM_NAME = 'START_TIME'
                    THEN TO_DATE(ITM_VALUE1, 'YYYYMMDDHH24MISS') END) AS START_TIME,
                MAX(CASE WHEN ITM_NAME = 'END_TIME'
                    THEN TO_DATE(ITM_VALUE1, 'YYYYMMDDHH24MISS') END) AS END_TIME
            FROM {QUALITY_LONG_TABLE}
            WHERE CRATE_ID IN ({{IN_LIST}})
              AND ITM_NAME IN ('START_TIME', 'END_TIME')
            GROUP BY CRATE_ID
        ),
        QC_IN AS (
            SELECT c.CRATE_ID, q.MAX_SHAPE_CURVATURE
            FROM CRATE_TIME c
            JOIN {EDGE_GRAD_TABLE} q
              ON q.TANK_ID = c.TANK_ID
             AND q.SAMPLETSTAMP >= c.START_TIME
             AND q.SAMPLETSTAMP <= c.END_TIME
             AND q.MEASUREDSIDE  = 'B'
             AND q.PURPOSE       = 'Production'
             AND q.SAMPLE_WIDTH  >= 1350
             AND q.SAMPLE_HEIGHT >= 1350
        ),
        QC_BEFORE AS (
            SELECT CRATE_ID, MAX_SHAPE_CURVATURE FROM (
                SELECT c.CRATE_ID, q.MAX_SHAPE_CURVATURE,
                    ROW_NUMBER() OVER (PARTITION BY c.CRATE_ID
                        ORDER BY c.START_TIME - q.SAMPLETSTAMP) AS RN
                FROM CRATE_TIME c
                JOIN {EDGE_GRAD_TABLE} q
                  ON q.TANK_ID = c.TANK_ID
                 AND q.SAMPLETSTAMP < c.START_TIME
                 AND q.MEASUREDSIDE  = 'B'
                 AND q.PURPOSE       = 'Production'
                 AND q.SAMPLE_WIDTH  >= 1350
                 AND q.SAMPLE_HEIGHT >= 1350
            ) WHERE RN = 1
        ),
        QC_AFTER AS (
            SELECT CRATE_ID, MAX_SHAPE_CURVATURE FROM (
                SELECT c.CRATE_ID, q.MAX_SHAPE_CURVATURE,
                    ROW_NUMBER() OVER (PARTITION BY c.CRATE_ID
                        ORDER BY q.SAMPLETSTAMP - c.END_TIME) AS RN
                FROM CRATE_TIME c
                JOIN {EDGE_GRAD_TABLE} q
                  ON q.TANK_ID = c.TANK_ID
                 AND q.SAMPLETSTAMP > c.END_TIME
                 AND q.MEASUREDSIDE  = 'B'
                 AND q.PURPOSE       = 'Production'
                 AND q.SAMPLE_WIDTH  >= 1350
                 AND q.SAMPLE_HEIGHT >= 1350
            ) WHERE RN = 1
        ),
        QC_ALL AS (
            SELECT * FROM QC_IN UNION ALL
            SELECT * FROM QC_BEFORE UNION ALL
            SELECT * FROM QC_AFTER
        )
        SELECT c.CRATE_ID, MAX(q.MAX_SHAPE_CURVATURE) AS B_CURVATURE
        FROM CRATE_TIME c
        LEFT JOIN QC_ALL q ON q.CRATE_ID = c.CRATE_ID
        GROUP BY c.CRATE_ID
    """
    df = _batched_query(sql, crate_list)
    if not df.empty:
        df["B_CURVATURE"] = pd.to_numeric(df["B_CURVATURE"], errors="coerce")
    return df


# ============================================================
# Merge & finalize
# ============================================================
def merge_attribute_results(quality_df: pd.DataFrame,
                            ret_df: pd.DataFrame,
                            bc_df: pd.DataFrame) -> pd.DataFrame:
    """Merge 3 tables + add derived customer columns + reorder."""
    result = (
        quality_df.merge(ret_df, on="CRATE_ID", how="left")
                  .merge(bc_df,  on="CRATE_ID", how="left")
    )
    
    # Ensure RET / BC columns exist
    if "RET_INT_MAX" not in result.columns:
        result["RET_INT_MAX"] = None
    if "B_CURVATURE" not in result.columns:
        result["B_CURVATURE"] = None
    
    # Customer-derived columns
    result["FSHEET_HAKY_CODE"] = result["PRODUCT_CODE"].astype(str).str[:6]
    result["FSHEET_CODE"]      = result["PRODUCT_CODE"].astype(str).str[:6]
    result["LINE_CODE"]        = result["CRATE_ID"].astype(str).str[:4]
    result["BOOKING_NO"]       = result["CRATE_CODE"]
    
    # Empty placeholder columns
    for col in ["DIRECTION", "STRESS_CODE", "F_LOT_SPLIT",
                "CORD_H3_MAX", "INITIAL_ID", "INITIAL_DATE",
                "LATEST_ID", "LATEST_DATE",
                "725MM_MWRNG_MAX", "555MM_MWRNG_MAX", "100MM_MWRNG_MAX"]:
        if col not in result.columns:
            result[col] = None
    
    # Keep only customer-specified column order
    for col in ATTR_CUSTOMER_COLUMN_ORDER:
        if col not in result.columns:
            result[col] = None
    result = result[ATTR_CUSTOMER_COLUMN_ORDER]
    
    return result.sort_values("CRATE_CODE", na_position="last").reset_index(drop=True)


# ============================================================
# Top-level: full attribute pipeline
# ============================================================
def run_attribute_pipeline(crate_list: list,
                           process: str = "MES") -> pd.DataFrame:
    """
    Run the full attribute pipeline (quality wide + RET + BC) and merge.
    
    Parameters
    ----------
    crate_list : list of CRATE_IDs
    process    : "MES" or "Juno"
    """
    if not crate_list:
        print("[WARN] No crate_list provided, skipping attribute pipeline")
        return pd.DataFrame(columns=ATTR_CUSTOMER_COLUMN_ORDER)

    print(f"  ▸ Quality wide table ({process})...")
    quality_df = query_quality_wide(crate_list, process)
    print(f"      → {len(quality_df)} rows")

    print(f"  ▸ RET ({process})...")
    ret_df = query_ret(crate_list, process)
    print(f"      → {len(ret_df)} rows")

    print(f"  ▸ B_CURVATURE...")
    bc_df = query_bc(crate_list)
    print(f"      → {len(bc_df)} rows")

    print(f"  ▸ Merging attribute results...")
    final = merge_attribute_results(quality_df, ret_df, bc_df)
    print(f"      → {len(final)} rows × {len(final.columns)} cols")

    return final


# ============================================================
# Optional: display formatter for attribute table
# ============================================================
def format_attribute_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Format certain numeric columns for display."""
    display_format = {
        "RET_MRV_MAX": "{:.2E}",
        "RET_INT_MAX": "{:.2f}",
    }
    df_out = df.copy()
    for col, fmt in display_format.items():
        if col in df_out.columns:
            df_out[col] = df_out[col].apply(
                lambda x: fmt.format(x) if pd.notnull(x) else ""
            )
    return df_out