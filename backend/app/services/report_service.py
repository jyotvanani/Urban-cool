"""Report generation service: structured JSON report and PDF export."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import settings
from ..models.ml_model import feature_contributions
from ..utils.logger import logger
from ..utils.validators import priority_from_category
from .data_service import get_hotspot_by_id


def build_report(zone_id: str) -> Optional[dict]:
    """Build a structured report dict for a zone, or None if not found."""
    zone = get_hotspot_by_id(zone_id)
    if not zone:
        return None

    category = zone.get("hotspot_category", "Moderate")
    contributions = feature_contributions(zone)

    implementation_steps = _implementation_suggestions(zone, category)

    return {
        "zone_summary": {
            "zone_id": zone.get("zone_id"),
            "zone_name": zone.get("zone_name"),
            "city": zone.get("city"),
            "latitude": zone.get("latitude"),
            "longitude": zone.get("longitude"),
        },
        "heat_condition": {
            "heat_risk_score": zone.get("heat_risk_score"),
            "hotspot_category": category,
            "lst_temperature": zone.get("lst_temperature"),
            "air_temperature": zone.get("air_temperature"),
            "humidity": zone.get("humidity"),
            "wind_speed": zone.get("wind_speed"),
        },
        "main_causes": zone.get("main_drivers", []),
        "feature_contribution_percentages": contributions,
        "recommended_actions": zone.get("recommended_action"),
        "expected_temperature_reduction": zone.get("expected_temp_reduction"),
        "priority_level": zone.get("priority_level", priority_from_category(category)),
        "implementation_suggestions": implementation_steps,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def _implementation_suggestions(zone: dict, category: str) -> list:
    """Return a list of concrete implementation suggestions."""
    steps = []
    ndvi = float(zone.get("ndvi", 0.3) or 0.3)
    ndbi = float(zone.get("ndbi", 0.5) or 0.5)
    built = float(zone.get("built_up_density", 0.5) or 0.5)
    water_dist = float(zone.get("water_body_distance_km", 2) or 2)

    if ndvi < 0.25:
        steps.append("Plant native shade trees along streets and in open plots.")
    if ndbi > 0.6 and built > 0.7:
        steps.append("Roll out cool-roof coatings on public and commercial buildings.")
        steps.append("Replace dark pavements with high-albedo / reflective materials.")
    if water_dist > 3:
        steps.append("Create a blue-green corridor linking the zone to nearby water bodies.")
    if category in ("Severe", "High"):
        steps.append("Prioritize funding and run a 12-month monitoring program.")
    if not steps:
        steps.append("Maintain existing green cover and monitor heat trends seasonally.")
    return steps


def generate_pdf(zone_id: str) -> Optional[Path]:
    """Generate a PDF report for the zone and return its file path.

    Returns None if the zone cannot be found.
    """
    report = build_report(zone_id)
    if not report:
        return None

    summary = report["zone_summary"]
    heat = report["heat_condition"]

    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = settings.REPORTS_DIR / f"report_{zone_id}.pdf"

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(20, 90, 140)
        pdf.cell(0, 12, "UrbanCool AI", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, "Urban Heat Mitigation Report", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        pdf.set_draw_color(20, 90, 140)
        pdf.set_line_width(0.6)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        def field(label: str, value: str) -> None:
            # Label on its own line (bold), value wrapped below it. Using full
            # width multi_cell avoids horizontal-space rendering errors.
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(0, 7, f"{label}:")
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 7, str(value))
            pdf.ln(1)

        field("Zone Name", f"{summary.get('zone_name')} ({summary.get('city')})")
        field("Current Heat Score", f"{heat.get('heat_risk_score')} / 100 ({heat.get('hotspot_category')})")
        field("LST Temperature", f"{heat.get('lst_temperature')} C")
        field("Air Temperature", f"{heat.get('air_temperature')} C")
        field("Main Heat Drivers", ", ".join(report.get("main_causes", [])) or "N/A")
        field("Recommended Cooling Strategy", report.get("recommended_actions") or "N/A")
        field("Expected Temp Reduction", f"{report.get('expected_temperature_reduction')} C")
        field("Priority Level", report.get("priority_level"))

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(20, 90, 140)
        pdf.cell(0, 8, "Implementation Suggestions", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(60, 60, 60)
        for step in report.get("implementation_suggestions", []):
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, f"- {step}")

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(20, 90, 140)
        pdf.cell(0, 8, "Conclusion", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(60, 60, 60)
        conclusion = (
            f"{summary.get('zone_name')} is classified as a "
            f"{heat.get('hotspot_category')} heat zone. Implementing the recommended "
            f"cooling strategy is expected to reduce surface temperature by about "
            f"{report.get('expected_temperature_reduction')} C, improving thermal "
            f"comfort and resilience for residents."
        )
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, conclusion)

        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(140, 140, 140)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 6, f"Generated by UrbanCool AI on {report.get('generated_at')}",
                 new_x="LMARGIN", new_y="NEXT")

        pdf.output(str(output_path))
        logger.info("Generated PDF report at %s", output_path)
        return output_path
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("PDF generation failed: %s", exc)
        return None
