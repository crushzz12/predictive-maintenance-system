from pathlib import Path

from predictive_maintenance.data_loader import load_cwru_file, segment_signal
from predictive_maintenance.condition import (
    build_baseline_profile, save_baseline, load_baseline
)
from predictive_maintenance.analysis_service import extract_feature_vector

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_DIRECTORY = PROJECT_ROOT / "runtime" / "baselines"


def get_baseline_path(machine_id):
    """Get the file path for a machine's baseline."""

    return BASELINE_DIRECTORY / f"machine_{machine_id}.json"


def load_machine_baseline(machine_id):
    """Load the baseline for a specific machine."""

    file_path = get_baseline_path(machine_id)
    if not file_path.exists():
        return None

    return load_baseline(file_path)


def build_machine_baseline(
    file_path,
    machine_id,
    sampling_rate,
    window_duration,
    channel="DE_time",
    rpm_override=None,
    source_filename=None
):
    """Build a baseline for a machine and save to a JSON file."""

    signal, file_rpm = load_cwru_file(file_path, channel=channel)
    
    # Prioritize manual override rpm value over file metadata
    if rpm_override is not None:
        rpm = rpm_override
    else:
        rpm = file_rpm

    if rpm is None:
        raise ValueError("RPM was not found in the file. Enter RPM manually.")

    # Divide signal into windows
    windows= segment_signal(signal, sampling_rate, window_duration)
    if len(windows) < 2:
        raise ValueError("At least two complete windows are required for a baseline.")

    # Extract all baseline features
    feature_rows = []
    for window in windows:
        features = extract_feature_vector(window, sampling_rate, rpm)
        feature_rows.append(features)

    # Build the baseline JSON
    feature_profile = build_baseline_profile(feature_rows)

    baseline = {
        "metadata": {
            "machine_id": machine_id,
            "source_file": source_filename,
            "sampling_rate_hz": sampling_rate,
            "windows_duration_s": window_duration,
            "window_count": len(windows),
            "rpm": rpm
        },
        "features": feature_profile
    }

    # Save baseline to JSON file
    save_baseline(baseline, get_baseline_path(machine_id))

    return baseline
