from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.utils.crypto import get_random_string
from django.contrib import messages
from .models import CustomUser, PasswordResetRequest, OTPVerificacion
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
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
            return render(request, 'autenticacion/registrarse.html', {'error': 'Este correo ya estÃ¡ registrado. Usa otro correo o inicia sesiÃ³n.'})

        if password != confirm_password:
            return render(request, 'autenticacion/registrarse.html', {'error': 'Las contraseÃ±as no coinciden.'})

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
        existing_user = CustomUser.objects.filter(email=email).first()
        if existing_user and existing_user.is_locked:
            return render(request, 'autenticacion/iniciar-sesion.html', {'error': 'Usuario bloqueado. Contacta al administrador.', 'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

        user = authenticate(request, username=email, password=password)
        if user is not None:
            user.failed_login_attempts = 0
            user.is_locked = False
            user.locked_at = None
            user.save(update_fields=['failed_login_attempts', 'is_locked', 'locked_at'])
            AccessLog.objects.create(
                user=user,
                email=user.email,
                ip_address=get_client_ip(request),
                action='otp_sent',
                path=request.path,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            otp = OTPVerificacion.objects.create(user=user)
            otp.enviar_codigo()
            request.session['otp_user_id'] = user.pk
            request.session['otp_next'] = 'student_list'
            return redirect('verificar_otp')
        else:
            if existing_user:
                existing_user.failed_login_attempts += 1
                if existing_user.failed_login_attempts >= 5:
                    existing_user.is_locked = True
                    existing_user.locked_at = timezone.now()
                existing_user.save(update_fields=['failed_login_attempts', 'is_locked', 'locked_at'])
            AccessLog.objects.create(
                email=email,
                ip_address=get_client_ip(request),
                action='login_failed',
                path=request.path,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            return render(request, 'autenticacion/iniciar-sesion.html', {'error': 'Correo o contraseÃ±a invÃ¡lidos.', 'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})

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
            
            messages.success(request, 'Se enviÃ³ un enlace de recuperaciÃ³n a tu correo.')
            return redirect('recuperar_contrasena')
        
        messages.error(request, 'No existe un usuario con este correo.')
        return redirect('recuperar_contrasena')
    return render(request, 'autenticacion/recuperar-contrasena.html')

def reset_password_view(request, token):
    reset_request = PasswordResetRequest.objects.filter(token=token).first()
    if not (reset_request and reset_request.is_valid):    # doesn't check for 2nd condition if reset_request is None
        messages.error(request, 'El enlace de recuperaciÃ³n no es vÃ¡lido o expirÃ³. Solicita uno nuevo.')
        return redirect('recuperar_contrasena')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            return render(request, 'autenticacion/reset-password.html', {'error': 'Las contraseÃ±as no coinciden.', 'token': token})

        try:
            validate_password(new_password, reset_request.user)
        except ValidationError as exc:
            return render(request, 'autenticacion/reset-password.html', {'error': ' '.join(exc.messages), 'token': token})
        
        reset_request.user.set_password(new_password)       # hash the new password
        reset_request.user.save()
        reset_request.delete()  # Invalidate the used token

        messages.success(request, 'Tu contraseÃ±a fue restablecida correctamente. Ya puedes iniciar sesiÃ³n.')
        return redirect('iniciar_sesion')
    return render(request, 'autenticacion/reset-password.html', {'token': token})


def logout_view(request):
    request.session.pop('otp_user_id', None)
    request.session.pop('otp_next', None)
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


def verificar_otp_view(request):
    pending_user_id = request.session.get('otp_user_id')
    if not pending_user_id:
        messages.error(request, 'Inicia sesion para recibir un codigo de verificacion.')
        return redirect('iniciar_sesion')

    user = CustomUser.objects.filter(pk=pending_user_id, is_active=True, is_locked=False).first()
    if not user:
        request.session.pop('otp_user_id', None)
        request.session.pop('otp_next', None)
        messages.error(request, 'No se pudo verificar el usuario. Inicia sesion nuevamente.')
        return redirect('iniciar_sesion')

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        otp = OTPVerificacion.objects.filter(user=user, codigo=codigo, usado=False).first()
        if otp and otp.es_valido:
            otp.usado = True
            otp.save()
            login(request, user, backend='autenticacion.backends.EmailBackend')
            request.session.pop('otp_user_id', None)
            next_url = request.session.pop('otp_next', 'student_list')
            AccessLog.objects.create(
                user=user,
                email=user.email,
                ip_address=get_client_ip(request),
                action='login_success',
                path=request.path,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            messages.success(request, 'Codigo verificado correctamente.')
            return redirect(next_url)
        return render(request, 'autenticacion/verificar-otp.html', {
            'email': user.email,
            'error': 'Codigo invalido o expirado.',
        })
    return render(request, 'autenticacion/verificar-otp.html', {'email': user.email})


def reenviar_otp_view(request):
    pending_user_id = request.session.get('otp_user_id')
    user = CustomUser.objects.filter(pk=pending_user_id, is_active=True, is_locked=False).first()
    if not user:
        messages.error(request, 'Inicia sesion para reenviar el codigo OTP.')
        return redirect('iniciar_sesion')

    otp = OTPVerificacion.objects.create(user=user)
    try:
        otp.enviar_codigo()
        messages.success(request, 'Se ha reenviado el codigo OTP a tu correo.')
    except Exception:
        messages.error(request, 'Error al enviar el codigo OTP.')
    return redirect('verificar_otp')
