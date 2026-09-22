import numpy as np
import matplotlib.pyplot as plt

# 1000 measurements per second (f = 1000Hz)
sampling_rate = 1000
duration = 1

time = np.arange(0, duration, 1 / sampling_rate)

# Print results
print(len(time))
print(time[:10])

# Frequency
rpm = 1800
frequency = rpm / 60

print("Rotational frequency:", frequency, "Hz")

# Artificial Vibration Simple Harmonic Motion, x(t) = A sin(2*pi*ft)
amplitude = 0.5
vibration = amplitude * np.sin(
    2 * np.pi * frequency * time
)

# Root Mean Square (RMS)
rms = np.sqrt(np.mean(vibration ** 2))

print("RMS vibration:", rms)

# Plot relationship
plt.plot(time, vibration)
plt.xlim(0, 0.2)

plt.xlabel("Time (s)")
plt.ylabel("Acceleration")
plt.title("Simulated 1800 RPM Motor Vibration")

plt.show()