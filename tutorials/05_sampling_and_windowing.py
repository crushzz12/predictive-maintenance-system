import numpy as np
import matplotlib.pyplot as plt


def calculate_fft(signal, sampling_rate):
    N = len(signal)
    fft_values = np.fft.rfft(signal)

    frequencies = np.fft.rfftfreq(N, d=1 / sampling_rate)

    amplitudes = (2 / N) * np.abs(fft_values)

    amplitudes[0] /= 2

    if N % 2 == 0:
        amplitudes[-1] /= 2

    return frequencies, amplitudes


# Create spectral leakage
sampling_rate = 2000
duration = 1

time = np.arange(0, duration, 1 / sampling_rate)

# 30.5 Hz is used instead of 30 Hz
frequency = 700
amplitude = 1.0

signal = amplitude * np.sin(
    2 * np.pi * frequency * time
)

# Calculate the FFT
frequencies, fft_amplitude = calculate_fft(signal, sampling_rate)

# Plot graph
plt.plot(frequencies, fft_amplitude)

plt.xlim(20, 45)

plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.title("FFT of 30.5 Hz Signal Without Windowing")

plt.show()

# Apply a Hann window
N = len(signal)
window = np.hanning(N)
windowed_signal = signal * window

# Plot the window itself
plt.plot(time, window)
plt.xlabel("Time (s)")
plt.ylabel("Window amplitude")
plt.title("Hann Window")

plt.show()

# Plot windowed time signal
plt.plot(time, signal, label="Original")
plt.plot(time, windowed_signal, label="Windowed")

plt.xlim(0, 1)

plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.title("Original vs Hann-Windowed Signal")
plt.legend()

plt.show()

# Calculate windowed FFT
windowed_fft = np.fft.rfft(windowed_signal)

# Restores the amplitude after windowing (windowing causes amplitude to be lower)
coherent_gain = np.mean(window)

windowed_amplitude = (
    2 / (N * coherent_gain)
) * np.abs(windowed_fft)

windowed_amplitude[0] /= 2

if N % 2 == 0:
    windowed_amplitude[-1] /= 2

# Plot graph
plt.plot(frequencies, windowed_amplitude)

plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.title("FFT of 30.5 Hz Signal with Hann Window")

plt.show()

# Aliasing
# When frequency = 700, plot graph (Nyquist = 500 Hz)
# It shows 300 Hz instead but its actually 700 Hz
# When increase sampling_rate = 2000 (Nyquist = 1000 Hz), now it shows as 700 Hz
