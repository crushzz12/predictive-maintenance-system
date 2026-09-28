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
