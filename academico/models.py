from django.conf import settings
from django.db import models
from escuela.models import active_academic_year_default


class AcademicGrade(models.Model):
    PERIOD_CHOICES = [
        ('1', 'Primer lapso'),
        ('2', 'Segundo lapso'),
        ('3', 'Tercer lapso'),
        ('final', 'Final'),
    ]

    student = models.ForeignKey('estudiante.Student', on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey('materia.Subject', on_delete=models.CASCADE, related_name='grades')
    teacher = models.ForeignKey('profesor.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='grades')
    academic_year = models.CharField(max_length=9, default=active_academic_year_default)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    grade = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    qualitative = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    is_locked = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__last_name', 'subject__name', 'period']
        unique_together = ['student', 'subject', 'academic_year', 'period']

    def __str__(self):
        return f'{self.student} - {self.subject} - {self.grade}'


class ClassSchedule(models.Model):
    DAY_CHOICES = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miercoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sabado'),
    ]

    class_assigned = models.ForeignKey('escuela.Class', on_delete=models.CASCADE, related_name='schedule_items')
    subject = models.ForeignKey('materia.Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('profesor.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    classroom = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f'{self.get_day_display()} {self.start_time} - {self.subject}'


class SchoolEvent(models.Model):
    EVENT_CLASSES = [
        ('academico', 'Academico'),
        ('administrativo', 'Administrativo'),
        ('feriado', 'Feriado'),
        ('actividad', 'Actividad'),
    ]

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_CLASSES, default='academico')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    audience = models.CharField(max_length=120, default='Toda la comunidad')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.title


class DisciplineObservation(models.Model):
    SEVERITY_CHOICES = [
        ('leve', 'Leve'),
        ('media', 'Media'),
        ('grave', 'Grave'),
    ]

    student = models.ForeignKey('estudiante.Student', on_delete=models.CASCADE, related_name='discipline_observations')
    teacher = models.ForeignKey('profesor.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='leve')
    description = models.TextField()
    action_taken = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.student} - {self.get_severity_display()}'


class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ('todos', 'Todos'),
        ('administradores', 'Administradores'),
        ('profesores', 'Profesores'),
        ('representantes', 'Representantes'),
    ]

    title = models.CharField(max_length=160)
    body = models.TextField()
    audience = models.CharField(max_length=30, choices=AUDIENCE_CHOICES, default='todos')
    send_email = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class CommunicationMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_academic_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_academic_messages')
    subject = models.CharField(max_length=160)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject


class WhatsAppMessageLog(models.Model):
    recipient = models.CharField(max_length=30)
    message = models.TextField()
    status = models.CharField(max_length=40, default='pendiente')
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient} - {self.status}'
