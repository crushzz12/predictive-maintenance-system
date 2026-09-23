import numpy as np
import matplotlib.pyplot as plt

# Same motor info from src/03
sampling_rate = 1000
duration = 1

rpm = 1800
rotational_frequency = rpm / 60

time = np.arange(0, duration, 1 / sampling_rate)

amplitude_1x = 1.0
amplitude_2x = 0.4
amplitude_3x = 0.2

vibration_1x = amplitude_1x * np.sin(
    2 * np.pi * rotational_frequency * time
)

vibration_2x = amplitude_2x * np.sin(
    2 * np.pi * (2 * rotational_frequency) * time
)

vibration_3x = amplitude_3x * np.sin(
    2 * np.pi * (3 * rotational_frequency) * time
)

combined_vibration = (vibration_1x + vibration_2x + vibration_3x)

# Add noise (same as src/03)
rng = np.random.default_rng(42)
noise_amplitude = 0.15
noise = noise_amplitude * rng.normal(0, 1, len(time))
measured_vibration = combined_vibration + noise

# Plot graph
plt.plot(time, measured_vibration)
plt.xlim(0, 0.2)

plt.xlabel("Time (s)")
plt.ylabel("Acceleration")
plt.title("Time-Domain Vibration Signal")

plt.show()

# FFT (Fast Fourier Transform) - Changes the signal from time domain to frequency domain

# Remove mean first (non-zero mean or DC offset causes large component at 0 Hz in FFT)
# Not really interested in 0 Hz component in this case
signal = measured_vibration - np.mean(measured_vibration)

# Count the num of samples
N = len(signal)
# print("Number of samples:", N)

# Perform FFT (rfft gives positive frequencies only / real-valued input)
fft_values = np.fft.rfft(signal)
# Note: this result gives the y-axis (amplitude and phase of each frequency)

# Create frequency axis (x-axis)
frequencies = np.fft.rfftfreq(N, d=1 / sampling_rate)
# print(frequencies[:10])

# Convert FFT results into amplitudes
fft_amplitude = np.abs(fft_values)

# Normalization (so the results do not depend on N, and recovers the negative side by x 2)
fft_amplitude = (2 / N) * fft_amplitude

# DC component should not be doubled
fft_amplitude[0] /= 2

# Nyquist component should not be doubled
if N % 2 == 0:
    fft_amplitude[-1] /= 2

# Plot FFT
plt.plot(frequencies, fft_amplitude)

plt.xlim(0, 200)

plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.title("Frequency Spectrum of Simulated Machine Vibration")

plt.show()

# Identify strongest frequency
# fft_amplitude[1:] starts from 1 so ignores 0 Hz
# np.argsort() returns indices that would sort them in asc order
# [-3:] takes the final three, which are the three largest
# + 1 corrects the index because index 0 was removed just now when [1:]
indices = np.argsort(fft_amplitude[1:])[-3:] + 1

# Now indices is from 3rd largest to largest, so reverse it to make largest first
indices = indices[np.argsort(
    fft_amplitude[indices]
)[::-1]]

# Print out the results
print("\nThree strongest frequency components")
print("------------------------------------")

for index in indices:
    print(
        f"{frequencies[index]:.1f} Hz "
        f"-> amplitude {fft_amplitude[index]:.3f}"
    )
