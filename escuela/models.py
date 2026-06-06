from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
import uuid
# Create your models here.


def active_academic_year_default():
    return SchoolConfiguration.get_solo().active_academic_year

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{ ' '.join([self.user.first_name, self.user.last_name]) if (self.user.first_name or self.user.last_name) else 'Unknown'}: {self.message}"


class SchoolConfiguration(models.Model):
    institution_name = models.CharField(max_length=180, default='Unidad Educativa Estrella de Belen')
    active_academic_year = models.CharField(max_length=9, default='2025-2026')
    director_name = models.CharField(max_length=120, blank=True)
    director_document = models.CharField(max_length=40, blank=True)
    rif = models.CharField(max_length=40, blank=True)
    dea_code = models.CharField(max_length=40, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    report_footer = models.TextField(blank=True)
    payment_reminder_days = models.PositiveSmallIntegerField(default=3)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuracion escolar'
        verbose_name_plural = 'Configuracion escolar'

    def __str__(self):
        return self.institution_name

    @classmethod
    def get_solo(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)
    model_name = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} - {self.model_name} #{self.object_id}'


def representative_invitation_token():
    return get_random_string(48)


class RepresentativeInvitation(models.Model):
    STATUS_PENDING = 'pendiente'
    STATUS_ACCEPTED = 'aceptada'
    STATUS_EXPIRED = 'expirada'
    STATUS_CANCELLED = 'cancelada'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_ACCEPTED, 'Aceptada'),
        (STATUS_EXPIRED, 'Expirada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    parent = models.ForeignKey('estudiante.Parent', on_delete=models.CASCADE, related_name='portal_invitations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='representative_invitations')
    email = models.EmailField()
    token = models.CharField(max_length=64, default=representative_invitation_token, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='representative_invitations_created')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Invitacion {self.email} - {self.get_status_display()}'

    @property
    def is_valid(self):
        return self.status == self.STATUS_PENDING and timezone.now() <= self.expires_at

    def mark_expired_if_needed(self):
        if self.status == self.STATUS_PENDING and timezone.now() > self.expires_at:
            self.status = self.STATUS_EXPIRED
            self.save(update_fields=['status'])

class Class(models.Model):
    class_id = models.CharField(max_length=10, unique=True)
    section = models.CharField(max_length=5)
    academic_year = models.DateField()
    department = models.CharField(max_length=100, null=True, blank=True)
    teachers = models.ManyToManyField(to='profesor.Teacher', blank=True)

    class Meta:
        # ensure no duplicate classes for same section and academic year
        unique_together = ['class_id', 'section', 'academic_year'] # Composite business key
        ordering = ['academic_year', 'class_id', 'section']

    def __str__(self):
        return f"{self.class_id} - {self.section} ({self.academic_year.year})"
    

class ClassTeacherAssignment(models.Model):
    class_assigned = models.ForeignKey(to='Class', on_delete=models.CASCADE)
    teacher = models.ForeignKey(to='profesor.Teacher', on_delete=models.CASCADE)
    subject = models.ForeignKey(to='materia.Subject', on_delete=models.CASCADE)

    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)   # to mark current assignments

    class Meta:
        unique_together = ['class_assigned', 'teacher', 'subject']  # prevent duplicate assignments
        ordering = ['class_assigned', 'teacher', 'subject']
        verbose_name = 'Class Teacher Assignment'   # for better readability in admin
        verbose_name_plural = 'Class Teacher Assignments'

    def __str__(self):
        return f"{self.teacher.name} teaches {self.subject.name} in {self.class_assigned.class_id}-{self.class_assigned.section}"
