# AI assistance disclosure:
# OpenAI ChatGPT was used to discuss the implementation, explain relevant concepts, 
# and provide code examples.
# The final implementation was adapted and tested as part of this project.

from predictive_maintenance.data_loader import load_cwru_file, segment_signal
from predictive_maintenance.features import extract_time_features
from predictive_maintenance.spectrum import calculate_fft, get_frequency_amplitude
from predictive_maintenance.bearing import extract_envelope_features
from predictive_maintenance.db import add_analysis_run


def extract_feature_vector(signal, sampling_rate, rpm):
    """Extract all features used by the condition-monitoring application."""

    time_features = extract_time_features(signal)
    frequencies, amplitudes = calculate_fft(signal, sampling_rate)
    shaft_frequency = rpm / 60

    spectral_features = {
        "amp_1x": get_frequency_amplitude(frequencies, amplitudes, shaft_frequency),
        "amp_2x": get_frequency_amplitude(frequencies, amplitudes, 2 * shaft_frequency),
        "amp_3x": get_frequency_amplitude(frequencies, amplitudes, 3 * shaft_frequency)
    }

    envelope_features = extract_envelope_features(signal, sampling_rate, rpm)

    # Merge all domain features into a single feature vector
    return {
        **time_features,
        **spectral_features,
        **envelope_features
    }


def analyze_recording(
    file_path,
    machine_id,
    sampling_rate,
    window_duration,
    channel="DE_time",
    rpm_override=None,
    source_filename=None,
    known_condition=None
):
    """
    Analyze an uploaded vibration recording, segment it into windows and store each window
    in SQLite.
    """
    
    signal, file_rpm = load_cwru_file(file_path, channel=channel)

    # Prioritize manual override rpm value over file metadata
    if rpm_override is not None:
        rpm = rpm_override
    else:
        rpm = file_rpm

    if rpm is None:
        raise ValueError("RPM was not found in the file. Enter RPM manually.")
    if rpm <= 0:
        raise ValueError("RPM must be positive.")

    # Divide signal into windows
    windows = segment_signal(signal, sampling_rate, window_duration)
    if not windows:
        raise ValueError("Recording is shorter than the selected window duration.")

    # Extract features for each window and commit to database
    analysis_ids = []
    for index, window in enumerate(windows):
        features = extract_feature_vector(window, sampling_rate, rpm)
        
        analysis_id = add_analysis_run(
            machine_id=machine_id,
            source_file=source_filename,
            known_condition=known_condition,
            rpm=rpm,
            sampling_rate_hz=sampling_rate,
            window_start_s=index * window_duration,
            window_duration_s=window_duration,
            all_features=features
        )

        analysis_ids.append(analysis_id)

    return {
        "analysis_ids": analysis_ids,
        "window_count": len(analysis_ids),
        "rpm": rpm
    }
