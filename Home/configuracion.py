"""
Configuración del Sistema Escolar Estrella de Belén
Versión organizada y en español
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-para-desarrollo-solo')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Aplicaciones instaladas
APLICACIONES = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicaciones del sistema (en español)
    'escuela',
    'estudiante', 
    'profesor',
    'materia',
    'reportes',
    'bitacora',
    'autenticacion',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de URLs
ROOT_URLCONF = 'Home.urls'

# Configuración de templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'escuela.context_processors.dashboards',
                'escuela.context_processors.configuracion_sistema',
            ],
        },
    },
]

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'base_datos.sqlite3',
    }
}

# Validación de contraseñas
VALIDACION_CONTRASEÑAS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internacionalización
IDIOMA = 'es-es'
ZONA_HORARIA = 'America/Caracas'
USAR_I18N = True
USAR_TZ = True

# Archivos estáticos
URL_ESTATICOS = 'static/'
DIRECTORIOS_ESTATICOS = [
    BASE_DIR / "static",
]

# Archivos multimedia
URL_MEDIA = '/media/'
DIRECTORIO_MEDIA = BASE_DIR / 'media'

# Modelo de usuario personalizado
MODELO_USUARIO = 'autenticacion.UsuarioPersonalizado'
BACKENDS_AUTENTICACION = [
    'django.contrib.auth.backends.ModelBackend',
    'autenticacion.backends.BackendEmail',
]

# Configuración de email (desarrollo)
BACKEND_EMAIL = 'django.core.mail.backends.console.EmailBackend'

# Campo automático por defecto
CAMPO_AUTO_POR_DEFECTO = 'django.db.models.BigAutoField'

# Configuración de sesión
TIEMPO_VIDA_SESION = 1209600  # 2 semanas en segundos
GUARDAR_SESION_AL_CERRAR = True

# Configuración de seguridad (producción)
if not DEBUG:
    SEGURO_SSL_REDIRECT = True
    COOKIE_SESION_SEGURA = True
    COOKIE_CSRF_SEGURA = True
    ENCABEZADO_HSTS = 31536000  # 1 año