import numpy as np
import pytest

from backend.services import vector_store
from backend.services.vector_store import VectorStoreManager, re_tokenize


@pytest.fixture
def store():
    old = VectorStoreManager._instance
    VectorStoreManager._instance = None
    instance = VectorStoreManager.__new__(VectorStoreManager)
    instance.model = None
    instance.chunks = []
    instance.embeddings = []
    VectorStoreManager._instance = instance
    yield instance
    VectorStoreManager._instance = old


def test_singleton_keyword_search_and_mutation(store):
    assert VectorStoreManager.get_instance() is store
    store.add_chunks([])
    assert store.similarity_search("anything") == []
    chunks = [
        {"text": "revenue profit margin", "source_doc": "a.csv"},
        {"text": "revenue expense", "source_doc": "b.csv"},
        {"text": "weather forecast", "source_doc": "c.txt"},
    ]
    store.add_chunks(chunks)
    results = store.similarity_search("revenue profit", k=2)
    assert [r["chunk"]["source_doc"] for r in results] == ["a.csv", "b.csv"]
    assert store.similarity_search("revenue", k=1)[0]["chunk"] == chunks[0]
    store.remove_document_chunks("b.csv")
    assert len(store.chunks) == 2
    store.remove_document_chunks("missing")
    store.clear()
    assert store.chunks == [] and store.embeddings == []
    assert re_tokenize("Net-profit, $10.50!") == ["Net", "profit", "10", "50"]


class FakeModel:
    def encode(self, texts, show_progress_bar=False):
        return np.array([[len(text), text.count("a"), 1.0] for text in texts], dtype=float)


class BrokenModel:
    def encode(self, texts, show_progress_bar=False):
        raise RuntimeError("embedding unavailable")


def test_embedding_path_vstack_and_failure_fallback(store):
    store.model = FakeModel()
    store.add_chunks([{"text": "aa", "source_doc": "a"}])
    store.add_chunks([{"text": "bbbb", "source_doc": "b"}])
    assert store.embeddings.shape == (2, 3)
    results = store.similarity_search("aaaa", k=2)
    assert len(results) == 2

    broken = VectorStoreManager.__new__(VectorStoreManager)
    broken.model = BrokenModel()
    broken.chunks = []
    broken.embeddings = []
    broken.add_chunks([{"text": "profit", "source_doc": "p"}])
    assert broken.similarity_search("profit") == [{"chunk": {"text": "profit", "source_doc": "p"}, "score": 1.0}]
