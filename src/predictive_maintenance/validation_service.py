from pathlib import Path

import pandas as pd

from predictive_maintenance.data_loader import load_cwru_file, segment_signal
from predictive_maintenance.analysis_service import extract_feature_vector
from predictive_maintenance.condition import build_baseline_profile, evaluate_analysis

EXPECTED_BEARING_EVIDENCE = {
    "Normal": "No strong evidence",
    "Inner race": "Inner-race frequency",
    "Ball": "Rolling-element frequency",
    "Outer race": "Outer-race frequency"
}


def build_validation_baseline(
    normal_file,
    sampling_rate,
    window_duration,
    baseline_fraction=0.60
):
    """
    Build a baseline from the first portion of a healthy recording and reserve the remaining
    windows for validation.
    """

    signal, rpm = load_cwru_file(normal_file)
    windows = segment_signal(signal, sampling_rate, window_duration)
    
    # Ensure enough samples to form both sets (min 2 baseline and 1 validation)
    if len(windows) < 3:
        raise ValueError("Not enough healthy windows for baseline and validation.")

    split_index = int(len(windows) * baseline_fraction)
    # Ensure at least 2 windows for baseline to calculate mean / std
    if split_index < 2:
        split_index = 2

    # Ensure at least 1 validation window remains
    if split_index >= len(windows):
        split_index = len(windows) - 1

    # Divide normal recording into baseline and validation windows
    baseline_windows = windows[:split_index]
    validation_windows = windows[split_index:]

    # Extract all features from only baseline portion
    baseline_feature_rows = []
    for window in baseline_windows:
        features = extract_feature_vector(window, sampling_rate, rpm)
        baseline_feature_rows.append(features)

    # Build the baseline JSON
    feature_profile = build_baseline_profile(baseline_feature_rows)

    baseline = {
        "metadata": {
            "source_file": Path(normal_file).name,
            "sampling_rate_hz": sampling_rate,
            "windows_duration_s": window_duration,
            "total_window_count": len(windows),
            "baseline_window_count": len(baseline_windows),
            "validation_window_count": len(validation_windows),
            "baseline_fraction": baseline_fraction
        },
        "features": feature_profile
    }

    return {
        "baseline": baseline,
        "validation_windows": validation_windows,
        "rpm": rpm,
        "baseline_window_count": len(baseline_windows)
    }


def evaluate_window(window, rpm, sampling_rate, baseline):
    """Extract features from one signal window and evaluate health status against baseline."""

    features = extract_feature_vector(window, sampling_rate, rpm)
    assessment = evaluate_analysis(features, baseline)

    return features, assessment


def make_validation_row(
    condition,
    source_file,
    window_index,
    window_start_s,
    features,
    assessment
):
    """Build a dictionary record for features for one signal window."""

    health = assessment["health"]
    bearing = assessment["bearing"]
    health_z_scores = health["z_scores"]
    z_scores = bearing["z_scores"]

    # Determine health ground truth / anomaly detection (True if not "Normal")
    true_abnormal = condition != "Normal"
    predicted_abnormal = health["status"] != "Normal"

    if bearing["has_strong_evidence"]:
        predicted_bearing = bearing["strongest_label"]
    else:
        predicted_bearing = "No strong evidence"

    return {
        # Window and source metadata
        "source_file": source_file,
        "window_index": window_index,
        "window_start_s": window_start_s,
        "known_condition": condition,
        # Overall health assessment
        "predicted_status": health["status"],
        "true_abnormal": true_abnormal,
        "predicted_abnormal": predicted_abnormal,
        # Z-scores for health assessment
        "warning_flags": ", ".join(health["warning_flags"]),
        "critical_flags": ", ".join(health["critical_flags"]),
        "rms_z": health_z_scores.get("rms"),
        "kurtosis_z": health_z_scores.get("kurtosis"),
        "crest_factor_z": health_z_scores.get("crest_factor"),
        "amp_1x_z": health_z_scores.get("amp_1x"),
        # Fault diagnosis
        "predicted_bearing_evidence": predicted_bearing,
        "expected_bearing_evidence": EXPECTED_BEARING_EVIDENCE[condition],
        "bearing_match": predicted_bearing == EXPECTED_BEARING_EVIDENCE[condition],
        # Time-domain features
        "rms": features["rms"],
        "kurtosis": features["kurtosis"],
        "crest_factor": features["crest_factor"],
        # Envelope amplitudes
        "env_bpfo_amp": features["env_bpfo_amp"],
        "env_bpfi_amp": features["env_bpfi_amp"],
        "env_rolling_amp": features["env_rolling_amp"],
        # Z-scores for BPFO, BPFI, Rolling-element
        "bpfo_z": z_scores.get("env_bpfo_amp"),
        "bpfi_z": z_scores.get("env_bpfi_amp"),
        "rolling_z": z_scores.get("env_rolling_amp")
    }


