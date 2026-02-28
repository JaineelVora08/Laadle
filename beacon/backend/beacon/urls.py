"""
beacon URL Configuration.
Routes all API traffic to the correct service app.
"""
from django.contrib import admin
from django.urls import path, include
from apps.auth_service import urls as auth_urls
from apps.user_profile_service import urls as profile_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.auth_service.urls')),
    path('api/profile/', include('apps.user_profile_service.urls')),
    path('internal/users/', include((auth_urls.urlpatterns_internal, 'auth_service'), namespace='internal-users')),
    path('internal/profile/', include((profile_urls.urlpatterns_internal, 'user_profile_service'), namespace='internal-profile')),
    path('api/domains/', include('apps.domain_management_service.urls')),
    path('api/', include('apps.mentor_matching_service.urls')),
    path('internal/trust-score/', include('apps.trust_score_service.urls')),
    path('api/query/', include('apps.query_orchestrator.urls')),
    path('api/scheduler/', include('apps.adaptive_scheduler_service.urls')),
    path('api/dm/', include('apps.direct_messaging_service.urls')),
]
