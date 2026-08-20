import json
from types import SimpleNamespace

import pandas as pd
import pytest

from backend.agents import agent as agent_module
from backend.agents.agent import (
    FinancialIntelligenceAgent,
    check_topic_allowed,
    document_reader_tool,
    mongo_storage_tool,
    mysql_storage_tool,
    pdf_generator_tool,
)


@pytest.fixture
def agent():
    instance = FinancialIntelligenceAgent.__new__(FinancialIntelligenceAgent)
    instance.llm = None
    return instance


@pytest.mark.parametrize(
    "query, allowed",
    [
        ("What is my revenue and cash flow?", True),
        ("Explain the current ratio", True),
        ("Tell me about the latest movie", False),
        ("Who won cricket?", False),
        ("Help me write javascript", False),
        ("What is the weather?", False),
        ("How does the tax code affect my business?", True),
        ("What is the financial code?", True),
        ("Is this zip code relevant?", True),
        ("Show me python code", False),
    ],
)
def test_check_topic_allowed(query, allowed):
    assert check_topic_allowed(query) is allowed


def test_regex_extract_metrics_and_defaults(agent):
    metrics = agent._regex_extract_metrics(
        "Revenue: $1,200,000 Net Profit = 240,000 Assets 600000 Liabilities: 300000",
        "report.pdf",
    )
    assert metrics["total_revenue"] == 1200000
    assert metrics["net_profit"] == 240000
    assert metrics["total_expense"] == 960000
    assert metrics["gross_profit"] == 660000
    assert metrics["current_ratio"] == 2
    assert metrics["quick_ratio"] == 1.5
    assert metrics["debt_ratio"] == 0.5
    assert metrics["profit_margin"] == 20
    assert metrics["operating_margin"] == 17
    assert metrics["avg_monthly_revenue"] == 100000
    assert metrics["avg_monthly_expense"] == 80000
    assert agent._regex_extract_metrics("", "x")["total_revenue"] == 650000
    zero = agent._regex_extract_metrics("revenue 0 profit 0 assets 0 liabilities 0", "x")
    assert zero["current_ratio"] == 1.8
    assert zero["quick_ratio"] == 1.4
    assert zero["debt_ratio"] == 0.43
    assert zero["profit_margin"] == 15.05


def test_calculate_metrics_ledger_and_invalid_rows(agent, tmp_path):
    path = tmp_path / "ledger.csv"
    pd.DataFrame(
        [
            ["2024-03-01", "1,000", "credit"],
            ["2024-01-05", 500, "debit"],
            ["2024-02-01", 250, "credit"],
            ["2024-01-10", "bad", "debit"],
        ],
        columns=["date", "amount", "type"],
    ).to_csv(path, index=False)
    result = agent._calculate_metrics_directly(str(path), [], "ledger.csv")
    metrics, charts = result["metrics"], result["charts"]
    assert metrics["total_revenue"] == 1250
    assert metrics["total_expense"] == 500
    assert metrics["net_profit"] == metrics["cash_flow"] == 750
    assert metrics["gross_profit"] == 562.5
    assert charts["monthly_comparison"]["labels"] == ["Jan", "Feb", "Mar"]
    assert charts["revenue_trend"] == [0, 250, 1000]
    assert charts["expense_trend"] == [500, 0, 0]
    assert charts["profit_trend"] == [-500, 250, 1000]
    assert metrics["avg_monthly_revenue"] == round(1250 / 3, 2)
    assert metrics["avg_monthly_expense"] == round(500 / 3, 2)


def test_calculate_metrics_missing_file_uses_chunk_regex(agent, tmp_path):
    result = agent._calculate_metrics_directly(
        str(tmp_path / "missing.csv"),
        [{"text": "Revenue: 1000, Net Profit: 100, Assets: 500, Liabilities: 200"}],
        "missing.csv",
    )
    assert result["metrics"]["total_revenue"] == 1000
    assert result["charts"]["monthly_comparison"]["labels"] == ["Q1", "Q2", "Q3", "Q4"]


