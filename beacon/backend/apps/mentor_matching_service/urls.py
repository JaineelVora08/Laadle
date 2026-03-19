from django.urls import path
from . import views

urlpatterns = [
    # Public API
    path('mentor-matching/find/', views.FindMentorView.as_view(), name='mentor-find'),
    path('mentor-matching/connect/', views.ConnectMentorView.as_view(), name='mentor-connect'),
    path('peer-matching/find/', views.FindPeerView.as_view(), name='peer-find'),
    # Internal API
    path('internal/mentor-matching/find/', views.InternalFindMentorView.as_view(), name='mentor-internal-find'),
    path('internal/mentor-matching/connect/', views.InternalConnectMentorView.as_view(), name='mentor-internal-connect'),
]
