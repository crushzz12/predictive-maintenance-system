import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import kurtosis

# Define the machine
sampling_rate = 2000
duration = 2

rpm = 1800
rotational_frequency = rpm / 60

time = np.arange(0, duration, 1 / sampling_rate)

N = len(time)


# Convert time-domain to frequency-domain using FFT with/without windowing
def calculate_fft(signal, sampling_rate, window="hann"):
    N = len(signal)

    # Remove DC offset
    centered_signal = signal - np.mean(signal)

    # If using hann window
    if window == "hann":
        window_values = np.hanning(N)
        processed_signal = (centered_signal * window_values)
        coherent_gain = np.mean(window_values)

    else:
        processed_signal = centered_signal
        coherent_gain = 1.0

    # Calculate FFT values (y-axis) and frequencies (x-axis)
    fft_values = np.fft.rfft(processed_signal)
    frequencies = np.fft.rfftfreq(N, d=1/ sampling_rate)

    amplitudes = (2 / (N * coherent_gain)) * np.abs(fft_values)
    amplitudes[0] /= 2
    if N % 2 == 0:
        amplitudes[-1] /= 2

    return frequencies, amplitudes


# Find the bin closest to the target frequency and returns its amplitude
def get_frequency_amplitude(frequencies, amplitudes, target_frequency):
    # Find the index that has the min distance between frequency and target frequency
    index = np.argmin(
        np.abs(
            frequencies - target_frequency
        )
    )

    return amplitudes[index]


# Calculate RMS of spectral amplitude within a range (low to high frequency)
def calculate_band_rms(frequencies, amplitudes, low_frequency, high_frequency):
    # Boolean array where True means within the range
    mask = ((frequencies >= low_frequency) & (frequencies <= high_frequency))

    # Return the RMS
    return np.sqrt(np.mean(amplitudes[mask] ** 2))


# Feature extraction (returns a dictionary of all features including time-domain features)
def extract_features(signal, sampling_rate, rotational_frequency):
    # Calculate time-domain features
    mean_value = np.mean(signal)
    rms = np.sqrt(np.mean(signal ** 2))
    peak = np.max(np.abs(signal))
    peak_to_peak = np.ptp(signal)
    standard_deviation = np.std(signal)

    # Calculate impulsive features
    crest_factor = peak / rms
    kurtosis_value = kurtosis(signal, fisher=False, bias=False)

    frequencies, amplitudes = calculate_fft(signal, sampling_rate)

    amplitude_1x = get_frequency_amplitude(frequencies, amplitudes, rotational_frequency)
    amplitude_2x = get_frequency_amplitude(frequencies, amplitudes, 2 * rotational_frequency)
    amplitude_3x = get_frequency_amplitude(frequencies, amplitudes, 3 * rotational_frequency)

    high_frequency_band = calculate_band_rms(frequencies, amplitudes, 200, 300)

    return {
        "mean": mean_value,
        "rms": rms,
        "peak": peak,
        "peak_to_peak": peak_to_peak,
        "std": standard_deviation,
        "crest_factor": crest_factor,
        "kurtosis": kurtosis_value,
        "amp_1x": amplitude_1x,
        "amp_2x": amplitude_2x,
        "amp_3x": amplitude_3x,
        "hf_band_rms": high_frequency_band
    }


# Create machine conditions (healthy, imbalance, bearing-like)
def generate_signal(condition, seed):
    rng = np.random.default_rng(seed)

    # Add slight randomness in amplitude, noise and phase
    amplitude_variation = rng.normal(1.0, 0.03)
    noise_level = rng.normal(0.08, 0.01)
    phase = rng.uniform(0, 2 * np.pi)

    # Healthy condition
    if condition == "healthy":
        amplitude_1x = 0.45
    elif condition == "imbalance":
        amplitude_1x = 1.00
    elif condition == "bearing":
        amplitude_1x = 0.45
    else:
        raise ValueError("Unknown machine condition")

    # Generate signal
    signal = (
        amplitude_1x 
        * amplitude_variation 
        * np.sin(
            2 * np.pi * rotational_frequency * time + phase
        )
    )

    # Add a small 2x component
    signal += 0.08 * np.sin(
        2 * np.pi * 2 * rotational_frequency * time
    )

    # Add measurement noise
    signal += (noise_level * rng.normal(0, 1, N))

    # Add bearing-like impacts
    if condition == "bearing":
        impact_frequency = 8
        impact_amplitude = rng.normal(1.6, 0.1)

        # Damped ringing response
        ring_frequency = 250
        ring_duration = 0.03
        decay_rate = 120

        # Create ringing
        ring_time = np.arange(0, ring_duration, 1 / sampling_rate)
        ring = (
            np.exp(-decay_rate * ring_time)
            * 
            np.sin(2 * np.pi * ring_frequency * ring_time)
        )

        # Calculate repeated impact locations
        impact_interval = int(sampling_rate / impact_frequency)
        impact_indices = np.arange(impact_interval, N, impact_interval)

        # Add each ringing to the signal
        for index in impact_indices:
            end_index = min(index + len(ring), N)
            available_length = (end_index - index)
            signal[index:end_index] += (impact_amplitude * ring[:available_length])

    return signal


