from django.db import models
from django.conf import settings


class Constancia(models.Model):
	title = models.CharField(max_length=150)
	student = models.ForeignKey('estudiante.Student', on_delete=models.CASCADE)
	issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	date_issued = models.DateField(auto_now_add=True)
	reason = models.TextField(blank=True)
	notes = models.TextField(blank=True)

	def __str__(self):
		return f"{self.title} - {self.student.first_name} {self.student.last_name}"

	class Meta:
		ordering = ['-date_issued']
