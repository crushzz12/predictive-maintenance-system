from predictive_maintenance.spectrum import (
    bandpass_filter, calculate_envelope_spectrum, get_frequency_amplitude
)

CWRU_MULTIPLIERS = {
    "bpfi": 5.4152,  # Ball Pass Frequency Inner race
    "bpfo": 3.5848,  # Ball Pass Frequency Outer race
    "ftf": 0.39828,  # Cage
    "rolling_element": 4.7135  # Ball
}


# Returns a dictionary of frequencies in Hz for shaft and each fault
def calculate_bearing_frequencies(rpm):
    """Calculate characteristics CWRU drive-end bearing frequencies."""

    if rpm <= 0:
        raise ValueError("RPM must be positive.")

    # Convert revolutions per minute to cycles per second (1X shaft speed in Hz)
    shaft_frequency = rpm / 60

    return {
        "shaft": shaft_frequency,
        "bpfi": CWRU_MULTIPLIERS["bpfi"] * shaft_frequency,
        "bpfo": CWRU_MULTIPLIERS["bpfo"] * shaft_frequency,
        "ftf": CWRU_MULTIPLIERS["ftf"] * shaft_frequency,
        "rolling_element": CWRU_MULTIPLIERS["rolling_element"] * shaft_frequency
    }


def frequency_to_order(frequency, rpm):
    """Convert frequency in Hz to running-speed order (multiples of 1X shaft speed)."""

    shaft_frequency = rpm / 60

    return frequency / shaft_frequency


def extract_envelope_features(signal, sampling_rate, rpm, low_cut=500, high_cut=5000):
    """Extract envelope-spectrum amplitudes at characteristics bearing frequencies."""

    bearing_frequencies = calculate_bearing_frequencies(rpm)
    filtered_signal = bandpass_filter(
        signal, sampling_rate, low_cut=low_cut, high_cut=high_cut, order=4
    )

    frequencies, amplitudes, _ = calculate_envelope_spectrum(filtered_signal, sampling_rate)

    return {
        "env_bpfo_amp": get_frequency_amplitude(
            frequencies, amplitudes, bearing_frequencies["bpfo"]
        ),
        "env_bpfi_amp": get_frequency_amplitude(
            frequencies, amplitudes, bearing_frequencies["bpfi"]
        ),
        "env_rolling_amp": get_frequency_amplitude(
            frequencies, amplitudes, bearing_frequencies["rolling_element"]
        )
    }
