from django.contrib import admin

from .models import Payment, PaymentConfig, PaymentReminder


@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'amount', 'due_day', 'allowed_days', 'is_active')
    list_filter = ('is_active', 'academic_year')
    search_fields = ('name', 'academic_year')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'representative', 'concept', 'due_date', 'payment_date', 'amount_due', 'amount_paid', 'balance', 'status')
    list_filter = ('status', 'academic_year', 'due_date')
    search_fields = ('student__first_name', 'student__last_name', 'student__student_id', 'reference')
    date_hierarchy = 'due_date'


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = ('payment', 'user', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message', 'user__email')