# Generate each signal
healthy_signal = generate_signal("healthy", seed=1)
imbalance_signal = generate_signal("imbalance", seed=2)
bearing_signal = generate_signal("bearing", seed=3)

# Extract features for each signal
healthy_features = extract_features(healthy_signal, sampling_rate, rotational_frequency)
imbalance_features = extract_features(imbalance_signal, sampling_rate, rotational_frequency)
bearing_features = extract_features(bearing_signal, sampling_rate, rotational_frequency)

# Print comparison using Pandas
comparison = pd.DataFrame([
    {
        # ** unpacks and merges the dictionary together
        "condition": "Healthy",
        **healthy_features
    },
    {
        "condition": "Imbalance",
        **imbalance_features
    },
    {
        "condition": "Bearing-like",
        **bearing_features
    }
])

# Print the specified columns in the specified order
print(
    comparison[
        [
            "condition", 
            "rms",
            "peak",
            "crest_factor",
            "kurtosis",
            "amp_1x",
            "hf_band_rms"
        ]
    ]
)

# Repeated trials (30)
results = []

conditions = [
    "healthy", 
    "imbalance", 
    "bearing"
]

for condition in conditions:
    for trial in range(30):
        signal = generate_signal(
            condition, seed=1000 + trial + conditions.index(condition) * 100
        )

        features = extract_features(signal, sampling_rate, rotational_frequency)

        features["condition"] = condition
        features["trial"] = trial + 1

        results.append(features)

results_df = pd.DataFrame(results)
print(results_df.head())

# Calculate averages by condition
summary = results_df.groupby(
    "condition"
)[
    [
        "rms",
        "crest_factor",
        "kurtosis",
        "amp_1x",
        "hf_band_rms"
    ]
].agg(
    ["mean", "std"]
)

print(summary)

# Visualize with a box plot
healthy_rms = results_df[results_df["condition"] == "healthy"]["rms"]
imbalance_rms = results_df[results_df["condition"] == "imbalance"]["rms"]
bearing_rms = results_df[results_df["condition"] == "bearing"]["rms"]

plt.boxplot(
    [
        healthy_rms, imbalance_rms, bearing_rms
    ],
    tick_labels=["Healthy", "Imbalance", "Bearing-like"]
)

plt.ylabel("RMS vibration")
plt.title("RMS Comparison Across Conditions")

plt.show()

# Create a healthy baseline
healthy_data = results_df[results_df["condition"] == "healthy"]
baseline_mean = healthy_data[
    [
        "rms",
        "crest_factor",
        "kurtosis",
        "amp_1x",
        "hf_band_rms"
    ]
].mean()

baseline_std = healthy_data[
    [
        "rms",
        "crest_factor",
        "kurtosis",
        "amp_1x",
        "hf_band_rms"
    ]
].std()

# Create thresholds
thresholds = (baseline_mean + 3 * baseline_std)
print("\nHealthy baseline thresholds")
print(thresholds)


# Condition assessment
def assess_condition(features, thresholds):
    flags = {
        "high_rms": features["rms"] > thresholds["rms"],
        "high_impulsiveness":
            (
                features["crest_factor"] > thresholds["crest_factor"]
            )
            or
            (
                features["kurtosis"] > thresholds["kurtosis"]
            ),
        "high_1x": features["amp_1x"] > thresholds["amp_1x"],
        "high_frequency": features["hf_band_rms"] > thresholds["hf_band_rms"]
    }
    # Count them (True = 1, False = 0)
    abnormal_count = sum(flags.values())

    # Add fault indicator (early stage / primitive)
    if (flags["high_1x"] and not flags["high_impulsiveness"]):
        fault_indicator = ("Possible imbalance-type behaviour")
    elif (flags["high_impulsiveness"] and flags["high_frequency"]):
        fault_indicator = ("Possible bearing-like impulsive behaviour")
    elif abnormal_count > 0:
        fault_indicator = ("General abnormal vibration")
    else:
        fault_indicator = ("No abnormal behaviour detected")

    # Assign Normal / Warning / Critical
    if abnormal_count == 0:
        status = "Normal"
    elif abnormal_count == 1:
        status = "Warning"
    else:
        status = "Critical"

    return status, fault_indicator, flags

# Test a new signal
test_signal = generate_signal("imbalance", seed=9999)
test_features = extract_features(test_signal, sampling_rate, rotational_frequency)
status, fault_indicator, flags = assess_condition(test_features, thresholds)

# Print results
print("\nCondition Assessment")
print("--------------------")
print("Status:", status)
print("Indicator:", fault_indicator)
print("\nTriggered indicators:")
for name, triggered in flags.items():
    print(f"{name}: {triggered}")

# Test all three unknown conditions
for condition in conditions:
    signal = generate_signal(condition, seed=5000 + conditions.index(condition))
    features = extract_features(signal, sampling_rate, rotational_frequency)
    status, indicator, flags = assess_condition(features, thresholds)

    print("\n--------------------")
    print("Actual:", condition)
    print("Status:", status)
    print("Indicator:", indicator)

# Save results using Pandas file export
results_df.to_csv(
    "results/lesson7_condition_features.csv",
    index=False
)
