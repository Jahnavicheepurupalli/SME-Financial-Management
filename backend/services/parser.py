import os
import csv
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

class DocumentParser:
    @staticmethod
    def parse_pdf(file_path):
        """Extracts text and tables from PDF page-by-page."""
        chunks = []
        filename = os.path.basename(file_path)
        
        try:
            # First try PyMuPDF for quick text extraction
            doc = fitz.open(file_path)
            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                text = page.get_text()
                if text.strip():
                    chunks.append({
                        "text": text,
                        "page_num": page_num,
                        "source_doc": filename,
                        "type": "text"
                    })
            doc.close()
        except Exception as e:
            print(f"PyMuPDF error: {e}")

        # If no text extracted, or to capture structured tables, use pdfplumber
        if not chunks:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page_idx, page in enumerate(pdf.pages):
                        page_num = page_idx + 1
                        text = page.extract_text()
                        if text and text.strip():
                            chunks.append({
                                "text": text,
                                "page_num": page_num,
                                "source_doc": filename,
                                "type": "text"
                            })
                            
                        # Extract tables
                        tables = page.extract_tables()
                        for table in tables:
                            table_str = DocumentParser._format_table(table)
                            if table_str:
                                chunks.append({
                                    "text": table_str,
                                    "page_num": page_num,
                                    "source_doc": filename,
                                    "type": "table"
                                })
            except Exception as e:
                print(f"pdfplumber error: {e}")
                
        # If still empty, it might be a scanned PDF. Let's try OCR.
        if not chunks:
            chunks = DocumentParser.ocr_pdf(file_path)

        return chunks

    @staticmethod
    def ocr_pdf(file_path):
        """Performs OCR on pages of scanned PDFs."""
        chunks = []
        filename = os.path.basename(file_path)
        try:
            doc = fitz.open(file_path)
            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                pix = page.get_pixmap()
                img_data = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                try:
                    text = pytesseract.image_to_string(img_data)
                except Exception as t_err:
                    print(f"Tesseract not configured or missing: {t_err}. Mocking text from scan.")
                    text = f"[Scanned Page {page_num}] Unable to run full OCR because Tesseract binary is not installed on system."
                
                if text.strip():
                    chunks.append({
                        "text": text,
                        "page_num": page_num,
                        "source_doc": filename,
                        "type": "ocr_text"
                    })
            doc.close()
        except Exception as e:
            print(f"OCR PDF error: {e}")
        return chunks

    @staticmethod
    def parse_image(file_path):
        """OCR for images (PNG, JPG)."""
        filename = os.path.basename(file_path)
        try:
            img = Image.open(file_path)
            try:
                text = pytesseract.image_to_string(img)
            except Exception as t_err:
                print(f"Tesseract missing: {t_err}")
                text = f"[Scanned Image] Tesseract OCR not available to parse {filename}."
                
            return [{
                "text": text,
                "page_num": 1,
                "source_doc": filename,
                "type": "ocr_text"
            }]
        except Exception as e:
            print(f"Parse Image error: {e}")
            return []

    @staticmethod
    def parse_csv(file_path):
        """Converts CSV to rows of text for chunking using pandas."""
        chunks = []
        filename = os.path.basename(file_path)
        try:
            df = pd.read_csv(file_path)
            # Limit to top 500 rows to optimize processing and avoid token/timeout limits
            if len(df) > 500:
                df = df.head(500)
                
            cols = df.columns.tolist()
            rows = df.values.tolist()
            
            # Chunk rows in batches of 50 rows to avoid blowing token limit
            batch_size = 50
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i+batch_size]
                table_repr = [cols] + batch
                table_str = DocumentParser._format_table(table_repr)
                chunks.append({
                    "text": f"Financial CSV Dataset Chunk (Rows {i+1} to {i+len(batch)}):\n{table_str}",
                    "page_num": 1,
                    "source_doc": filename,
                    "type": "csv_data"
                })
        except Exception as e:
            print(f"CSV Parse error: {e}")
        return chunks

    @staticmethod
    def parse_excel(file_path):
        """Converts Excel sheets to chunked tables."""
        chunks = []
        filename = os.path.basename(file_path)
        try:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                # Convert dataframe to table style representation
                table_list = [df.columns.tolist()] + df.values.tolist()
                
                batch_size = 50
                for i in range(0, len(table_list), batch_size):
                    batch = table_list[i:i+batch_size]
                    table_str = DocumentParser._format_table(batch)
                    chunks.append({
                        "text": f"Excel Sheet: {sheet_name} Chunk (Rows {i+1} to {i+len(batch)}):\n{table_str}",
                        "page_num": 1,
                        "source_doc": filename,
                        "type": "excel_data"
                    })
        except Exception as e:
            print(f"Excel Parse error: {e}")
        return chunks

    @staticmethod
    def _format_table(table):
        if not table:
            return ""
        lines = []
        for row in table:
            # Clean and stringify each cell
            clean_row = [str(cell).strip() if cell is not None else "" for cell in row]
            lines.append(" | ".join(clean_row))
        return "\n".join(lines)
