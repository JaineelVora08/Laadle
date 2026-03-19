import logging
from datetime import timedelta

from django.utils import timezone
from apps.ai_services.embedding_generator import EmbeddingGenerator
from apps.ai_services.rag_engine import RAGEngine
from apps.ai_services.llm_synthesizer import LLMSynthesizer
from apps.ai_services.conflict_consensus_engine import ConflictConsensusEngine
from apps.query_orchestrator.models import Query, QueryCluster, SeniorQueryAssignment
from apps.mentor_matching_service.matching_engine import MentorMatchingEngine
from apps.domain_management_service.graph_models import UserNode
from apps.auth_service.models import User


logger = logging.getLogger(__name__)

# Default response window in hours
DEFAULT_RESPONSE_WINDOW_HOURS = 24


class QueryOrchestrator:
    """
    Central coordinator for query processing pipeline.
    Connects: EmbeddingGenerator → RAGEngine → MentorMatching →
              SeniorInbox → ConflictEngine → LLMSynthesizer
    """

    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
        self.rag_engine = RAGEngine()
        self.synthesizer = LLMSynthesizer()
        self.conflict_engine = ConflictConsensusEngine()
        self.matching_engine = MentorMatchingEngine()

    # ── Query-compaction threshold (cosine similarity) ──
    COMPACTION_THRESHOLD = 0.85

    def handle_new_query(self, student_id: str, domain_ids: list, content: str) -> dict:
        """
        Full pipeline for a new student query (multi-domain):
        1.   Generate embedding
        1.5  COMPACTION CHECK — attach to existing cluster if similar pending query exists
        2.   Retrieve similar cases (RAG) across all domains
        3.   Generate provisional LLM answer
        4.   Generate follow-up questions
        5.   Find matched seniors across all domains
        6.   Save Query to DB (as cluster lead)
        7.   Store embedding in Pinecone
        8.   Create senior assignments
        Returns: QuerySubmitResponse dict
        """
        # Step 1: Generate embedding
        query_embedding = self.embedding_gen.generate_query_embedding(content)

        # Step 1.5: COMPACTION CHECK — look for a similar pending query
        similar_pending = self._find_similar_pending_query(query_embedding, domain_ids)
        if similar_pending is not None:
            lead_query, similarity_score = similar_pending
            return self._attach_to_cluster(
                student_id=student_id,
                domain_ids=domain_ids,
                content=content,
                query_embedding=query_embedding,
                lead_query=lead_query,
                similarity_score=similarity_score,
            )

        # Step 2: Retrieve similar past cases across ALL selected domains
        similar_cases = []
        seen_ids = set()
        for domain_id in domain_ids:
            cases = self.rag_engine.retrieve_similar_cases(query_embedding, domain_id)
            for c in cases:
                case_id = c.get('id') or c.get('query_text', '')
                if case_id not in seen_ids:
                    seen_ids.add(case_id)
                    similar_cases.append(c)

        # Step 3: Generate provisional answer using past senior responses
        high_trust = [c for c in similar_cases if c.get('trust_score', 0) > 0.7]

        # Retrieve actual senior responses from resolved similar queries (PostgreSQL)
        past_senior_responses = self.rag_engine.retrieve_past_senior_responses(
            content, domain_ids, top_k=5
        )

        provisional_answer = self.rag_engine.generate_provisional_response(
            content, similar_cases, high_trust,
            past_senior_responses=past_senior_responses
        )

        # Step 4: Generate follow-up questions using historical patterns
        historical_followups = [
            c['query_text'] for c in similar_cases 
            if c.get('type') == 'resolved_followup'
        ]
        # Use the first domain for follow-up question context
        primary_domain_id = domain_ids[0] if domain_ids else ''
        followups = self.synthesizer.generate_followup_questions(
            content, primary_domain_id, historical_followups=historical_followups
        )

        # Step 5: Find matched seniors across ALL selected domains
        all_senior_ids = []
        for domain_id in domain_ids:
            matched = self.matching_engine.find_mentors(student_id, domain_id, priority=1, top_k=5)
            for m in matched:
                sid = str(m['senior_id'])
                if sid not in all_senior_ids:
                    all_senior_ids.append(sid)

        # Also get connected seniors across all domains
        connected_senior_ids = self._get_connected_seniors_for_domains(student_id, domain_ids)
        for senior_id in connected_senior_ids:
            if senior_id not in all_senior_ids:
                all_senior_ids.append(senior_id)

        # Step 6: Create cluster + save Query as cluster lead
        cluster = QueryCluster.objects.create(
            representative_content=content,
            domain_ids=domain_ids,
            status='PENDING',
        )
        now = timezone.now()
        query = Query.objects.create(
            student_id=student_id,
            domain_ids=domain_ids,
            content=content,
            status='PENDING',
            rag_response=provisional_answer,
            follow_up_questions=followups,
            matched_seniors=all_senior_ids,
            cluster=cluster,
            is_cluster_lead=True,
            response_window_hours=DEFAULT_RESPONSE_WINDOW_HOURS,
            response_deadline=now + timedelta(hours=DEFAULT_RESPONSE_WINDOW_HOURS),
        )

        # Step 7: Store query embedding in Pinecone for future RAG
        self.embedding_gen.store(
            vector_id=str(query.id),
            embedding=query_embedding,
            metadata={
                'domain_ids': [str(d) for d in domain_ids],
                'domain_id': str(primary_domain_id),  # backward compat
                'query_text': content,
                'type': 'pending_query',
                'status': 'PENDING',
                'cluster_id': str(cluster.id),
            }
        )

        # Step 8: Create senior assignments (dispatch to inboxes)
        #         Only for seniors that exist in local DB (FK constraint)
        from apps.auth_service.models import User as AuthUser
        for senior_id in all_senior_ids:
            if not AuthUser.objects.filter(id=senior_id).exists():
                import logging
                logging.getLogger(__name__).warning(
                    'Skipping assignment: senior %s not in local DB', senior_id
                )
                continue
            SeniorQueryAssignment.objects.get_or_create(
                query=query,
                senior_id=senior_id
            )

        return {
            'query_id': str(query.id),
            'status': query.status,
            'provisional_answer': provisional_answer,
            'follow_up_questions': followups,
            'matched_seniors': all_senior_ids,
            'timestamp': query.timestamp.isoformat(),
            'cluster_id': str(cluster.id),
            'cluster_student_count': 1,
        }

    @staticmethod
    def _get_connected_seniors_for_domains(student_id: str, domain_ids: list) -> list[str]:
        """Get connected seniors across multiple domains."""
        connected = []
        try:
            student_node = UserNode.nodes.get(uid=str(student_id))
            for senior_node in student_node.mentored_by.all():
                if senior_node.role != 'SENIOR':
                    continue
                if senior_node.uid in connected:
                    continue
                if not User.objects.filter(id=senior_node.uid, role='SENIOR').exists():
                    continue
                connected.append(str(senior_node.uid))
        except Exception:
            return []
        return connected

    # ── Query-compaction helpers ────────────────────────────────

    def _find_similar_pending_query(self, query_embedding: list, domain_ids: list):
        """
        Search Pinecone for pending query vectors similar to *query_embedding*.
        Returns (lead_query, similarity_score) if a match above threshold is found,
        or None otherwise.
        """
        domain_ids_str = [str(d) for d in domain_ids]
        try:
            matches = self.embedding_gen.query_similar(
                embedding=query_embedding,
                top_k=3,
                filter={
                    'type': 'pending_query',
                    'status': 'PENDING',
                }
            )
        except Exception as exc:
            logger.warning('Compaction Pinecone lookup failed: %s', exc)
            return None

        for match in matches:
            if match['score'] < self.COMPACTION_THRESHOLD:
                continue
            # Verify the query is still pending in PostgreSQL
            vector_id = match['id']
            try:
                candidate = Query.objects.get(id=vector_id)
            except (Query.DoesNotExist, Exception):
                continue
            if candidate.status not in ('PENDING', 'IN_PROGRESS'):
                continue
            # Check domain overlap
            candidate_domains = {str(d) for d in (candidate.domain_ids or [])}
            if not candidate_domains & set(domain_ids_str):
                continue
            # Found a valid similar pending query — return its cluster lead
            if candidate.cluster and candidate.is_cluster_lead:
                return (candidate, match['score'])
            # candidate is a child; find the lead
            if candidate.cluster:
                lead = candidate.cluster.queries.filter(is_cluster_lead=True).first()
                if lead:
                    return (lead, match['score'])
            # standalone pending query without cluster yet — use it directly
            return (candidate, match['score'])

        return None

    def _attach_to_cluster(self, student_id: str, domain_ids: list,
                           content: str, query_embedding: list,
                           lead_query, similarity_score: float) -> dict:
        """
        Attach a new student query to an existing cluster instead of
        running the full mentor-matching pipeline.
        Returns the same response shape as handle_new_query.
        """
        # Ensure the lead query has a cluster
        cluster = lead_query.cluster
        if cluster is None:
            cluster = QueryCluster.objects.create(
                representative_content=lead_query.content,
                domain_ids=lead_query.domain_ids,
                status=lead_query.status,
            )
            lead_query.cluster = cluster
            lead_query.is_cluster_lead = True
            lead_query.save(update_fields=['cluster', 'is_cluster_lead'])

        # Widen cluster domain coverage
        existing_domains = {str(d) for d in (cluster.domain_ids or [])}
        new_domains = {str(d) for d in domain_ids}
        merged = list(existing_domains | new_domains)
        if set(merged) != existing_domains:
            cluster.domain_ids = merged
            cluster.save(update_fields=['domain_ids'])

        # Save the child query
        child = Query.objects.create(
            student_id=student_id,
            domain_ids=domain_ids,
            content=content,
            status='PENDING',
            rag_response=lead_query.rag_response,  # reuse provisional answer
            follow_up_questions=lead_query.follow_up_questions,
            matched_seniors=lead_query.matched_seniors,
            cluster=cluster,
            is_cluster_lead=False,
        )

        # Store embedding in Pinecone (so future queries can also match)
        primary_domain_id = domain_ids[0] if domain_ids else ''
        self.embedding_gen.store(
            vector_id=str(child.id),
            embedding=query_embedding,
            metadata={
                'domain_ids': [str(d) for d in domain_ids],
                'domain_id': str(primary_domain_id),
                'query_text': content,
                'type': 'pending_query',
                'status': 'PENDING',
                'cluster_id': str(cluster.id),
            }
        )

        cluster_count = cluster.queries.count()
        logger.info(
            'Query %s attached to cluster %s (lead=%s, score=%.3f, total=%d)',
            child.id, cluster.id, lead_query.id, similarity_score, cluster_count,
        )

        return {
            'query_id': str(child.id),
            'status': child.status,
            'provisional_answer': child.rag_response,
            'follow_up_questions': child.follow_up_questions,
            'matched_seniors': child.matched_seniors,
            'timestamp': child.timestamp.isoformat(),
            'cluster_id': str(cluster.id),
            'cluster_student_count': cluster_count,
        }

    def handle_senior_response(self, senior_id: str, query_id: str,
                                advice_content: str) -> dict:
        """
        Step 1 of Senior Response Flow:
        1. Record the senior's main advice
        2. Generate predicted FAQ follow-ups based on this advice
        3. Return FAQs to senior for Step 2
        """
        query = Query.objects.get(id=query_id)
        assignment = SeniorQueryAssignment.objects.get(query=query, senior_id=senior_id)
        
        # Save main advice
        assignment.advice_content = advice_content
        assignment.status = 'RESPONDED'
        assignment.responded_at = timezone.now()
        
        from apps.auth_service.models import User
        senior = User.objects.get(id=senior_id)
        assignment.trust_score_at_response = senior.trust_score
        assignment.save()

        # Update consistency score based on reply time
        reply_time_hours = (assignment.responded_at - assignment.assigned_at).total_seconds() / 3600.0
        from apps.trust_score_service.calculator import TrustScoreCalculator
        trust_calc = TrustScoreCalculator()
        try:
            trust_calc.update_feedback(senior_id, {
                'days_inactive': 0,
                'reply_time_hours': reply_time_hours,
            })
        except Exception:
            pass

        # Generate predicted FAQs based on the senior's actual answer
        # We combine the student query and senior answer for better context
        context = f"Student Q: {query.content}\nSenior A: {advice_content}"
        
        # Also pull historical patterns across all domains
        query_embedding = self.embedding_gen.generate_query_embedding(query.content)
        all_similar_cases = []
        for did in query.domain_ids:
            all_similar_cases.extend(
                self.rag_engine.retrieve_similar_cases(query_embedding, did)
            )
        historical_followups = [
            c['query_text'] for c in all_similar_cases 
            if c.get('type') == 'resolved_followup'
        ]
        
        primary_domain_id = query.domain_ids[0] if query.domain_ids else ''
        predicted_faqs = self.synthesizer.generate_followup_questions(
            context, str(primary_domain_id), historical_followups=historical_followups
        )

        # Store predicted FAQs on the query for Step 2
        query.follow_up_questions = predicted_faqs
        query.save()

        return {
            'query_id': str(query.id),
            'status': 'AWAITING_FAQ',
            'predicted_faqs': predicted_faqs
        }

    # Minimum total responses required before minority penalization kicks in.
    # If only 2 seniors responded, a 1-vs-1 split is too thin to penalize.
    MIN_RESPONSES_FOR_PENALTY = 3

    def handle_senior_faq_response(self, senior_id: str, query_id: str,
                                    faq_answers: list) -> dict:
        """
        Step 2 of Senior Response Flow (decoupled from resolution):
        1. Record FAQ answers and mark this assignment as faq_completed
        2. Store each FAQ in Pinecone for future Quick-Reply
        3. Check if ALL assigned seniors have completed — if so, auto-finalize
        Does NOT trigger majority/synthesis/trust logic directly.
        """
        query = Query.objects.get(id=query_id)
        assignment = SeniorQueryAssignment.objects.get(query=query, senior_id=senior_id)

        # 1. Record FAQ answers
        assignment.answered_followups = faq_answers
        assignment.faq_completed = True
        assignment.save(update_fields=['answered_followups', 'faq_completed'])

        # 2. Store each FAQ in Pinecone for future Quick-Reply
        for i, faq in enumerate(faq_answers):
            try:
                faq_embedding = self.embedding_gen.generate(faq.get('question', ''))
                self.embedding_gen.store(
                    vector_id=f"{query.id}_faq_{senior_id}_{i}",
                    embedding=faq_embedding,
                    metadata={
                        'domain_ids': query.domain_ids,
                        'domain_id': str(query.domain_ids[0]) if query.domain_ids else '',
                        'query_text': faq.get('question', ''),
                        'answer_text': faq.get('answer', ''),
                        'senior_id': str(senior_id),
                        'trust_score': assignment.trust_score_at_response,
                        'type': 'resolved_followup',
                        'parent_query_id': str(query.id),
                    }
                )
            except Exception as exc:
                logger.warning('Failed storing FAQ vector for query %s item %s: %s', query.id, i, exc)

        # Update query status to IN_PROGRESS once at least one senior completes
        if query.status == 'PENDING':
            query.status = 'IN_PROGRESS'
            query.save(update_fields=['status'])

        # 3. Check if ALL assigned seniors have completed both steps
        total_assigned = query.assignments.count()
        total_faq_done = query.assignments.filter(faq_completed=True).count()
        total_responded = query.assignments.filter(status='RESPONDED').count()

        auto_finalized = False
        if total_faq_done == total_assigned and total_assigned > 0:
            # All seniors responded — auto-finalize
            result = self.finalize_query(str(query.id), triggered_by='ALL_RESPONDED')
            auto_finalized = True
            return {
                **result,
                'auto_finalized': True,
                'finalized_by': 'ALL_RESPONDED',
            }

        return {
            'query_id': str(query.id),
            'status': 'AWAITING_MORE_RESPONSES',
            'responses_received': total_responded,
            'faq_completed_count': total_faq_done,
            'total_assigned': total_assigned,
            'auto_finalized': False,
            'message': (
                f'Response recorded. {total_faq_done}/{total_assigned} seniors have '
                f'completed their responses. Waiting for more or student finalization.'
            ),
        }

    def get_query_response_status(self, query_id: str) -> dict:
        """
        Returns the current response status for a query including counts,
        deadline info, and whether early finalization is available.
        """
        query = Query.objects.get(id=query_id)
        total_assigned = query.assignments.count()
        total_responded = query.assignments.filter(status='RESPONDED').count()
        total_faq_done = query.assignments.filter(faq_completed=True).count()

        now = timezone.now()
        deadline = query.response_deadline
        deadline_passed = deadline and now >= deadline
        time_remaining = None
        if deadline and not deadline_passed:
            remaining = deadline - now
            time_remaining = max(0, remaining.total_seconds())

        can_finalize = (
            total_faq_done >= 1
            and query.status != 'RESOLVED'
            and query.finalized_by is None
        )

        return {
            'query_id': str(query.id),
            'status': query.status,
            'total_assigned': total_assigned,
            'responses_received': total_responded,
            'faq_completed_count': total_faq_done,
            'response_deadline': deadline.isoformat() if deadline else None,
            'deadline_passed': deadline_passed,
            'time_remaining_seconds': time_remaining,
            'can_finalize': can_finalize,
            'finalized_by': query.finalized_by,
        }

    def finalize_query(self, query_id: str, triggered_by: str = 'STUDENT') -> dict:
        """
        Majority-based decision mechanism. Called when:
        - Student clicks "Finalize Now" (triggered_by='STUDENT')
        - Response deadline expires (triggered_by='DEADLINE')
        - All assigned seniors completed (triggered_by='ALL_RESPONDED')

        Steps:
        1. Gather all completed responses
        2. LLM categorization into opinion groups
        3. Determine majority (largest cluster) — majority from those who answered
        4. Boost majority seniors' alignment, penalize minority
        5. RAG-based anomaly detection
        6. Synthesize final answer from MAJORITY group only
        7. Mark query resolved, propagate to cluster
        8. Store resolved Q&A in Pinecone
        """
        query = Query.objects.get(id=query_id)

        if query.status == 'RESOLVED':
            return {
                'query_id': str(query.id),
                'error': 'Query already resolved.',
                'final_answer': query.final_response,
            }

        # 1. Gather ALL completed responses (faq_completed = True)
        completed_assignments = SeniorQueryAssignment.objects.filter(
            query=query, status='RESPONDED', faq_completed=True
        )

        if not completed_assignments.exists():
            # Fallback: also consider seniors who responded with advice but didn't do FAQ
            completed_assignments = SeniorQueryAssignment.objects.filter(
                query=query, status='RESPONDED'
            )

        if not completed_assignments.exists():
            return {
                'query_id': str(query.id),
                'error': 'No senior responses available to finalize.',
            }

        advice_list = [
            {
                'content': r.advice_content,
                'senior_id': str(r.senior_id),
                'trust_score': r.trust_score_at_response or 0.5,
                'similarity_score': r.similarity_score or 0.5,
            }
            for r in completed_assignments
        ]

        # 2. LLM categorization into opinion groups
        try:
            categorization = self.synthesizer.categorize_advice(query.content, advice_list)
        except Exception as exc:
            logger.warning('categorize_advice failed for query %s: %s', query.id, exc)
            categorization = {}

        valid_senior_ids = {a['senior_id'] for a in advice_list}
        raw_groups = categorization.get('groups') if isinstance(categorization, dict) else []
        groups = []
        if isinstance(raw_groups, list):
            for i, group in enumerate(raw_groups, 1):
                if not isinstance(group, dict):
                    continue
                senior_ids = [
                    str(sid) for sid in group.get('senior_ids', [])
                    if str(sid) in valid_senior_ids
                ]
                if not senior_ids:
                    continue
                groups.append({
                    'label': group.get('label') or f'Group {i}',
                    'senior_ids': senior_ids,
                    'avg_trust': float(group.get('avg_trust', 0.0) or 0.0),
                })

        if not groups and advice_list:
            groups = [{
                'label': 'All responses',
                'senior_ids': [a['senior_id'] for a in advice_list],
                'avg_trust': sum(a.get('trust_score', 0.5) for a in advice_list) / len(advice_list),
            }]

        # 3. Determine majority: largest cluster by count, tiebreak by avg_trust
        groups.sort(key=lambda g: (len(g['senior_ids']), g.get('avg_trust', 0.0)), reverse=True)
        majority_group = groups[0] if groups else None
        minority_groups = groups[1:] if len(groups) > 1 else []

        # 4. Trust score updates — only for seniors who answered
        total_responses = len(advice_list)
        majority_count = len(majority_group.get('senior_ids', [])) if majority_group else 0
        majority_senior_ids = set(majority_group.get('senior_ids', [])) if majority_group else set()

        from apps.trust_score_service.calculator import TrustScoreCalculator
        trust_calc = TrustScoreCalculator()

        # Boost majority seniors' alignment
        if majority_group:
            for sid in majority_group.get('senior_ids', []):
                try:
                    trust_calc.update_feedback(sid, {
                        'is_majority': True,
                        'M': majority_count,
                        'm': majority_count,
                        'N': total_responses,
                    })
                except Exception:
                    pass

        # Penalize minority seniors — only if enough responses
        if total_responses >= self.MIN_RESPONSES_FOR_PENALTY:
            for mg in minority_groups:
                minority_count = len(mg.get('senior_ids', []))
                for sid in mg.get('senior_ids', []):
                    try:
                        trust_calc.update_feedback(sid, {
                            'is_majority': False,
                            'M': majority_count,
                            'm': minority_count,
                            'N': total_responses,
                        })
                    except Exception:
                        pass

        # 5. RAG-based historical anomaly detection
        anomaly_detected = False
        anomaly_warning = None

        if majority_group:
            try:
                majority_advice_texts = [
                    a['content'] for a in advice_list
                    if a['senior_id'] in majority_senior_ids
                ]
                majority_combined = ' '.join(majority_advice_texts)

                query_embedding = self.embedding_gen.generate_query_embedding(query.content)
                similar_cases = []
                for did in query.domain_ids:
                    similar_cases.extend(
                        self.rag_engine.retrieve_similar_cases(query_embedding, did)
                    )
                historical_advice_texts = [
                    c['advice_text'] for c in similar_cases
                    if c.get('advice_text') and c.get('type') == 'resolved_qa'
                ]

                if historical_advice_texts:
                    anomaly_detected = self.conflict_engine.detect_anomaly(
                        majority_combined, historical_advice_texts
                    )
                    if anomaly_detected:
                        conflict_record = self.conflict_engine.flag_conflict(
                            query_id=str(query.id),
                            new_advice=majority_combined,
                            conflicting_advice=historical_advice_texts[0],
                        )
                        anomaly_warning = (
                            f"The majority advice differs significantly from historical answers "
                            f"to similar questions. This has been flagged for review "
                            f"(Record ID: {conflict_record['id']})."
                        )
            except Exception as exc:
                logger.warning('Anomaly detection skipped for query %s: %s', query.id, exc)

        # 6. Synthesize final answer from MAJORITY group responses only
        majority_advice = [
            a for a in advice_list if a['senior_id'] in majority_senior_ids
        ] if majority_senior_ids else advice_list

        synthesis = self.synthesizer.synthesize(query.content, majority_advice)

        # 7. Mark query resolved
        query.final_response = synthesis['final_answer']
        query.is_resolved = True
        query.status = 'RESOLVED'
        query.finalized_by = triggered_by
        query.save(update_fields=[
            'final_response', 'is_resolved', 'status', 'finalized_by'
        ])

        # 7.5 Propagate to cluster
        if query.cluster:
            cluster = query.cluster
            cluster.final_response = synthesis['final_answer']
            cluster.status = 'RESOLVED'
            cluster.save(update_fields=['final_response', 'status'])

            Query.objects.filter(
                cluster=cluster, is_cluster_lead=False,
            ).update(
                final_response=synthesis['final_answer'],
                is_resolved=True,
                status='RESOLVED',
                finalized_by=triggered_by,
            )
            logger.info(
                'Cluster %s resolved (%s) — propagated to %d child queries',
                cluster.id, triggered_by,
                cluster.queries.filter(is_cluster_lead=False).count(),
            )

        # 8. Store resolved Q&A in Pinecone
        try:
            qa_embedding = self.embedding_gen.generate(
                f"Q: {query.content}\nA: {synthesis['final_answer']}"
            )
            self.embedding_gen.store(
                vector_id=f"{query.id}_resolved",
                embedding=qa_embedding,
                metadata={
                    'domain_ids': query.domain_ids,
                    'domain_id': str(query.domain_ids[0]) if query.domain_ids else '',
                    'query_text': query.content,
                    'advice_text': synthesis['final_answer'],
                    'type': 'resolved_qa',
                    'status': 'RESOLVED',
                    'cluster_id': str(query.cluster_id) if query.cluster_id else '',
                    'finalized_by': triggered_by,
                    'majority_senior_ids': list(majority_senior_ids),
                }
            )
        except Exception as exc:
            logger.warning('Failed storing resolved QA vector for query %s: %s', query.id, exc)

        # Build contributing_seniors — only majority group members
        contributing_seniors = []
        for r in completed_assignments:
            sid = str(r.senior_id)
            in_majority = sid in majority_senior_ids
            weight = next(
                (a.get('weight', 0.0) for a in synthesis.get('contributing_seniors', [])
                 if str(a.get('senior_id')) == sid),
                0.0,
            )
            contributing_seniors.append({
                'senior_id': sid,
                'trust_score': float(r.trust_score_at_response or 0),
                'weight': float(weight),
                'in_majority': in_majority,
            })

        return {
            'query_id': str(query.id),
            'final_answer': synthesis['final_answer'],
            'agreements': synthesis.get('agreements', []),
            'disagreements': synthesis.get('disagreements', []),
            'majority_label': majority_group.get('label') if majority_group else None,
            'opinion_groups': groups,
            'anomaly_detected': anomaly_detected,
            'anomaly_warning': anomaly_warning,
            'conflict_detected': anomaly_detected,
            'conflict_details': anomaly_warning,
            'contributing_seniors': contributing_seniors,
            'finalized_by': triggered_by,
            'total_responses_considered': total_responses,
            'majority_count': majority_count,
        }

    def check_and_finalize_expired_queries(self) -> list:
        """
        Batch job: finds all unresolved queries past their response_deadline
        that have at least 1 completed response, and auto-finalizes them.
        Returns list of finalized query IDs.
        """
        now = timezone.now()
        expired_queries = Query.objects.filter(
            status__in=['PENDING', 'IN_PROGRESS'],
            is_cluster_lead=True,
            finalized_by__isnull=True,
            response_deadline__lte=now,
        )

        finalized_ids = []
        for query in expired_queries:
            has_responses = query.assignments.filter(status='RESPONDED').exists()
            if not has_responses:
                logger.info(
                    'Query %s deadline passed but no responses — skipping auto-finalize.',
                    query.id,
                )
                continue

            try:
                self.finalize_query(str(query.id), triggered_by='DEADLINE')
                finalized_ids.append(str(query.id))
                logger.info('Auto-finalized expired query %s', query.id)
            except Exception as exc:
                logger.error('Failed to auto-finalize query %s: %s', query.id, exc)

        return finalized_ids

    # Similarity thresholds for follow-up matching
    FAQ_LOCAL_THRESHOLD = 0.85   # Same-query FAQ match
    FAQ_GLOBAL_THRESHOLD = 0.80  # Cross-query FAQ match from RAG

    def handle_followup_question(self, query_id: str, followup_text: str) -> dict:
        """
        3-Step Quick-Reply Logic for Student Follow-ups:
        1. Match against this query's FAQ vectors in Pinecone (parent_query_id filter)
        2. Match against global Pinecone resolved_followups across ALL domains
        3. Fallback to pending senior notification
        """
        query = Query.objects.get(id=query_id)
        followup_embedding = self.embedding_gen.generate_query_embedding(followup_text)

        # Step 1: Match against this query's stored FAQ vectors in Pinecone.
        # FAQs are stored with type='resolved_followup' and parent_query_id
        # in handle_senior_faq_response — one Pinecone query replaces N embed calls.
        local_matches = self.embedding_gen.query_similar(
            followup_embedding,
            top_k=1,
            filter={
                'type': 'resolved_followup',
                'parent_query_id': str(query_id),
            }
        )

        if local_matches and local_matches[0]['score'] > self.FAQ_LOCAL_THRESHOLD:
            return {
                'answer': local_matches[0]['metadata'].get('answer_text'),
                'source': 'INSTANT_SENIOR_MATCH',
                'confidence': local_matches[0]['score'],
            }

        # Step 2: Global RAG match across ALL query domains (multi-domain filter)
        domain_ids_str = [str(d) for d in query.domain_ids] if query.domain_ids else []
        domain_filter = (
            {'domain_id': {'$in': domain_ids_str}} if domain_ids_str else {}
        )
        global_matches = self.embedding_gen.query_similar(
            followup_embedding,
            top_k=1,
            filter={
                'type': 'resolved_followup',
                **domain_filter,
            }
        )

        if global_matches and global_matches[0]['score'] > self.FAQ_GLOBAL_THRESHOLD:
            return {
                'answer': global_matches[0]['metadata'].get('answer_text'),
                'source': 'PROVISIONAL_RAG_MATCH',
                'confidence': global_matches[0]['score'],
                'disclaimer': "This is a provisional answer from similar past questions. Your senior will verify it soon."
            }

        # Step 3: Fallback to pending
        return {
            'answer': None,
            'source': 'PENDING_SENIOR',
            'message': "This is a new question. Your senior has been notified and will respond shortly."
        }
