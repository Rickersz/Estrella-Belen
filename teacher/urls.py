from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('add/', views.add_teacher, name='add_teacher'),    # must be before detail view to avoid conflict
    path('<str:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('edit/<slug:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('delete/<slug:teacher_id>/', views.delete_teacher, name='delete_teacher'),
]