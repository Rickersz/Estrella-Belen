from django.db import models
import uuid


# Create your models here.

class Parent(models.Model):
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
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')]
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
    
    @property
    def grado_completo(self):
        return f"{self.etapa} / {self.grado} - {self.section}"
    

    def save(self, *args, **kwargs):

        if not self.slug:
            base = f"{self.first_name}-{self.last_name}-{self.student_id}"
            base = base.lower().replace(" ", "-")
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"

        super().save(*args, **kwargs)
    
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)  # 2025-2026
    etapa = models.CharField(max_length=20)
    grado = models.CharField(max_length=20)
    section = models.CharField(max_length=5)
    monto_inscripcion = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, default="Active")
    date_enrolled = models.DateTimeField(auto_now_add=True)
