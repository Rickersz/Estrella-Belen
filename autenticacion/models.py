from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import random


def generate_password_reset_token():
    return get_random_string(length=32)


def generate_otp():
    """Genera un código OTP de 6 dígitos."""
    return str(random.randint(100000, 999999))


class CustomUserManager(BaseUserManager):        # custom user manager to handle email-based user creation
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
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

    # Bloqueo por intentos fallidos
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

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
    token = models.CharField(max_length=32, default=generate_password_reset_token, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    TOKEN_VALIDITY_PERIOD = timezone.timedelta(minutes=15)
    
    @property
    def is_valid(self):
        return timezone.now() <= self.created_at + self.TOKEN_VALIDITY_PERIOD
    
    def send_reset_email(self, request):        
        # reset_link = f'http://localhost:8000/authentication/reset-password/{self.token}/'
        base_url = request.build_absolute_uri('/')[:-1]  # Get base URL without trailing slash
        endpoint =  reverse('restablecer_contrasena', args=[self.token])
        reset_link = base_url + endpoint
        send_mail(
            "Password Reset Request",
            f"Click the following link to reset your password: \n{reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )


class OTPVerificacion(models.Model):
    """Código OTP de un solo uso para 2FA (ítem 15)."""
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    codigo     = models.CharField(max_length=6, default=generate_otp)
    creado_en  = models.DateTimeField(auto_now_add=True)
    usado      = models.BooleanField(default=False)

    VALIDEZ = timezone.timedelta(minutes=10)

    @property
    def es_valido(self):
        return not self.usado and timezone.now() <= self.creado_en + self.VALIDEZ

    def enviar_codigo(self):
        send_mail(
            subject='Código de verificación - Estrella de Belén',
            message=(
                f'Tu código de verificación es: {self.codigo}\n\n'
                f'Este código es válido por 10 minutos.\n'
                f'Si no solicitaste este código, ignora este mensaje.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
            fail_silently=True,
        )

    def __str__(self):
        return f"OTP {self.codigo} para {self.user.email}"

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Código OTP'
        verbose_name_plural = 'Códigos OTP'
