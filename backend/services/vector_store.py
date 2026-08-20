import numpy as np
import logging
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMER = True
except ImportError:
    HAS_SENTENCE_TRANSFORMER = False

class VectorStoreManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.model = None
        self.chunks = []
        self.embeddings = []
        self.keyword_only = False
        
        if HAS_SENTENCE_TRANSFORMER:
            try:
                # Using a fast, free local transformer model
                logger.info("Loading local SentenceTransformer model (all-MiniLM-L6-v2)...")
                # Add a local download timeout/retry wrapper
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("SentenceTransformer loaded.")
            except Exception:
                logger.warning(
                    "SentenceTransformer failed to load. Running with keyword search fallback.",
                    exc_info=True
                )
        else:
            logger.warning("SentenceTransformer library not found. Running with keyword search fallback.")
        
    def clear(self):
        self.chunks = []
        self.embeddings = []
        self.keyword_only = False

    def remove_document_chunks(self, filename):
        """Removes chunks belonging to a specific file and re-encodes the rest."""
        if not self.chunks:
            return
        remaining_chunks = [c for c in self.chunks if c.get("source_doc") != filename]
        self.clear()
        if remaining_chunks:
            self.add_chunks(remaining_chunks)


    def add_chunks(self, chunks):
        """Encodes and indexes document chunks."""
        if not chunks:
            return
        
        if self.model is not None and not self.keyword_only:
            try:
                texts = [c["text"] for c in chunks]
                embs = self.model.encode(texts, show_progress_bar=False)
                
                if len(self.embeddings) == 0 and not self.chunks:
                    new_embeddings = np.array(embs)
                elif len(self.embeddings) == len(self.chunks):
                    new_embeddings = np.vstack([self.embeddings, embs])
                else:
                    logger.warning("Embedding index was already inconsistent; switching to keyword search.")
                    self.keyword_only = True
                    self.embeddings = []
                    self.chunks.extend(chunks)
                    return
                self.chunks.extend(chunks)
                self.embeddings = new_embeddings
            except Exception:
                self.chunks.extend(chunks)
                self.embeddings = []
                self.keyword_only = True
                logger.exception(
                    "Failed to compute embeddings; switching to keyword search for all indexed chunks."
                )
        else:
            self.chunks.extend(chunks)
            
    def similarity_search(self, query, k=8):
        """Finds top-k matching chunks."""
        if not self.chunks:
            return []
            
        embeddings_aligned = len(self.embeddings) == len(self.chunks)
        if self.model is not None and len(self.embeddings) > 0 and embeddings_aligned and not self.keyword_only:
            try:
                query_emb = self.model.encode([query], show_progress_bar=False)[0]
                
                # Calculate cosine similarity
                norms = np.linalg.norm(self.embeddings, axis=1)
                query_norm = np.linalg.norm(query_emb)
                
                # Avoid divide by zero
                norms = np.where(norms == 0, 1e-9, norms)
                query_norm = 1e-9 if query_norm == 0 else query_norm
                
                scores = np.dot(self.embeddings, query_emb) / (norms * query_norm)
                
                # Sort in descending order
                top_k_indices = np.argsort(scores)[::-1][:k]
                
                results = []
                for idx in top_k_indices:
                    results.append({
                        "chunk": self.chunks[idx],
                        "score": float(scores[idx])
                    })
                return results
            except Exception:
                logger.warning("Cosine similarity search failed; falling back to keyword matching.", exc_info=True)
        elif self.model is not None and len(self.embeddings) != len(self.chunks):
            logger.warning("Embedding index is out of sync with chunks; using keyword search.")

        # Resilient keyword word-overlap matching
        query_words = set(re_tokenize(query.lower()))
        results = []
        for chunk in self.chunks:
            text = chunk.get("text", "").lower()
            text_words = set(re_tokenize(text))
            overlap = len(query_words.intersection(text_words))
            results.append({
                "chunk": chunk,
                "score": float(overlap)
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

def re_tokenize(text):
    import re
    return re.findall(r'\b\w+\b', text)
