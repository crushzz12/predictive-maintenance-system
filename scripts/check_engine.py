from pathlib import Path

from predictive_maintenance.data_loader import load_cwru_file
from predictive_maintenance.features import extract_time_features
from predictive_maintenance.spectrum import calculate_fft, find_peak_near
from predictive_maintenance.bearing import calculate_bearing_frequencies

SAMPLING_RATE = 48000
file_path = Path("data/cwru/raw/135.mat")

# Load data and take two seconds window
signal, rpm = load_cwru_file(file_path)
analysis_signal = signal[:2 * SAMPLING_RATE]

# Time-domain and spectral feature extraction
features = extract_time_features(analysis_signal)
frequencies, amplitudes = calculate_fft(analysis_signal, SAMPLING_RATE)

# Bearing calculations and find BPFO-region peak 
bearing_frequencies = calculate_bearing_frequencies(rpm)
expected_bpfo = bearing_frequencies["bpfo"]
peak_frequency, peak_amplitude = find_peak_near(frequencies, amplitudes, expected_bpfo)

# Print results
print("\nCWRU Analysis Engine Check")
print("--------------------------")
print(f"RPM: {rpm:.1f}")
print(f"RMS: {features['rms']:.6f}")
print(f"Kurtosis: {features['kurtosis']:.4f}")
print(f"Expected BPFO: {expected_bpfo:.2f} Hz")
print(f"Strongest nearby peak: {peak_frequency:.2f}")
print(f"Peak amplitude: {peak_amplitude:.6f}")
