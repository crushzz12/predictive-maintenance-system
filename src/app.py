import sqlite3

from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, render_template, abort, request, redirect, url_for, flash

from werkzeug.utils import secure_filename

from predictive_maintenance.analysis_service import analyze_recording
from predictive_maintenance.baseline_service import build_machine_baseline, load_machine_baseline
from predictive_maintenance.condition import load_baseline, evaluate_analysis
from predictive_maintenance.db import (
    initialize_database,
    get_all_machines,
    get_machine_by_id,
    get_analysis_history,
    get_analysis_by_id,
    get_maintenance_history,
    add_machine,
    add_maintenance_record
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

app = Flask(__name__)

# For flash for local testing only, not suitable for production
app.config["SECRET_KEY"] = "development-key"

# Restrict max file upload size to 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

@app.route("/")
def index():
    """Show all machines"""

    machines = get_all_machines()

    return render_template("index.html", machines=machines)


@app.route("/machine/<int:machine_id>")
def machine_detail(machine_id):
    """Show machine info and its important analysis records."""

    machine = get_machine_by_id(machine_id)
    if machine is None:
        abort(404)

    # Get analysis histories (by default is ordered newest first)
    analyses = get_analysis_history(machine_id)
    baseline = load_machine_baseline(machine_id)

    analysis_items = []
    for row in analyses:
        analysis = dict(row)
        if baseline is not None:
            analysis["assessment"] = evaluate_analysis(analysis, baseline)
        else:
            analysis["assessment"] = None
        analysis_items.append(analysis)
    analyses = analysis_items
    latest_analysis = analyses[0] if analyses else None

    # Prepare chart data (reverse it to become from oldest to newest for charts)
    chart_rows = list(reversed(analyses))
    chart_labels = [f"Run {row['analysis_id']}" for row in chart_rows]
    rms_values = [row["rms"] for row in chart_rows]
    kurtosis_values = [row["kurtosis"] for row in chart_rows]

    return render_template(
        "machine.html",
        machine=machine,
        analyses=analyses,
        latest_analysis=latest_analysis,
        chart_labels=chart_labels,
        rms_values=rms_values,
        kurtosis_values=kurtosis_values
    )


@app.route("/analysis/<int:analysis_id>")
def analysis_detail(analysis_id):
    """Show detailed analysis info including features and status."""

    analysis = dict(get_analysis_by_id(analysis_id))
    if analysis is None:
        abort(404)

    machine_id = analysis["machine_id"]
    baseline = load_machine_baseline(machine_id)
    assessment = evaluate_analysis(analysis, baseline)

    return render_template("analysis.html", analysis=analysis, assessment=assessment)


@app.route("/machine/<int:machine_id>/maintenance", methods=["GET", "POST"])
def maintenance(machine_id):
    """Show maintenance history of the machine."""

    machine = get_machine_by_id(machine_id)
    if machine is None:
        abort(404)

    if request.method == "POST":
        # Retrieve input from users
        serviced_at = request.form["serviced_at"]
        action = request.form["action"].strip()
        notes = request.form.get("notes")

        # Check validity of users input, if valid, add record to database
        if not action:
            flash("Maintenance action is required.", "error")
        else:
            add_maintenance_record(
                machine_id=machine_id,
                serviced_at=serviced_at,
                action=action,
                notes=notes
            )
            flash("Maintenance record added.", "success")
            return redirect(request.url)

    # Via GET or not action
    records = get_maintenance_history(machine_id)
    return render_template("maintenance.html", machine=machine, records=records)


@app.route("/machines/new", methods=["GET", "POST"])
def new_machine():
    """Create a new machine and register into database."""

    if request.method == "POST":
        # Retrieve input from users
        name = request.form.get("name","").strip()
        machine_type = request.form.get("machine_type")
        bearing_model = request.form.get("bearing_model")
        description = request.form.get("description")

        # Check validity of users input
        if not name:
            flash("Machine name is required.", "error")
            return render_template("new_machine.html")

        # Try adding machine to database
        try:
            machine_id = add_machine(
                name=name,
                machine_type=machine_type,
                bearing_model=bearing_model,
                description=description
            )
        except sqlite3.IntegrityError:
            flash("A machine with that name already exists.", "error")
            return render_template("new_machine.html")

        # Success feedback and redirect to the new machine detail page
        flash("Machine created successfully.", "success")
        return redirect(url_for("machine_detail", machine_id=machine_id))
    
    # Initial page load
    else:
        return render_template("new_machine.html")


@app.route("/machine/<int:machine_id>/analysis/new", methods=["GET", "POST"])
def new_analysis(machine_id):
    """Upload a new vibration analysis."""

    machine = get_machine_by_id(machine_id)
    if machine is None:
        abort(404)

    if request.method == "POST":
        # Check if file exists and file format is .mat
        uploaded_file = request.files.get("file")
        if uploaded_file is None or uploaded_file.filename == "":
            flash("Select a MATLAB file.", "error")
            return redirect(request.url)

        filename = secure_filename(uploaded_file.filename)
        if not filename.lower().endswith(".mat"):
            flash("Only .mat files are supported.", "error")
            return redirect(request.url)

        # Check validity of users input
        try:
            sampling_rate = int(request.form["sampling_rate"])
            window_duration = float(request.form["window_duration"])
            rpm_text = request.form.get("rpm", "").strip()
            rpm_override = float(rpm_text) if rpm_text else None
        except ValueError:
            flash("Sampling rate, window duration and RPM must contain valid numbers.", "error")
            return redirect(request.url)

        # Process file in temporary directory to store info only instead of .mat files
        try:
            with TemporaryDirectory() as temp_dir:
                temporary_path = Path(temp_dir) / filename
                uploaded_file.save(temporary_path)

                result = analyze_recording(
                    file_path=temporary_path,
                    machine_id=machine_id,
                    sampling_rate=sampling_rate,
                    window_duration=window_duration,
                    rpm_override=rpm_override,
                    source_filename=filename
                )
        except (ValueError, KeyError, FileNotFoundError) as error:
            flash(str(error), "error")
            return redirect(request.url)

        # Success feedback and redirect to the new machine detail page
        flash(f"Analysis completed. {result['window_count']} windows were processed.", "success")
        return redirect(url_for("machine_detail", machine_id=machine_id))

    # Initial page load
    else:
        return render_template("new_analysis.html", machine=machine)


@app.route("/machine/<int:machine_id>/baseline", methods=["GET", "POST"])
def machine_baseline(machine_id):
    machine = get_machine_by_id(machine_id)
    if machine is None:
        abort(404)

    if request.method == "POST":
        # Check if file exists and file format is .mat
        uploaded_file = request.files.get("file")
        if uploaded_file is None or uploaded_file.filename == "":
            flash("Select a healthy baseline file.", "error")
            return redirect(request.url)

        filename = secure_filename(uploaded_file.filename)
        if not filename.lower().endswith(".mat"):
            flash("Only .mat files are supported.", "error")
            return redirect(request.url)

        # Check validity of users input
        try:
            sampling_rate = int(request.form["sampling_rate"])
            window_duration = float(request.form["window_duration"])
            rpm_text = request.form.get("rpm", "").strip()
            rpm_override = float(rpm_text) if rpm_text else None
        except ValueError:
            flash("Sampling rate, window duration and RPM must contain valid numbers.", "error")
            return redirect(request.url)

        # Build baseline in temporary directory to store baseline only instead of .mat files
        try:
            with TemporaryDirectory() as temp_dir:
                temporary_path = Path(temp_dir) / filename
                uploaded_file.save(temporary_path)

                build_machine_baseline(
                    file_path=temporary_path,
                    machine_id=machine_id,
                    sampling_rate=sampling_rate,
                    window_duration=window_duration,
                    rpm_override=rpm_override,
                    source_filename=filename
                )
        except (ValueError, KeyError, FileNotFoundError) as error:
            flash(str(error), "error")
            return redirect(request.url)

        # Success feedback and refresh page
        flash(f"Healthy baseline rebuilt.", "success")
        return redirect(request.url)

    # Initial page load
    else:
        baseline = load_machine_baseline(machine_id)
        return render_template("baseline.html", machine=machine, baseline=baseline)


if __name__ == "__main__":
    initialize_database()

    app.run(debug=True)
