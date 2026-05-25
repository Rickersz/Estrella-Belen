from django.contrib import admin
from .models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'ip_address', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('email', 'ip_address', 'user__email')
