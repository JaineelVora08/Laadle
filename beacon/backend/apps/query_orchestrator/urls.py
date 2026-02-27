from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.SubmitQueryView.as_view(), name='query-submit'),
    path('<str:query_id>/status/', views.QueryStatusView.as_view(), name='query-status'),
    path('<str:query_id>/senior-response/', views.SeniorResponseView.as_view(), name='query-senior-response'),
    path('pending/senior/<str:senior_id>/', views.SeniorPendingQueriesView.as_view(), name='query-senior-pending'),
]
