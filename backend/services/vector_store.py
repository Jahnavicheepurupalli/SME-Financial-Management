import numpy as np
import os

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
        
        if HAS_SENTENCE_TRANSFORMER:
            try:
                # Using a fast, free local transformer model
                print("Loading local SentenceTransformer model (all-MiniLM-L6-v2)...")
                # Add a local download timeout/retry wrapper
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("SentenceTransformer loaded.")
            except Exception as e:
                print(f"Warning: SentenceTransformer failed to load: {e}. Running with keyword search fallback.")
        else:
            print("SentenceTransformer library not found. Running with keyword search fallback.")
        
    def clear(self):
        self.chunks = []
        self.embeddings = []

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
        
        self.chunks.extend(chunks)
        
        if self.model is not None:
            try:
                texts = [c["text"] for c in chunks]
                embs = self.model.encode(texts, show_progress_bar=False)
                
                if len(self.embeddings) == 0:
                    self.embeddings = np.array(embs)
                else:
                    self.embeddings = np.vstack([self.embeddings, embs])
            except Exception as e:
                print(f"Warning: Failed to compute embeddings: {e}. Chunks will be indexed with keyword search.")
            
    def similarity_search(self, query, k=8):
        """Finds top-k matching chunks."""
        if not self.chunks:
            return []
            
        if self.model is not None and len(self.embeddings) > 0:
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
            except Exception as e:
                print(f"Warning: Cosine similarity search failed: {e}. Falling back to keyword matching.")

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
