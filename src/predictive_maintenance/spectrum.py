import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt


# Convert time-domain to frequency domain using Fast Fourier Transform (FFT)
def calculate_fft(signal, sampling_rate, window="hann"):
    """Calculate a single-sided amplitude spectrum."""

    signal = np.asarray(signal)
    if signal.size == 0:
        raise ValueError("Signal cannot be empty.")
    if sampling_rate <= 0:
        raise ValueError("Sampling rate must be positive.")

    N = len(signal)

    # Remove DC offset
    centered_signal = signal - np.mean(signal)

    # Apply windowing to mitigate spectral leakage
    # Calculate coherent gain to correct peak amplitude
    if window == "hann":
        window_values = np.hanning(N)
        processed_signal = centered_signal * window_values
        coherent_gain = np.mean(window_values)
    elif window is None:
        processed_signal = centered_signal
        coherent_gain = 1.0
    else:
        raise ValueError(f"Unsupported window: {window}")

    # Calculate real FFT (rfft), returns only positive frequencies
    fft_values = np.fft.rfft(processed_signal)
    frequencies = np.fft.rfftfreq(N, d=1 / sampling_rate)

    # Convert double-sided spectrum to single-sided peak amplitude
    # (Folds negative frequencies onto positive ones)
    amplitudes = (2 / (N * coherent_gain)) * np.abs(fft_values)

    # Undo * 2 above for DC (0 Hz) and Nyquist (Fs / 2, when N is even)
    # (They have no negative counterparts)
    amplitudes[0] /= 2
    if N % 2 == 0:
        amplitudes[-1] /= 2

    return frequencies, amplitudes


def get_frequency_amplitude(frequencies, amplitudes, target_frequency):
    """Return the amplitude at the FFT bin closest to a requested frequency."""

    index = np.argmin(np.abs(frequencies - target_frequency))

    return amplitudes[index]


def find_peak_near(frequencies, amplitudes, target_frequency, search_width=5.0):
    """Find the strongest spectral peak within a frequency range around the target frequency."""

    # Set range of target frequency +/- search width
    lower_bound = target_frequency - search_width
    upper_bound = target_frequency + search_width
    mask = (frequencies >= lower_bound) & (frequencies <= upper_bound)

    if not np.any(mask):
        raise ValueError("Search region contains no FFT bins.")

    local_frequencies = frequencies[mask]
    local_amplitudes = amplitudes[mask]
    local_peak_index = np.argmax(local_amplitudes)

    return local_frequencies[local_peak_index], local_amplitudes[local_peak_index]


def calculate_band_rms(frequencies, amplitudes, low_frequency, high_frequency):
    """Calculate RMS spectral amplitude inside a frequency band."""

    if low_frequency > high_frequency:
        raise ValueError("Invalid band: Low frequency cannot be greater than high frequency.")

    # Select bins within the range
    mask = (frequencies >= low_frequency) & (frequencies <= high_frequency)

    if not np.any(mask):
        raise ValueError("Frequency band contains no data.")

    # Calculate the RMS
    return np.sqrt(np.mean(amplitudes[mask] ** 2))


def bandpass_filter(signal, sampling_rate, low_cut, high_cut, order=4):
    """Apply a zero-phase Butterworth band-pass filter."""

    if low_cut <= 0:
        raise ValueError("Low cutoff must be positive.")
    if low_cut >= high_cut:
        raise ValueError("Low cutoff is must be less than high cutoff.")

    nyquist = sampling_rate / 2
    if high_cut >= nyquist:
        raise ValueError("High cutoff must be below the Nyquist frequency.")

    # Use second-order sections (sos), more stable
    sos = butter(order, [low_cut, high_cut], btype="bandpass", fs=sampling_rate, output="sos")

    # Apply forward-backward filtering to avoid phase shift
    return sosfiltfilt(sos, signal)


def calculate_envelope_spectrum(signal, sampling_rate):
    """Calculate the Hilbert envelope and its frequency spectrum."""

    signal = np.asarray(signal)
    if signal.size == 0:
        raise ValueError("Signal cannot be empty.")
    if sampling_rate <= 0:
        raise ValueError("Sampling rate must be positive.")

    # Computes the Hilbert transform and its absolute value
    analytic_signal = hilbert(signal)
    envelope = np.abs(analytic_signal)

    # Calculate spectrum of the envelope
    frequencies, amplitudes = calculate_fft(envelope, sampling_rate, window="hann")

    return frequencies, amplitudes, envelope
