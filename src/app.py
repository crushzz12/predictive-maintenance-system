from flask import Flask, render_template, abort

from predictive_maintenance.db import (
    initialize_database,
    get_all_machines,
    get_machine_by_id,
    get_analysis_history,
    get_analysis_by_id,
    get_maintenance_history
)

app = Flask(__name__)

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

    analyses = get_analysis_history(machine_id)

    return render_template("machine.html", machine=machine, analyses=analyses)


@app.route("/analysis/<int:analysis_id>")
def analysis_detail(analysis_id):
    """Show detailed analysis info including features and status."""

    analysis = get_analysis_by_id(analysis_id)
    if analysis is None:
        abort(404)

    return render_template("analysis.html", analysis=analysis)


@app.route("/machine/<int:machine_id>/maintenance")
def maintenance(machine_id):
    """Show maintenance history of the machine."""

    machine = get_machine_by_id(machine_id)
    if machine is None:
        abort(404)

    records = get_maintenance_history(machine_id)

    return render_template("maintenance.html", machine=machine, records=records)


if __name__ == "__main__":
    initialize_database()

    app.run(debug=True)
