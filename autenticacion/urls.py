from django.urls import path, include
from . import views

urlpatterns = [
    path('registrarse/', views.signup_view, name='registrarse'),
    path('signup/', views.signup_view, name='signup'),
    path('iniciar-sesion/', views.login_view, name='iniciar_sesion'),
    path('login/', views.login_view, name='login'),
    path('recuperar-contrasena/', views.forgot_password_view, name='recuperar_contrasena'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('restablecer-contrasena/<str:token>/', views.reset_password_view, name='restablecer_contrasena'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    path('cerrar-sesion/', views.logout_view, name='cerrar_sesion'),
    path('logout/', views.logout_view, name='logout'),
    path('verificar-otp/', views.verificar_otp_view, name='verificar_otp'),
    path('reenviar-otp/', views.reenviar_otp_view, name='reenviar_otp'),
]
