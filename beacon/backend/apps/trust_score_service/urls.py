from django.urls import path
from . import views

urlpatterns = [
    path('recalculate/', views.RecalculateTrustView.as_view(), name='trust-recalculate'),
    path('update-feedback/', views.UpdateFeedbackView.as_view(), name='trust-update-feedback'),
]
