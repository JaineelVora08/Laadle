from django.urls import path

from .consumers import BeaconLiveConsumer

websocket_urlpatterns = [
    path('ws/live/<uuid:user_id>/', BeaconLiveConsumer.as_asgi()),
]
