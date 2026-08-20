import io
import os
from types import SimpleNamespace

import pandas as pd
import pytest

from backend.models.models import AnalysisHistory, Document, User
from backend.routes import document as document_module


@pytest.mark.parametrize(
    "filename, allowed",
    [
        ("a.pdf", True),
        ("a.csv", True),
        ("a.xlsx", True),
        ("a.xls", True),
        ("a.txt", False),
        ("a.png", False),
        ("noextension", False),
        ("A.PDF", True),
    ],
)
def test_allowed_file(filename, allowed):
    assert document_module.allowed_file(filename) is allowed


def test_check_is_financial_file_csv_branches(tmp_path):
    financial = tmp_path / "financial.csv"
    financial.write_text("date,amount,type\n2024-01-01,10,credit\n")
    assert document_module.check_is_financial_file(str(financial), "CSV") is True
    resume = tmp_path / "resume.csv"
    resume.write_text("Resume,Work Experience,Education\nA,B,C\n")
    assert document_module.check_is_financial_file(str(resume), "CSV") is False
    weak_resume = tmp_path / "weak.csv"
    weak_resume.write_text("Resume,revenue\nA,10\n")
    assert document_module.check_is_financial_file(str(weak_resume), "CSV") is False
    weak_fin = tmp_path / "weak-fin.csv"
    weak_fin.write_text("revenue\n10\n")
    assert document_module.check_is_financial_file(str(weak_fin), "CSV") is False
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    assert document_module.check_is_financial_file(str(empty), "CSV") is False
    assert document_module.check_is_financial_file(str(tmp_path / "missing.csv"), "CSV") is False


def test_check_is_financial_file_excel_and_pdf(monkeypatch, tmp_path):
    workbook = tmp_path / "financial.xlsx"
    pd.DataFrame({"revenue": [1], "assets": [2]}).to_excel(workbook, index=False)
    assert document_module.check_is_financial_file(str(workbook), "Excel") is True

    class Page:
        def get_text(self):
            return "invoice revenue amount"
    class Doc:
        def __len__(self): return 1
        def __getitem__(self, index): return Page()
        def close(self): pass
    monkeypatch.setitem(__import__("sys").modules, "fitz", SimpleNamespace(open=lambda _: Doc()))
    assert document_module.check_is_financial_file(str(tmp_path / "a.pdf"), "PDF") is True


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_upload_validation_and_happy_path(client, auth_token, monkeypatch, session_factory, tmp_path):
    assert client.post("/api/upload", headers=_headers(auth_token)).status_code == 400
    assert client.post("/api/upload", data={"file": (io.BytesIO(b"x"), "")}, headers=_headers(auth_token), content_type="multipart/form-data").status_code == 400
    assert client.post("/api/upload", data={"file": (io.BytesIO(b"x"), "x.txt")}, headers=_headers(auth_token), content_type="multipart/form-data").status_code == 400
    real_getsize = document_module.os.path.getsize
    monkeypatch.setattr(document_module.os.path, "getsize", lambda path: 11 * 1024 * 1024)
    assert client.post("/api/upload", data={"file": (io.BytesIO(b"revenue,assets\n1,2"), "large.csv")}, headers=_headers(auth_token), content_type="multipart/form-data").status_code == 400
    monkeypatch.setattr(document_module.os.path, "getsize", real_getsize)

    monkeypatch.setattr(document_module, "check_is_financial_file", lambda *args: False)
    response = client.post("/api/upload", data={"file": (io.BytesIO(b"resume"), "resume.csv")}, headers=_headers(auth_token), content_type="multipart/form-data")
    assert response.status_code == 400
    assert not (tmp_path / "uploads" / "resume.csv").exists()

    monkeypatch.setattr(document_module, "check_is_financial_file", lambda *args: True)
    monkeypatch.setattr(document_module.DocumentParser, "parse_csv", lambda path: [{"text": "revenue", "source_doc": "good.csv", "page_num": 1}])
    monkeypatch.setattr(document_module.VectorStoreManager, "get_instance", lambda: SimpleNamespace(clear=lambda: None, add_chunks=lambda chunks: None))
    monkeypatch.setattr(document_module, "FinancialIntelligenceAgent", lambda: SimpleNamespace(run_analysis=lambda doc_id: {
        "current_state_analysis": {}, "gap_detection": [], "forward_looking_flags": [], "metrics": {"total_revenue": 1}, "charts": {}
    }))
    response = client.post("/api/upload", data={"file": (io.BytesIO(b"revenue,assets\n1,2"), "good.csv")}, headers=_headers(auth_token), content_type="multipart/form-data")
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True and body["document"]["filename"] == "good.csv"
    db = session_factory()
    assert db.query(Document).filter(Document.filename == "good.csv").first() is not None
    db.close()


