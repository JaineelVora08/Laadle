from django.db import models


class UserProfile(models.Model):
    """
    Extended profile data beyond auth.
    References auth_service.User via user_id.
    Fields: user_id, bio, avatar_url, domains_of_interest
    """
    pass
