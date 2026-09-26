import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import kurtosis


# Calculate time-domain features and return a dictionary containing the features
def calculate_time_features(signal):
    # Calculate time-domain features
    mean_value = np.mean(signal)
    rms = np.sqrt(np.mean(signal ** 2))
    peak = np.max(np.abs(signal))
    peak_to_peak = np.ptp(signal)
    standard_deviation = np.std(signal)

    # Calculate the crest factor
    crest_factor = peak / rms

    # Calculate kurtosis (Pearson's Kurtosis, normal distribution: 3)
    kurtosis_value = kurtosis(
        signal,
        fisher=False,
        bias=False
    )

    # Return a dictionary
    return {
        "mean": mean_value,
        "rms": rms,
        "peak": peak,
        "peak_to_peak": peak_to_peak,
        "std": standard_deviation,
        "crest_factor": crest_factor,
        "kurtosis": kurtosis_value
    }


# Convert time-domain to frequency-domain using FFT
def calculate_fft(signal, sampling_rate):
    N = len(signal)
    fft_values = np.fft.rfft(signal)

    frequencies = np.fft.rfftfreq(N, d=1 / sampling_rate)

    amplitudes = (2 / N) * np.abs(fft_values)

    amplitudes[0] /= 2

    if N % 2 == 0:
        amplitudes[-1] /= 2

    return frequencies, amplitudes


# Build a healthy signal (similar to src/05)
sampling_rate = 2000
duration = 2

rpm = 1800
rotational_frequency = rpm / 60

time = np.arange(0, duration, 1 / sampling_rate)
N = len(time)

rng = np.random.default_rng(42)

base_vibration = 0.5 * np.sin(
    2 * np.pi * rotational_frequency * time
)

noise = 0.08 * rng.normal(0, 1, N)

healthy_signal = base_vibration + noise

# Calculate time-domain features
healthy_features = calculate_time_features(healthy_signal)

# Print results
for name, value in healthy_features.items():
    print(f"{name}: {value:.4f}")

# Create repeated impacts
impact_frequency = 8
impact_amplitude = 2.0

impact_interval = int(sampling_rate / impact_frequency)

fault_signal = healthy_signal.copy()

impact_indices = np.arange(impact_interval, N, impact_interval)

fault_signal[impact_indices] += impact_amplitude

# Plot healthy vs impulsive vibration
# plt.plot(time, healthy_signal)

# plt.xlim(0, 0.5)
# plt.xlabel("Time (s)")
# plt.ylabel("Acceleration")
# plt.title("Healthy Simulated Vibration")
# plt.show()

# plt.plot(time, fault_signal)

# plt.xlim(0, 0.5)
# plt.xlabel("Time (s)")
# plt.ylabel("Acceleration")
# plt.title("Simulated Vibration with Repeated Impacts")
# plt.show()

# Compare the features
fault_features = calculate_time_features(fault_signal)

print("\nHealthy")
print("-------")

for name, value in healthy_features.items():
    print(f"{name}: {value:.4f}")

print("\nImpulsive")
print("---------")

for name, value in fault_features.items():
    print(f"{name}: {value:.4f}")

# Damped ringing response
ring_frequency = 250
ring_duration = 0.03
decay_rate = 120
ring_time = np.arange(0, ring_duration, 1 / sampling_rate)

# Exponential decay (starts high and decreases towards zero) * Oscillation (sin(2pi*ft))
ring = (
    np.exp(-decay_rate * ring_time)
    * 
    np.sin(2 * np.pi * ring_frequency * ring_time)
)

# Plot ring itself
# plt.plot(ring_time, ring)
# plt.xlabel("Time (s)")
# plt.ylabel("Amplitude")
# plt.title("Damped Vibration Following an Impact")

# plt.show()

# Add repeated ringing impacts
bearing_fault_signal = healthy_signal.copy()

# Prevent adding more samples than the original ones / remaining ones
for index in impact_indices:
    end_index = min(index + len(ring), N)
    available_length = end_index - index

    bearing_fault_signal[index:end_index] += (impact_amplitude * ring[:available_length])

# Plot graph
plt.plot(time, bearing_fault_signal)
plt.xlim(0, 0.5)
plt.xlabel("Time (s)")
plt.ylabel("Acceleration")
plt.title("Simulated Bearing-Like Impulsive Vibration")

plt.show()

# Calculate the features
bearing_features = calculate_time_features(bearing_fault_signal)

feature_names = [
    "rms",
    "peak",
    "crest_factor",
    "kurtosis"
]

print("\nFeature Comparison")
print("------------------")

for feature in feature_names:
    print(
        f"{feature:15}"
        f"Healthy = {healthy_features[feature]:8.4f}  "
        f"Bearing-like: {bearing_features[feature]:8.4f}"
    )

# Calculate FFT and plot
frequencies, amplitudes = calculate_fft(bearing_fault_signal, sampling_rate)

plt.plot(frequencies, amplitudes)
plt.xlim(0, 500)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.title("Spectrum of Bearing-Like Signal")

plt.show()
