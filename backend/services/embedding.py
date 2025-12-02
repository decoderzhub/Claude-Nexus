"""
Embedding service for Claude Nexus.

Provides vector embeddings for semantic search in the knowledge graph.
Supports multiple backends:
1. Ollama (recommended) - Local LLM with embedding models
2. TF-IDF (fallback) - Lightweight semantic embeddings without ML deps

The service automatically falls back through providers until one works.
"""

import asyncio
import hashlib
import json
import math
import re
from collections import Counter
from typing import Optional
from pathlib import Path

# Try to import httpx for Ollama API calls
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class OllamaEmbedding:
    """Embedding provider using local Ollama instance."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text"
    ):
        self.base_url = base_url
        self.model = model
        self.dimension = 768  # nomic-embed-text dimension
        self._available: Optional[bool] = None

    async def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        if self._available is not None:
            return self._available

        if not HTTPX_AVAILABLE:
            self._available = False
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                    self._available = self.model.split(":")[0] in models
                else:
                    self._available = False
        except Exception:
            self._available = False

        return self._available

    async def embed(self, text: str) -> list[float]:
        """Generate embedding using Ollama."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        # Ollama doesn't support batch embedding, so we parallelize
        tasks = [self.embed(text) for text in texts]
        return await asyncio.gather(*tasks)


