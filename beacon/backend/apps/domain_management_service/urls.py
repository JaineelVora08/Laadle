from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.AddDomainView.as_view(), name='domain-add'),
    path('user/<str:user_id>/', views.UserDomainsView.as_view(), name='domain-user'),
    path('all/', views.AllDomainsView.as_view(), name='domain-all'),
]
