
from django.contrib.auth.models import UserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(UserManager):
    def _create_user(self, password=None, **extra_fields):        
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(password, **extra_fields)
    
    def create_superuser(self, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(password, **extra_fields)
    

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(blank=True, default="", unique=True, max_length=16)
    password = models.CharField(max_length=128, blank=True, null=True)  # Password can be null if id_42 is provided
    id_42 = models.CharField(max_length=128, blank=True, null=True)  # Field for id_42
    two_factor_token = models.CharField(max_length=128, blank=True, null=True)  # Field for two-factor authentication token

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, default='avatars/default.png')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def clean(self):
        # Ensure that either password or id_42 is set, but not both
        if not self.password and not self.id_42:
            raise ValidationError(_('Either password or id_42 must be set.'))
        if self.password and self.id_42:
            raise ValidationError(_('You cannot set both password and id_42.'))

    def save(self, *args, **kwargs):
        # If id_42 is set, make password null
        if self.id_42:
            self.password = None
        # If password is set, make id_42 null
        elif self.password:
            self.id_42 = None

        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.username
