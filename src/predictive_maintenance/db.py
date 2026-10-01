import sqlite3
from pathlib import Path

# Convert path into absolute path with .resolve() and find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_DIRECTORY = (PROJECT_ROOT / "database")
DEFAULT_DATABASE_PATH = (DATABASE_DIRECTORY / "predictive-maintenance.db")
SCHEMA_PATH = (DATABASE_DIRECTORY / "schema.sql")


def get_connection(database_path=DEFAULT_DATABASE_PATH):
    """Open a SQLite database connection."""

    database_path = Path(database_path)

    # Ensure that parent directory exists before SQLite creating the file
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)

    # Allow access columns with their names like a dictionary (such as, row["rms"])
    connection.row_factory = sqlite3.Row

    # Enable foreign key checks
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database(database_path=DEFAULT_DATABASE_PATH):
    """Create database tables from schema.sql."""

    if not SCHEMA_PATH.exists():
        return FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    connection = get_connection(database_path)
    try:
        # Execute all SQL queries in schema.sql
        connection.executescript(schema)
        connection.commit()
    finally:
        # Guarantee that the database connection is always closed, even if an error occurs.
        # To prevent file locking
        connection.close()


def add_machine(
    name, 
    machine_type=None, 
    bearing_model=None, 
    description=None, 
    database_path=DEFAULT_DATABASE_PATH
):
    """Insert a machine and return its ID."""

    connection = get_connection(database_path)
    try:
        # Add a new row of machine info into the database table
        cursor = connection.execute(
            """
            INSERT INTO machines (name, machine_type, bearing_model, description) 
            VALUES(?, ?, ?, ?)
            """, 
            (name, machine_type, bearing_model, description)
        )
        connection.commit()

        # Return the auto-incremented primary ID key of that row
        return cursor.lastrowid
    finally:
        connection.close()


def get_machine_by_name(name, database_path=DEFAULT_DATABASE_PATH):
    """Find the machine and return its info, or None if machine is not found."""

    connection = get_connection(database_path)
    try:
        info = connection.execute("SELECT * FROM machines WHERE name = ?", (name,)).fetchone()

        return info
    finally:
        connection.close()


def get_or_create_machine(
    name, 
    machine_type=None, 
    bearing_model=None, 
    description=None, 
    database_path=DEFAULT_DATABASE_PATH
):
    """Return the machine ID or add a new machine if it does not exist."""

    # Check if the machine exists
    machine = get_machine_by_name(name, database_path)
    if machine is not None:
        return machine["id"]

    # No machine exists, so create a new one
    return add_machine(
        name=name, 
        machine_type=machine_type, 
        bearing_model=bearing_model, 
        description=description, 
        database_path=database_path
    )


def add_analysis_run(
    machine_id,
    sampling_rate_hz,
    window_duration_s,
    features,
    source_file=None,
    known_condition=None,
    measured_at=None,
    rpm=None,
    window_start_s=None,
    spectral_features=None,
    health_status=None,
    fault_indicator=None,
    database_path=DEFAULT_DATABASE_PATH
):
    """Record one analysis run and its features, and return its primary key ID."""

    if spectral_features is None:
        spectral_features = {}

    connection = get_connection(database_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO analysis_runs (
                machine_id, source_file, known_condition, measured_at, rpm, sampling_rate_hz,
                window_start_s, window_duration_s, health_status, fault_indicator
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                machine_id, source_file, known_condition, measured_at, rpm, sampling_rate_hz,
                window_start_s, window_duration_s, health_status, fault_indicator
            )
        )

        analysis_run_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO analysis_features (
                analysis_run_id, mean, rms, peak, peak_to_peak, std, crest_factor, kurtosis, 
                amp_1x, amp_2x, amp_3x
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_run_id,

                # Insert time-domain features, while .get() get values and prevents KeyError
                features.get("mean"),
                features.get("rms"),
                features.get("peak"),
                features.get("peak_to_peak"),
                features.get("std"),
                features.get("crest_factor"),
                features.get("kurtosis"),

                # Insert spectral / frequency-domain features
                spectral_features.get("amp_1x"),
                spectral_features.get("amp_2x"),
                spectral_features.get("amp_3x")
            )
        )
        connection.commit()

        return analysis_run_id
    except Exception:
        # Rollback if there are data failed to store to prevent only one table has data.
        connection.rollback()
        raise 
    finally:
        connection.close()


