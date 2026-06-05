"""Main pipeline: fetch → transform → compute → merge → format."""
import pandas as pd

from config import (
    RECEIVER_OUTPUT_ORDER, GENERAL_OUTPUT_ORDER,
    ATTRIBUTE_PROCESS,
)
from utils import (
    fetch_crate_resume,
    fetch_defects_per_batch,
    fetch_cube_data,
    build_super_df,
    transform_cube_to_msl,
    compute_receiver_spec,
    compute_general_spec,
    compute_solid_density,
    list_available_specs,
    merge_with_msl,
    merge_with_solid,
    add_composite_columns,
    format_as_percent,
    reorder_columns,
    run_attribute_pipeline,
)


# ============================================================
# Helpers
# ============================================================
def post_process(ratio_df: pd.DataFrame,
                 msl_df: pd.DataFrame,
                 solid_df: pd.DataFrame,
                 column_order: list = None,
                 drop_empty: bool = True) -> pd.DataFrame:
    """Common post-processing."""
    df = merge_with_msl(ratio_df, msl_df)
    df = merge_with_solid(df, solid_df)
    df = add_composite_columns(df)
    df = format_as_percent(df, exclude=["in_qty"])
    if column_order:
        df = reorder_columns(df, column_order)
    
    # 🆕 Drop columns that are all empty / all 0%
    if drop_empty:
        df = drop_all_empty_columns(
            df, 
            keep=["Gen", "thickness", "crate_id", "in_qty"]   # 一定要保留的
        )
    
    return df


def safe_sheet_name(name: str) -> str:
    """Make a string Excel-sheet-safe (≤ 31 chars, no special chars)."""
    bad_chars = [":", "\\", "/", "?", "*", "[", "]"]
    for c in bad_chars:
        name = name.replace(c, "_")
    return name[:31]

def drop_all_empty_columns(df: pd.DataFrame, 
                           keep: list = None) -> pd.DataFrame:
    """
    Drop columns that are entirely empty (NaN, None, or empty string).
    
    Parameters
    ----------
    df : DataFrame
    keep : list of columns to always keep, even if empty
    """
    keep = set(keep or [])
    
    cols_to_drop = []
    for col in df.columns:
        if col in keep:
            continue
        
        s = df[col]
        # Check if all values are NaN/None/empty string
        is_empty = s.isna() | (s.astype(str).str.strip() == "") | (s.astype(str).str.strip() == "0.00%")
        
        if is_empty.all():
            cols_to_drop.append(col)
    
    if cols_to_drop:
        print(f"      → Dropped empty columns: {cols_to_drop}")
    
    return df.drop(columns=cols_to_drop)


