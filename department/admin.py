from django.contrib import admin

# Register your models here.
from .models import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'hod', 'start_date')
    search_fields = ('name', 'head__name')
    list_filter = ('start_date',)