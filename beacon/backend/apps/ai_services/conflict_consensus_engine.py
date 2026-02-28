import numpy as np
from apps.ai_services.embedding_generator import EmbeddingGenerator
from apps.query_orchestrator.models import ConflictRecord


class ConflictConsensusEngine:
    """
    Detects when new senior advice contradicts historical trends.
    Uses embedding cosine similarity to measure deviation.
    Threshold for anomaly: avg_similarity < 0.3
    """
    ANOMALY_THRESHOLD = 0.3

    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()

    @staticmethod
    def _cosine_similarity(vec_a: list, vec_b: list) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        return float(dot / norm) if norm > 0 else 0.0

    def detect_anomaly(self, new_advice: str, historical_advice: list) -> bool:
        """
        Embeds new_advice and each item in historical_advice.
        Computes average cosine similarity.
        Returns: True if anomaly detected (avg_similarity < threshold)
        """
        if not historical_advice:
            return False

        new_embedding = self.embedding_gen.generate(new_advice)

        similarities = []
        for past_advice in historical_advice:
            past_embedding = self.embedding_gen.generate(past_advice)
            sim = self._cosine_similarity(new_embedding, past_embedding)
            similarities.append(sim)

        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity < self.ANOMALY_THRESHOLD

    def flag_conflict(self, query_id: str, new_advice: str, conflicting_advice: str) -> dict:
        """
        Stores ConflictRecord in PostgreSQL.
        Returns: ConflictRecord dict
        """
        record = ConflictRecord.objects.create(
            query_id=query_id,
            new_advice=new_advice,
            conflicting_advice=conflicting_advice
        )
        return {
            'id': str(record.id),
            'query_id': str(record.query_id),
            'new_advice': record.new_advice,
            'conflicting_advice': record.conflicting_advice,
            'flagged_at': record.flagged_at.isoformat()
        }