# ============================================================
# Pipeline
# ============================================================
def run_pipeline(spec_names: list = None,
                 attribute_process: str = ATTRIBUTE_PROCESS,
                 start_date: str = None,
                 end_date: str = None) -> dict:
    """
    Full pipeline.

    Parameters
    ----------
    spec_names : list of spec keys to compute. If None, runs ALL specs.
    attribute_process : "MES" or "Juno"
    start_date : optional, e.g. "2025-06-03" — explicit date range start
    end_date : optional, e.g. "2025-06-04" — explicit date range end

    Returns
    -------
    dict with:
      - "receiver_specs" : dict[spec_name -> DataFrame]
      - "general_spec"   : DataFrame (one)
      - "solid_density"  : DataFrame
      - "attribute"      : DataFrame
    """
    # ----- 1. Crate resume -----
    date_label = f" ({start_date} ~ {end_date})" if start_date else ""
    print(f"[1/8] Fetching crate resume (MESDW + Audit){date_label}...")
    crate_resume = fetch_crate_resume(start_date=start_date, end_date=end_date)
    batch_ids = crate_resume["batch_id"].unique().tolist()
    crate_ids = crate_resume["crate_id"].unique().tolist()
    print(f"      → {len(crate_resume)} rows, "
          f"{len(batch_ids)} batches, {len(crate_ids)} crates")

    # ----- 2. SOLID density -----
    print("[2/8] Computing SOLID density...")
    solid_df = compute_solid_density(crate_resume)

    # ----- 3. Defects -----
    print("[3/8] Fetching defects per batch...")
    defect_df = fetch_defects_per_batch(batch_ids)
    print(f"      → {len(defect_df)} defect rows")

    # ----- 4. Build super_df -----
    print("[4/8] Building super_df...")
    super_df = build_super_df(defect_df, crate_resume)

    # ----- 5. Cube MSL -----
    print("[5/8] Fetching cube MSL data...")
    df_cube = fetch_cube_data(crate_ids)
    msl_df  = transform_cube_to_msl(df_cube)
    print(f"      → MSL rows: {len(msl_df)}")

    # ----- 6. Attribute -----
    print(f"[6/8] Running attribute pipeline ({attribute_process})...")
    attribute_df = run_attribute_pipeline(crate_ids, process=attribute_process)

    # ----- 7. Compute spec ratios -----
    if spec_names is None:
        spec_names = list_available_specs()
    
    print(f"\n[7/8] Computing {len(spec_names)} specs:")
    for s in spec_names:
        print(f"        - {s}")
    
    receiver_results = {}
    for spec in spec_names:
        print(f"\n  ▸ {spec}")
        try:
            ratio_df = compute_receiver_spec(super_df, spec)
            final_df = post_process(ratio_df, msl_df, solid_df, RECEIVER_OUTPUT_ORDER)
            receiver_results[spec] = final_df
            print(f"    → {len(final_df)} rows × {len(final_df.columns)} cols")
        except Exception as e:
            print(f"    ❌ Failed: {repr(e)[:200]}")
            receiver_results[spec] = pd.DataFrame()

    # ----- 8. General spec -----
    print(f"\n[8/8] Computing general spec...")
    general_df    = compute_general_spec(super_df)
    final_general = post_process(general_df, msl_df, solid_df, GENERAL_OUTPUT_ORDER)
    print(f"      → {len(final_general)} rows × {len(final_general.columns)} cols")

    # ----- Summary -----
    print(f"\n{'='*60}")
    print(f"✅ Pipeline Done.")
    print(f"{'='*60}")
    for s, df in receiver_results.items():
        print(f"   {s:25}: {len(df):>5} rows × {len(df.columns):>3} cols")
    print(f"   {'General':25}: {len(final_general):>5} rows × {len(final_general.columns):>3} cols")
    print(f"   {'Solid':25}: {len(solid_df):>5} rows × {len(solid_df.columns):>3} cols")
    print(f"   {'Attribute':25}: {len(attribute_df):>5} rows × {len(attribute_df.columns):>3} cols")
    
    return {
        "receiver_specs": receiver_results,
        "general_spec":   final_general,
        "solid_density":  solid_df,
        "attribute":      attribute_df,
    }


# ============================================================
# Excel export (one sheet per spec)
# ============================================================
def export_to_excel(results: dict, output_path: str = "defect_report.xlsx"):
    """Export all results to a multi-sheet Excel file."""
    print(f"\n📤 Exporting to {output_path}...")
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # ---- One sheet per receiver spec ----
        for spec_name, df in results["receiver_specs"].items():
            if df.empty:
                print(f"  ⚠️ Skipping '{spec_name}' (empty)")
                continue
            sheet = safe_sheet_name(spec_name)
            df.to_excel(writer, sheet_name=sheet, index=False)
            print(f"  ✅ {sheet}: {len(df)} rows")
        
        # ---- General ----
        results["general_spec"].to_excel(writer, sheet_name="General Spec", index=False)
        print(f"  ✅ General Spec: {len(results['general_spec'])} rows")
        
        # ---- SOLID ----
        results["solid_density"].to_excel(writer, sheet_name="SOLID Density", index=False)
        print(f"  ✅ SOLID Density: {len(results['solid_density'])} rows")
        
        # ---- Attribute ----
        results["attribute"].to_excel(writer, sheet_name="Attribute", index=False)
        print(f"  ✅ Attribute: {len(results['attribute'])} rows")
        
        # 🎨 Format RET_MRV_MAX as scientific notation
        attr_df = results["attribute"]
        if "RET_MRV_MAX" in attr_df.columns:
            attr_sheet = writer.sheets["Attribute"]
            col_idx = list(attr_df.columns).index("RET_MRV_MAX") + 1
            col_letter = attr_sheet.cell(row=1, column=col_idx).column_letter
            for row_num in range(2, len(attr_df) + 2):
                attr_sheet[f"{col_letter}{row_num}"].number_format = "0.00E+00"
    
    print(f"📁 Saved to: {output_path}")


# ============================================================
# Entry
# ============================================================
if __name__ == "__main__":
    print("Available specs:")
    for s in list_available_specs():
        print(f"  - {s}")
    
    # Option A: 跑全部 specs（預設）
    results = run_pipeline(attribute_process="MES")
    
    # Option B: 只跑指定的幾個
    # results = run_pipeline(
    #     spec_names=["HF_Gen8.6_0.4t", "BJ_Gen8.5_0.4t"],
    #     attribute_process="MES"
    # )
    
    export_to_excel(results, output_path="defect_report_all_reciever.xlsx")