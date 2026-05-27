from django.urls import path

from . import views


urlpatterns = [
    path('', views.academic_dashboard, name='academic_dashboard'),
    path('notas/', views.grade_list, name='grade_list'),
    path('notas/nueva/', views.grade_create, name='grade_create'),
    path('notas/<int:pk>/editar/', views.grade_edit, name='grade_edit'),
    path('historial/', views.academic_history, name='academic_history'),
    path('historial/<int:student_id>/', views.academic_history, name='academic_history_student'),
    path('boletin/<int:student_id>/', views.report_card_pdf, name='report_card_pdf'),
    path('horario/', views.schedule_list, name='schedule_list'),
    path('horario/nuevo/', views.schedule_create, name='schedule_create'),
    path('calendario/', views.calendar_list, name='calendar_list'),
    path('calendario/nuevo/', views.calendar_create, name='calendar_create'),
    path('observaciones/', views.observation_list, name='observation_list'),
    path('observaciones/nueva/', views.observation_create, name='observation_create'),
    path('anuncios/', views.announcement_list, name='announcement_list'),
    path('anuncios/nuevo/', views.announcement_create, name='announcement_create'),
    path('mensajes/', views.message_list, name='message_list'),
    path('mensajes/nuevo/', views.message_create, name='message_create'),
    path('constancias/', views.constancias_portal, name='constancias_portal'),
    path('estadisticas/', views.academic_stats, name='academic_stats'),
    path('exportar/notas.xlsx/', views.export_grades_excel, name='export_grades_excel'),
]
