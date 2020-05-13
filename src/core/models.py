from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **kwargs):
        """Creates and saves a new user"""
        if not email:
            raise ValueError('Users must have an email address')
        new_user = self.model(email=self.normalize_email(email), **kwargs)
        new_user.set_password(password)
        new_user.save(using=self.db)
        return new_user

    def create_superuser(self, email, password):
        """Creates and saves a new super user"""
        new_user = self.create_user(email, password)
        new_user.is_staff = True
        new_user.is_superuser = True
        new_user.save(using=self.db)
        return new_user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'email'