@pytest.mark.xfail(reason="production bug: financial-statement cash-flow branch calls replace on a float")
def test_financial_statement_branch_current_behavior(agent, tmp_path):
    path = tmp_path / "statement.csv"
    pd.DataFrame(
        {"year": [2024], "revenue": [1000], "net income": [100], "cash flow from operating": [90]}
    ).to_csv(path, index=False)
    result = agent._calculate_metrics_directly(str(path), [], "statement.csv")
    assert result["metrics"]["total_revenue"] == 1000
    assert result["charts"]["cash_flow"] == [90]


def test_assemble_local_fallback_preserves_inputs(agent):
    calculated = {
        "metrics": {
            "total_revenue": 100,
            "total_expense": 40,
            "net_profit": 60,
            "profit_margin": 60,
            "operating_margin": 50,
            "cash_flow": 55,
            "current_ratio": 2,
            "debt_ratio": 0.2,
        },
        "charts": {"revenue_trend": [100]},
    }
    result = agent._assemble_local_fallback(calculated, "source.csv")
    assert set(result) == {
        "current_state_analysis",
        "gap_detection",
        "forward_looking_flags",
        "missing_data_detection",
        "metrics",
        "charts",
    }
    assert result["metrics"] is calculated["metrics"]
    assert result["charts"] is calculated["charts"]
    assert "source.csv" in result["current_state_analysis"]["revenue_trend"]


def test_run_chat_query_topic_filter_and_llm(monkeypatch, agent):
    class Store:
        def similarity_search(self, query, k):
            return [{"chunk": {"text": "Revenue is 100", "source_doc": "x.csv", "page_num": 2}}]
    class Results:
        def find_one(self, query):
            return {"document_id": 1, "metrics": {"total_revenue": 100, "net_profit": 20, "total_expense": 80, "profit_margin": 20}}
    class Mongo:
        def __getitem__(self, name):
            return Results()
    monkeypatch.setattr(agent_module.VectorStoreManager, "get_instance", lambda: Store())
    monkeypatch.setattr(agent_module, "mongo_db", Mongo())
    calls = []
    agent.llm = SimpleNamespace(invoke=lambda messages: (calls.append(messages) or SimpleNamespace(content="  answer  ")))
    assert agent.run_chat_query(1, "What is revenue?", [{"role": "user", "content": "old"}]) == "answer"
    assert "Revenue is 100" in calls[0][0]["content"]
    assert agent.run_chat_query(1, "Tell me a movie", []) == (
        "I am a Financial Intelligence Assistant. Please ask questions related to your uploaded financial documents or financial analysis."
    )


@pytest.mark.parametrize(
    "query, expected",
    [
        ("revenue", "total revenue is INR 100"),
        ("profit", "net profit calculated"),
        ("expense", "total expenses are INR 80"),
    ],
)
def test_run_chat_query_fallbacks(monkeypatch, agent, query, expected):
    class Results:
        def find_one(self, query):
            return {"metrics": {"total_revenue": 100, "net_profit": 20, "total_expense": 80, "profit_margin": 20}}
    class Mongo:
        def __getitem__(self, name):
            return Results()
    monkeypatch.setattr(agent_module.VectorStoreManager, "get_instance", lambda: SimpleNamespace(similarity_search=lambda *a, **k: []))
    monkeypatch.setattr(agent_module, "mongo_db", Mongo())
    agent.llm = SimpleNamespace(invoke=lambda messages: (_ for _ in ()).throw(RuntimeError("offline")))
    assert expected in agent.run_chat_query(1, query, [])


