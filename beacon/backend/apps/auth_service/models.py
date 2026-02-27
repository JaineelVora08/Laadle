from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
import uuid


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def create_user(self, email, name, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError('Email is required')
        if not name:
            raise ValueError('Name is required')
        if not password:
            raise ValueError('Password is required')

        role = extra_fields.pop('role', 'STUDENT')
        role = role.upper()
        if role not in dict(User.ROLE_CHOICES):
            raise ValueError('Role must be STUDENT or SENIOR')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            role=role,
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'SENIOR')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Base user model stored in PostgreSQL.
    Shared by both Student and Senior roles.
    Fields: id, name, email, role, availability, trust_score, current_level, active_load
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    ROLE_CHOICES = (('STUDENT', 'Student'), ('SENIOR', 'Senior'))

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    availability = models.BooleanField(default=True)
    trust_score = models.FloatField(default=0.0)
    current_level = models.CharField(max_length=100, blank=True, default='')
    active_load = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def clean(self):
        super().clean()
        if self.role:
            self.role = self.role.upper()
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError({'role': 'Role must be STUDENT or SENIOR.'})
        if self.active_load < 0:
            raise ValidationError({'active_load': 'Active load cannot be negative.'})
        if self.trust_score < 0:
            raise ValidationError({'trust_score': 'Trust score cannot be negative.'})
        if self.role == 'STUDENT' and self.active_load != 0:
            raise ValidationError({'active_load': 'Student active load must be 0.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

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

    def clean(self):
        super().clean()
        if self.user.role != 'STUDENT':
            raise ValidationError({'user': 'Student profile must be linked to a STUDENT user.'})
        if self.momentum_score < 0:
            raise ValidationError({'momentum_score': 'Momentum score cannot be negative.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

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

    def clean(self):
        super().clean()
        if self.user.role != 'SENIOR':
            raise ValidationError({'user': 'Senior profile must be linked to a SENIOR user.'})
        if self.consistency_score < 0:
            raise ValidationError({'consistency_score': 'Consistency score cannot be negative.'})
        if self.alignment_score < 0:
            raise ValidationError({'alignment_score': 'Alignment score cannot be negative.'})
        if self.follow_through_rate < 0:
            raise ValidationError({'follow_through_rate': 'Follow-through rate cannot be negative.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

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

    def clean(self):
        super().clean()
        if self.user.role != 'SENIOR':
            raise ValidationError({'user': 'Achievements can only be attached to SENIOR users.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

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

    def clean(self):
        super().clean()
        if self.senior.role != 'SENIOR':
            raise ValidationError({'senior': 'Trust metrics can only be attached to SENIOR users.'})
        if self.student_feedback_score < 0:
            raise ValidationError({'student_feedback_score': 'Score cannot be negative.'})
        if self.consistency_score < 0:
            raise ValidationError({'consistency_score': 'Score cannot be negative.'})
        if self.alignment_score < 0:
            raise ValidationError({'alignment_score': 'Score cannot be negative.'})
        if self.follow_through_rate < 0:
            raise ValidationError({'follow_through_rate': 'Score cannot be negative.'})
        if self.achievement_weight < 0:
            raise ValidationError({'achievement_weight': 'Score cannot be negative.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        app_label = 'auth_service'
