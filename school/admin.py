from django.contrib import admin

# Register your models here.
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')

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