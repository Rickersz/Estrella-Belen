from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date
import uuid


# Create your models here.

class Parent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='representante')
    father_name = models.CharField(max_length=100)
    father_mobile = models.CharField(max_length=100)
    father_email = models.EmailField(max_length=100, blank=True, null=True)

    mother_name = models.CharField(max_length=100)
    mother_mobile = models.CharField(max_length=100)
    mother_email = models.EmailField(max_length=100, blank=True, null=True)

    # extras del HTML (se agregan sin cambiar nombres)
    cedula_padre = models.CharField(max_length=20, blank=True, null=True)
    fechan_padre = models.DateField(blank=True, null=True)
    trabaja_padre = models.CharField(max_length=10, blank=True, null=True)
    lugar_trabajo_padre = models.CharField(max_length=150, blank=True, null=True)

    fechan_madre = models.DateField(blank=True, null=True)
    trabaja_madre = models.CharField(max_length=10, blank=True, null=True)
    lugar_trabajo_madre = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f'{self.father_name} & {self.mother_name}'
    
class Student(models.Model):
    # IDENTIDAD 
    student_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_class = models.CharField(max_length=15)
    tiene_cedula = models.BooleanField(default=False)
    cedula = models.CharField(max_length=20, null=True, blank=True)
    nacionalidad = models.CharField(max_length=50, blank=True, null=True)
    estado_natal = models.CharField(max_length=50, blank=True, null=True)
    edad = models.CharField(max_length=10, blank=True, null=True)
    etnia = models.CharField(max_length=50, blank=True, null=True)
    pais_extranjero = models.CharField(max_length=50, blank=True, null=True)
    direccion_completa = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)

    # ACADEMICO
    etapa = models.CharField(max_length=20, null=True, blank=True)
    grado = models.CharField(max_length=20, null=True, blank=True)
    section = models.CharField(max_length=15)
    admission_number = models.CharField(max_length=15)
    joining_date = models.DateField()

    # PERSONAL
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Masculino'), ('Female', 'Femenino'), ('Others', 'Otro')]
    )

    date_of_birth = models.DateField()

    # TALLAS
    pantalon = models.CharField(max_length=20, blank=True, null=True)
    camisa = models.CharField(max_length=20, blank=True, null=True)
    calzado = models.CharField(max_length=20, blank=True, null=True)
    peso = models.CharField(max_length=10, blank=True, null=True)
    estatura = models.CharField(max_length=10, blank=True, null=True)
    transporte = models.CharField(max_length=100, blank=True, null=True)

    vive_con_padres = models.CharField(max_length=5, blank=True, null=True)
    huerfano = models.CharField(max_length=5, blank=True, null=True)

    # SALUD
    discapacidad = models.CharField(max_length=5, blank=True, null=True)
    condicion = models.CharField(max_length=100, blank=True, null=True)
    area_condicion = models.CharField(max_length=100, blank=True, null=True)
    tipo_discapacidad = models.CharField(max_length=100, blank=True, null=True)

    carnet_discapacidad = models.CharField(max_length=5, blank=True, null=True)
    informe_medico = models.CharField(max_length=5, blank=True, null=True)
    recibe_tratamiento = models.CharField(max_length=5, blank=True, null=True)
    cual_tratamiento = models.CharField(max_length=100, blank=True, null=True)

    # ESCOLARIDAD
    plantel_anterior = models.CharField(max_length=150, blank=True, null=True)
    repitiente = models.CharField(max_length=5, blank=True, null=True)
    aula_integrada = models.CharField(max_length=100, blank=True, null=True)
    cargado_sge = models.CharField(max_length=5, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, null=True, blank=True)
    student_image = models.ImageField(upload_to='students/', null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    
    @property
    def grado_completo(self):
        return f"{self.etapa} / {self.grado} - {self.section}"

    @property
    def edad_actual(self):
        birth_date = self.date_of_birth
        if isinstance(birth_date, str):
            birth_date = parse_date(birth_date)
        if not birth_date:
            return 0
        today = timezone.localdate()
        years = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            years -= 1
        return max(years, 0)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.student_id}"
    

    def save(self, *args, **kwargs):

        if not self.slug:
            base = f"{self.first_name}-{self.last_name}-{self.student_id}"
            base = base.lower().replace(" ", "-")
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        if self.date_of_birth:
            self.edad = str(self.edad_actual)

        super().save(*args, **kwargs)
    
