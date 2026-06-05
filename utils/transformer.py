"""Cleaning, merging, cube pivot."""
import pandas as pd

from config import (
    DEFECT_DICT,
    CUBE_RENAME, CUBE_DEFECT_COL, CUBE_VALUE_COL, CUBE_TIME_COLS,
    DEFECT_SHORT_NAMES, MSL_COLUMNS,
)


def build_super_df(defect_df: pd.DataFrame, 
                   crate_resume: pd.DataFrame) -> pd.DataFrame:
    """Merge defect data with crate resume + clean derived columns."""
    df = crate_resume.merge(defect_df, on="batch_id", how="left")
    
    df["lis_defect_type"] = df["lis_defect_type"].replace(DEFECT_DICT)
    df["defect_size"] = df["mrs_size"].fillna(df["isis_size"])
    df = df.drop(
        columns=["mrs_size", "isis_size", "x_position", "y_position"],
        errors="ignore",
    )
    return df


def transform_cube_to_msl(df_cube: pd.DataFrame) -> pd.DataFrame:
    """Pivot cube data → MSL table (one row per crate)."""
    if df_cube.empty:
        return pd.DataFrame(columns=MSL_COLUMNS)
    
    df = df_cube.rename(columns=CUBE_RENAME)
    
    exclude = {CUBE_DEFECT_COL, CUBE_VALUE_COL, *CUBE_TIME_COLS}
    index_cols = [c for c in df.columns if c not in exclude]
    
    pivot_df = (
        df.pivot_table(
            index=index_cols,
            columns=CUBE_DEFECT_COL,
            values=CUBE_VALUE_COL,
            aggfunc="first",
        )
        .reset_index()
        .fillna(0)
    )
    
    pivot_df = pivot_df.rename(columns=DEFECT_SHORT_NAMES)
    pivot_df = pivot_df[pivot_df["crate_id"].str.contains("TC", na=False)]
    
    available = [c for c in MSL_COLUMNS if c in pivot_df.columns]
    return pivot_df[available].copy()