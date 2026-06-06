"""Compute ratios: receiver-spec, general-spec, and SOLID density."""
import pandas as pd

from config import RECEIVER_SPECS, TANKS_TO_PROCESS
from utils.db_connections import get_PPDA
from utils.sql_queries import build_crbis_input_query, build_crbis_defect_query


"""Compute ratios using user-selected spec."""
import pandas as pd

from config import RECEIVER_SPECS, TANKS_TO_PROCESS
from utils.db_connections import get_PPDA
from utils.sql_queries import build_crbis_input_query, build_crbis_defect_query


# ============================================================
# Helpers
# ============================================================
def list_available_specs(specs: dict = RECEIVER_SPECS) -> list:
    """List all spec names the user can select."""
    return list(specs.keys())


def get_spec_summary(specs: dict = RECEIVER_SPECS) -> pd.DataFrame:
    """All specs as a tidy table — useful for UI/preview."""
    rows = []
    for spec_name, spec_cfg in specs.items():
        for key, rule in spec_cfg.items():
            rows.append({
                "spec_name": spec_name,
                "key":       key,
                "type":      rule["type"],
                "min_size":  rule["min_size"],
                "max_size":  rule.get("max_size"),
            })
    return pd.DataFrame(rows)


# ============================================================
# Receiver-spec ratios
# ============================================================
def compute_receiver_spec(df: pd.DataFrame,
                          spec_name: str,
                          specs: dict = RECEIVER_SPECS) -> pd.DataFrame:
    """
    Compute defect ratios per crate, using the user-selected spec.
    
    Parameters
    ----------
    df : DataFrame with columns crate_id, in_qty, lis_defect_type, defect_size
    spec_name : key in `specs` dict (e.g., "HF_Gen8.6_0.4t")
    """
    if spec_name not in specs:
        raise ValueError(
            f"Spec '{spec_name}' not found.\n"
            f"Available: {list(specs.keys())}"
        )
    
    spec = specs[spec_name]
    qty_per_crate = df.groupby("crate_id")["in_qty"].first()
    
    ratios = []
    for name, cfg in spec.items():
        mask = (
            (df["lis_defect_type"] == cfg["type"]) &
            (df["defect_size"] >= cfg["min_size"])
        )
        if "max_size" in cfg:
            mask &= (df["defect_size"] < cfg["max_size"])
        
        counts = df[mask].groupby("crate_id").size()
        ratio = counts.reindex(qty_per_crate.index, fill_value=0) / qty_per_crate
        ratios.append(ratio.rename(name))
    
    result = pd.concat(ratios, axis=1).fillna(0)
    result = result.join(qty_per_crate).reset_index()
    #result.insert(0, "spec_name", spec_name)
    return result


# ============================================================
# General-spec ratios (loss_code suffix grouped by defect_type)
# ============================================================
def compute_general_spec(df: pd.DataFrame, suffix: str = "0") -> pd.DataFrame:
    qty_per_crate = df.groupby("crate_id")["in_qty"].first()
    
    mask = df["loss_code"].astype(str).str.endswith(suffix, na=False)
    counts = (
        df[mask]
        .groupby(["crate_id", "lis_defect_type"])
        .size()
        .unstack(fill_value=0)
    )
    counts = counts.reindex(qty_per_crate.index, fill_value=0)
    
    ratios = counts.div(qty_per_crate, axis=0)
    return ratios.join(qty_per_crate).reset_index()


# ============================================================
# SOLID density (unchanged)
# ============================================================
def _compute_solid_density_for_tank(sub: pd.DataFrame, tank: str) -> pd.DataFrame:
    sub = sub.copy()
    sub["START_TIME"] = pd.to_datetime(sub["START_TIME"])
    sub["END_TIME"]   = pd.to_datetime(sub["END_TIME"])
    
    overall_start = sub["START_TIME"].min()
    overall_end   = sub["END_TIME"].max()
    fmt = "%Y-%m-%d %H:%M"
    
    print(f"  [{tank}] {overall_start} → {overall_end} ({len(sub)} crates)")
    
    df_input = get_PPDA(build_crbis_input_query(
        tank, overall_start.strftime(fmt), overall_end.strftime(fmt)
    ))
    df_defect = get_PPDA(build_crbis_defect_query(
        tank, overall_start.strftime(fmt), overall_end.strftime(fmt)
    ))
    
    df_input["sample_ts"]  = pd.to_datetime(df_input["sample_ts"])
    df_defect["sample_ts"] = pd.to_datetime(df_defect["sample_ts"])
    
    print(f"     → input rows: {len(df_input)}, defect rows: {len(df_defect)}")
    
    results = []
    for _, row in sub.iterrows():
        s, e = row["START_TIME"], row["END_TIME"]
        defect_cnts = ((df_defect["sample_ts"] >= s) & (df_defect["sample_ts"] <= e)).sum()
        input_cnts  = ((df_input["sample_ts"]  >= s) & (df_input["sample_ts"]  <= e)).sum()
        density = defect_cnts / input_cnts if input_cnts > 0 else None
        
        results.append({
            "crate_id":    row["crate_id"],
            "tank_id":     tank,
            "defect_cnts": int(defect_cnts),
            "input_cnts":  int(input_cnts),
            "crBIS":       density,
        })
    
    return pd.DataFrame(results)


def compute_solid_density(crate_df: pd.DataFrame,
                          tanks: list = None) -> pd.DataFrame:
    if tanks is None:
        tanks = TANKS_TO_PROCESS
    
    print(f"[SOLID] Computing density for {len(tanks)} tanks: {tanks}")
    
    results = []
    for tank in tanks:
        sub = crate_df[crate_df["tank_id"] == tank]
        if sub.empty:
            print(f"  [{tank}] no crates, skipped")
            continue
        try:
            res = _compute_solid_density_for_tank(sub, tank)
            if not res.empty:
                results.append(res)
        except Exception as e:
            print(f"  [ERROR] {tank} failed: {repr(e)[:200]}")
    
    if not results:
        return pd.DataFrame(
            columns=["crate_id", "tank_id", "defect_cnts", "input_cnts", "crBIS"]
        )
    return pd.concat(results, ignore_index=True)