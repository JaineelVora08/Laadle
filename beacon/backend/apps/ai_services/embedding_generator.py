class EmbeddingGenerator:
    """
    Wraps external embedding API (e.g. OpenAI text-embedding-ada-002).
    Stores/retrieves vectors in Pinecone index: "beacon-domains"
    """

    def generate(self, text: str) -> list:
        """
        Calls embedding API with text.
        Returns: embedding vector list[float] (length 1536)
        """
        pass

    def store(self, vector_id: str, embedding: list, metadata: dict) -> bool:
        """
        Upserts embedding into Pinecone.
        metadata keys: domain_name, type, domain_id
        Returns: True if successful
        """
        pass

    def query_similar(self, embedding: list, top_k: int = 5, filter: dict = None) -> list:
        """
        Queries Pinecone for top_k similar vectors.
        Returns: list of { id, score, metadata }
        """
        pass
