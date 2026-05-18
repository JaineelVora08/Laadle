from rest_framework.pagination import CursorPagination


class TimestampPagination(CursorPagination):
    ordering = '-timestamp'
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CreatedAtPagination(CursorPagination):
    ordering = '-created_at'
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SentAtPagination(CursorPagination):
    ordering = '-sent_at'
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
