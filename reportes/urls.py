from django.urls import path
from . import views

urlpatterns = [
    path('', views.reportes_home, name='reportes_home'),
    path('representante/', views.representative_reports, name='representative_reports'),
    path('representante/constancia/<int:student_id>/<str:report_type>/', views.representative_constancia_pdf, name='representative_constancia_pdf'),
    path('create/', views.constancia_create, name='constancia_create'),
    path('constancia/<int:pk>/', views.constancia_detail, name='constancia_detail'),
]
