from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.add_student, name='add_student'),    # must be before detail view to avoid conflict
    path('gestion-escolar/', views.school_operations_dashboard, name='school_operations_dashboard'),
    path('cupos/', views.capacity_list, name='capacity_list'),
    path('asistencia/', views.attendance_list, name='attendance_list'),
    path('cierre-anual/', views.school_year_closure, name='school_year_closure'),
    path('download/csv/', views.download_students_csv, name='download_students_csv'),
    path('constancia/<slug:slug>/', views.constancia_inscripcion, name='constancia_inscripcion'),
    path('<slug:slug>/documentos/', views.student_documents, name='student_documents'),
    path('<slug:slug>/salud/', views.student_health, name='student_health'),
    path('edit/<slug:slug>/', views.edit_student, name='edit_student'),
    path('delete/<slug:slug>/', views.delete_student, name='delete_student'),
    path('<slug:slug>/', views.student_detail, name='student_detail'),
]
