from django.urls import path
from . import views

urlpatterns = [
    path('mentor-matching/find/', views.FindMentorView.as_view(), name='mentor-find'),
    path('mentor-matching/connect/', views.ConnectMentorView.as_view(), name='mentor-connect'),
    path('peer-matching/find/', views.FindPeerView.as_view(), name='peer-find'),
]
