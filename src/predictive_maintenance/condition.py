def build_upper_thresholds(healthy_data, feature_names, sigma=3.0):
    """Build upper thresholds from healthy baseline data."""

    mean_values = healthy_data[feature_names].mean()
    std_values = healthy_data[feature_names].std()

    # Upper control limit = mean + k * std
    return mean_values + sigma * std_values


def compare_to_thresholds(features, thresholds):
    """Return True / False flags, which indicate whether features exceed thresholds."""

    flags = {}

    for feature_name, threshold in thresholds.items():
        # Skip thresholds that were not extracted for this signal window
        if feature_name not in features:
            continue

        # Flag an alarm (True) if feature exceeds its upper thresholds, if not, False
        flags[feature_name] = (features[feature_name] > threshold)

    return flags


def determine_status(flags):
    """Classify overall machine health based on the count of tripped alarm flags."""

    # Count abnormal feature flags (True = 1, False = 0)
    abnormal_count = sum(flags.values())

    if abnormal_count == 0:
        return "Normal"
    if abnormal_count == 1:
        return "Warning"

    return "Critical"
