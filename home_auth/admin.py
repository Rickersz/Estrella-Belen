from django.contrib import admin

# Register your models here.
from .models import CustomUser, PasswordResetRequest

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_admin', 'is_student', 'is_teacher', 'is_authorized', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_admin', 'is_student', 'is_teacher', 'is_authorized')
    ordering = ('email',)

    # Controls how fields are grouped and displayed when editing a user
    fieldsets = (
        (None, {'fields' : ('email','password')}),
        ('Personal info', {'fields': ('first_name', 'last_name',)}),
        ('Roles', {'fields': ('is_student', 'is_teacher', 'is_admin')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_authorized',
                                    'groups', 'user_permissions')}),
    )

@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'token', 'created_at', 'is_valid')
    search_fields = ('email', 'token')
    ordering = ('-created_at',)



admin.site.site_header = "School Management System Admin"
admin.site.site_title = "School Management System Admin Portal"
