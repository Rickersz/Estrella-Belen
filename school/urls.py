from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),

    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('user-management/', views.user_management, name='user_management'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    
    path('mark-notification-as-read/<str:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('clear-all-notifications/', views.clear_notifications, name='clear_all_notifications'),
    path('show-all-notifications/', views.show_all_notifications, name='show_all_notifications'),
]