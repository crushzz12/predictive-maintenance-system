from pathlib import Path

from predictive_maintenance.data_loader import load_cwru_file
from predictive_maintenance.features import extract_time_features
from predictive_maintenance.spectrum import calculate_fft, get_frequency_amplitude
from predictive_maintenance.bearing import extract_envelope_features
from predictive_maintenance.db import (
    initialize_database,
    get_or_create_machine,
    add_analysis_run,
    get_analysis_history,
    get_all_machines,
    get_machine_by_id,
    get_analysis_by_id
)

SAMPLING_RATE = 48000
WINDOW_DURATION = 1.0

# Setup database and register a machine
initialize_database()
machine_id = get_or_create_machine(
    name="CWRU Drive-End Bearing Rig",
    machine_type="Electric motor test rig",
    bearing_model="SKF 6205-2RS JEM",
    description="CWRU Bearing Data Center drive-end test rig."
)
print("Machine ID:", machine_id)

file_path = Path("data/cwru/raw/135.mat")
signal, rpm = load_cwru_file(file_path)

# Create a 1 sec signal window
window_samples = int(SAMPLING_RATE * WINDOW_DURATION)
analysis_signal = signal[:window_samples]

# Feature Extraction
features = extract_time_features(analysis_signal)
frequencies, amplitudes = calculate_fft(analysis_signal, SAMPLING_RATE)

# Extract amplitudes for the shaft frequency and harmonics
shaft_frequency = rpm / 60
spectral_features = {
    "amp_1x": get_frequency_amplitude(frequencies, amplitudes, shaft_frequency),
    "amp_2x": get_frequency_amplitude(frequencies, amplitudes, 2 * shaft_frequency),
    "amp_3x": get_frequency_amplitude(frequencies, amplitudes, 3 * shaft_frequency)
}

# Extract amplitudes for envelope-spectrum at bpfo, bpfi and rolling element frequency
envelope_features = extract_envelope_features(analysis_signal, SAMPLING_RATE, rpm)

# Combine all features together by adding the key/value pairs
all_features = {
    **features,
    **spectral_features,
    **envelope_features
}

# Register the data into database
analysis_id = add_analysis_run(
    machine_id=machine_id, 
    sampling_rate_hz=SAMPLING_RATE, 
    window_duration_s=WINDOW_DURATION, 
    all_features=all_features,
    source_file="135.mat",
    known_condition="Outer race",
    rpm=rpm,
    window_start_s=0.0,
)

# Print out the analysis histories
histories = get_analysis_history(machine_id)
print("\nStored analysis records")
print("-----------------------")
for history in histories:
    print(
        f"ID: {history['analysis_id']} | "
        f"Condition: {history['known_condition']} | "
        f"RPM: {history['rpm']:.1f} | "
        f"RMS: {history['rms']:.6f} | "
        f"Kurtosis: {history['kurtosis']:.4f}"
    )

# Test get info by ID functions
"""
machines = get_all_machines()
for machine in machines:
    print(dict(machine))

machine = get_machine_by_id(1)
print(dict(machine))

analysis = get_analysis_by_id(1)
print(dict(analysis))
"""
