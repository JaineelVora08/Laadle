from django.contrib.auth.models import AbstractBaseUser
from django.db import models
import uuid


class User(AbstractBaseUser):
    """
    Base user model stored in PostgreSQL.
    Shared by both Student and Senior roles.
    Fields: id, name, email, role, availability, trust_score, current_level, active_load
    """
    pass


class Student(models.Model):
    """
    Extended profile for students.
    Fields: user (OneToOne), low_energy_mode, momentum_score
    """
    pass


class Senior(models.Model):
    """
    Extended profile for seniors.
    Fields: user (OneToOne), consistency_score, alignment_score, follow_through_rate
    """
    pass


class Achievement(models.Model):
    """
    Verified achievement uploaded by senior.
    Fields: id, user, title, proof_url, verified, created_at
    """
    pass


class TrustMetrics(models.Model):
    """
    Trust score breakdown for a senior. Used by trust_score_service.
    Fields: senior, student_feedback_score, consistency_score,
            alignment_score, follow_through_rate, achievement_weight
    """
    pass
