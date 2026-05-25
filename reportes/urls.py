from django.urls import path
from . import views

urlpatterns = [
    path('', views.reportes_home, name='reportes_home'),
    path('create/', views.constancia_create, name='constancia_create'),
    path('constancia/<int:pk>/', views.constancia_detail, name='constancia_detail'),
]