def run_validation(
    data_directory,
    sampling_rate=48000,
    window_duration=1.0,
    baseline_fraction=0.60
):
    """Run validation across healthy and fault bearing datasets."""

    data_directory = Path(data_directory)
    files = {
        "Normal": "97.mat",
        "Inner race": "109.mat",
        "Ball": "122.mat",
        "Outer race": "135.mat",
    }

    # Create validation-only baseline
    normal_result = build_validation_baseline(
        normal_file=data_directory / files["Normal"],
        sampling_rate=sampling_rate,
        window_duration=window_duration,
        baseline_fraction=baseline_fraction
    )

    baseline = normal_result["baseline"]
    rows = []

    normal_rpm = normal_result["rpm"]
    baseline_window_count = normal_result["baseline_window_count"]

    # Evaluate healthy validation windows 
    for index, window in enumerate(
        normal_result["validation_windows"],
        start=baseline_window_count
    ):
        features, assessment = evaluate_window(window, normal_rpm, sampling_rate, baseline)
        rows.append(
            make_validation_row(
                condition="Normal",
                source_file=files["Normal"],
                window_index=index,
                window_start_s=index * window_duration,
                features=features,
                assessment=assessment
            )
        )
    
    # Evaluate fault condition datasets
    fault_conditions = ("Inner race", "Ball", "Outer race")

    for condition in fault_conditions:
        file_path = data_directory / files[condition]
        signal, rpm = load_cwru_file(file_path)
        windows = segment_signal(signal, sampling_rate, window_duration)
        for index, window in enumerate(windows):
            features, assessment = evaluate_window(window, rpm, sampling_rate, baseline)
            rows.append(
                make_validation_row(
                    condition=condition,
                    source_file=files[condition],
                    window_index=index,
                    window_start_s=index * window_duration,
                    features=features,
                    assessment=assessment
                )
            )

    results = pd.DataFrame(rows)

    return results, baseline


def calculate_health_metrics(results):
    """Calculate the confusion matrix and performance metrics."""

    # Extract ground truth and prediction
    true_abnormal = results["true_abnormal"]
    predicted_abnormal = results["predicted_abnormal"]

    # Calculate the confusion matrix (~ is NOT)
    # True positive (predicted abnormal, actual abnormal)
    tp = int((true_abnormal & predicted_abnormal).sum())

    # True negative (predicted normal, actual normal)
    tn = int((~true_abnormal & ~predicted_abnormal).sum())

    # False positive (predicted abnormal, actual normal)
    fp = int((~true_abnormal & predicted_abnormal).sum())

    # False negative (predicted normal, actual abnormal)
    fn = int((true_abnormal & ~predicted_abnormal).sum())

    total = tp + tn + fp + fn

    # Find performance metrics based on confusion matrix data
    accuracy = (tp + tn) / total if total else 0.0

    # Sensitivity / Recall (Out of all faulty/abnormal windows, how many detected)
    sensitivity = tp / (tp + fn) if (tp + fn) else 0.0

    # Specificity (Out of all normal windows, how many correctly identified)
    specificity = tn / (tn + fp) if (tn + fp) else 0.0

    # Precision (how many positive (abnormal) predictions were actually correct)
    precision = tp / (tp + fp) if (tp + fp) else 0.0

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "precision": precision
    }


def calculate_condition_summary(results):
    """Calculate summary metrics for each bearing condition."""

    summary = (
        results.groupby("known_condition")
        .agg(
            windows=("source_file", "count"),
            abnormal_detection_rate=("predicted_abnormal", "mean"),
            bearing_match_rate=("bearing_match", "mean"),
            mean_bpfo_z=("bpfo_z", "mean"),
            mean_bpfi_z=("bpfi_z", "mean"),
            mean_rolling_z=("rolling_z", "mean")
        )
        .reset_index()
    )

    return summary


def calculate_bearing_matrix(results):
    """Generate a confusion matrix comparing actual and predicted bearing conditions."""

    return pd.crosstab(
        results["known_condition"],
        results["predicted_bearing_evidence"]
    )


def calculate_bearing_metrics(results):
    """Calculate the confusion matrix and performance metrics for bearing."""

    fault_results = results[results["known_condition"] != "Normal"]
    localization_accuracy = fault_results["bearing_match"].mean()
    overall_match_rate = results["bearing_match"].mean()

    return {
        "localization_accuracy": localization_accuracy,
        "overall_match_rate": overall_match_rate
    }
