from django.utils import timezone
from apps.ai_services.embedding_generator import EmbeddingGenerator
from apps.ai_services.rag_engine import RAGEngine
from apps.ai_services.llm_synthesizer import LLMSynthesizer
from apps.ai_services.conflict_consensus_engine import ConflictConsensusEngine
from apps.query_orchestrator.models import Query, SeniorQueryAssignment
from apps.mentor_matching_service.matching_engine import MentorMatchingEngine


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

    def handle_new_query(self, student_id: str, domain_id: str, content: str) -> dict:
        """
        Full pipeline for a new student query:
        1. Generate embedding
        2. Retrieve similar cases (RAG)
        3. Generate provisional LLM answer
        4. Generate follow-up questions
        5. Find matched seniors
        6. Save Query to DB
        7. Store embedding in Pinecone
        8. Create senior assignments
        Returns: QuerySubmitResponse dict
        """
        # Step 1: Generate embedding
        query_embedding = self.embedding_gen.generate_query_embedding(content)

        # Step 2: Retrieve similar past cases
        similar_cases = self.rag_engine.retrieve_similar_cases(query_embedding, domain_id)

        # Step 3: Generate provisional answer
        high_trust = [c for c in similar_cases if c.get('trust_score', 0) > 0.7]
        provisional_answer = self.rag_engine.generate_provisional_response(
            content, similar_cases, high_trust
        )

        # Step 4: Generate follow-up questions using historical patterns
        historical_followups = [
            c['query_text'] for c in similar_cases 
            if c.get('type') == 'resolved_followup'
        ]
        followups = self.synthesizer.generate_followup_questions(
            content, domain_id, historical_followups=historical_followups
        )

        # Step 5: Find matched seniors via mentor matching engine
        matched = self.matching_engine.find_mentors(student_id, domain_id, priority=1)
        matched_senior_ids = [m['senior_id'] for m in matched]

        # Step 6: Save Query to PostgreSQL
        query = Query.objects.create(
            student_id=student_id,
            domain_id=domain_id,
            content=content,
            status='PENDING',
            rag_response=provisional_answer,
            follow_up_questions=followups,
            matched_seniors=[str(sid) for sid in matched_senior_ids]
        )

        # Step 7: Store query embedding in Pinecone for future RAG
        self.embedding_gen.store(
            vector_id=str(query.id),
            embedding=query_embedding,
            metadata={
                'domain_id': str(domain_id),
                'query_text': content,
                'type': 'query'
            }
        )

        # Step 8: Create senior assignments (dispatch to inboxes)
        for senior_id in matched_senior_ids:
            SeniorQueryAssignment.objects.create(
                query=query,
                senior_id=senior_id
            )

        return {
            'query_id': str(query.id),
            'status': query.status,
            'provisional_answer': provisional_answer,
            'follow_up_questions': followups,
            'matched_seniors': [str(sid) for sid in matched_senior_ids],
            'timestamp': query.timestamp.isoformat()
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

        # Generate predicted FAQs based on the senior's actual answer
        # We combine the student query and senior answer for better context
        context = f"Student Q: {query.content}\nSenior A: {advice_content}"
        
        # Also pull historical patterns
        query_embedding = self.embedding_gen.generate_query_embedding(query.content)
        similar_cases = self.rag_engine.retrieve_similar_cases(query_embedding, query.domain_id)
        historical_followups = [
            c['query_text'] for c in similar_cases 
            if c.get('type') == 'resolved_followup'
        ]
        
        predicted_faqs = self.synthesizer.generate_followup_questions(
            context, str(query.domain_id), historical_followups=historical_followups
        )

        # Store predicted FAQs on the query for Step 2
        query.follow_up_questions = predicted_faqs
        query.save()

        return {
            'query_id': str(query.id),
            'status': 'AWAITING_FAQ',
            'predicted_faqs': predicted_faqs
        }

    def handle_senior_faq_response(self, senior_id: str, query_id: str,
                                    faq_answers: list) -> dict:
        """
        Step 2 of Senior Response Flow:
        1. Record FAQ answers
        2. Run conflict detection
        3. Synthesize all responses
        4. Update query as resolved
        5. Store main Q&A AND each FAQ in Pinecone
        6. Update trust score
        """
        query = Query.objects.get(id=query_id)
        assignment = SeniorQueryAssignment.objects.get(query=query, senior_id=senior_id)
        
        # 1. Record FAQ answers
        # faq_answers format: [{"question": "...", "answer": "..."}]
        assignment.answered_followups = faq_answers
        assignment.save()

        # 2. Conflict detection (against other seniors' main advice)
        other_responses = SeniorQueryAssignment.objects.filter(
            query=query, status='RESPONDED'
        ).exclude(senior_id=senior_id)

        historical_advice = [r.advice_content for r in other_responses if r.advice_content]
        conflict_detected = False
        conflict_details = None

        if historical_advice:
            conflict_detected = self.conflict_engine.detect_anomaly(
                assignment.advice_content, historical_advice
            )
            if conflict_detected:
                conflict_record = self.conflict_engine.flag_conflict(
                    query_id=str(query.id),
                    new_advice=assignment.advice_content,
                    conflicting_advice=historical_advice[0]
                )
                conflict_details = (
                    f"Conflict detected between senior {senior_id}'s advice and "
                    f"previous responses. Record ID: {conflict_record['id']}"
                )

        # 3. Gather ALL responses and synthesize
        all_responses = SeniorQueryAssignment.objects.filter(
            query=query, status='RESPONDED'
        )

        advice_list = [
            {
                'content': r.advice_content,
                'senior_id': str(r.senior_id),
                'trust_score': r.trust_score_at_response,
                'similarity_score': r.similarity_score or 0.5
            }
            for r in all_responses
        ]

        synthesis = self.synthesizer.synthesize(query.content, advice_list)

        # 4. Update query as resolved
        query.final_response = synthesis['final_answer']
        query.is_resolved = True
        query.status = 'RESOLVED'
        query.save()

        # 5. Store main Q&A in Pinecone
        qa_embedding = self.embedding_gen.generate(
            f"Q: {query.content}\nA: {synthesis['final_answer']}"
        )
        self.embedding_gen.store(
            vector_id=f"{query.id}_resolved",
            embedding=qa_embedding,
            metadata={
                'domain_id': str(query.domain_id),
                'query_text': query.content,
                'advice_text': synthesis['final_answer'],
                'senior_id': str(senior_id),
                'trust_score': assignment.trust_score_at_response,
                'type': 'resolved_qa'
            }
        )

        # 5b. Store each FAQ in Pinecone for future Quick-Reply
        for i, faq in enumerate(faq_answers):
            faq_embedding = self.embedding_gen.generate(faq['question'])
            self.embedding_gen.store(
                vector_id=f"{query.id}_faq_{i}",
                embedding=faq_embedding,
                metadata={
                    'domain_id': str(query.domain_id),
                    'query_text': faq['question'],
                    'answer_text': faq['answer'],
                    'senior_id': str(senior_id),
                    'trust_score': assignment.trust_score_at_response,
                    'type': 'resolved_followup',
                    'parent_query_id': str(query.id)
                }
            )

        # 6. Update trust score
        try:
            from apps.trust_score_service.calculator import TrustScoreCalculator
            trust_calc = TrustScoreCalculator()
            trust_calc.update_feedback(str(senior_id), {
                'query_id': str(query.id),
                'responded': True,
                'follow_through': len(faq_answers) > 0
            })
        except Exception:
            pass

        # Build contributing_seniors list
        contributing_seniors = []
        for r in all_responses:
            weight = next(
                (a.get('weight', 0.0) for a in synthesis.get('contributing_seniors', [])
                 if str(a.get('senior_id')) == str(r.senior_id)),
                0.0,
            )
            contributing_seniors.append({
                'senior_id': str(r.senior_id),
                'trust_score': float(r.trust_score_at_response or 0),
                'weight': float(weight),
            })

        return {
            'query_id': str(query.id),
            'final_answer': synthesis['final_answer'],
            'agreements': synthesis.get('agreements', []),
            'disagreements': synthesis.get('disagreements', []),
            'conflict_detected': conflict_detected,
            'conflict_details': conflict_details,
            'contributing_seniors': contributing_seniors,
        }

    def handle_followup_question(self, query_id: str, followup_text: str) -> dict:
        """
        3-Step Quick-Reply Logic for Student Follow-ups:
        1. Match against senior's answered FAQs for THIS query
        2. Match against global Pinecone resolved_followups
        3. Fallback to pending senior notification
        """
        query = Query.objects.get(id=query_id)
        followup_embedding = self.embedding_gen.generate_query_embedding(followup_text)

        # Step 1: Match against senior's answered FAQs for THIS query
        assignments = SeniorQueryAssignment.objects.filter(
            query=query, status='RESPONDED'
        )
        
        for assignment in assignments:
            if assignment.answered_followups:
                for faq in assignment.answered_followups:
                    # Simple semantic check (could use local cosine sim if we had vectors)
                    # For now, we'll use the embedding generator to compare
                    faq_embedding = self.embedding_gen.generate_query_embedding(faq['question'])
                    import numpy as np
                    sim = np.dot(followup_embedding, faq_embedding) / (
                        np.linalg.norm(followup_embedding) * np.linalg.norm(faq_embedding)
                    )
                    
                    if sim > 0.85:
                        return {
                            'answer': faq['answer'],
                            'source': 'INSTANT_SENIOR_MATCH',
                            'confidence': float(sim)
                        }

        # Step 2: Global RAG match against other past follow-ups
        similar = self.embedding_gen.query_similar(
            followup_embedding, 
            top_k=1, 
            filter={'type': 'resolved_followup', 'domain_id': str(query.domain_id)}
        )
        
        if similar and similar[0]['score'] > 0.8:
            return {
                'answer': similar[0]['metadata'].get('answer_text'),
                'source': 'PROVISIONAL_RAG_MATCH',
                'confidence': similar[0]['score'],
                'disclaimer': "This is a provisional answer from similar past questions. Your senior will verify it soon."
            }

        # Step 3: Fallback to pending
        return {
            'answer': None,
            'source': 'PENDING_SENIOR',
            'message': "This is a new question. Your senior has been notified and will respond shortly."
        }