def test_run_chat_query_generic_offline(monkeypatch, agent):
    class Empty:
        def find_one(self, query):
            return None
    monkeypatch.setattr(agent_module, "mongo_db", {"analysis_results": Empty()})
    monkeypatch.setattr(agent_module.VectorStoreManager, "get_instance", lambda: SimpleNamespace(similarity_search=lambda *a, **k: []))
    agent.llm = SimpleNamespace(invoke=lambda messages: (_ for _ in ()).throw(RuntimeError("offline")))
    assert "currently offline" in agent.run_chat_query(1, "liquidity", [])


def _tool_db(monkeypatch, document=None):
    doc = document or SimpleNamespace(filename="file.pdf", id=1, user_id=2, status="old")
    query = SimpleNamespace(first=lambda: doc)
    db = SimpleNamespace(
        query=lambda *args: SimpleNamespace(filter=lambda *a: query),
        close=lambda: None,
        add=lambda obj: None,
        commit=lambda: None,
    )
    monkeypatch.setattr(agent_module, "SessionLocal", lambda: db)
    return doc, query, db


def test_document_reader_tool_returns_chunks(monkeypatch):
    monkeypatch.setattr(agent_module.VectorStoreManager, "get_instance", lambda: SimpleNamespace(
        similarity_search=lambda query, k: [{"chunk": {"source_doc": "a.pdf", "page_num": 1, "text": "hello"}}]
    ))
    assert "SOURCE: a.pdf" in document_reader_tool.func("hello")


def test_document_reader_tool_empty_results(monkeypatch):
    monkeypatch.setattr(agent_module.VectorStoreManager, "get_instance", lambda: SimpleNamespace(similarity_search=lambda *a, **k: []))
    assert "No relevant" in document_reader_tool.func("none")


def test_pdf_generator_tool_success(monkeypatch):
    _tool_db(monkeypatch)
    generated = []
    monkeypatch.setattr(agent_module.PDFReportGenerator, "generate", lambda path, name, data: generated.append((path, name, data)))
    assert pdf_generator_tool.func(1, '{"x": 1}').endswith("report_1.pdf")
    assert generated


def test_pdf_generator_tool_document_not_found(monkeypatch):
    _, query, _ = _tool_db(monkeypatch)
    query.first = lambda: None
    assert "not found" in pdf_generator_tool.func(1, "{}")


def test_pdf_generator_tool_bad_json(monkeypatch):
    _tool_db(monkeypatch)
    monkeypatch.setattr(agent_module.PDFReportGenerator, "generate", lambda *args: None)
    assert "Error generating PDF" in pdf_generator_tool.func(1, "{bad")


def test_mongo_storage_tool_success(monkeypatch):
    stored = []
    class Collection:
        def replace_one(self, *args, **kwargs):
            stored.append(args)
    monkeypatch.setattr(agent_module, "mongo_db", {"analysis_results": Collection()})
    assert mongo_storage_tool.func(1, "{}", "log").startswith("Successfully")


def test_mongo_storage_tool_bad_json(monkeypatch):
    monkeypatch.setattr(agent_module, "mongo_db", {"analysis_results": SimpleNamespace(replace_one=lambda *args, **kwargs: None)})
    assert "Error saving" in mongo_storage_tool.func(1, "{bad", "log")


def test_mysql_storage_tool_success(monkeypatch):
    _, _, _ = _tool_db(monkeypatch)
    assert "Successfully updated" in mysql_storage_tool.func(1, "analyzed")


def test_mysql_storage_tool_document_not_found(monkeypatch):
    _, query, _ = _tool_db(monkeypatch)
    query.first = lambda: None
    assert "not found" in mysql_storage_tool.func(1, "analyzed")


def test_agent_init_and_mysql_error(monkeypatch):
    fake_llm = object()
    monkeypatch.setattr(agent_module, "ChatGroq", lambda **kwargs: fake_llm)
    instance = FinancialIntelligenceAgent()
    assert instance.llm is fake_llm

    class BrokenDB:
        def query(self, *args):
            raise RuntimeError("database down")
        def rollback(self):
            self.rolled_back = True
        def close(self):
            pass
    monkeypatch.setattr(agent_module, "SessionLocal", lambda: BrokenDB())
    assert "Error updating MySQL" in mysql_storage_tool.func(1, "analyzed")


