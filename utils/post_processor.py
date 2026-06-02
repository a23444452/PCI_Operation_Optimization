"""Final post-processing: merge with cube, build composite cols, format %."""
import pandas as pd

from config import COMPOSITE_COLUMNS


def merge_with_msl(ratio_df: pd.DataFrame, 
                   msl_df: pd.DataFrame) -> pd.DataFrame:
    """Left-join ratio result with cube MSL table on crate_id."""
    return ratio_df.merge(msl_df, on="crate_id", how="left")


def add_composite_columns(df: pd.DataFrame, 
                          composites: dict = COMPOSITE_COLUMNS) -> pd.DataFrame:
    """
    Add composite columns by summing matching columns.
    
    composites = { "new_col_name": ["prefix1", "prefix2", ...] }
    
    Matches columns whose name (case-insensitive) starts with any prefix
    OR exactly equals a prefix.
    """
    df = df.copy()
    for new_col, prefixes in composites.items():
        cols = _match_columns(df.columns, prefixes)
        if cols:
            print(f"  • {new_col} ← sum of {cols}")
            df[new_col] = df[cols].sum(axis=1)
        else:
            print(f"  ⚠️ {new_col}: no matching columns")
            df[new_col] = 0
    return df


def _match_columns(columns, prefixes: list) -> list:
    """Return columns that match any of the given prefixes (or exact match)."""
    matched = []
    for c in columns:
        c_low = str(c).lower()
        for p in prefixes:
            p_low = p.lower()
            if c_low == p_low or c_low.startswith(p_low):
                matched.append(c)
                break
    return matched


def format_as_percent(df: pd.DataFrame, 
                      exclude: list = None) -> pd.DataFrame:
    """Format all numeric columns as percentage strings (except `exclude`)."""
    df = df.copy()
    exclude = set(exclude or ["in_qty"])
    num_cols = [
        c for c in df.select_dtypes(include="number").columns 
        if c not in exclude
    ]
    for col in num_cols:
        df[col] = df[col].apply(
            lambda x: f"{x:.2%}" if pd.notnull(x) else x
        )
    return df


def reorder_columns(df: pd.DataFrame, order: list) -> pd.DataFrame:
    """Reorder columns; missing ones are added as None, extra ones kept at end."""
    df = df.copy()
    for col in order:
        if col not in df.columns:
            df[col] = None
    in_order = [c for c in order if c in df.columns]
    extras = [c for c in df.columns if c not in order]
    return df[in_order + extras]