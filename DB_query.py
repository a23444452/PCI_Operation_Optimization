"""Main pipeline: produce two reports — receiver spec & general spec."""
import pandas as pd

from config import RECEIVER_OUTPUT_ORDER
from utils import (
    fetch_batch_crate_qty,
    fetch_defects_per_batch,
    fetch_cube_data,
    build_super_df,
    transform_cube_to_msl,
    compute_general_spec,
    compute_receiver_spec,
    merge_with_msl,
    add_composite_columns,
    format_as_percent,
    reorder_columns,
)


def post_process(ratio_df: pd.DataFrame, 
                 msl_df: pd.DataFrame,
                 column_order: list = None) -> pd.DataFrame:
    """Common post-processing: merge cube → composite cols → format → reorder."""
    df = merge_with_msl(ratio_df, msl_df)
    df = add_composite_columns(df)
    df = format_as_percent(df, exclude=["in_qty"])
    if column_order:
        df = reorder_columns(df, column_order)
    return df


def run_pipeline(receiver: str = "TC") -> dict:
    """
    Run the full pipeline.
    
    Returns
    -------
    dict with two DataFrames:
      - "receiver_spec": receiver-spec result + cube + post-process
      - "general_spec":  general-spec result + cube + post-process
    """
    # ----- 1. Get batch/crate/qty mapping -----
    print("[1/6] Fetching batch/crate/qty...")
    batch_crate_df = fetch_batch_crate_qty()
    batch_ids = batch_crate_df["batch_id"].unique().tolist()
    crate_ids = batch_crate_df["crate_id"].dropna().unique().tolist()
    print(f"      → {len(batch_ids)} batches, {len(crate_ids)} crates")

    # ----- 2. Fetch defects -----
    print("[2/6] Fetching defects...")
    defect_df = fetch_defects_per_batch(batch_ids)
    print(f"      → {len(defect_df)} defect rows")

    # ----- 3. Build super_df -----
    print("[3/6] Building super_df...")
    super_df = build_super_df(defect_df, batch_crate_df)

    # ----- 4. Compute both spec ratios -----
    print("[4/6] Computing ratios...")
    receiver_df = compute_receiver_spec(super_df, receiver)
    general_df  = compute_general_spec(super_df)

    # ----- 5. Fetch & transform cube -----
    print("[5/6] Fetching cube MSL data...")
    df_cube = fetch_cube_data(crate_ids)
    msl_df  = transform_cube_to_msl(df_cube)
    print(f"      → MSL rows: {len(msl_df)}")

    # ----- 6. Post-process both reports -----
    print("[6/6] Post-processing...")
    print("  ▸ Receiver spec:")
    final_receiver = post_process(receiver_df, msl_df, RECEIVER_OUTPUT_ORDER)
    
    print("  ▸ General spec:")
    final_general  = post_process(general_df, msl_df)

    print(f"\n✅ Done.")
    print(f"   Receiver: {len(final_receiver)} rows × {len(final_receiver.columns)} cols")
    print(f"   General:  {len(final_general)}  rows × {len(final_general.columns)}  cols")
    
    return {
        "receiver_spec": final_receiver,
        "general_spec":  final_general,
    }


if __name__ == "__main__":
    results = run_pipeline(receiver="TC")
    
    # Preview
    print("\n=== RECEIVER SPEC ===")
    print(results["receiver_spec"].head())
    
    print("\n=== GENERAL SPEC ===")
    print(results["general_spec"].head())
    
    # Export
    with pd.ExcelWriter("defect_report.xlsx", engine="openpyxl") as writer:
        results["receiver_spec"].to_excel(writer, sheet_name="Receiver Spec", index=False)
        results["general_spec"].to_excel(writer, sheet_name="General Spec", index=False)
    
    print("\n📁 Saved to: defect_report.xlsx")