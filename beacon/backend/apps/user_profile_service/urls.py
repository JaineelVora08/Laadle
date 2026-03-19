from django.urls import path
from . import views

urlpatterns = [
    path('<str:user_id>/', views.UserProfileView.as_view(), name='user-profile'),
    path('<str:user_id>/update/', views.UpdateProfileView.as_view(), name='user-profile-update'),
    path('<str:user_id>/achievements/', views.AchievementView.as_view(), name='user-achievements'),
    path('<str:user_id>/onboarding/', views.SeniorOnboardingView.as_view(), name='senior-onboarding'),
]

urlpatterns_internal = [
    path('<str:user_id>/', views.InternalProfileView.as_view(), name='internal-profile-detail'),
]
