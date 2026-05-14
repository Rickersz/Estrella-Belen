from django.contrib import admin

# Register your models here.
from .models import Subject

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name',)
    search_fields = ('code', 'name')
    list_filter = ('class_level',)
