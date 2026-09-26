import numpy as np
import matplotlib.pyplot as plt


# Vibration, y(t) = A sin(2 * pi * ft)
def calculate_vibration(amplitude, frequency):
    vibration = amplitude * np.sin(
        2 * np.pi * frequency * time
    )
    return vibration


# Same motor info from src/01
sampling_rate = 1000
duration = 1

rpm = 1800
rotational_frequency = rpm / 60

time = np.arange(0, duration, 1 / sampling_rate)

# print("RPM:", rpm)
# print("Rotational frequency:", rotational_frequency, "Hz")

# Create each vibration component separately
amplitude_1x = 1.0
amplitude_2x = 0.4
amplitude_3x = 0.2

vibration_1x = calculate_vibration(amplitude_1x, rotational_frequency)
vibration_2x = calculate_vibration(amplitude_2x, 2 * rotational_frequency)
vibration_3x = calculate_vibration(amplitude_3x, 3 * rotational_frequency)

# Plot graph
# plt.plot(time, vibration_1x, label="1x - 30 Hz")
# plt.plot(time, vibration_2x, label="2x - 60 Hz")
# plt.plot(time, vibration_3x, label="3x - 90 Hz")

# plt.xlim(0, 0.1)

# plt.xlabel("Time (s)")
# plt.ylabel("Amplitude")
# plt.title("Individual Vibration Components")
# plt.legend()

# plt.show()

# Calculate the combined vibration
combined_vibration = (vibration_1x + vibration_2x + vibration_3x)

# plt.plot(time, combined_vibration)

# plt.xlim(0, 0.2)

# plt.xlabel("Time (s)")
# plt.ylabel("Amplitude")
# plt.title("Combined Motor Vibration")

# plt.show()

# Add noise
rng = np.random.default_rng(42)

noise_amplitude = 0.15

noise = noise_amplitude * rng.normal(0, 1, len(time))

measured_vibration = combined_vibration + noise

# Plot graph
plt.plot(time, measured_vibration)

plt.xlim(0, 0.2)

plt.xlabel("Time (s)")
plt.ylabel("Acceleration")
plt.title("Simulated Machine Vibration with Noise")

plt.show()

# Calculate RMS
rms = np.sqrt(np.mean(measured_vibration ** 2))
# print(f"RMS: {rms:.4f}")

# Calculate the rest time-domain features
mean_value = np.mean(measured_vibration)
peak = np.max(np.abs(measured_vibration))
peak_to_peak = np.max(measured_vibration) - np.min(measured_vibration)
standard_deviation = np.std(measured_vibration)

# Print all values
print("\nTime-Domain Features")
print("--------------------")
print(f"Mean              : {mean_value:.4f}")
print(f"RMS               : {rms:.4f}")
print(f"Peak              : {peak:.4f}")
print(f"Peak-to-peak      : {peak_to_peak:.4f}")
print(f"Standard deviation: {standard_deviation:.4f}")

# Results
# Normal condition: RMS: 0.7916
# when only amplitude_2x = 0: RMS: 0.7385
# when only amplitude_3x - 0: RMS: 0.7783
# when amplitude_1x = 0.3, amplitude_2x = 1.0, amplitude_3x = 0.1: RMS: 0.7592 (Check Graph)
