"""Report endpoints: JSON report and PDF download."""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..services.report_service import build_report, generate_pdf
from ..utils.logger import logger
from ..utils.response import error_response, success_response

router = APIRouter(tags=["reports"])


@router.get("/api/report/{zone_id}")
def report(zone_id: str):
    """Return a structured JSON report for the given zone."""
    try:
        data = build_report(zone_id)
        if not data:
            return error_response(
                f"No report available: zone '{zone_id}' not found",
                fallback_used=False,
            )
        return success_response(data, "Report generated successfully")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Report generation failed for %s: %s", zone_id, exc)
        return error_response(
            f"Could not generate report for '{zone_id}'",
            fallback_used=True,
        )


@router.get("/api/report/{zone_id}/download")
def download_report(zone_id: str):
    """Generate and return a PDF report for the given zone."""
    try:
        path = generate_pdf(zone_id)
        if not path or not path.exists():
            return error_response(
                f"Could not generate PDF for zone '{zone_id}'",
                fallback_used=False,
            )
        return FileResponse(
            path=str(path),
            media_type="application/pdf",
            filename=path.name,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("PDF download failed for %s: %s", zone_id, exc)
        return error_response(
            f"Could not download PDF report for '{zone_id}'",
            fallback_used=True,
        )
