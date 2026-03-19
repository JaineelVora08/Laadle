from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """
    Extended profile data beyond auth.
    References auth_service.User via user_id.
    Fields: user_id, bio, avatar_url, domains_of_interest
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='extended_profile')
    bio = models.TextField(blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')
    domains_of_interest = models.JSONField(default=list, blank=True)

    class Meta:
        app_label = 'user_profile_service'
