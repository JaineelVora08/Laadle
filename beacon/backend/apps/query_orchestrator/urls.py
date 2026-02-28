from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.SubmitQueryView.as_view(), name='query-submit'),
    path('<str:query_id>/status/', views.QueryStatusView.as_view(), name='query-status'),
    path('<str:query_id>/senior-response/', views.SeniorResponseView.as_view(), name='query-senior-response'),
    path('<str:query_id>/senior-faq/', views.SeniorFAQResponseView.as_view(), name='query-senior-faq'),
    path('<str:query_id>/followup/', views.FollowUpView.as_view(), name='query-followup'),
    path('pending/senior/<str:senior_id>/', views.SeniorPendingQueriesView.as_view(), name='query-senior-pending'),
    path('student/<str:student_id>/', views.StudentQueriesView.as_view(), name='query-student-list'),
]
