from pathlib import Path
import numpy as np
from scipy.io import loadmat


# File Loader
def load_cwru_file(file_path, channel="DE_time"):
    """Load a vibration channel and RPM value from a CWRU MATLAB file."""

    # Path validation
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    # Load MATLAB data
    data = loadmat(file_path)

    # Filter headers like __header__, __version__, __globals__ in .mat files
    keys = [key for key in data.keys() if not key.startswith("__")]

    # Find the key that has channel (DE_time, by default) in it, like X097_DE_time
    signal_matches = [key for key in keys if channel in key]

    if not signal_matches:
        raise KeyError(f"Channel '{channel}' not found in {file_path.name}")

    signal_key = signal_matches[0]

    # Squeeze the data from 2D (N, 1) to 1D (N,)
    signal = np.asarray(data[signal_key]).squeeze()

    # Check whether the signal is being squeezed successfully into 1D
    if signal.ndim != 1:
        raise ValueError("Loaded vibration signal is not 1D.")

    # Find the key that has RPM in it (such as X097_RPM), if not found then = None
    rpm_key = next((key for key in keys if "RPM" in key), None)

    # Squeeze into 1D and turn the value into float
    rpm = None
    if rpm_key is not None:
        rpm = float(np.asarray(data[rpm_key]).squeeze())

    return signal, rpm


# Signal segmentation
def segment_signal(signal, sampling_rate, window_duration=1.0):
    """Divide the time-series signal into equal non-overlapping windows."""

    # Calculate the window size in samples
    samples_per_window = int(sampling_rate * window_duration)
    if samples_per_window <= 0:
        raise ValueError("Window duration must be positive.")

    # Ignore the remaining samples at the end that cannot form a complete window by using //
    number_of_windows = len(signal) // samples_per_window

    windows = []

    # For each window
    for window_index in range(number_of_windows):
        start = window_index * samples_per_window
        end = start + samples_per_window
        windows.append(signal[start:end])

    return windows