def test_history_detail_and_report(client, auth_token, session_factory, monkeypatch, tmp_path):
    db = session_factory()
    user = db.query(User).filter(User.email == "test@example.com").first()
    doc = Document(user_id=user.id, filename="report.csv", file_path=str(tmp_path / "report.csv"), status="analyzed", file_type="CSV")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    foreign = User(full_name="Other", email="other@example.com", password_hash="x")
    db.add(foreign)
    db.commit()
    db.refresh(foreign)
    other_doc = Document(user_id=foreign.id, filename="other.csv", file_path="x", status="analyzed", file_type="CSV")
    db.add(other_doc)
    db.commit()
    db.refresh(other_doc)
    doc_id = doc.id
    other_id = other_doc.id
    db.close()
    assert client.get(f"/api/history/{other_id}", headers=_headers(auth_token)).status_code == 404
    monkeypatch.setattr(document_module, "mongo_db", {"analysis_results": SimpleNamespace(find_one=lambda q: None)})
    assert client.get(f"/api/history/{doc_id}", headers=_headers(auth_token)).status_code == 404
    monkeypatch.setattr(document_module, "mongo_db", {"analysis_results": SimpleNamespace(find_one=lambda q: {"_id": "x", "document_id": doc_id})})
    assert client.get(f"/api/history/{doc_id}", headers=_headers(auth_token)).status_code == 200
    assert client.get("/api/history", headers=_headers(auth_token)).get_json()["history"]
    assert client.get("/api/report/9999", headers=_headers(auth_token)).status_code == 404
    os.makedirs(tmp_path / "reports", exist_ok=True)
    (tmp_path / "reports" / f"report_{doc_id}.pdf").write_bytes(b"%PDF")
    assert client.get(f"/api/report/{doc_id}", headers=_headers(auth_token)).status_code == 200


def test_chat_and_delete(client, auth_token, session_factory, monkeypatch, tmp_path):
    db = session_factory()
    user = db.query(User).filter(User.email == "test@example.com").first()
    uploaded = tmp_path / "uploaded.csv"
    uploaded.write_text("data")
    doc = Document(user_id=user.id, filename="uploaded.csv", file_path=str(uploaded), status="analyzed", file_type="CSV")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = doc.id
    report = tmp_path / "reports" / f"report_{doc_id}.pdf"
    report.parent.mkdir(exist_ok=True)
    report.write_text("pdf")
    history = AnalysisHistory(user_id=user.id, document_id=doc_id, status="analyzed")
    db.add(history)
    db.commit()
    db.close()
    assert client.post("/api/chat", json={}, headers=_headers(auth_token)).status_code == 400
    assert client.post("/api/chat", json={"message": "x", "document_id": 999}, headers=_headers(auth_token)).status_code == 404
    monkeypatch.setattr(document_module, "FinancialIntelligenceAgent", lambda: SimpleNamespace(run_chat_query=lambda *args: "answer"))
    assert client.post("/api/chat", json={"message": "x", "document_id": doc_id}, headers=_headers(auth_token)).get_json()["response"] == "answer"
    monkeypatch.setattr(document_module, "FinancialIntelligenceAgent", lambda: (_ for _ in ()).throw(RuntimeError("failed")))
    assert client.post("/api/chat", json={"message": "x", "document_id": doc_id}, headers=_headers(auth_token)).status_code == 500

    class Collection:
        def delete_one(self, query): return SimpleNamespace(deleted_count=1)
    monkeypatch.setattr(document_module, "mongo_db", {"analysis_results": Collection()})
    removed = []
    monkeypatch.setattr(document_module.VectorStoreManager, "get_instance", lambda: SimpleNamespace(remove_document_chunks=lambda name: removed.append(name)))
    assert client.delete("/api/document/delete/999", headers=_headers(auth_token)).status_code == 404
    assert client.delete(f"/api/document/delete/{doc_id}", headers=_headers(auth_token)).status_code == 200
    assert not uploaded.exists() and not report.exists()
    assert removed == ["uploaded.csv"]
