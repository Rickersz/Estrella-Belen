from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/representante/', views.representative_dashboard, name='representative_dashboard'),

    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('user-management/', views.user_management, name='user_management'),
    path('configuracion/', views.system_configuration, name='system_configuration'),
    path('representantes/', views.representative_management, name='representative_management'),
    path('representantes/<int:parent_id>/acceso/', views.representative_access, name='representative_access'),
    path('representantes/<int:parent_id>/reenviar/', views.resend_representative_invitation, name='resend_representative_invitation'),
    path('representantes/<int:parent_id>/bloquear/', views.toggle_representative_access, name='toggle_representative_access'),
    path('representantes/<int:parent_id>/desvincular/', views.unlink_representative_access, name='unlink_representative_access'),
    path('representantes/invitacion/<str:token>/', views.accept_representative_invitation, name='accept_representative_invitation'),
    path('solicitudes-acceso/', views.access_request_list, name='access_request_list'),
    path('solicitudes-acceso/<int:request_id>/<str:status>/', views.update_access_request_status, name='update_access_request_status'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('toggle-lock-user/<int:user_id>/', views.toggle_lock_user, name='toggle_lock_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    
    path('mark-notification-as-read/<str:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('clear-all-notifications/', views.clear_notifications, name='clear_all_notifications'),
    path('show-all-notifications/', views.show_all_notifications, name='show_all_notifications'),
]
