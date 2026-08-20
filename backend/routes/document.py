import os
import logging
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from backend.config import Config
from backend.database.db import SessionLocal, session_scope, mongo_db
from backend.models.models import Document, AnalysisHistory
from backend.services.parser import DocumentParser
from backend.services.vector_store import VectorStoreManager
from backend.agents.agent import FinancialIntelligenceAgent
from backend.exceptions import AnalysisStorageError, DocumentParseError
from backend.utils.paths import report_path
from backend.utils.responses import error_response, internal_error, success_response
from backend.utils.serializers import serialize_document, serialize_history_entry
logger = logging.getLogger(__name__)

doc_bp = Blueprint('document', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'csv', 'xlsx', 'xls'}

NON_FINANCIAL_MESSAGE = (
    "This platform only accepts financial documents such as invoices, bank statements, "
    "balance sheets, profit and loss statements, cash flow reports, and other business "
    "financial records."
)


def get_owned_document(db, doc_id, user_id):
    return db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == int(user_id)
    ).first()


def _remove_file(file_path):
    if not os.path.exists(file_path):
        return
    try:
        os.remove(file_path)
    except OSError:
        logger.warning("Unable to remove file %s.", file_path, exc_info=True)


def _mark_document_failed(document_id):
    try:
        with session_scope(SessionLocal) as failed_db:
            failed_doc = failed_db.query(Document).filter(Document.id == document_id).first()
            if failed_doc:
                failed_doc.status = "failed"
                failed_db.commit()
    except Exception:
        logger.exception("Unable to mark document %s as failed.", document_id)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_is_financial_file(file_path, file_type):
    """Classifies uploaded document content to ensure it is a valid financial document."""
    text = ""
    try:
        if file_type == "PDF":
            import fitz
            doc = fitz.open(file_path)
            pages_to_read = min(len(doc), 5)
            extracted = []
            for i in range(pages_to_read):
                t = doc[i].get_text()
                if t:
                    extracted.append(t)
            doc.close()
            text = "\n".join(extracted)
        elif file_type == "CSV":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline() for _ in range(40)]
                text = "\n".join(lines)
        elif file_type == "Excel":
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            sheets = wb.sheetnames
            if sheets:
                ws = wb[sheets[0]]
                rows = []
                for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                    if r_idx > 25:
                        break
                    rows.append(" ".join([str(val) for val in row if val is not None]))
                text = "\n".join(rows)
            wb.close()
    except Exception as e:
        logger.exception("Unable to inspect uploaded file %s during validation.", file_path)
        raise DocumentParseError(
            f"Unable to read uploaded {file_type.lower()} file: {e}",
            user_message=(
                f"The uploaded {file_type.lower()} file could not be read; it may be corrupt or unreadable."
            )
        ) from e

    if not text or not text.strip():
        return False

    text_lower = text.lower()

    # Explicit Non-Financial / Resume / Academic / Certificate indicators
    non_financial_keywords = [
        "curriculum vitae", "resume", "work experience", "education", "hobbies",
        "objective", "academic background", "personal details", "declaration",
        "skills & abilities", "technical skills", "projects undertaken", "certificate of",
        "certifies that", "degree of", "university", "bachelor of", "master of", "diploma in",
        "schooling", "gpa", "cgpa", "semester", "personal profile", "employment history",
        "job summary", "passed the examination", "coursework", "references available",
        "cover letter", "dear sir/madam", "application for", "hall ticket", "admit card"
    ]

    non_fin_matches = [kw for kw in non_financial_keywords if kw in text_lower]

    # Explicit Financial Document keywords & structure indicators
    financial_keywords = [
        "revenue", "expense", "profit", "loss", "income", "balance sheet", "assets", "liabilities", "equity",
        "cash flow", "financial statement", "transaction", "gst", "invoice", "payroll", "ledger", "account",
        "cogs", "sales", "ebitda", "capital", "retained earning", "tax", "audit", "credit", "debit", "deposit", 
        "withdrawal", "price", "amount", "cost", "margin", "liquidity", "debt", "quick ratio", "current ratio",
        "bank statement", "account statement", "opening balance", "closing balance", "subtotal", "bill to",
        "invoice date", "tax invoice", "statement period", "net profit", "gross profit", "operating cash flow"
    ]

    fin_matches = [kw for kw in financial_keywords if kw in text_lower]

    # If document has resume/academic/certificate indicators and weak financial context, reject
    if len(non_fin_matches) >= 2 or (len(non_fin_matches) >= 1 and len(fin_matches) < 3):
        logger.info("Rejected non-financial document with validation indicators: %s", non_fin_matches)
        return False

    # Require at least 2 distinct financial keywords
    if len(fin_matches) < 2:
        logger.info("Rejected document with insufficient financial keywords: %s", fin_matches)
        return False

    return True

