import numpy as np
from scipy.stats import kurtosis


# Feature extraction, returns a dictionary of time-domain features
def extract_time_features(signal):
    """Calculate standard time-domain vibration features."""
    
    signal = np.asarray(signal)
    if signal.size == 0:
        raise ValueError("Signal cannot be empty.")

    # Calculate amplitude metrics
    mean_value = np.mean(signal)
    rms = np.sqrt(np.mean(signal ** 2))
    peak = np.max(np.abs(signal))
    peak_to_peak = np.ptp(signal)
    standard_deviation = np.std(signal)

    # Prevent dividing by zero problem
    if rms == 0:
        crest_factor = 0.0
    else:
        crest_factor = peak / rms

    # Calculate kurtosis (Pearson's Kurtosis, normal distribution: 3)
    kurtosis_value = kurtosis(signal, fisher=False, bias=False)

    return {
        "mean": mean_value,
        "rms": rms,
        "peak": peak,
        "peak_to_peak": peak_to_peak,
        "std": standard_deviation,
        "crest_factor": crest_factor,
        "kurtosis": kurtosis_value
    }
