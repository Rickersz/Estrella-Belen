from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.add_student, name='add_student'),    # must be before detail view to avoid conflict
    path('<slug:slug>/', views.student_detail, name='student_detail'),
    path('edit/<slug:slug>/', views.edit_student, name='edit_student'),
    path('delete/<slug:slug>/', views.delete_student, name='delete_student'),

    # download student data as CSV
    path('download/csv/', views.download_students_csv, name='download_students_csv'),
]