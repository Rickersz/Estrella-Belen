from django.utils import timezone

from escuela.models import Notification, SchoolConfiguration
from estudiante.models import Student
from .models import Payment


def is_admin(user):
    return user.is_authenticated and getattr(user, 'is_admin', False)


def is_teacher(user):
    return user.is_authenticated and getattr(user, 'is_teacher', False)


def is_representative(user):
    return user.is_authenticated and getattr(user, 'is_representative', False)


def can_manage_payments(user):
    return is_admin(user)


def can_view_payments(user):
    return is_admin(user) or is_representative(user)


def representative_students(user):
    parent = getattr(user, 'representante', None)
    if not parent:
        return Student.objects.none()
    return parent.student_set.select_related('parent').all()


def refresh_overdue_payments():
    today = timezone.localdate()
    payments = Payment.objects.filter(status__in=[Payment.STATUS_PENDING, Payment.STATUS_PARTIAL], due_date__lt=today)
    updated = 0
    for payment in payments:
        old_status = payment.status
        payment.refresh_status()
        if payment.status != old_status:
            payment.save(update_fields=['status', 'balance', 'payment_date', 'updated_at'])
            updated += 1
    return updated


def create_payment_notifications():
    today = timezone.localdate()
    reminder_days = SchoolConfiguration.get_solo().payment_reminder_days
    due_soon = Payment.objects.select_related('representative__user', 'student').filter(
        status__in=[Payment.STATUS_PENDING, Payment.STATUS_PARTIAL],
        due_date__gte=today,
        due_date__lte=today + timezone.timedelta(days=reminder_days),
    )
    overdue = Payment.objects.select_related('representative__user', 'student').filter(
        status=Payment.STATUS_OVERDUE,
        balance__gt=0,
    )
    created = 0
    for payment in list(due_soon) + list(overdue):
        user = getattr(payment.representative, 'user', None)
        if not user:
            continue
        label = 'vencido' if payment.status == Payment.STATUS_OVERDUE else 'proximo a vencer'
        message = f'Pago {label}: {payment.student.first_name} {payment.student.last_name} debe {payment.balance}.'
        _, was_created = Notification.objects.get_or_create(user=user, message=message)
        if was_created:
            created += 1
    return created
