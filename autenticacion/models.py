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
    is_representative = models.BooleanField(default=False)

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
            "Restablecer contraseña - Estrella de Belen",
            (
                "Recibimos una solicitud para restablecer tu contraseña.\n\n"
                f"Abre este enlace para crear una nueva contraseña:\n{reset_link}\n\n"
                "Este enlace es valido por 15 minutos. Si no solicitaste este cambio, ignora este mensaje."
            ),
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )


class AccessRequest(models.Model):
    STATUS_PENDING = 'pendiente'
    STATUS_REVIEWED = 'revisada'
    STATUS_APPROVED = 'aprobada'
    STATUS_REJECTED = 'rechazada'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_REVIEWED, 'Revisada'),
        (STATUS_APPROVED, 'Aprobada'),
        (STATUS_REJECTED, 'Rechazada'),
    ]

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    document_id = models.CharField(max_length=30, blank=True)
    student_name = models.CharField(max_length=120)
    student_grade = models.CharField(max_length=80, blank=True)
    relationship = models.CharField(max_length=60, default='Representante')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='access_requests_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.student_name} - {self.get_status_display()}'


class OTPVerificacion(models.Model):
    """Código OTP de un solo uso para 2FA (ítem 15)."""
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    codigo     = models.CharField(max_length=6, default=generate_otp)
    creado_en  = models.DateTimeField(auto_now_add=True)
    usado      = models.BooleanField(default=False)
    intentos   = models.PositiveSmallIntegerField(default=0)
    enviado_en = models.DateTimeField(auto_now_add=True)

    VALIDEZ = timezone.timedelta(minutes=10)

    @property
    def es_valido(self):
        return not self.usado and timezone.now() <= self.creado_en + self.VALIDEZ

    def enviar_codigo(self):
        enviados = send_mail(
            subject='Codigo de verificacion - Estrella de Belen',
            message=(
                f'Tu codigo de verificacion es: {self.codigo}\n\n'
                f'Este codigo es valido por 10 minutos.\n'
                f'Si no solicitaste este codigo, ignora este mensaje.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
            fail_silently=False,
        )
        self.enviado_en = timezone.now()
        self.save(update_fields=['enviado_en'])
        return enviados

    def __str__(self):
        return f"OTP {self.codigo} para {self.user.email}"

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Código OTP'
        verbose_name_plural = 'Códigos OTP'
