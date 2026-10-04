from pathlib import Path

from predictive_maintenance.condition import load_baseline, assess_condition
from predictive_maintenance.db import (
    get_all_machines, get_analysis_history, update_analysis_assessment
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = PROJECT_ROOT / "config" / "condition_baseline.json"

baseline = load_baseline(BASELINE_PATH)

machines = get_all_machines()

for machine in machines:
    analyses = get_analysis_history(machine["id"])
    for analysis in analyses:
        features = {
            "rms": analysis["rms"],
            "kurtosis": analysis["kurtosis"],
            "crest_factor": analysis["crest_factor"],
            "amp_1x": analysis["amp_1x"]
        }

        assessment = assess_condition(features, baseline)
        update_analysis_assessment(
            analysis_id=analysis["analysis_id"],
            health_status=assessment["status"],
            fault_indicator=assessment["fault_indicator"]
        )

        print(
            f"Analysis {analysis['analysis_id']}: "
            f"{assessment['status']} | {assessment['fault_indicator']}"
        )
