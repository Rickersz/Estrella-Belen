from django.contrib import admin

# Register your models here.

from .models import Teacher
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'name', 'gender', 'date_of_birth', 'joining_date', 'mobile_number', 'email', 'city', 'state', 'country')
    search_fields = ('teacher_id', 'name', 'email', 'mobile_number')
    list_filter = ('gender', 'city', 'state', 'country')    