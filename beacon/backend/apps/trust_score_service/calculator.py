import logging
import math

from django.db import transaction

from apps.auth_service.models import TrustMetrics, User
from apps.domain_management_service.graph_models import UserNode


logger = logging.getLogger(__name__)


class TrustScoreCalculator:
    """
    Computes and updates trust scores for seniors.
    Reads from TrustMetrics (PostgreSQL), writes to both PostgreSQL and Neo4j.
    Formula weights: feedback=0.25, follow_through=0.25, consistency=0.20,
                     alignment=0.15, achievement=0.15
    """

    DEFAULT_TOTAL_TRUST = 40.0
    DEFAULT_COMPONENT_SCORE = 50.0

    @staticmethod
    def _clamp_score(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def _update_feedback_ema(self, old_F: float, new_rating: float, alpha: float = 0.15) -> float:
        new_F = (alpha * new_rating) + ((1 - alpha) * old_F)
        return self._clamp_score(new_F)

    def _update_success_rate(self, n_success: int, n_total: int, k: int = 2) -> float:
        score = ((n_success + k) / (n_total + 2 * k)) * 100
        return self._clamp_score(score)

    def _update_consistency(
        self,
        old_C: float,
        days_inactive: int,
        reply_time_hours: float,
        lambda_decay: float = 0.05,
    ) -> float:
        decayed_C = old_C * math.exp(-lambda_decay * days_inactive)
        if reply_time_hours < 2:
            gamma_reply = 5.0
        elif reply_time_hours > 48:
            gamma_reply = 1.0
        else:
            gamma_reply = 3.0
        return self._clamp_score(decayed_C + gamma_reply)

    def _update_alignment(
        self,
        old_A: float,
        is_majority: bool,
        M: int,
        m: int,
        N: int,
        delta_bonus: float = 2,
        rho: float = 10,
    ) -> float:
        if is_majority:
            return self._clamp_score(old_A + delta_bonus)
        isolation_factor = (M - m) / N
        return self._clamp_score(old_A - (rho * isolation_factor))

    def _cosine_similarity(self, vector_a: list[float], vector_b: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        magnitude_a = math.sqrt(sum(a * a for a in vector_a))
        magnitude_b = math.sqrt(sum(b * b for b in vector_b))
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        cosine_value = dot_product / (magnitude_a * magnitude_b)
        return max(-1.0, min(1.0, cosine_value))

    def _compute_interaction_performance(
        self,
        F: float,
        S: float,
        C: float,
        A: float,
        contextual_V: float,
        weights: tuple[float, float, float, float, float] = (0.2, 0.3, 0.15, 0.2, 0.15),
    ) -> float:
        performance = (
            weights[0] * F
            + weights[1] * S
            + weights[2] * C
            + weights[3] * A
            + weights[4] * contextual_V
        )
        return self._clamp_score(performance)

    def _update_total_trust_score(
        self,
        current_T: float,
        P: float,
        alpha_growth: float = 0.1,
        beta_penalty: float = 0.15,
    ) -> float:
        if P > current_T:
            resistance = (100 - current_T) / 100
            new_T = current_T + alpha_growth * (P - current_T) * resistance
        else:
            new_T = current_T - beta_penalty * (current_T - P)
        return self._clamp_score(new_T)

    def _default_metric_values(self) -> dict:
        return {
            'student_feedback_score': self.DEFAULT_COMPONENT_SCORE,
            'follow_through_rate': self.DEFAULT_COMPONENT_SCORE,
            'consistency_score': self.DEFAULT_COMPONENT_SCORE,
            'alignment_score': self.DEFAULT_COMPONENT_SCORE,
            'achievement_weight': self.DEFAULT_COMPONENT_SCORE,
            'n_success': 0,
            'n_total': 0,
        }

    def _bootstrap_metrics_if_needed(self, metrics: TrustMetrics) -> bool:
        component_values = (
            metrics.student_feedback_score,
            metrics.follow_through_rate,
            metrics.consistency_score,
            metrics.alignment_score,
            metrics.achievement_weight,
        )
        is_uninitialized = all(value == 0 for value in component_values) and metrics.n_success == 0 and metrics.n_total == 0
        if not is_uninitialized:
            return False

        defaults = self._default_metric_values()
        metrics.student_feedback_score = defaults['student_feedback_score']
        metrics.follow_through_rate = defaults['follow_through_rate']
        metrics.consistency_score = defaults['consistency_score']
        metrics.alignment_score = defaults['alignment_score']
        metrics.achievement_weight = defaults['achievement_weight']
        metrics.n_success = defaults['n_success']
        metrics.n_total = defaults['n_total']
        metrics.save()
        return True

    def _mirror_to_neo4j(self, senior_id: str, trust_score: float) -> None:
        try:
            user_node = UserNode.nodes.get(uid=senior_id)
            user_node.trust_score = trust_score
            user_node.save()
        except Exception as exc:
            logger.warning('Neo4j trust score sync failed for senior %s: %s', senior_id, exc)

    def compute(self, senior_id: str) -> float:
        """
        Fetches TrustMetrics for senior_id, applies weighted formula.
        Writes result back to User.trust_score (PostgreSQL) and UserNode.trust_score (Neo4j).
        Returns: new trust score float
        """
        with transaction.atomic():
            senior = User.objects.select_for_update().get(id=senior_id, role='SENIOR')
            metrics, created = TrustMetrics.objects.select_for_update().get_or_create(
                senior=senior,
                defaults=self._default_metric_values(),
            )

            if created:
                senior.trust_score = self.DEFAULT_TOTAL_TRUST
                senior.save(update_fields=['trust_score'])
            elif senior.trust_score <= 0:
                senior.trust_score = self.DEFAULT_TOTAL_TRUST
                senior.save(update_fields=['trust_score'])

            self._bootstrap_metrics_if_needed(metrics)

            F = self._clamp_score(metrics.student_feedback_score)
            S = self._clamp_score(metrics.follow_through_rate)
            C = self._clamp_score(metrics.consistency_score)
            A = self._clamp_score(metrics.alignment_score)
            contextual_V = self._clamp_score(metrics.achievement_weight)

            P = self._compute_interaction_performance(F, S, C, A, contextual_V)
            new_total = self._update_total_trust_score(senior.trust_score, P)

            senior.trust_score = new_total
            senior.save(update_fields=['trust_score'])

        self._mirror_to_neo4j(str(senior.id), new_total)
        return float(new_total)

    def update_feedback(self, senior_id: str, feedback_data: dict) -> dict:
        """
        Updates individual TrustMetrics fields after a query is resolved.
        Triggers compute() after update.
        Returns: { senior_id, new_trust_score }
        """
        with transaction.atomic():
            senior = User.objects.select_for_update().get(id=senior_id, role='SENIOR')
            metrics, _ = TrustMetrics.objects.select_for_update().get_or_create(
                senior=senior,
                defaults=self._default_metric_values(),
            )

            self._bootstrap_metrics_if_needed(metrics)

            if senior.trust_score <= 0:
                senior.trust_score = self.DEFAULT_TOTAL_TRUST
                senior.save(update_fields=['trust_score'])

            if 'student_feedback_score' in feedback_data:
                metrics.student_feedback_score = self._update_feedback_ema(
                    metrics.student_feedback_score,
                    float(feedback_data['student_feedback_score']),
                )

            if 'n_success' in feedback_data:
                metrics.n_success = int(feedback_data['n_success'])
            if 'n_total' in feedback_data:
                metrics.n_total = int(feedback_data['n_total'])

            if metrics.n_success > metrics.n_total:
                metrics.n_success = metrics.n_total

            if 'follow_through_rate' in feedback_data:
                metrics.follow_through_rate = self._clamp_score(feedback_data['follow_through_rate'])
            else:
                metrics.follow_through_rate = self._update_success_rate(metrics.n_success, metrics.n_total)

            if 'days_inactive' in feedback_data and 'reply_time_hours' in feedback_data:
                metrics.consistency_score = self._update_consistency(
                    metrics.consistency_score,
                    int(feedback_data['days_inactive']),
                    float(feedback_data['reply_time_hours']),
                )

            if 'is_majority' in feedback_data:
                is_majority = bool(feedback_data['is_majority'])
                if is_majority:
                    metrics.alignment_score = self._update_alignment(
                        metrics.alignment_score,
                        True,
                        1,
                        1,
                        1,
                    )
                else:
                    metrics.alignment_score = self._update_alignment(
                        metrics.alignment_score,
                        False,
                        int(feedback_data['M']),
                        int(feedback_data['m']),
                        int(feedback_data['N']),
                    )

            if 'achievement_weight' in feedback_data:
                metrics.achievement_weight = self._clamp_score(feedback_data['achievement_weight'])

            query_embedding = feedback_data.get('query_embedding')
            achievement_embedding = feedback_data.get('achievement_embedding')
            if query_embedding is not None and achievement_embedding is not None:
                cosine_value = self._cosine_similarity(query_embedding, achievement_embedding)
                contextual_V = self._clamp_score(100 * cosine_value)
                metrics.achievement_weight = contextual_V

            if 'contextual_V' in feedback_data:
                metrics.achievement_weight = self._clamp_score(feedback_data['contextual_V'])

            metrics.save()

        new_score = self.compute(senior_id)
        return {
            'senior_id': senior_id,
            'new_trust_score': new_score,
        }