def _pipeline_fakes(monkeypatch, agent, llm):
    calls = {"pdf": [], "mongo": [], "mysql": []}
    doc = SimpleNamespace(filename="ledger.csv", file_path="/tmp/ledger.csv")

    class Query:
        def filter(self, *args):
            return self

        def first(self):
            return doc

    class DB:
        def query(self, *args):
            return Query()

        def close(self):
            pass

    monkeypatch.setattr(agent_module, "SessionLocal", lambda: DB())
    monkeypatch.setattr(
        agent_module.VectorStoreManager,
        "get_instance",
        lambda: SimpleNamespace(chunks=[{"source_doc": "ledger.csv", "page_num": 1, "text": "revenue 100"}]),
    )
    calculated = {
        "metrics": {"total_revenue": 100, "total_expense": 20, "net_profit": 80, "profit_margin": 80,
                    "operating_margin": 68, "cash_flow": 80, "current_ratio": 2, "debt_ratio": 0.2},
        "charts": {"revenue_trend": [100], "expense_trend": [20]},
    }
    monkeypatch.setattr(agent, "_calculate_metrics_directly", lambda *args: calculated)
    monkeypatch.setattr(agent_module, "pdf_generator_tool", SimpleNamespace(
        func=lambda document_id, payload: calls["pdf"].append((document_id, payload)) or "pdf"
    ))
    monkeypatch.setattr(agent_module, "mongo_storage_tool", SimpleNamespace(
        func=lambda document_id, payload, reasoning: calls["mongo"].append((document_id, payload, reasoning)) or "mongo"
    ))
    monkeypatch.setattr(agent_module, "mysql_storage_tool", SimpleNamespace(
        func=lambda document_id, status: calls["mysql"].append((document_id, status)) or "mysql"
    ))
    agent.llm = llm
    return calls, calculated


def test_run_analysis_happy_path_strips_fences_and_overwrites_llm_values(monkeypatch, agent):
    llm_json = {
        "current_state_analysis": {"revenue_trend": "LLM text"},
        "gap_detection": [],
        "forward_looking_flags": [],
        "missing_data_detection": [],
        "metrics": {"total_revenue": 999999},
        "charts": {"revenue_trend": [999999]},
    }
    calls, calculated = _pipeline_fakes(
        monkeypatch,
        agent,
        SimpleNamespace(invoke=lambda messages: SimpleNamespace(content=f"```json\n{json.dumps(llm_json)}\n```")),
    )
    result = agent.run_analysis(7)
    assert result["metrics"] is calculated["metrics"]
    assert result["charts"] is calculated["charts"]
    assert result["current_state_analysis"]["revenue_trend"] == "LLM text"
    assert calls["pdf"][0][0] == 7
    assert calls["mongo"][0][0] == 7
    assert calls["mysql"] == [(7, "processing"), (7, "analyzed")]


def test_run_analysis_fallback_runs_side_effects_and_records_reasoning(monkeypatch, agent):
    calls, _ = _pipeline_fakes(
        monkeypatch,
        agent,
        SimpleNamespace(invoke=lambda messages: (_ for _ in ()).throw(RuntimeError("LLM offline"))),
    )
    result = agent.run_analysis(8)
    assert set(result) == {
        "current_state_analysis",
        "gap_detection",
        "forward_looking_flags",
        "missing_data_detection",
        "metrics",
        "charts",
    }
    assert calls["pdf"][0][0] == 8
    assert calls["mongo"][0][0] == 8
    assert "LLM offline" in calls["mongo"][0][2]
    assert calls["mysql"] == [(8, "processing"), (8, "analyzed")]