class Enrollment(models.Model):
    STATUS_ACTIVE = 'activo'
    STATUS_PROMOTED = 'promovido'
    STATUS_REPEATING = 'repite'
    STATUS_WITHDRAWN = 'retirado'
    STATUS_GRADUATED = 'egresado'
    STATUS_CLOSED = 'cerrado'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activo'),
        (STATUS_PROMOTED, 'Promovido'),
        (STATUS_REPEATING, 'Repite'),
        (STATUS_WITHDRAWN, 'Retirado'),
        (STATUS_GRADUATED, 'Egresado'),
        (STATUS_CLOSED, 'Cerrado'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)  # 2025-2026
    etapa = models.CharField(max_length=20)
    grado = models.CharField(max_length=20)
    section = models.CharField(max_length=5)
    monto_inscripcion = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    result_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    next_academic_year = models.CharField(max_length=9, blank=True)
    observations = models.TextField(blank=True)

    status = models.CharField(max_length=20, default=STATUS_ACTIVE)
    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-academic_year', 'student__last_name']
        unique_together = ['student', 'academic_year']

    def __str__(self):
        return f'{self.student} - {self.academic_year} - {self.grado} {self.section}'


class GradeSectionCapacity(models.Model):
    academic_year = models.CharField(max_length=9)
    etapa = models.CharField(max_length=20)
    grado = models.CharField(max_length=20)
    section = models.CharField(max_length=15)
    capacity = models.PositiveSmallIntegerField(default=30)

    class Meta:
        ordering = ['academic_year', 'etapa', 'grado', 'section']
        unique_together = ['academic_year', 'etapa', 'grado', 'section']

    @property
    def enrolled_count(self):
        return Enrollment.objects.filter(
            academic_year=self.academic_year,
            etapa=self.etapa,
            grado=self.grado,
            section=self.section,
            result_status=Enrollment.STATUS_ACTIVE,
        ).count()

    @property
    def available_slots(self):
        return max(self.capacity - self.enrolled_count, 0)

    def __str__(self):
        return f'{self.grado} {self.section} ({self.academic_year})'


class StudentDocumentChecklist(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='documents')
    birth_certificate = models.BooleanField(default=False)
    identity_card_copy = models.BooleanField(default=False)
    representative_id_copy = models.BooleanField(default=False)
    student_photos = models.BooleanField(default=False)
    previous_school_certificate = models.BooleanField(default=False)
    vaccination_card = models.BooleanField(default=False)
    medical_report = models.BooleanField(default=False)
    authorizations = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Documentos - {self.student}'


class StudentHealthRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='health_record')
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=40, blank=True)
    medical_insurance = models.CharField(max_length=120, blank=True)
    special_condition = models.TextField(blank=True)
    important_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Ficha medica - {self.student}'


class AttendanceRecord(models.Model):
    STATUS_PRESENT = 'presente'
    STATUS_ABSENT = 'ausente'
    STATUS_LATE = 'retardo'
    STATUS_JUSTIFIED = 'justificado'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Presente'),
        (STATUS_ABSENT, 'Ausente'),
        (STATUS_LATE, 'Retardo'),
        (STATUS_JUSTIFIED, 'Justificado'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.localdate)
    academic_year = models.CharField(max_length=9)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'student__last_name']
        unique_together = ['student', 'date']

    def __str__(self):
        return f'{self.student} - {self.date} - {self.get_status_display()}'
