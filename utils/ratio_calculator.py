"""Compute ratios based on receiver-specific & general specs."""
import pandas as pd

from config import RECEIVER_SPECS


def compute_general_spec(df: pd.DataFrame, suffix: str = "0") -> pd.DataFrame:
    """
    For each crate: ratio of loss_codes ending with `suffix`,
    grouped by defect_type. One column per defect type.
    """
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


def compute_receiver_spec(df: pd.DataFrame, 
                          receiver: str,
                          specs: dict = RECEIVER_SPECS) -> pd.DataFrame:
    """Compute defect ratios based on a receiver's spec."""
    if receiver not in specs:
        raise ValueError(
            f"Receiver '{receiver}' not found. Available: {list(specs)}"
        )
    
    spec = specs[receiver]
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
    result.insert(0, "receiver", receiver)
    return result