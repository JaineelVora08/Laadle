import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from django.conf import settings


def _average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """Mean-pool token embeddings, ignoring padding tokens."""
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


# ── Module-level singleton so the model is loaded only once ──
_model = None
_tokenizer = None


def _load_model():
    global _model, _tokenizer
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained('intfloat/e5-base-v2')
        _model = AutoModel.from_pretrained('intfloat/e5-base-v2')
        _model.eval()
    return _tokenizer, _model


class EmbeddingGenerator:
    """
    Wraps intfloat/e5-base-v2 local embeddings and Pinecone vector storage.
    Model: e5-base-v2  (768 dimensions, L2-normalised)

    E5 requires every input to be prefixed:
      - "query: <text>"   for search queries
      - "passage: <text>" for documents / passages to index
    """

    def __init__(self):
        self.tokenizer, self.model = _load_model()
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

    @torch.no_grad()
    def _embed(self, texts: list[str]) -> list[list[float]]:
        """
        Core embedding method — runs e5-base-v2 inference.
        Caller is responsible for adding the 'query: ' or 'passage: ' prefix.
        Returns: list of L2-normalised embedding vectors (each length 768).
        """
        batch_dict = self.tokenizer(
            texts, max_length=512, padding=True, truncation=True, return_tensors='pt'
        )
        outputs = self.model(**batch_dict)
        embeddings = _average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings.tolist()

    # ── Public API ────────────────────────────────────────────

    def generate(self, text: str) -> list:
        """
        Embed a *passage* (document to be stored / indexed).
        Returns: embedding vector list[float] (length 768)
        """
        try:
            return self._embed([f"passage: {text}"])[0]
        except Exception as e:
            print(f"[EmbeddingGenerator] E5 embed error: {e}")
            return [0.0] * 768

    def generate_query_embedding(self, text: str) -> list:
        """
        Embed a *query* (search / retrieval intent).
        Returns: embedding vector list[float] (length 768)
        """
        try:
            return self._embed([f"query: {text}"])[0]
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
