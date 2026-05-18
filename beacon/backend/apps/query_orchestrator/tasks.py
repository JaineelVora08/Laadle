import logging
from datetime import timedelta

from celery import chain, group, shared_task
from django.core.cache import cache
from django.utils import timezone

from apps.ai_services.embedding_generator import EmbeddingGenerator
from apps.ai_services.rag_engine import RAGEngine
from apps.ai_services.llm_synthesizer import LLMSynthesizer
from apps.auth_service.models import User
from apps.mentor_matching_service.matching_engine import MentorMatchingEngine
from apps.query_orchestrator.models import Query, QueryCluster, SeniorQueryAssignment
from apps.realtime.utils import push_to_user

logger = logging.getLogger(__name__)


@shared_task(queue='embedding_queue')
def step1_embed(query_id):
    query = Query.objects.get(id=query_id)
    embedding_gen = EmbeddingGenerator()
    vec = embedding_gen.generate_query_embedding(query.content)
    cache.set(f'qemb:{query_id}', vec, timeout=600)
    primary_domain_id = query.domain_ids[0] if query.domain_ids else ''
    embedding_gen.store(str(query.id), vec, {
        'domain_ids': [str(d) for d in query.domain_ids],
        'domain_id': str(primary_domain_id),
        'query_text': query.content,
        'type': 'pending_query',
        'status': query.status,
        'cluster_id': str(query.cluster_id) if query.cluster_id else '',
    })
    return str(query_id)


@shared_task(queue='llm_queue', rate_limit='20/m')
def step2_provisional_and_followups(query_id):
    query = Query.objects.get(id=query_id)
    vec = cache.get(f'qemb:{query_id}')
    if vec is None:
        vec = EmbeddingGenerator().generate_query_embedding(query.content)

    rag = RAGEngine()
    similar_cases = []
    seen_ids = set()
    for domain_id in query.domain_ids:
        for case in rag.retrieve_similar_cases(vec, domain_id):
            case_id = case.get('id') or case.get('query_text', '')
            if case_id and case_id not in seen_ids:
                seen_ids.add(case_id)
                similar_cases.append(case)

    primary_domain_id = query.domain_ids[0] if query.domain_ids else ''
    result = LLMSynthesizer().generate_provisional_and_followups(
        query.content,
        primary_domain_id,
        similar_cases=similar_cases,
        past_senior_responses=rag.retrieve_past_senior_responses(
            query.content,
            query.domain_ids,
            top_k=5,
        ),
    )

    query.rag_response = result.get('answer', '')
    query.follow_up_questions = result.get('followups', [])
    query.status = 'IN_PROGRESS'
    query.save(update_fields=['rag_response', 'follow_up_questions', 'status'])
    cache.set(f'qstatus:{query_id}', {
        'status': query.status,
        'provisional_answer': query.rag_response,
        'follow_up_questions': query.follow_up_questions,
    }, timeout=60)
    push_to_user(str(query.student_id), {
        'type': 'provisional_ready',
        'query_id': str(query_id),
        'answer': query.rag_response,
        'followups': query.follow_up_questions,
    })
    return str(query_id)


@shared_task(queue='default')
def step3_match_mentors(query_id):
    query = Query.objects.get(id=query_id)
    engine = MentorMatchingEngine()
    matched_senior_ids = []
    for domain_id in query.domain_ids:
        for mentor in engine.find_mentors(str(query.student_id), str(domain_id), priority=1, top_k=5):
            senior_id = str(mentor['senior_id'])
            if senior_id not in matched_senior_ids:
                matched_senior_ids.append(senior_id)

    existing_seniors = {
        str(senior_id)
        for senior_id in User.objects.filter(
            id__in=matched_senior_ids,
            role='SENIOR',
        ).values_list('id', flat=True)
    }
    for senior_id in matched_senior_ids:
        if senior_id in existing_seniors:
            SeniorQueryAssignment.objects.get_or_create(query=query, senior_id=senior_id)

    query.matched_seniors = matched_senior_ids
    query.save(update_fields=['matched_seniors'])
    for senior_id in matched_senior_ids:
        push_to_user(senior_id, {'type': 'new_assignment', 'query_id': str(query.id)})
    return matched_senior_ids


@shared_task(queue='llm_queue', rate_limit='20/m')
def process_senior_advice(assignment_id):
    assignment = SeniorQueryAssignment.objects.select_related('query', 'senior').get(id=assignment_id)
    query = assignment.query
    from apps.query_orchestrator.orchestrator import QueryOrchestrator

    orchestrator = QueryOrchestrator()
    context = f'Student Q: {query.content}\nSenior A: {assignment.advice_content}'
    vec = orchestrator.embedding_gen.generate_query_embedding(query.content)
    historical_followups = []
    for domain_id in query.domain_ids:
        historical_followups.extend([
            c['query_text']
            for c in orchestrator.rag_engine.retrieve_similar_cases(vec, domain_id)
            if c.get('type') == 'resolved_followup'
        ])
    predicted_faqs = orchestrator.synthesizer.generate_followup_questions(
        context,
        str(query.domain_ids[0]) if query.domain_ids else '',
        historical_followups=historical_followups,
    )
    query.follow_up_questions = predicted_faqs
    query.save(update_fields=['follow_up_questions'])
    push_to_user(str(assignment.senior_id), {
        'type': 'senior_faqs_ready',
        'query_id': str(query.id),
        'predicted_faqs': predicted_faqs,
    })
    return predicted_faqs


@shared_task(queue='default')
def finalize_query_async(query_id, triggered_by='ALL_RESPONDED'):
    from apps.query_orchestrator.orchestrator import QueryOrchestrator

    result = QueryOrchestrator().finalize_query(str(query_id), triggered_by=triggered_by)
    try:
        query = Query.objects.get(id=query_id)
        push_to_user(str(query.student_id), {
            'type': 'query_resolved',
            'query_id': str(query_id),
            'final_answer': result.get('final_answer'),
        })
    except Query.DoesNotExist:
        pass
    return result


@shared_task(queue='default')
def sync_active_load_to_neo4j(senior_id, new_load):
    from apps.domain_management_service.graph_models import UserNode

    user_node = UserNode.nodes.get(uid=str(senior_id))
    user_node.active_load = int(new_load)
    user_node.save()


def create_pending_query(student_id: str, domain_ids: list[str], content: str) -> Query:
    cluster = QueryCluster.objects.create(
        representative_content=content,
        domain_ids=domain_ids,
        status='PENDING',
    )
    now = timezone.now()
    return Query.objects.create(
        student_id=student_id,
        domain_ids=domain_ids,
        content=content,
        status='PENDING',
        cluster=cluster,
        is_cluster_lead=True,
        response_deadline=now + timedelta(hours=24),
    )


def dispatch_pipeline(query_id):
    chain(
        step1_embed.s(str(query_id)),
        group(
            step2_provisional_and_followups.s(),
            step3_match_mentors.s(),
        ),
    ).apply_async()
