from django.contrib import admin

# Register your models here.
from .models import AuditLog, Notification, RepresentativeInvitation, SchoolConfiguration

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')


@admin.register(SchoolConfiguration)
class SchoolConfigurationAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'active_academic_year', 'email', 'phone', 'updated_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'model_name', 'object_id', 'user', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'model_name', 'object_id', 'description', 'user__email')


@admin.register(RepresentativeInvitation)
class RepresentativeInvitationAdmin(admin.ModelAdmin):
    list_display = ('parent', 'email', 'status', 'created_by', 'created_at', 'expires_at', 'accepted_at')
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = ('email', 'parent__father_name', 'parent__mother_name', 'user__email')

from .models import Class, ClassTeacherAssignment
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('class_id', 'section', 'academic_year', 'department')
    list_filter = ('academic_year', 'department')
    search_fields = ('class_id', 'section')

@admin.register(ClassTeacherAssignment)
class ClassTeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('class_assigned', 'teacher', 'subject', 'assigned_date', 'is_active')
    list_filter = ('is_active', 'assigned_date')
    search_fields = ('class_assigned__class_id', 'teacher__name', 'subject__name')
