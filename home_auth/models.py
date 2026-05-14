from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

class CustomUserManager(BaseUserManager):        # custom user manager to handle email-based user creation
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            return ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)     # hash the password
        user.save(using=self._db)       # save the user to the database
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractUser):
    username = None  #  email as the unique identifier
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_authorized = models.BooleanField(default=False)

    # user roles
    is_admin = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'        # forces email as login identifier
    REQUIRED_FIELDS = []  # email & password are required by default

    objects = CustomUserManager()   # use the custom user manager (for email-based creation)

    # Set related_name to None to prevent reverse relationship creation
    groups = models.ManyToManyField(
        'auth.Group',               # Django's built-in Group model
        related_name='+',          # Prevent reverse relationship by using '+' it 
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',          # Django's built-in Permission model
        related_name='+',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class PasswordResetRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.CharField(max_length=32, default=get_random_string(length=32), editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    TOKEN_VALIDITY_PERIOD = timezone.timedelta(minutes=15)
    
    @property
    def is_valid(self):
        return timezone.now() <= self.created_at + self.TOKEN_VALIDITY_PERIOD
    
    def send_reset_email(self, request):        
        # reset_link = f'http://localhost:8000/authentication/reset-password/{self.token}/'
        base_url = request.build_absolute_uri('/')[:-1]  # Get base URL without trailing slash
        endpoint =  reverse('reset_password', args=[self.token])
        reset_link = base_url + endpoint
        send_mail(
            "Password Reset Request",
            f"Click the following link to reset your password: \n{reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )