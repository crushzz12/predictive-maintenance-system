import json
from pathlib import Path
import numpy as np

HEALTH_FEATURES = (
    "rms",
    "kurtosis",
    "crest_factor",
    "amp_1x"
)

BEARING_FEATURES = (
    "env_bpfo_amp",
    "env_bpfi_amp",
    "env_rolling_amp"
)

BASELINE_FEATURES = HEALTH_FEATURES + BEARING_FEATURES

BEARING_LABELS = {
    "env_bpfo_amp": "Outer-race frequency",
    "env_bpfi_amp": "Inner-race frequency",
    "env_rolling_amp": "Rolling-element frequency"
}


def build_baseline_profile(
    feature_rows, feature_names=BASELINE_FEATURES, warning_sigma=3.0, critical_sigma=6.0
):
    """Calculate alarm thresholds from healthy baseline windows."""

    profile = {}
    for feature_name in feature_names:
        values = [row[feature_name] for row in feature_rows if row.get(feature_name) is not None]
        values = np.asarray(values, dtype=float)
        
        # Ensure the samples are enough to calculate standard deviation
        if len(values) < 2:
            raise ValueError(f"Not enough baseline values for {feature_name}.")

        mean_value = float(np.mean(values))
        std_value = float(np.std(values, ddof=1)) # ddof=1 for sample std

        profile[feature_name] = {
            "mean": mean_value,
            "std": std_value,
            "warning_threshold": mean_value + warning_sigma * std_value,
            "critical_threshold": mean_value + critical_sigma * std_value
        }

    return profile


def save_baseline(baseline, file_path):
    """Save the baseline profile to a JSON file."""

    file_path = Path(file_path)

    # Ensure that parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write data to JSON using UTF-8 encoding
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(baseline, file, indent=4) # indent=4 optional for readability


def load_baseline(file_path):
    """Load the baseline profile from a JSON file."""

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Baseline file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_z_score(value, mean, std):
    """Calculate how many standard deviations away (above or below) from the mean."""

    # Prevent division by zero
    if std <= 0:
        return 0.0

    return (value - mean) / std


def assess_condition(features, baseline):
    """Compare one measurement against the healthy baseline profile."""

    warning_flags = []
    critical_flags = []
    z_scores = {}

    baseline_features = baseline["features"]
    for feature_name, limits in baseline_features.items():
        value = features.get(feature_name)
        if value is None:
            continue

        mean_value = limits["mean"]
        std_value = limits["std"]
        warning_threshold = limits["warning_threshold"]
        critical_threshold = limits["critical_threshold"]

        # Find z-score (how many std away (above or below) from the mean)
        z_score = calculate_z_score(value, mean_value, std_value)
        z_scores[feature_name] = z_score

        # Classify alert (critical has higher priority than warning)
        if value > critical_threshold:
            critical_flags.append(feature_name)
        elif value > warning_threshold:
            warning_flags.append(feature_name)

    # Determine overall health status
    abnormal_features = warning_flags + critical_flags
    if critical_flags or len(abnormal_features) >= 2:
        status = "Critical"
    elif abnormal_features:
        status = "Warning"
    else:
        status = "Normal"

    # Remove duplicates from the list
    abnormal_set = set(abnormal_features)

    # Find fault patterns
    impulsive = "kurtosis" in abnormal_set or "crest_factor" in abnormal_set
    high_rms = "rms" in abnormal_set
    high_1x = "amp_1x" in abnormal_set

    if not abnormal_features:
        fault_indicator = "No abnormal vibration indicators"
    elif impulsive and high_rms:
        fault_indicator = "Elevated vibration with impulsive behaviour"
    elif impulsive:
        fault_indicator = "Impulsive vibration pattern"
    elif high_1x:
        fault_indicator = "Elevated 1x running-speed vibration"
    elif high_rms:
        fault_indicator = "Elevated overall vibration"
    else:
        fault_indicator = "Abnormal vibration pattern"

    return {
        "status": status,
        "fault_indicator": fault_indicator,
        "warning_flags": warning_flags,
        "critical_flags": critical_flags,
        "z_scores": z_scores
    }


def assess_bearing_evidence(features, baseline, evidence_threshold=3.0):
    """Assess evidence of bearing faults against a healthy baseline."""

    z_scores = {}

    # Calculate z-score against baseline for each bearing feature
    for feature_name in BEARING_LABELS:
        value = features.get(feature_name)
        if value is None:
            continue

        limits = baseline["features"][feature_name]
        z_score = calculate_z_score(value=value, mean=limits["mean"], std=limits["std"])
        z_scores[feature_name] = z_score

    # Return default null state if no valid metrics could be evaluated
    if not z_scores:
        return {
            "strongest_feature": None,
            "strongest_label": None,
            "strongest_z_score": None,
            "has_strong_evidence": False,
            "z_scores": {}
        }

    strongest_feature = max(z_scores, key=z_scores.get)
    strongest_z_score = z_scores[strongest_feature]
    has_strong_evidence = strongest_z_score >= evidence_threshold

    return {
        "strongest_feature": strongest_feature,
        "strongest_label": BEARING_LABELS[strongest_feature],
        "strongest_z_score": strongest_z_score,
        "has_strong_evidence": has_strong_evidence,
        "z_scores": z_scores
    }


def evaluate_analysis(features, baseline):
    """Evaluate overall machine health status and bearing fault evidence."""

    health_features = {key: features.get(key) for key in HEALTH_FEATURES}
    bearing_features = {key: features.get(key) for key in BEARING_FEATURES}

    return {
        "health": assess_condition(health_features, baseline),
        "bearing": assess_bearing_evidence(bearing_features, baseline)
    }
