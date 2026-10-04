PRAGMA foreign_keys = ON;

-- Create table for the each machine
CREATE TABLE IF NOT EXISTS machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    machine_type TEXT,
    bearing_model TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create table for each analysis run
CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL,
    source_file TEXT,
    known_condition TEXT,
    measured_at TEXT,
    rpm REAL,
    sampling_rate_hz INTEGER NOT NULL,
    window_start_s REAL,
    window_duration_s REAL NOT NULL,
    health_status TEXT CHECK (
        health_status IS NULL
        OR health_status IN ('Normal', 'Warning', 'Critical')
    ),
    fault_indicator TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

-- Create table for signal features of each analysis run
CREATE TABLE IF NOT EXISTS analysis_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_run_id INTEGER NOT NULL UNIQUE,
    mean REAL,
    rms REAL,
    peak REAL,
    peak_to_peak REAL,
    std REAL,
    crest_factor REAL,
    kurtosis REAL,
    amp_1x REAL,
    amp_2x REAL,
    amp_3x REAL,
    env_bpfo_amp REAL,
    env_bpfi_amp REAL,
    env_rolling_amp REAL,
    FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);

-- Create table for each maintenance records
CREATE TABLE IF NOT EXISTS maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL,
    serviced_at TEXT NOT NULL,
    action TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

-- Create database indexes to use B-Tree Search (O(log N))
CREATE INDEX IF NOT EXISTS idx_analysis_machine
ON analysis_runs(machine_id);

-- ORDER BY reads rows from index without loading every record into memory
CREATE INDEX IF NOT EXISTS idx_analysis_created_at
ON analysis_runs(created_at);

CREATE INDEX IF NOT EXISTS idx_maintenance_machine
ON maintenance_records(machine_id);
