from sentence_transformers import SentenceTransformer
from django.conf import settings


# ── Module-level singleton so the model is loaded only once ──
_model = None


def _load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('intfloat/e5-base-v2')
    return _model


class EmbeddingGenerator:
    """
    Wraps intfloat/e5-base-v2 local embeddings and Pinecone vector storage.
    Model: e5-base-v2  (768 dimensions, L2-normalised)

    E5 requires every input to be prefixed:
      - "query: <text>"   for search queries
      - "passage: <text>" for documents / passages to index
    """

    def __init__(self):
        self.model = _load_model()
        self._init_pinecone()

    def _init_pinecone(self):
        """Initialize Pinecone index (lazy — only if API key is set)."""
        self.index = None
        if getattr(settings, 'PINECONE_API_KEY', None):
            try:
                from pinecone import Pinecone, ServerlessSpec
                pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                index_name = settings.PINECONE_INDEX

                existing = [idx.name for idx in pc.list_indexes()]
                if index_name not in existing:
                    pc.create_index(
                        name=index_name,
                        dimension=768,
                        metric='cosine',
                        spec=ServerlessSpec(
                            cloud='aws',
                            region=getattr(settings, 'PINECONE_ENV', None) or 'us-east-1'
                        )
                    )
                self.index = pc.Index(index_name)
            except Exception as e:
                print(f"[EmbeddingGenerator] Pinecone init skipped: {e}")

    # ── Public API ────────────────────────────────────────────

    def generate(self, text: str) -> list:
        """
        Embed a *passage* (document to be stored / indexed).
        Returns: embedding vector list[float] (length 768)
        """
        try:
            embedding = self.model.encode(
                [f"passage: {text}"], normalize_embeddings=True
            )
            return embedding[0].tolist()
        except Exception as e:
            print(f"[EmbeddingGenerator] E5 embed error: {e}")
            return [0.0] * 768

    def generate_query_embedding(self, text: str) -> list:
        """
        Embed a *query* (search / retrieval intent).
        Returns: embedding vector list[float] (length 768)
        """
        try:
            embedding = self.model.encode(
                [f"query: {text}"], normalize_embeddings=True
            )
            return embedding[0].tolist()
        except Exception as e:
            print(f"[EmbeddingGenerator] E5 query embed error: {e}")
            return [0.0] * 768

    def store(self, vector_id: str, embedding: list, metadata: dict) -> bool:
        """
        Upserts embedding into Pinecone.
        Returns: True if successful, False if Pinecone not configured
        """
        if not self.index:
            print("[EmbeddingGenerator] Pinecone not configured, skipping store.")
            return False
        self.index.upsert(vectors=[(vector_id, embedding, metadata)])
        return True

    def query_similar(self, embedding: list, top_k: int = 5, filter: dict = None) -> list:
        """
        Queries Pinecone for top_k similar vectors.
        Returns: list of { id, score, metadata }
        """
        if not self.index:
            print("[EmbeddingGenerator] Pinecone not configured, returning empty.")
            return []
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            filter=filter,
            include_metadata=True
        )
        return [
            {
                'id': match.id,
                'score': match.score,
                'metadata': match.metadata
            }
            for match in results.matches
        ]
