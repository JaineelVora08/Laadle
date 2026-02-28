from django.urls import path
from . import views

urlpatterns = [
    # Public API
    path('add/', views.AddDomainView.as_view(), name='domain-add'),
    path('user/<str:user_id>/', views.UserDomainsView.as_view(), name='domain-user'),
    path('all/', views.AllDomainsView.as_view(), name='domain-all'),
    # Internal API
    path('internal/user/<str:user_id>/', views.InternalUserDomainsView.as_view(), name='domain-internal-user'),
    path('internal/<str:domain_id>/', views.InternalDomainDetailView.as_view(), name='domain-internal-detail'),
]
