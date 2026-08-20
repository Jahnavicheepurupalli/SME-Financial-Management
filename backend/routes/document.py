import os
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from backend.config import Config
from backend.database.db import session_scope, mongo_db
from backend.models.models import Document, AnalysisHistory
from backend.services.parser import DocumentParser
from backend.services.vector_store import VectorStoreManager
from backend.agents.agent import FinancialIntelligenceAgent
from backend.utils.paths import report_path
from backend.utils.responses import error_response, success_response
from backend.utils.serializers import serialize_document, serialize_history_entry

doc_bp = Blueprint('document', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'csv', 'xlsx', 'xls'}

NON_FINANCIAL_MESSAGE = (
    "This platform only accepts financial documents such as invoices, bank statements, "
    "balance sheets, profit and loss statements, cash flow reports, and other business "
    "financial records."
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_owned_document(db, doc_id, user_id):
    """Fetches a document only if it belongs to the authenticated user."""
    return db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == int(user_id)
    ).first()

def remove_file_quietly(path, context):
    if not path or not os.path.exists(path):
        return
    try:
        os.remove(path)
    except Exception as e:
        print(f"[DEBUG {context}] Failed to delete {path}: {e}")

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
        print(f"[DEBUG VALIDATION] Fast validation extraction error: {e}")
        return False

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
        print(f"[VALIDATION] Rejected non-financial document. Non-financial keywords found: {non_fin_matches}")
        return False

    # Require at least 2 distinct financial keywords
    if len(fin_matches) < 2:
        print(f"[VALIDATION] Rejected document. Insufficient financial keywords found: {fin_matches}")
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
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(file_path)
    file_size = os.path.getsize(file_path)

    # Validate file size
    if file_size > 10 * 1024 * 1024:  # 10 MB limit
        os.remove(file_path)
        return error_response("File exceeds the 10MB size limit.")

    # Determine file type category
    ext = filename.rsplit('.', 1)[1].lower()
    file_type = "PDF"
    if ext == 'csv':
        file_type = "CSV"
    elif ext in ['xlsx', 'xls']:
        file_type = "Excel"

    # content-based validation check before parser/db record/embeddings/analysis
    if not check_is_financial_file(file_path, file_type):
        remove_file_quietly(file_path, "VALIDATION")
        return error_response(NON_FINANCIAL_MESSAGE)

    # Initialize MySQL DB session and create record since file is validated
    try:
        with session_scope() as db:
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
            chunks = parsers[file_type](file_path) if file_type in parsers else []

            if not chunks:
                doc_record.status = "failed"
                db.commit()
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
                pdf_url=f"/api/report/{doc_record.id}",
                document=serialize_document(doc_record, status="analyzed")
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f"An error occurred during upload/analysis processing: {str(e)}", 500)

@doc_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    with session_scope() as db:
        docs = db.query(Document).filter(Document.user_id == int(user_id)).order_by(Document.created_at.desc()).all()
        return jsonify({"history": [serialize_history_entry(doc) for doc in docs]}), 200

@doc_bp.route('/history/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_history_detail(doc_id):
    user_id = get_jwt_identity()
    with session_scope() as db:
        doc = get_owned_document(db, doc_id, user_id)
        if not doc:
            return error_response("Document not found", 404)
            
        result = mongo_db["analysis_results"].find_one({"document_id": doc_id})
        if not result:
            return error_response("Analysis details not found", 404)
            
        if '_id' in result:
            result['_id'] = str(result['_id'])
            
        return jsonify({"analysis": result, "filename": doc.filename}), 200

@doc_bp.route('/report/<int:doc_id>', methods=['GET'])
@jwt_required()
def download_report(doc_id):
    user_id = get_jwt_identity()
    with session_scope() as db:
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
        with session_scope() as db:
            doc = get_owned_document(db, doc_id, user_id)
            if not doc:
                return error_response("Document not found or unauthorized", 404)
                
            agent = FinancialIntelligenceAgent()
            response_text = agent.run_chat_query(doc_id, message, history)
            
            return success_response(response=response_text)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f"Chatbot error: {str(e)}", 500)

@doc_bp.route('/document/delete/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id):
    user_id = get_jwt_identity()
    try:
        with session_scope() as db:
            doc = get_owned_document(db, doc_id, user_id)
            if not doc:
                return error_response("Document not found or unauthorized", 404)
                
            filename = doc.filename
            file_path = doc.file_path
            
            # 1. Delete database records in MySQL
            db.query(AnalysisHistory).filter(AnalysisHistory.document_id == doc_id).delete()
            db.delete(doc)
            db.commit()
            
            # 2. Delete analysis from MongoDB
            mongo_db["analysis_results"].delete_one({"document_id": doc_id})
            
            # 3. Delete physical files if they exist
            remove_file_quietly(file_path, "DELETE")
            remove_file_quietly(report_path(doc_id), "DELETE")
            
            # 4. Remove document chunks from vector store
            vstore = VectorStoreManager.get_instance()
            vstore.remove_document_chunks(filename)
            
            return success_response("Document deleted successfully")
    except Exception as e:
        return error_response(f"Error deleting document: {str(e)}", 500)
