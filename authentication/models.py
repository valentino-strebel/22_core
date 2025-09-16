from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom manager for the User model.

    Provides helper methods to create regular users and superusers
    using email as the unique identifier instead of a username.
    """

    def create_user(self, email, full_name, password=None, **extra_fields):
        """
        Create and return a regular user with the given email, full name, and password.

        Args:
            email (str): The user's email address (required, unique).
            full_name (str): The user's full name.
            password (str, optional): The user's password. Defaults to None.
            **extra_fields: Additional fields for the user model.

        Raises:
            ValueError: If no email is provided.

        Returns:
            User: A newly created User instance.
        """
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        """
        Create and return a superuser with the given email, full name, and password.

        Args:
            email (str): The superuser's email address.
            full_name (str): The superuser's full name.
            password (str, optional): The superuser's password. Defaults to None.
            **extra_fields: Additional fields for the user model.

        Raises:
            ValueError: If is_staff or is_superuser are not set to True.

        Returns:
            User: A newly created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model.

    Uses email as the unique identifier instead of a username.
    Includes fields for full name, staff status, active status,
    and the date the account was created.
    """

    email = models.EmailField(unique=True, help_text="Unique email address used for authentication.")
    full_name = models.CharField(max_length=255, help_text="The user's full name.")
    is_active = models.BooleanField(default=True, help_text="Indicates whether the user account is active.")
    is_staff = models.BooleanField(default=False, help_text="Designates whether the user can access the admin site.")
    date_joined = models.DateTimeField(default=timezone.now, help_text="The date and time when the user joined.")

    objects = UserManager()

    USERNAME_FIELD = "email"  # Used as the unique identifier for authentication
    REQUIRED_FIELDS = ["full_name"]  # Required when creating a superuser via createsuperuser

    def __str__(self):
        """
        Return a string representation of the user.
        """
        return self.email
