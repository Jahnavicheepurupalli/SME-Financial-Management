import csv
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

from backend.exceptions import DocumentParseError
from backend.services.parser import DocumentParser


def test_format_table():
    assert DocumentParser._format_table([]) == ""
    assert DocumentParser._format_table([[None, "  value ", 3]]) == " | value | 3"
    assert DocumentParser._format_table([["a", "b"], ["c", None]]) == "a | b\nc | "


def test_parse_csv_batches_and_limits(tmp_path):
    path = tmp_path / "data.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "amount", "type"])
        writer.writerows([[f"2024-01-{(i % 28) + 1:02}", i, "credit"] for i in range(600)])
    chunks = DocumentParser.parse_csv(str(path))
    assert len(chunks) == 10
    assert chunks[0]["type"] == "csv_data"
    assert "date | amount | type" in chunks[0]["text"]
    assert "Rows 1 to 50" in chunks[0]["text"]
    assert "Rows 451 to 500" in chunks[-1]["text"]
    assert all(c["source_doc"] == "data.csv" and c["page_num"] == 1 for c in chunks)
    with pytest.raises(DocumentParseError):
        DocumentParser.parse_csv(str(tmp_path / "missing.csv"))


def test_parse_excel_multisheet_and_broken(tmp_path):
    path = tmp_path / "book.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"revenue": [1, 2]}).to_excel(writer, sheet_name="Income", index=False)
        pd.DataFrame({"assets": [3]}).to_excel(writer, sheet_name="Balance", index=False)
    chunks = DocumentParser.parse_excel(str(path))
    assert len(chunks) == 2
    assert {c["type"] for c in chunks} == {"excel_data"}
    assert "Excel Sheet: Income" in chunks[0]["text"]
    assert "Excel Sheet: Balance" in chunks[1]["text"]
    broken = tmp_path / "broken.xlsx"
    broken.write_text("not excel")
    with pytest.raises(DocumentParseError):
        DocumentParser.parse_excel(str(broken))


def test_parse_pdf_fallbacks(monkeypatch, tmp_path):
    class Page:
        def __init__(self, text="", tables=None):
            self._text, self._tables = text, tables or []
        def get_text(self):
            return self._text
        def extract_text(self):
            return self._text
        def extract_tables(self):
            return self._tables

    class Doc:
        def __init__(self, pages):
            self.pages = pages
        def __iter__(self):
            return iter(self.pages)
        def __len__(self):
            return len(self.pages)
        def __getitem__(self, i):
            return self.pages[i]
        def close(self):
            pass

    class Fit:
        @staticmethod
        def open(_):
            raise RuntimeError("bad pdf")
    class Pdf:
        @staticmethod
        def open(_):
            class Ctx:
                def __enter__(self):
                    return Doc([Page("profit 20", [["a", "b"], ["1", "2"]])])
                def __exit__(self, *args):
                    pass
                pages = [Page("profit 20", [["a", "b"], ["1", "2"]])]
            return Ctx()
    monkeypatch.setattr("backend.services.parser.fitz", Fit)
    monkeypatch.setattr("backend.services.parser.pdfplumber", Pdf)
    assert len(DocumentParser.parse_pdf(str(tmp_path / "a.pdf"))) == 3

    class EmptyPdf:
        @staticmethod
        def open(_):
            class Ctx:
                pages = [Page("")]
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return Ctx()
    monkeypatch.setattr("backend.services.parser.pdfplumber", EmptyPdf)
    monkeypatch.setattr(DocumentParser, "ocr_pdf", lambda _: [{"type": "ocr_text"}])
    assert DocumentParser.parse_pdf(str(tmp_path / "scan.pdf")) == [{"type": "ocr_text"}]


def test_ocr_pdf_and_image_paths(monkeypatch, tmp_path):
    class Pix:
        width, height, samples = 1, 1, b"\x00\x00\x00"
        def get_pixmap(self): return self
    class Doc:
        def __iter__(self): return iter([Pix()])
        def __len__(self): return 1
        def close(self): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr("backend.services.parser.fitz", type("Fit", (), {"open": staticmethod(lambda _: Doc())}))
    monkeypatch.setattr("backend.services.parser.pytesseract", type("T", (), {"image_to_string": staticmethod(lambda _: "OCR text")}))
    assert DocumentParser.ocr_pdf("scan.pdf")[0]["text"] == "OCR text"
    monkeypatch.setattr("backend.services.parser.pytesseract", type("T", (), {"image_to_string": staticmethod(lambda _: (_ for _ in ()).throw(RuntimeError("missing")))}))
    with pytest.raises(DocumentParseError):
        DocumentParser.ocr_pdf("scan.pdf")

    image_path = tmp_path / "image.png"
    Image.new("RGB", (2, 2), "white").save(image_path)
    monkeypatch.setattr("backend.services.parser.pytesseract", type("T", (), {"image_to_string": staticmethod(lambda _: "image text")}))
    assert DocumentParser.parse_image(str(image_path))[0]["text"] == "image text"
    with pytest.raises(DocumentParseError):
        DocumentParser.parse_image(str(tmp_path / "no.png"))
