from typing import Dict, Any, List, Optional
import pandas as pd


def generate_cleaning_validation_report(
    profile_before: Dict[str, Any],
    profile_after: Dict[str, Any],
    pipeline_step_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Step 19: Pre/Post diff comparison and validation scorecard generator.
    Evaluates data health delta, integrity preservation, and compliance.
    """
    rows_before = profile_before.get("total_rows", 0)
    rows_after = profile_after.get("total_rows", 0)
    rows_removed = rows_before - rows_after

    cols_before = profile_before.get("total_cols", 0)
    cols_after = profile_after.get("total_cols", 0)

    # Missing values comparison
    missing_before = sum(c.get("missing_count", 0) for c in profile_before.get("columns", {}).values())
    missing_after = sum(c.get("missing_count", 0) for c in profile_after.get("columns", {}).values())
    missing_resolved = max(0, missing_before - missing_after)

    # Duplicates comparison
    dups_before = profile_before.get("duplicate_rows", 0)
    dups_after = profile_after.get("duplicate_rows", 0)
    dups_removed = dups_before - dups_after

    # Outliers handled
    outliers_data = pipeline_step_results.get("outliers", {})
    total_outliers = sum(
        v.get("outliers_detected", 0) for k, v in outliers_data.items() if isinstance(v, dict)
    )

    # Scorecard assessment
    warnings = []
    if rows_after == 0 and rows_before > 0:
        overall_status = "FAIL"
        warnings.append("All rows were removed during the cleaning process.")
    elif (rows_removed / rows_before) > 0.5 if rows_before > 0 else False:
        overall_status = "WARNING"
        warnings.append("More than 50% of source records were eliminated during cleaning.")
    elif missing_after > 0:
        overall_status = "WARNING"
        warnings.append(f"{missing_after} missing values remain (e.g. protected key/ID columns).")
    else:
        overall_status = "PASS"

    # Cross-field findings
    cross_field_findings = pipeline_step_results.get("cross_field", {}).get("cross_field_findings", [])
    if any(f.get("status") == "VIOLATION" for f in cross_field_findings):
        if overall_status == "PASS":
            overall_status = "WARNING"
        warnings.append("Business cross-field rule violations detected in dataset.")

    # Quality score (0 - 100)
    penalty = 0.0
    if rows_before > 0:
        penalty += min(30.0, (missing_after / (rows_after * max(1, cols_after))) * 100.0)
    if dups_after > 0:
        penalty += 15.0
    if any(f.get("status") == "VIOLATION" for f in cross_field_findings):
        penalty += 20.0
        
    quality_score = max(0.0, min(100.0, round(100.0 - penalty, 1)))

    return {
        "overall_status": overall_status,
        "quality_score": quality_score,
        "summary": {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_removed": rows_removed,
            "cols_before": cols_before,
            "cols_after": cols_after,
            "missing_before": missing_before,
            "missing_after": missing_after,
            "missing_resolved": missing_resolved,
            "duplicates_before": dups_before,
            "duplicates_after": dups_after,
            "duplicates_removed": dups_removed,
            "outliers_handled": total_outliers
        },
        "warnings": warnings,
        "cross_field_findings": cross_field_findings
    }
