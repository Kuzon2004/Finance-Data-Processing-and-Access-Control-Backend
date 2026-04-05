import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager

class Role(models.TextChoices):
    VIEWER = 'VIEWER', 'Viewer'
    ANALYST = 'ANALYST', 'Analyst'
    ADMIN = 'ADMIN', 'Admin'

class CustomUserManager(BaseUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Intercept terminal createsuperuser command to inject our custom role."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)

    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
