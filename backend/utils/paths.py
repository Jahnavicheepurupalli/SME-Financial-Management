import os

from backend.config import Config


def report_path(document_id):
    """Absolute path of the generated PDF report for a document."""
    return os.path.join(Config.REPORTS_FOLDER, f"report_{document_id}.pdf")
