from backend.services import vector_store
from backend.services.vector_store import VectorStoreManager


def test_vector_store_init_without_sentence_transformers(monkeypatch):
    monkeypatch.setattr(vector_store, "HAS_SENTENCE_TRANSFORMER", False)
    store = VectorStoreManager()
    assert store.model is None
    assert store.chunks == []


def test_vector_store_init_with_working_sentence_transformer(monkeypatch):
    class FakeTransformer:
        def __init__(self, name):
            self.name = name

    monkeypatch.setattr(vector_store, "HAS_SENTENCE_TRANSFORMER", True)
    monkeypatch.setattr(vector_store, "SentenceTransformer", FakeTransformer, raising=False)
    store = VectorStoreManager()
    assert store.model.name == "all-MiniLM-L6-v2"


def test_vector_store_init_with_failing_sentence_transformer(monkeypatch):
    def fail(name):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(vector_store, "HAS_SENTENCE_TRANSFORMER", True)
    monkeypatch.setattr(vector_store, "SentenceTransformer", fail, raising=False)
    store = VectorStoreManager()
    assert store.model is None
