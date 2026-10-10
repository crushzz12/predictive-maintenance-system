# Predictive Maintenance and Machine Condition Monitoring System

This project is a vibration-based condition monitoring application built with Python and Flask to detect abnormal machine behaviour. It turns raw accelerometer readings into condition indicators and compares them to a machine-specific healthy baseline. Then, it reports bearing-fault evidence which an engineer can inspect and verify.

## Why I Built This

Raw vibration time series alone is very hard to interpret without signal processing and a healthy reference.

This project combines mechanical vibration analysis with software engineering to create a simple workflow for machine condition assessment.

## Features

**Asset and baseline management**
- Machine asset management
- Healthy baseline configuration

**Signal analysis**
- MATLAB (`.mat`) vibration files upload
- Time-domain features extraction: Root Mean Square (RMS), kurtosis, and crest factor
- Fast Fourier Transform (FFT) analysis of 1x, 2x, and 3x running-speed components
- Envelope analysis for bearing defects
- Ball Pass Frequency Outer race (BPFO), Ball Pass Frequency Inner race (BPFI), and rolling-element evidence

**Assessment and records**
- Baseline-relative condition assessment
- SQLite-backed analysis history
- Maintenance records logging
- Validation dashboard
- PDF analysis reports

## How It Works

![Pipeline](docs/images/pipeline.svg#gh-light-mode-only)
![Pipeline](docs/images/pipeline-dark.svg#gh-dark-mode-only)

## Dashboard

## Engineering Methods

### Predictive Maintenance

Predictive maintenance uses information about equipment condition to identify faults before functional failure occurs. In this project, vibration measurements are used as the condition-monitoring input.

### RMS

Root Mean Square (RMS) represents the overall magnitude of the vibration signal. An increase relative to healthy operation may indicate a change in machine condition, although RMS alone is not sufficient to identify the fault type.

### Kurtosis and Crest Factor

Kurtosis and crest factor are used to identify impulsive behaviour in the vibration waveform. Repeated impacts can occur when damaged bearing surfaces pass through the load zone.

### FFT

The Fast Fourier Transform (FFT) converts the vibration signal from the time-domain to frequency-domain. This allows vibration components near the shaft rotational frequency and its harmonics to be examined.

### Envelope Analysis

Bearing faults often excite high-frequency structural resonance. Envelope analysis demodulates this vibration so that repetitive imapct frequencies can be identified more clearly.

### Bearing Characteristic Frequencies

This application evaluates evidence near characteritic bearing frequencies such as:

- BPFO: Ball Pass Frequency Outer race
- BPFI: Ball Pass Frequency Inner race
- Rolling-element defect frequency

These are used as diagnostic evidence rather than treated as absolute proof of a fault.

## Tech Stack

| Area | Technology |
|:---|:---|
| Programming | Python |
| Web application | Flask, Jinja2 |
| Numerical processing | NumPy |
| Signal processing | SciPy |
| Data handling | Pandas |
| Visualization | Matplotlib, Chart.js |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| PDF reporting | ReportLab |
| Development | VS Code, Git, GitHub |

## Project Structure


```text
predictive-maintenance-system/
│
├── src/
│   ├── app.py                     # Flask application and routes
│   │
│   ├── predictive_maintenance/
│   │   ├── analysis_service.py    # Analysis workflow
│   │   ├── baseline_service.py    # Healthy baseline workflow
│   │   ├── validation_service.py  # Validation workflow
│   │   ├── report_service.py      # PDF report generation
│   │   ├── data_loader.py         # Vibration file loading/segmentation
│   │   ├── features.py            # Time-domain features
│   │   ├── spectrum.py            # FFT and filtering functions
│   │   ├── bearing.py             # Bearing-frequency calculations
│   │   ├── condition.py           # Condition assessment logic
│   │   └── db.py                  # SQLite database functions
│   │
│   ├── templates/                 # Flask/Jinja HTML pages
│   └── static/                    # CSS, JavaScript, and favicon
│
├── database/
│   └── schema.sql                 # Database schema
│
├── scripts/                       # Validation and diagnostic scripts
├── tutorials/                     # Development/learning experiments
├── results/                       # Validation outputs
├── data/cwru/raw/                 # Local CWRU files, excluded from Git
│
├── pyproject.toml                 # Project dependencies/configuration
├── .gitignore
└── README.md
```

## Validation



## Installation

```bash
git clone <repository>
cd predictive-maintenance-system

python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
```

## Usage

```bash
python src/app.py
```

Open `http://localhost:5000`, then:

### 1. Register a machine

Open **Add Machine** and enter the machine name, type, bearing information, and description.

Each machine has its own analysis history, maintenance records, and healthy baseline.

### 2. Configure a healthy baseline

Open the selected machine and choose **Configure Baseline**.

Upload a vibration recording collected while the machine is known to be operating normally. Enter the required information of the recording.

It is recommended to use the `97.mat` from CWRU for the healthy baseline.

**Important:** Use only verified healthy recordings. A baseline containing abnormal vibration can lead to misleading condition assessments.

### 3. Upload a vibration recording

Select **New Analysis** from the machine dashboard and upload a supported MATLAB `.mat` vibration file. Then, enter the required information and start the analysis. The application will automatically perform calculations and save the results to the database (SQLite). 

It is recommended to use the `109.mat`, `122.mat`, or `135.mat` from CWRU for the fault examples.

**Current limitation:** The current version of the application only supports the **CWRU-style MATLAB** file structure. It is not a universal MAT or CSV vibration importer.

### 4. Review analysis details 

Return to the machine dashboard to examine the latest assessment, historical trends, and recent analyses.

Open an individual analysis to inspect its health status, bearing evidence, measurement information, and advanced signal features.

**Note:** A Normal, Warning, or Critical status indicates a level of statistical deviation from the configured healthy baseline. It is not a certified machinery safety classification.

### 5. Generate an engineering report

From the **Analysis Detail** page (from step 4), select **Download PDF Report**.

This report summarizes the machine, measurement conditions, signal features, condition assessment, and bearing-frequency evidence.

### 6. Review History and Maintenance

Open **Analysis History** to browse previous measurements. Open **Maintenance** to record inspection or maintenance actions associated with the machine.

## Input Data Format

- File type: MATLAB `.mat`
- Expected variables: [e.g. `DE_time`, `RPM`]
- Sampling rate [e.g. 12 kHz / 48 kHz]

## Limitation

Validation uses selected CWRU recordings rather than independent machines.

The healthy baseline contains limited data.

The system currently supports the CWRU-style MAT structure.

## Future Improvements

- Support CSV and live sensor acquisition
-Use longer healthy baseline recordings
- Use multiple operating loads or speeds
- Automatic envelope-band selection
- BPFO / BPFI harmonic and sideband scoring
- Store raw or compressed spectra for historical comparison
- Multi-resolution analysis windows
- Trend-based degradation detection
- Machine-learning comparison after sufficient labeled data
- Automated maintenance recommendations