@doc_bp.route('/upload', methods=['POST'])
@doc_bp.route('/document/upload', methods=['POST'])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return error_response("No file part in the request")

    file = request.files['file']
    if file.filename == '':
        return error_response("No selected file")

    if not allowed_file(file.filename):
        return error_response(NON_FINANCIAL_MESSAGE)

    # Ensure upload folder exists
    try:
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    except OSError:
        logger.exception("Unable to prepare upload folder %s.", Config.UPLOAD_FOLDER)
        return error_response("Unable to prepare storage for the uploaded file. Please try again.", 500)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    try:
        file.save(file_path)
        file_size = os.path.getsize(file_path)
    except Exception:
        logger.exception("Unable to save or inspect uploaded file %s.", filename)
        _remove_file(file_path)
        return error_response("Unable to save the uploaded file. Please try again.", 500)

    # Validate file size
    if file_size > 10 * 1024 * 1024:  # 10 MB limit
        _remove_file(file_path)
        return error_response("File exceeds the 10MB size limit.")

    # Determine file type category
    ext = filename.rsplit('.', 1)[1].lower()
    file_type = "PDF"
    if ext == 'csv':
        file_type = "CSV"
    elif ext in ['xlsx', 'xls']:
        file_type = "Excel"

    # content-based validation check before parser/db record/embeddings/analysis
    try:
        is_financial_file = check_is_financial_file(file_path, file_type)
    except DocumentParseError as e:
        logger.warning("Uploaded file failed content validation: %s", e, exc_info=True)
        _remove_file(file_path)
        return error_response(e.user_message, 422)

    if not is_financial_file:
        _remove_file(file_path)
        return error_response(NON_FINANCIAL_MESSAGE)

    # Initialize MySQL DB session and create record since file is validated
    db = SessionLocal()
    doc_record = None
    try:
        doc_record = Document(
            user_id=int(user_id),
            filename=filename,
            file_path=file_path,
            status="processing",
            file_type=file_type
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        # 1. Document Parsing & Text Extraction
        parsers = {
            "PDF": DocumentParser.parse_pdf,
            "CSV": DocumentParser.parse_csv,
            "Excel": DocumentParser.parse_excel
        }
        parser = parsers.get(file_type)
        chunks = parser(file_path) if parser else []

        if not chunks:
            doc_record.status = "failed"
            db.commit()
            _remove_file(file_path)
            return error_response("Document contains no extractable data or is corrupted.")

        # 2. Chunking & Embeddings
        vstore = VectorStoreManager.get_instance()
        vstore.clear()  # Clear workspace cache
        vstore.add_chunks(chunks)

        # 3. LangChain Agent Execution
        agent = FinancialIntelligenceAgent()
        analysis_result = agent.run_analysis(doc_record.id)

        return success_response(
            current_state_analysis=analysis_result.get("current_state_analysis", {}),
            gap_detection=analysis_result.get("gap_detection", []),
            forward_looking_flags=analysis_result.get("forward_looking_flags", []),
            metrics=analysis_result.get("metrics", {}),
            charts=analysis_result.get("charts", {}),
            analysis_mode=analysis_result.get("analysis_mode", "llm"),
            degraded_reason=analysis_result.get("degraded_reason"),
            metrics_source=analysis_result.get("metrics_source"),
            data_quality=analysis_result.get("data_quality"),
            pdf_url=f"/api/report/{doc_record.id}",
            document=serialize_document(doc_record, status="analyzed")
        )

    except DocumentParseError as e:
        db.rollback()
        logger.warning("Document %s could not be parsed: %s", filename, e, exc_info=True)
        if doc_record:
            _mark_document_failed(doc_record.id)
        _remove_file(file_path)
        return error_response(e.user_message, 422)
    except AnalysisStorageError:
        db.rollback()
        logger.exception("Analysis for document %s could not be saved.", filename)
        if doc_record:
            _mark_document_failed(doc_record.id)
        return error_response("Analysis could not be saved. Please try again.", 500)
    except Exception:
        db.rollback()
        logger.exception("Unexpected error during upload/analysis processing for %s.", filename)
        if doc_record:
            _mark_document_failed(doc_record.id)
        _remove_file(file_path)
        return internal_error()
    finally:
        db.close()

@doc_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    try:
        with session_scope(SessionLocal) as db:
            docs = db.query(Document).filter(Document.user_id == int(user_id)).order_by(Document.created_at.desc()).all()
            return jsonify({"history": [serialize_history_entry(doc) for doc in docs]}), 200
    except Exception:
        logger.exception("Unexpected error while loading document history.")
        return internal_error()

@doc_bp.route('/history/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_history_detail(doc_id):
    user_id = get_jwt_identity()
    try:
        with session_scope(SessionLocal) as db:
            doc = get_owned_document(db, doc_id, user_id)
            if not doc:
                return error_response("Document not found", 404)

            result = mongo_db["analysis_results"].find_one({"document_id": doc_id})
            if not result:
                return error_response("Analysis details not found", 404)

            if '_id' in result:
                result['_id'] = str(result['_id'])

            return jsonify({"analysis": result, "filename": doc.filename}), 200
    except Exception:
        logger.exception("Unexpected error while loading analysis details for document %s.", doc_id)
        return internal_error()

@doc_bp.route('/report/<int:doc_id>', methods=['GET'])
@jwt_required()
def download_report(doc_id):
    user_id = get_jwt_identity()
    try:
        with session_scope(SessionLocal) as db:
            doc = get_owned_document(db, doc_id, user_id)
            if not doc:
                return error_response("Document not found", 404)

            pdf_path = report_path(doc_id)
            if not os.path.exists(pdf_path):
                return error_response("PDF report file not found on server.", 404)

            return send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"Financial_Analysis_{doc.filename}.pdf"
            )
    except Exception:
        logger.exception("Unexpected error while downloading report for document %s.", doc_id)
        return internal_error()

@doc_bp.route('/chat', methods=['POST'])
@doc_bp.route('/document/chat', methods=['POST'])
@jwt_required()
def chat_with_document():
    data = request.get_json()
    if not data or 'message' not in data or 'document_id' not in data:
        return error_response("Missing message or document_id")


    doc_id = data['document_id']
    message = data['message']
    history = data.get('history', [])
    user_id = get_jwt_identity()

    try:
        with session_scope(SessionLocal) as db:
            doc = get_owned_document(db, doc_id, user_id)
            if not doc:
                return error_response("Document not found or unauthorized", 404)

            agent = FinancialIntelligenceAgent()
            response_text = agent.run_chat_query(doc_id, message, history)

            return success_response(response=response_text)
    except Exception:
        logger.exception("Unexpected error while answering document chat request.")
        return internal_error()

@doc_bp.route('/document/delete/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id):
    user_id = get_jwt_identity()
    try:
        with session_scope(SessionLocal) as db:
            doc = get_owned_document(db, doc_id, user_id)
            if not doc:
                return error_response("Document not found or unauthorized", 404)

            filename = doc.filename
            file_path = doc.file_path
            pdf_path = report_path(doc_id)

            # 1. Delete database records in MySQL
            db.query(AnalysisHistory).filter(AnalysisHistory.document_id == doc_id).delete()
            db.delete(doc)
            db.commit()

            cleanup_failures = []

            # 2. Delete analysis from MongoDB
            try:
                mongo_db["analysis_results"].delete_one({"document_id": doc_id})
            except Exception:
                cleanup_failures.append("analysis record")
                logger.exception("Failed to delete MongoDB analysis for document %s.", doc_id)

            # 3. Delete physical files if they exist
            for path, label in ((file_path, "uploaded file"), (pdf_path, "PDF report")):
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        cleanup_failures.append(label)
                        logger.warning("Failed to delete %s %s.", label, path, exc_info=True)

            # 4. Remove document chunks from vector store
            try:
                vstore = VectorStoreManager.get_instance()
                vstore.remove_document_chunks(filename)
            except Exception:
                cleanup_failures.append("vector store chunks")
                logger.exception("Failed to remove vector-store chunks for document %s.", doc_id)

            return success_response(
                "Document deleted successfully"
                if not cleanup_failures
                else f"Document deleted from the database, but cleanup failed for: {', '.join(cleanup_failures)}."
            )
    except Exception:
        logger.exception("Unexpected error deleting document %s.", doc_id)
        return internal_error()
