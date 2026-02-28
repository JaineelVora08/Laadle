from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='auth-register'),
    path('login/', views.LoginView.as_view(), name='auth-login'),
    path('google/login/', views.GoogleLoginView.as_view(), name='auth-google-login'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
]

urlpatterns_internal = [
    path('<str:user_id>/', views.InternalUserView.as_view(), name='internal-user-detail'),
    path('<str:senior_id>/increment-load/', views.InternalIncrementSeniorLoadView.as_view(), name='internal-user-increment-load'),
]
