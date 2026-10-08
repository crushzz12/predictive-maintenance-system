from pathlib import Path
from predictive_maintenance.validation_service import (
    run_validation,
    calculate_health_metrics,
    calculate_condition_summary,
    calculate_bearing_matrix
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "data" / "cwru" / "raw"
RESULTS_DIRECTORY = PROJECT_ROOT / "results"
RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)

results, baseline = run_validation(
    DATA_DIRECTORY,
    sampling_rate=48000,
    window_duration=1.0,
    baseline_fraction=0.60
)

metrics = calculate_health_metrics(results)
summary = calculate_condition_summary(results)
bearing_matrix = calculate_bearing_matrix(results)
normal_results = results[results["known_condition"] == "Normal"]

print("Health detection")
print("----------------")
print(metrics)
print("\nPer-condition summary")
print("---------------------")
print(summary)
print("\nBearing evidence matrix")
print("-----------------------")
print(bearing_matrix)

diagnostic_columns = [
    "window_start_s",
    "predicted_status",
    "warning_flags",
    "critical_flags",
    "rms_z",
    "kurtosis_z",
    "crest_factor_z",
    "amp_1x_z"
]

print(normal_results[diagnostic_columns])

# Save results to csv
results.to_csv(RESULTS_DIRECTORY / "validation_results.csv", index=False)
summary.to_csv(RESULTS_DIRECTORY / "validation_condition_summary.csv", index=False)
bearing_matrix.to_csv(RESULTS_DIRECTORY / "validation_bearing_matrix.csv", index=False)

# Compare 1s window duration vs 0.5s
for duration in (1.0, 0.5):
    results, baseline = run_validation(
        DATA_DIRECTORY,
        sampling_rate=48000,
        window_duration=duration,
        baseline_fraction=0.60
    )

    print(f"\nWindow duration: {duration} s")

    envelope_features = (
        "env_bpfo_amp",
        "env_bpfi_amp",
        "env_rolling_amp"
    )

    ball_inspection_columns = [
        "window_start_s",
        "bpfo_z",
        "bpfi_z",
        "rolling_z",
        "predicted_bearing_evidence",
        "env_bpfo_amp",
        "env_bpfi_amp",
        "env_rolling_amp"
    ]

    for feature in envelope_features:
        stats = baseline["features"][feature]
        print(f"{feature}: mean={stats['mean']:.6g}, std={stats['std']:.6g}")

    ball_results = results.loc[results["known_condition"] == "Ball", ball_inspection_columns]
    print(ball_results.to_string(index=False))

"""Shorter window improved healthy/fault separation in the selected recordings but significantly
reduced rolling-element fault frequency localization."""