def get_analysis_history(machine_id, limit=100, database_path=DEFAULT_DATABASE_PATH):
    """Return recent analysis histories for a machine."""

    connection = get_connection(database_path)
    try:
        # Ordered latest first
        histories = connection.execute(
            """
            SELECT 
                analysis_runs.id AS analysis_id,
                analysis_runs.machine_id,
                analysis_runs.source_file,
                analysis_runs.known_condition,
                analysis_runs.measured_at,
                analysis_runs.rpm,
                analysis_runs.sampling_rate_hz,
                analysis_runs.window_start_s,
                analysis_runs.window_duration_s,
                analysis_runs.health_status,
                analysis_runs.fault_indicator,
                analysis_runs.created_at,

                analysis_features.mean,
                analysis_features.rms,
                analysis_features.peak,
                analysis_features.peak_to_peak,
                analysis_features.std,
                analysis_features.crest_factor,
                analysis_features.kurtosis,
                analysis_features.amp_1x,
                analysis_features.amp_2x,
                analysis_features.amp_3x
            FROM analysis_runs 
            JOIN analysis_features ON analysis_runs.id = analysis_features.analysis_run_id
            WHERE analysis_runs.machine_id = ? 
            ORDER BY analysis_runs.id DESC 
            LIMIT ?
            """,
            (machine_id, limit)
        ).fetchall()

        return histories
    finally:
        connection.close()


def add_maintenance_record(
    machine_id,
    serviced_at,
    action,
    notes=None,
    database_path=DEFAULT_DATABASE_PATH
):
    """Insert a maintenance log entry and return its ID."""

    connection = get_connection(database_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO maintenance_records (machine_id, serviced_at, action, notes)
            VALUES (?, ?, ?, ?)
            """,
            (machine_id, serviced_at, action, notes)
        )
        connection.commit()

        return cursor.lastrowid
    finally:
        connection.close()


def get_maintenance_history(machine_id, database_path=DEFAULT_DATABASE_PATH):
    """Return all maintenance histories for a machine."""

    connection = get_connection(database_path)
    try:
        histories = connection.execute(
            "SELECT * FROM maintenance_records WHERE machine_id = ? ORDER BY serviced_at DESC",
            (machine_id,)
        ).fetchall()

        return histories
    finally:
        connection.close()


def get_all_machines(database_path=DEFAULT_DATABASE_PATH):
    """Get all registered machines in the database."""
    
    connection = get_connection(database_path)
    try:
        machines = connection.execute("SELECT * FROM machines ORDER BY name").fetchall()

        return machines
    finally:
        connection.close()


def get_machine_by_id(machine_id, database_path=DEFAULT_DATABASE_PATH):
    """Get the machine info by its ID."""

    connection = get_connection(database_path)
    try:
        machine = connection.execute(
            "SELECT * FROM machines WHERE id = ?", (machine_id,)
        ).fetchone()

        return machine
    finally:
        connection.close()


def get_analysis_by_id(analysis_id, database_path=DEFAULT_DATABASE_PATH):
    """Get info of an analysis run by its ID."""

    connection = get_connection(database_path)
    try:
        info = connection.execute(
            """
            SELECT
                analysis_runs.id AS analysis_id,
                analysis_runs.machine_id,
                analysis_runs.source_file,
                analysis_runs.known_condition,
                analysis_runs.measured_at,
                analysis_runs.rpm,
                analysis_runs.sampling_rate_hz,
                analysis_runs.window_start_s,
                analysis_runs.window_duration_s,
                analysis_runs.health_status,
                analysis_runs.fault_indicator,
                analysis_runs.created_at,

                analysis_features.mean,
                analysis_features.rms,
                analysis_features.peak,
                analysis_features.peak_to_peak,
                analysis_features.std,
                analysis_features.crest_factor,
                analysis_features.kurtosis,
                analysis_features.amp_1x,
                analysis_features.amp_2x,
                analysis_features.amp_3x,

                machines.name AS machine_name
            FROM analysis_runs 
            JOIN analysis_features ON analysis_runs.id = analysis_features.analysis_run_id
            JOIN machines ON analysis_runs.machine_id = machines.id
            WHERE analysis_runs.id = ? 
            """,
            (analysis_id,)
        ).fetchone()

        return info
    finally:
        connection.close()
