"""Service to run the root-level data pipeline from within the backend."""
import sys
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _pct_to_float(val) -> float | None:
    """Convert '2.75%' → 0.0275, or pass through numeric values."""
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s.endswith("%"):
        return float(s[:-1]) / 100
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _evaluate_against_criteria(receiver_specs_json: dict, criteria: dict) -> dict:
    """
    Evaluate each crate in receiver_specs against shipping criteria thresholds.

    Returns dict keyed by spec_name, each value is a list of:
      {"crate_id", "in_qty", "is_compliant", "failed_criteria": [...]}
    """
    result = {}
    for spec_name, rows in receiver_specs_json.items():
        if spec_name not in criteria or not rows:
            continue
        thresholds = criteria[spec_name]
        spec_eval = []
        for row in rows:
            failed = []
            for col, threshold in thresholds.items():
                value = _pct_to_float(row.get(col))
                if value is None:
                    continue
                if value >= threshold:
                    failed.append(col)
            spec_eval.append({
                "crate_id": row.get("crate_id", ""),
                "in_qty": row.get("in_qty", 0),
                "is_compliant": len(failed) == 0,
                "failed_criteria": failed,
            })
        result[spec_name] = spec_eval
    return result


def _ensure_root_in_path():
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def run_offload_pipeline(start_date: str, end_date: str, max_batches: int = 0, plant_filter: list[str] | None = None) -> dict:
    """
    Run the data pipeline for the given date range.

    Parameters
    ----------
    start_date : e.g. "2025-06-03"
    end_date : e.g. "2025-06-04"
    max_batches : if > 0, limit the number of batch IDs to query for defects
                  (speeds up pipeline for testing/preview)

    Returns dict with keys:
      - receiver_specs: dict[spec_name -> list[dict]]
      - general_spec: list[dict]
      - solid_density: list[dict]
      - attribute: list[dict]
      - summary: dict with row counts
    """
    _ensure_root_in_path()

    from utils import (
        fetch_crate_resume,
        fetch_defects_per_batch,
        compute_solid_density,
        build_super_df,
        compute_general_spec,
        compute_receiver_spec,
        list_available_specs,
        run_attribute_pipeline,
        format_attribute_for_display,
    )
    from utils.post_processor import (
        merge_with_msl,
        merge_with_solid,
        add_composite_columns,
        format_as_percent,
        reorder_columns,
    )
    from config import RECEIVER_OUTPUT_ORDER, GENERAL_OUTPUT_ORDER, ATTRIBUTE_PROCESS, SHIPPING_CRITERIA

    logger.info("Starting pipeline for %s ~ %s (max_batches=%d)", start_date, end_date, max_batches)

    # Step 1: Crate resume
    crate_resume = fetch_crate_resume(start_date=start_date, end_date=end_date)
    if crate_resume.empty:
        return {
            "receiver_specs": {},
            "general_spec": [],
            "solid_density": [],
            "attribute": [],
            "summary": {"total_specs": 0, "general_rows": 0, "solid_rows": 0, "attribute_rows": 0},
        }

    batch_ids = crate_resume["batch_id"].unique().tolist()
    crate_ids = crate_resume["crate_id"].unique().tolist()
    logger.info("Found %d crates, %d batches", len(crate_ids), len(batch_ids))

    # Step 2: Solid density (Oracle PPDA — skip in preview mode for speed)
    if max_batches == 0:
        solid_df = compute_solid_density(crate_resume)
    else:
        logger.info("Skipping SOLID density in preview mode (max_batches=%d)", max_batches)
        solid_df = pd.DataFrame(columns=["crate_id", "tank_id", "defect_cnts", "input_cnts", "crBIS"])

    # Step 3: Defects (optionally limited)
    if max_batches > 0:
        batch_ids = batch_ids[:max_batches]
        logger.info("Limited to %d batches for preview", max_batches)

    defect_df = fetch_defects_per_batch(batch_ids, verbose=False)

    # Step 4: Build super_df
    super_df = build_super_df(defect_df, crate_resume)

    # Step 5: Compute specs
    spec_names = list_available_specs()
    if plant_filter:
        spec_names = [s for s in spec_names if any(s.startswith(p) for p in plant_filter)]
    receiver_results = {}
    for spec in spec_names:
        try:
            ratio_df = compute_receiver_spec(super_df, spec)
            final_df = merge_with_solid(ratio_df, solid_df)
            final_df = add_composite_columns(final_df)
            final_df = format_as_percent(final_df, exclude=["in_qty"])
            receiver_results[spec] = final_df
        except Exception as e:
            logger.warning("Spec %s failed: %s", spec, str(e)[:200])
            receiver_results[spec] = pd.DataFrame()

    # Step 6: General spec
    general_df = compute_general_spec(super_df)
    general_df = merge_with_solid(general_df, solid_df)
    general_df = add_composite_columns(general_df)
    general_df = format_as_percent(general_df, exclude=["in_qty"])

    # Step 7: Attribute pipeline (Oracle PPDA) — skip in preview mode for speed
    if max_batches == 0:
        try:
            logger.info("Running attribute pipeline for %d crates...", len(crate_ids))
            attr_df = run_attribute_pipeline(crate_ids, process=ATTRIBUTE_PROCESS)
            attr_df = format_attribute_for_display(attr_df)
        except Exception as e:
            logger.warning("Attribute pipeline failed: %s", str(e)[:200])
            attr_df = pd.DataFrame()
    else:
        logger.info("Skipping attribute pipeline in preview mode (max_batches=%d)", max_batches)
        attr_df = pd.DataFrame()

    # Convert to JSON-serializable format
    def df_to_records(df: pd.DataFrame) -> list[dict]:
        if df is None or df.empty:
            return []
        df = df.fillna("")
        return df.to_dict(orient="records")

    receiver_specs_json = {}
    for spec_name, df in receiver_results.items():
        receiver_specs_json[spec_name] = df_to_records(df)

    # Step 8: Evaluate crates against shipping criteria
    evaluation = _evaluate_against_criteria(receiver_specs_json, SHIPPING_CRITERIA)

    summary = {
        "total_specs": len(receiver_specs_json),
        "general_rows": len(general_df),
        "solid_rows": len(solid_df),
        "attribute_rows": len(attr_df),
        "total_crates": len(crate_ids),
        "total_batches": len(batch_ids),
    }

    logger.info("Pipeline complete: %s", summary)

    return {
        "receiver_specs": receiver_specs_json,
        "general_spec": df_to_records(general_df),
        "solid_density": df_to_records(solid_df),
        "attribute": df_to_records(attr_df),
        "evaluation": evaluation,
        "summary": summary,
    }
