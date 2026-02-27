class TrustScoreCalculator:
    """
    Computes and updates trust scores for seniors.
    Reads from TrustMetrics (PostgreSQL), writes to both PostgreSQL and Neo4j.
    Formula weights: feedback=0.25, follow_through=0.25, consistency=0.20,
                     alignment=0.15, achievement=0.15
    """

    def compute(self, senior_id: str) -> float:
        """
        Fetches TrustMetrics for senior_id, applies weighted formula.
        Writes result back to User.trust_score (PostgreSQL) and UserNode.trust_score (Neo4j).
        Returns: new trust score float
        """
        pass

    def update_feedback(self, senior_id: str, feedback_data: dict) -> dict:
        """
        Updates individual TrustMetrics fields after a query is resolved.
        Triggers compute() after update.
        Returns: { senior_id, new_trust_score }
        """
        pass
