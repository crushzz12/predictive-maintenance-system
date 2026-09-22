import numpy as np
import matplotlib.pyplot as plt

# Basic info from src/01
sampling_rate = 1000
duration = 1

rpm = 1800
frequency = rpm / 60

time = np.arange(0, duration, 1 / sampling_rate)

amplitude = 1.0
clean_vibration = amplitude * np.sin(
    2 * np.pi * frequency * time
)

# Calculate mean
clean_mean_value = np.mean(clean_vibration)

# Calculate peak
clean_peak = np.max(np.abs(clean_vibration))

# Calculate peak-to-peak (np.ptp)
clean_peak_to_peak = np.max(clean_vibration) - np.min(clean_vibration)

# Calculate standard deviation
clean_standard_deviation = np.std(clean_vibration)

# Calculate RMS
clean_rms = np.sqrt(np.mean(clean_vibration ** 2))

# Print results
# Print all results
print("\nClean Results")
print("--------------------")
print(f"Mean              : {clean_mean_value:.4f}")
print(f"RMS               : {clean_rms:.4f}")
print(f"Peak              : {clean_peak:.4f}")
print(f"Peak-to-peak      : {clean_peak_to_peak:.4f}")
print(f"Standard deviation: {clean_standard_deviation:.4f}")

# Add simulated measurement noise (42 is random seed)
rng = np.random.default_rng(42)

# How strong the noise affects the sensor
noise_amplitude = 0.2

noise = noise_amplitude * rng.normal(
    0,
    1,
    len(time)
)

noisy_vibration = clean_vibration + noise

# Plot graph comparing clean vs noisy vibration
# plt.plot(time, clean_vibration, label="Clean")
# plt.plot(time, noisy_vibration, label="Noisy")

# plt.xlim(0, 0.2)

# plt.xlabel("Time (s)")
# plt.ylabel("Acceleration")
# plt.title("Clean vs Noisy Motor Vibration")
# plt.legend()

# plt.show()

# Calculate mean
mean_value = np.mean(noisy_vibration)

# Calculate peak
peak = np.max(np.abs(noisy_vibration))

# Calculate peak-to-peak (np.ptp)
peak_to_peak = np.max(noisy_vibration) - np.min(noisy_vibration)

# Calculate standard deviation
standard_deviation = np.std(noisy_vibration)

# Calculate RMS
rms = np.sqrt(np.mean(noisy_vibration ** 2))

# Print all results
print("\nTime-Domain Features")
print("--------------------")
print(f"Mean              : {mean_value:.4f}")
print(f"RMS               : {rms:.4f}")
print(f"Peak              : {peak:.4f}")
print(f"Peak-to-peak      : {peak_to_peak:.4f}")
print(f"Standard deviation: {standard_deviation:.4f}")

# Vibration Impact
impact_vibration = noisy_vibration.copy()

# Add one large event at 0.5s
impact_vibration[500] += 4

# Calculate new rms and peak
impact_rms = np.sqrt(np.mean(impact_vibration ** 2))
impact_peak = np.max(np.abs(impact_vibration))

impact_mean = np.mean(impact_vibration)
impact_peak_to_peak = np.ptp(impact_vibration)
impact_standard_deviation = np.std(impact_vibration)

# Print results
print("\nImpact Signal")
print("-------------")
print(f"Mean              : {impact_mean:.4f}")
print(f"RMS               : {impact_rms:.4f}")
print(f"Peak              : {impact_peak:.4f}")
print(f"Peak-to-peak      : {impact_peak_to_peak:.4f}")
print(f"Standard deviation: {impact_standard_deviation:.4f}")

# Plot graph
plt.plot(time, impact_vibration)

plt.xlim(0.45, 0.55)

plt.xlabel("Time (s)")
plt.ylabel("Acceleration")
plt.title("Vibration Signal with Simulated Impact")

plt.show()
