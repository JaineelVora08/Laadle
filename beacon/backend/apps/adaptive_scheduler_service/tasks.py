from celery import shared_task


@shared_task
def redistribute_tasks(senior_id: str):
    """
    Celery task: triggered when senior.active_load exceeds threshold.
    Finds next available senior via mentor_matching_service.
    Reassigns pending queries from overloaded senior.
    """
    pass


@shared_task
def broadcast_cold_start(query_id: str, domain_id: str):
    """
    Celery task: triggered when no mentor match found.
    Sends notification to ALL available seniors for the given domain.
    """
    pass
