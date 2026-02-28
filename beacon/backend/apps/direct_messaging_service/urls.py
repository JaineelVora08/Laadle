from django.urls import path
from .views import (
    InitiateChatRequestView,
    RespondChatRequestView,
    MessageListCreateView,
    ChatRequestListView,
)

urlpatterns = [
    # POST /api/dm/initiate/  — student starts a DM request
    path('initiate/', InitiateChatRequestView.as_view(), name='dm-initiate'),

    # GET  /api/dm/requests/  — list all requests for the authenticated user
    path('requests/', ChatRequestListView.as_view(), name='dm-request-list'),

    # POST /api/dm/requests/<id>/respond/  — senior accepts/rejects
    path('requests/<uuid:pk>/respond/', RespondChatRequestView.as_view(), name='dm-request-respond'),

    # GET/POST /api/dm/requests/<id>/messages/  — list or send messages
    path('requests/<uuid:pk>/messages/', MessageListCreateView.as_view(), name='dm-messages'),
]
