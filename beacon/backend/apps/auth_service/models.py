from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
import uuid


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def create_user(self, email, name, password=None, **extra_fields):
        """Create and return a regular user."""
        pass

    def create_superuser(self, email, name, password=None, **extra_fields):
        """Create and return a superuser."""
        pass


class User(AbstractBaseUser):
    """
    Base user model stored in PostgreSQL.
    Shared by both Student and Senior roles.
    Fields: id, name, email, role, availability, trust_score, current_level, active_load
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=[('STUDENT', 'Student'), ('SENIOR', 'Senior')])
    availability = models.BooleanField(default=True)
    trust_score = models.FloatField(default=0.0)
    current_level = models.CharField(max_length=100, blank=True, default='')
    active_load = models.IntegerField(default=0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        app_label = 'auth_service'


class Student(models.Model):
    """
    Extended profile for students.
    Fields: user (OneToOne), low_energy_mode, momentum_score
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    low_energy_mode = models.BooleanField(default=False)
    momentum_score = models.FloatField(default=0.0)

    class Meta:
        app_label = 'auth_service'


class Senior(models.Model):
    """
    Extended profile for seniors.
    Fields: user (OneToOne), consistency_score, alignment_score, follow_through_rate
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='senior_profile')
    consistency_score = models.FloatField(default=0.0)
    alignment_score = models.FloatField(default=0.0)
    follow_through_rate = models.FloatField(default=0.0)

    class Meta:
        app_label = 'auth_service'


class Achievement(models.Model):
    """
    Verified achievement uploaded by senior.
    Fields: id, user, title, proof_url, verified, created_at
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255)
    proof_url = models.URLField(blank=True, default='')
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'auth_service'


class TrustMetrics(models.Model):
    """
    Trust score breakdown for a senior. Used by trust_score_service.
    Fields: senior, student_feedback_score, consistency_score,
            alignment_score, follow_through_rate, achievement_weight
    """
    senior = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trust_metrics')
    student_feedback_score = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)
    alignment_score = models.FloatField(default=0.0)
    follow_through_rate = models.FloatField(default=0.0)
    achievement_weight = models.FloatField(default=0.0)
    n_success = models.IntegerField(default=0)
    n_total = models.IntegerField(default=0)

    class Meta:
        app_label = 'auth_service'
