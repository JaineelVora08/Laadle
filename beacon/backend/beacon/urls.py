"""
beacon URL Configuration.
Routes all API traffic to the correct service app.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.auth_service.urls')),
    path('api/profile/', include('apps.user_profile_service.urls')),
    path('api/domains/', include('apps.domain_management_service.urls')),
    path('api/', include('apps.mentor_matching_service.urls')),
    path('internal/trust-score/', include('apps.trust_score_service.urls')),
    path('api/query/', include('apps.query_orchestrator.urls')),
    path('api/scheduler/', include('apps.adaptive_scheduler_service.urls')),
]
