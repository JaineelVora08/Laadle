from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.SchedulerStatusView.as_view(), name='scheduler-status'),
]
