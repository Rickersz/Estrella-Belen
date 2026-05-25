from django.db import models
from django.conf import settings


class Constancia(models.Model):
	TIPO_INSCRIPCION = 'inscripcion'
	TIPO_SOLVENCIA = 'solvencia'
	TIPO_ESTUDIO = 'estudio'
	TIPO_COMPORTAMIENTO = 'comportamiento'

	TIPO_CHOICES = [
		(TIPO_INSCRIPCION, 'Constancia de Inscripcion'),
		(TIPO_SOLVENCIA, 'Solvencia'),
		(TIPO_ESTUDIO, 'Constancia de Estudio'),
		(TIPO_COMPORTAMIENTO, 'Certificado de Comportamiento'),
	]

	COMPORTAMIENTO_CHOICES = [
		('Excelente', 'Excelente'),
		('Distinguido', 'Distinguido'),
		('Suficiente', 'Suficiente'),
	]

	title = models.CharField(max_length=150)
	report_type = models.CharField(max_length=30, choices=TIPO_CHOICES, default=TIPO_INSCRIPCION)
	student = models.ForeignKey('estudiante.Student', on_delete=models.CASCADE)
	issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	date_issued = models.DateField(auto_now_add=True)
	academic_year = models.CharField(max_length=9, default='2025-2026')
	representative_name = models.CharField(max_length=150, blank=True)
	representative_id = models.CharField(max_length=30, blank=True)
	amount_paid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	solvent_until = models.CharField(max_length=80, blank=True)
	behavior_rating = models.CharField(max_length=30, choices=COMPORTAMIENTO_CHOICES, blank=True)
	reason = models.TextField(blank=True)
	notes = models.TextField(blank=True)

	def __str__(self):
		return f"{self.title} - {self.student.first_name} {self.student.last_name}"

	def save(self, *args, **kwargs):
		if not self.title:
			self.title = dict(self.TIPO_CHOICES).get(self.report_type, 'Constancia')
		super().save(*args, **kwargs)

	class Meta:
		ordering = ['-date_issued']
