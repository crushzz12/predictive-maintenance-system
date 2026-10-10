from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def format_number(value, decimals=3):
    """Format a number to fixed decimal places, returns - if missing or invalid."""

    if value is None:
        return "-"

    return f"{value:.{decimals}f}"


def generate_analysis_report(analysis, assessment):
    """Generate a downloadable PDF report for a machine analysis run."""

    buffer = BytesIO()

    # A4 with 18mm margins
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title and Header
    story.append(Paragraph("Predictive Maintenance Analysis Report", styles["Title"]))
    story.append(Spacer(1, 8 * mm))

    # Summary table
    generated_at = datetime.now().strftime("%d %b %Y %H:%M")
    if assessment["bearing"]["has_strong_evidence"]:
        bearing_evidence = assessment["bearing"]["strongest_label"]
    else:
        bearing_evidence = "No strong bearing-frequenct evidence"
    summary_data = [
        ["Machine", analysis["machine_name"]],
        ["Analysis", f"#{analysis['analysis_id']}"],
        ["Generated", generated_at],
        ["Status", assessment["health"]["status"]],
        ["General condition", assessment["health"]["fault_indicator"]],
        ["Bearing evidence", bearing_evidence]
    ]
    summary_table = Table(summary_data, colWidths=[45 * mm, 115 * mm])
    summary_table_style = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6)
    ])
    summary_table.setStyle(summary_table_style)
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    # Measurement data
    story.append(Paragraph("Measurement", styles["Heading2"]))
    measurement_data = [
        ["Source file", analysis["source_file"] or "-"],
        ["RPM", format_number(analysis["rpm"], decimals=0)],
        ["Sampling rate", f"{analysis['sampling_rate_hz']} Hz"],
        ["Window start", f"{analysis['window_start_s']} s"],
        ["Window duration", f"{analysis['window_duration_s']} s"]
    ]
    measurement_table = Table(measurement_data, colWidths=[50 * mm, 110 * mm])
    measurement_table.setStyle(summary_table_style)
    story.append(measurement_table)
    story.append(Spacer(1, 8 * mm))

    # Signal Features
    story.append(Paragraph("Signal Features", styles["Heading2"]))
    feature_data = [
        ["Feature", "Value"],
        ["RMS", format_number(analysis["rms"], decimals=4)],
        ["Kurtosis", format_number(analysis["kurtosis"], decimals=2)],
        ["Crest factor", format_number(analysis["crest_factor"], decimals=2)],
        ["1x amplitude", format_number(analysis["amp_1x"], decimals=5)],
        ["2x amplitude", format_number(analysis["amp_2x"], decimals=5)],
        ["3x amplitude", format_number(analysis["amp_3x"], decimals=5)]
    ]
    feature_table = Table(feature_data, colWidths=[80 * mm, 80 * mm])
    feature_table_style = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("PADDING", (0, 0), (-1, -1), 6)
    ])
    feature_table.setStyle(feature_table_style)
    story.append(feature_table)
    story.append(Spacer(1, 8 * mm))

    # Bearing Evidence
    story.append(Paragraph("Bearing Evidence", styles["Heading2"]))
    z_scores = assessment["bearing"]["z_scores"]
    bearing_data = [
        ["Envelope Feature", "Z-score"],
        ["Outer race (BPFO)", format_number(z_scores.get("env_bpfo_amp"), decimals=2)],
        ["Inner race (BPFI)", format_number(z_scores.get("env_bpfi_amp"), decimals=2)],
        ["Rolling element", format_number(z_scores.get("env_rolling_amp"), decimals=2)]
    ]
    bearing_table = Table(bearing_data, colWidths=[100 * mm, 60 * mm])
    bearing_table.setStyle(feature_table_style)
    story.append(bearing_table)
    story.append(Spacer(1, 10 * mm))

    # Engineering Disclaimer
    disclaimer_text = (
        "Alert status indicate statistical deviation from the configured healthy baseline " 
        "and do not represent certified mechanical safety limits."
    )
    story.append(Paragraph(disclaimer_text, styles["BodyText"]))

    # Render document to memory buffer
    document.build(story)
    buffer.seek(0)

    return buffer
    