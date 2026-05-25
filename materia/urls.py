from django.urls import path
from . import views

urlpatterns = [
    path('', views.subject_list, name='subject_list'),
    path('add/', views.add_subject, name='add_subject'),
    path('edit/<str:code>/', views.edit_subject, name='edit_subject'),
    path('delete/<str:code>/', views.delete_subject, name='delete_subject'),

    path('assignment/', views.assignment_list, name='assignment_list'),
    path('assignment/add/', views.add_assignment, name='add_assignment'),
    path('assignment/edit/<int:assignment_id>/', views.edit_assignment, name='edit_assignment'),
    path('assignment/delete/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
]