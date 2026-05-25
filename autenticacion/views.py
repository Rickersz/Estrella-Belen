from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.utils.crypto import get_random_string
from django.contrib import messages
from .models import CustomUser, PasswordResetRequest, OTPVerificacion
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from bitacora.models import AccessLog


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not first_name or not last_name or not email or not password:
            return render(request, 'autenticacion/registrarse.html', {'error': 'Completa todos los campos obligatorios.'})

        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'autenticacion/registrarse.html', {'error': 'Este correo ya está registrado. Usa otro correo o inicia sesión.'})

        if password != confirm_password:
            return render(request, 'autenticacion/registrarse.html', {'error': 'Las contraseñas no coinciden.'})

        try:
            validate_password(password)
        except ValidationError as exc:
            return render(request, 'autenticacion/registrarse.html', {'error': ' '.join(exc.messages)})

        user = CustomUser.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_student=True
        )
        login(request, user)
        return redirect('student_list')
    return render(request, 'autenticacion/registrarse.html')

from django.conf import settings
import requests

def login_view(request):
    # reCAPTCHA v2 integration: verify token server-side with Google's API
    if request.method == 'POST':
        token = request.POST.get('g-recaptcha-response')
        if not token:
            return render(request, 'autenticacion/iniciar-sesion.html', {'error': 'Por favor completa el reCAPTCHA.', 'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

        # Verify token with Google
        try:
            resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': token,
                'remoteip': get_client_ip(request),
            }, timeout=5)
            result = resp.json()
        except Exception:
            return render(request, 'autenticacion/iniciar-sesion.html', {'error': 'Error verificando reCAPTCHA. Intenta nuevamente.', 'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

        if not result.get('success'):
            return render(request, 'autenticacion/iniciar-sesion.html', {'error': 'reCAPTCHA no validado. Intentarlo de nuevo.', 'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            AccessLog.objects.create(
                user=user,
                email=user.email,
                ip_address=get_client_ip(request),
                action='login_success',
                path=request.path,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            login(request, user)
            return redirect('student_list')
        else:
            AccessLog.objects.create(
                email=email,
                ip_address=get_client_ip(request),
                action='login_failed',
                path=request.path,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            return render(request, 'autenticacion/iniciar-sesion.html', {'error': 'Correo o contraseña inválidos.', 'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

    # GET -> render login with site key
    return render(request, 'autenticacion/iniciar-sesion.html', {'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = CustomUser.objects.filter(email=email).first()
        if user:
            token = get_random_string(length=32)
            reset_request = PasswordResetRequest.objects.create(user=user, email=email, token=token)
            reset_request.send_reset_email(request)
            
            messages.success(request, 'Se envió un enlace de recuperación a tu correo.')
            return redirect('recuperar_contrasena')
        
        messages.error(request, 'No existe un usuario con este correo.')
        return redirect('recuperar_contrasena')
    return render(request, 'autenticacion/recuperar-contrasena.html')

def reset_password_view(request, token):
    reset_request = PasswordResetRequest.objects.filter(token=token).first()
    if not (reset_request and reset_request.is_valid):    # doesn't check for 2nd condition if reset_request is None
        messages.error(request, 'El enlace de recuperación no es válido o expiró. Solicita uno nuevo.')
        return redirect('recuperar_contrasena')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            return render(request, 'autenticacion/reset-password.html', {'error': 'Las contraseñas no coinciden.', 'token': token})

        try:
            validate_password(new_password, reset_request.user)
        except ValidationError as exc:
            return render(request, 'autenticacion/reset-password.html', {'error': ' '.join(exc.messages), 'token': token})
        
        reset_request.user.set_password(new_password)       # hash the new password
        reset_request.user.save()
        reset_request.delete()  # Invalidate the used token

        messages.success(request, 'Tu contraseña fue restablecida correctamente. Ya puedes iniciar sesión.')
        return redirect('iniciar_sesion')
    return render(request, 'autenticacion/reset-password.html', {'token': token})


def logout_view(request):
    if request.user.is_authenticated:
        AccessLog.objects.create(
            user=request.user,
            email=request.user.email,
            ip_address=get_client_ip(request),
            action='logout',
            path=request.path,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
    logout(request)
    return redirect('iniciar_sesion')


@login_required(login_url='iniciar_sesion')
def verificar_otp_view(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        otp = OTPVerificacion.objects.filter(user=request.user, codigo=codigo, usado=False).first()
        if otp and otp.es_valido:
            otp.usado = True
            otp.save()
            messages.success(request, 'Código verificado correctamente.')
            return redirect('index')
        messages.error(request, 'Código inválido o expirado.')
    return render(request, 'autenticacion/verificar-otp.html')


@login_required(login_url='iniciar_sesion')
def reenviar_otp_view(request):
    otp = OTPVerificacion.objects.create(user=request.user)
    try:
        otp.enviar_codigo()
        messages.success(request, 'Se ha reenviado el código OTP a tu correo.')
    except Exception:
        messages.error(request, 'Error al enviar el código OTP.')
    return redirect('verificar_otp')