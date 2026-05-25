from django.contrib import admin
from .models import Constancia


@admin.register(Constancia)
class ConstanciaAdmin(admin.ModelAdmin):
	list_display = ('title', 'student', 'issued_by', 'date_issued')
	search_fields = ('title', 'student__first_name', 'student__last_name')
	list_filter = ('date_issued',)
