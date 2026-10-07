from pathlib import Path

from predictive_maintenance.data_loader import load_cwru_file, segment_signal
from predictive_maintenance.features import extract_time_features
from predictive_maintenance.spectrum import calculate_fft, get_frequency_amplitude
from predictive_maintenance.bearing import extract_envelope_features
from predictive_maintenance.condition import (
    build_baseline_profile, save_baseline, assess_condition
)

SAMPLING_RATE = 48000
WINDOW_DURATION = 1.0

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NORMAL_FILE = PROJECT_ROOT / "data" / "cwru" / "raw" / "97.mat"
BASELINE_PATH = PROJECT_ROOT / "config" / "condition_baseline.json"

# Load and segment the normal recording
signal, rpm = load_cwru_file(NORMAL_FILE)
windows = segment_signal(signal, SAMPLING_RATE, WINDOW_DURATION)

# Reserve some parts of the windows for healthy baseline
BASELINE_FRACTION = 0.60
split_index = int(len(windows) * BASELINE_FRACTION)
if split_index < 2:
    raise ValueError("Not enough healthy windows to build a baseline.")

# Divide normal recording into baseline and validation windows
baseline_windows = windows[:split_index]
validation_windows = windows[split_index:]

print("Total healthy windows:", len(windows))
print("Baseline windows:", len(baseline_windows))
print("Held-out healthy windows:", len(validation_windows))

# Extract baseline features
feature_rows = []
for window in baseline_windows:
    time_features = extract_time_features(window)
    frequencies, amplitudes = calculate_fft(window, SAMPLING_RATE)
    shaft_frequency = rpm / 60
    amp_1x = get_frequency_amplitude(frequencies, amplitudes, shaft_frequency)
    envelope_features = extract_envelope_features(window, SAMPLING_RATE, rpm)

    # Copy all key/value pairs from time_features and then add amp_1x
    row = {
        **time_features,
        "amp_1x": amp_1x,
        **envelope_features
    }

    feature_rows.append(row)

# Build the baseline JSON
feature_profile = build_baseline_profile(feature_rows)

baseline = {
    "metadata": {
        "source_file": "97.mat",
        "known_condition": "Normal",
        "sampling_rate_hz": SAMPLING_RATE,
        "windows_duration_s": WINDOW_DURATION,
        "total_window_count": len(windows),
        "baseline_window_count": len(baseline_windows),
        "validation_window_count": len(validation_windows),
        "baseline_fraction": BASELINE_FRACTION,
        "note": (
            "Baseline built from first portion of one CWRU Normal 0 HP recording. "
            "Remaining windows reserved for validation."
        )
    },
    "features": feature_profile
}

# Save baseline to JSON file
save_baseline(baseline, BASELINE_PATH)
print("Baseline written to:", BASELINE_PATH)

for index, row in enumerate(feature_rows, start=1):
    assessment = assess_condition(row, baseline)
    print(index, assessment["status"])