class TFIDFEmbedding:
    """
    TF-IDF based embedding that captures semantic meaning without ML dependencies.

    Uses a vocabulary built from the corpus and generates sparse-to-dense
    embeddings based on term frequency and inverse document frequency.
    """

    def __init__(self, dimension: int = 384, vocab_path: Optional[Path] = None):
        self.dimension = dimension
        self.vocab_path = vocab_path
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.document_count = 0

        # Common English stop words to filter
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "need",
            "this", "that", "these", "those", "i", "you", "he", "she", "it",
            "we", "they", "what", "which", "who", "whom", "whose", "where",
            "when", "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "also", "now", "here",
        }

        # Load vocabulary if exists
        if vocab_path and vocab_path.exists():
            self._load_vocabulary()

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into meaningful terms."""
        # Lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-z][a-z0-9_]*\b', text)
        # Filter stop words and short words
        return [w for w in words if w not in self.stop_words and len(w) > 2]

    def _get_term_frequency(self, tokens: list[str]) -> dict[str, float]:
        """Calculate normalized term frequency."""
        counts = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {term: count / total for term, count in counts.items()}

    def update_vocabulary(self, texts: list[str]) -> None:
        """Update vocabulary and IDF from new documents."""
        # Count document frequency for each term
        doc_freq: dict[str, int] = {}

        for text in texts:
            tokens = set(self._tokenize(text))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
                if token not in self.vocabulary:
                    self.vocabulary[token] = len(self.vocabulary)

        # Update IDF values
        self.document_count += len(texts)
        for term, freq in doc_freq.items():
            # Smoothed IDF
            self.idf[term] = math.log((self.document_count + 1) / (freq + 1)) + 1

        # Save vocabulary
        if self.vocab_path:
            self._save_vocabulary()

    def embed(self, text: str) -> list[float]:
        """Generate TF-IDF based embedding."""
        tokens = self._tokenize(text)

        if not tokens:
            # Return zero vector for empty text
            return [0.0] * self.dimension

        tf = self._get_term_frequency(tokens)

        # Create sparse TF-IDF vector
        tfidf_vector: dict[int, float] = {}
        for term, freq in tf.items():
            if term in self.vocabulary:
                idx = self.vocabulary[term] % self.dimension
                idf = self.idf.get(term, 1.0)
                tfidf_vector[idx] = tfidf_vector.get(idx, 0) + freq * idf

        # Convert to dense and normalize
        embedding = [0.0] * self.dimension
        for idx, value in tfidf_vector.items():
            embedding[idx] = value

        # Add semantic hashing for terms not in vocabulary
        unknown_terms = [t for t in tokens if t not in self.vocabulary]
        if unknown_terms:
            for term in unknown_terms:
                # Distribute unknown terms across embedding space via hashing
                hash_val = int(hashlib.md5(term.encode()).hexdigest(), 16)
                idx = hash_val % self.dimension
                embedding[idx] += tf.get(term, 0) * 0.5

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm > 0:
            embedding = [v / norm for v in embedding]

        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]

    def _save_vocabulary(self) -> None:
        """Persist vocabulary to disk."""
        if not self.vocab_path:
            return
        self.vocab_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "vocabulary": self.vocabulary,
            "idf": self.idf,
            "document_count": self.document_count,
        }
        with open(self.vocab_path, 'w') as f:
            json.dump(data, f)

    def _load_vocabulary(self) -> None:
        """Load vocabulary from disk."""
        if not self.vocab_path or not self.vocab_path.exists():
            return
        try:
            with open(self.vocab_path, 'r') as f:
                data = json.load(f)
            self.vocabulary = data.get("vocabulary", {})
            self.idf = data.get("idf", {})
            self.document_count = data.get("document_count", 0)
        except Exception:
            pass


class EmbeddingService:
    """
    Unified embedding service with automatic fallback.

    Tries providers in order:
    1. Ollama (if available)
    2. TF-IDF (always available)
    """

    def __init__(self, vocab_path: Optional[Path] = None):
        self.ollama = OllamaEmbedding()
        self.tfidf = TFIDFEmbedding(vocab_path=vocab_path)
        self._active_provider: Optional[str] = None
        self.dimension = 384  # Default, updated based on provider

    async def _get_provider(self) -> str:
        """Determine which provider to use."""
        if self._active_provider:
            return self._active_provider

        # Try Ollama first
        if await self.ollama.is_available():
            self._active_provider = "ollama"
            self.dimension = self.ollama.dimension
        else:
            self._active_provider = "tfidf"
            self.dimension = self.tfidf.dimension

        return self._active_provider

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        provider = await self._get_provider()

        if provider == "ollama":
            try:
                return await self.ollama.embed(text)
            except Exception:
                # Fall back to TF-IDF on error
                self._active_provider = "tfidf"
                return self.tfidf.embed(text)
        else:
            return self.tfidf.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        provider = await self._get_provider()

        if provider == "ollama":
            try:
                return await self.ollama.embed_batch(texts)
            except Exception:
                self._active_provider = "tfidf"
                return self.tfidf.embed_batch(texts)
        else:
            return self.tfidf.embed_batch(texts)

    def embed_sync(self, text: str) -> list[float]:
        """Synchronous embedding (uses TF-IDF only)."""
        return self.tfidf.embed(text)

    def update_vocabulary(self, texts: list[str]) -> None:
        """Update TF-IDF vocabulary with new documents."""
        self.tfidf.update_vocabulary(texts)

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not embedding1 or not embedding2:
            return 0.0

        # Handle different dimensions by truncating to shorter
        min_len = min(len(embedding1), len(embedding2))
        e1 = embedding1[:min_len]
        e2 = embedding2[:min_len]

        dot_product = sum(a * b for a, b in zip(e1, e2))
        norm1 = math.sqrt(sum(a * a for a in e1))
        norm2 = math.sqrt(sum(b * b for b in e2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_similar(
        self,
        query_embedding: list[float],
        candidates: list[tuple[str, list[float]]],
        top_k: int = 10,
        threshold: float = 0.0
    ) -> list[tuple[str, float]]:
        """Find most similar embeddings from candidates."""
        results = []
        for candidate_id, candidate_embedding in candidates:
            if candidate_embedding:
                sim = self.similarity(query_embedding, candidate_embedding)
                if sim >= threshold:
                    results.append((candidate_id, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    @property
    def provider_name(self) -> str:
        """Get name of active provider."""
        return self._active_provider or "unknown"


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(vocab_path: Optional[Path] = None) -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(vocab_path=vocab_path)
    return _embedding_service


async def init_embedding_service(vocab_path: Optional[Path] = None) -> EmbeddingService:
    """Initialize and return embedding service, detecting best provider."""
    service = get_embedding_service(vocab_path)
    await service._get_provider()  # Trigger provider detection
    return service
