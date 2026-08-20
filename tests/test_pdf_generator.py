import pdfplumber

from backend.services.pdf_generator import PDFReportGenerator


def _full_analysis():
    return {
        "metrics": {
            "total_revenue": 1250000,
            "total_expense": 850000,
            "gross_profit": 562500,
            "net_profit": 400000,
            "profit_margin": 32,
            "operating_margin": 27,
            "current_ratio": 1.8,
            "quick_ratio": 1.4,
            "debt_ratio": 0.35,
            "cash_flow": 390000,
            "avg_monthly_revenue": 104166.67,
            "avg_monthly_expense": 70833.33,
        },
        "current_state_analysis": {
            "revenue_trend": "Revenue is growing steadily.",
            "expense_trend": "Operating costs remain controlled.",
            "net_profit": "Profit remains positive.",
            "operating_margin": "Margins support sustainable operations.",
            "cash_flow": "Cash generation is healthy.",
            "liquidity": "Liquidity covers near-term obligations.",
            "assets": "Assets support expansion.",
            "liabilities": "Liabilities are manageable.",
            "equity": "Equity is strengthening.",
            "debt_ratio": "Leverage remains moderate.",
            "current_ratio": "Working capital is adequate.",
            "profitability": "The business is profitable.",
            "financial_health": "Overall health is stable.",
            "source": {"document": "financial_statement.csv", "page": "1-3"},
        },
        "gap_detection": [
            {
                "problem": "Receivables concentration",
                "impact": "Delayed collections may reduce liquidity.",
                "recommendation": "Review customer payment terms.",
            }
        ],
        "missing_data_detection": [
            {
                "missing_data": "Audited balance sheet",
                "importance": "High",
                "recommendation": "Upload the latest audited statement.",
            }
        ],
        "forward_looking_flags": [
            {
                "flag": "Working capital opportunity",
                "reason": "Stable margins support measured growth.",
                "risk_level": "Low",
                "growth_score": 80,
                "confidence_score": 90,
            }
        ],
    }


def test_generate_full_analysis_pdf_and_cover_text(tmp_path):
    output = tmp_path / "full-report.pdf"
    PDFReportGenerator.generate(str(output), "financial_statement.csv", _full_analysis())
    assert output.exists()
    assert output.stat().st_size > 2000
    assert output.read_bytes().startswith(b"%PDF")
    with pdfplumber.open(output) as pdf:
        cover_text = pdf.pages[0].extract_text() or ""
    assert "financial_statement.csv" in cover_text


def test_generate_pdf_with_empty_collections(tmp_path):
    output = tmp_path / "empty-report.pdf"
    PDFReportGenerator.generate(
        str(output),
        "empty.csv",
        {
            "metrics": {},
            "current_state_analysis": {},
            "gap_detection": [],
            "missing_data_detection": [],
            "forward_looking_flags": [],
        },
    )
    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 1000


def test_generate_pdf_handles_non_numeric_and_partial_values(tmp_path):
    output = tmp_path / "partial-report.pdf"
    PDFReportGenerator.generate(
        str(output),
        "partial.csv",
        {
            "metrics": {"total_revenue": "N/A", "net_profit": "unknown"},
            "current_state_analysis": {"source": {"document": "partial.csv"}},
            "gap_detection": [{}],
            "missing_data_detection": [{}],
            "forward_looking_flags": [{}],
        },
    )
    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")
