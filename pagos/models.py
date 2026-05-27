from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class PaymentConfig(models.Model):
    name = models.CharField(max_length=120, default='Mensualidad')
    academic_year = models.CharField(max_length=9, default='2025-2026')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_day = models.PositiveSmallIntegerField(default=5)
    allowed_days = models.PositiveSmallIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-is_active', 'academic_year', 'name']

    def __str__(self):
        return f'{self.name} {self.academic_year}'


class Payment(models.Model):
    STATUS_PAID = 'pagado'
    STATUS_PENDING = 'pendiente'
    STATUS_PARTIAL = 'parcial'
    STATUS_OVERDUE = 'vencido'

    STATUS_CHOICES = [
        (STATUS_PAID, 'Pagado'),
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_PARTIAL, 'Parcial'),
        (STATUS_OVERDUE, 'Vencido'),
    ]

    VERIFICATION_NOT_REQUIRED = 'no_requiere'
    VERIFICATION_PENDING = 'pendiente_revision'
    VERIFICATION_APPROVED = 'aprobado'
    VERIFICATION_REJECTED = 'rechazado'

    VERIFICATION_CHOICES = [
        (VERIFICATION_NOT_REQUIRED, 'No requiere revision'),
        (VERIFICATION_PENDING, 'Pendiente por verificar'),
        (VERIFICATION_APPROVED, 'Verificado'),
        (VERIFICATION_REJECTED, 'Rechazado'),
    ]

    student = models.ForeignKey('estudiante.Student', on_delete=models.CASCADE, related_name='payments')
    representative = models.ForeignKey('estudiante.Parent', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    concept = models.CharField(max_length=150, default='Mensualidad')
    academic_year = models.CharField(max_length=9, default='2025-2026')
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reference = models.CharField(max_length=80, blank=True)
    reported_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reported_reference = models.CharField(max_length=80, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_payments')
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_CHOICES, default=VERIFICATION_NOT_REQUIRED)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', 'student__last_name']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['verification_status', 'reported_at']),
        ]

    def __str__(self):
        return f'{self.student} - {self.concept} - {self.get_status_display()}'

    @property
    def is_overdue(self):
        return self.balance > 0 and self.due_date < timezone.localdate()

    @property
    def representative_name(self):
        parent = self.representative or getattr(self.student, 'parent', None)
        if not parent:
            return 'Sin representante'
        return parent.mother_name or parent.father_name or str(parent)

    def refresh_status(self):
        paid = self.amount_paid or Decimal('0')
        due = self.amount_due or Decimal('0')
        self.balance = max(due - paid, Decimal('0'))
        if self.balance <= 0:
            self.status = self.STATUS_PAID
            if not self.payment_date:
                self.payment_date = timezone.localdate()
        elif paid > 0:
            self.status = self.STATUS_OVERDUE if self.due_date < timezone.localdate() else self.STATUS_PARTIAL
        else:
            self.status = self.STATUS_OVERDUE if self.due_date < timezone.localdate() else self.STATUS_PENDING

    def save(self, *args, **kwargs):
        if not self.representative_id and self.student_id:
            self.representative = self.student.parent
        self.refresh_status()
        super().save(*args, **kwargs)


class PaymentReminder(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message
