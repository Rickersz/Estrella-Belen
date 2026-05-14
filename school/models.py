from django.db import models
from django.conf import settings
import uuid
# Create your models here.

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{ ' '.join([self.user.first_name, self.user.last_name]) if (self.user.first_name or self.user.last_name) else 'Unknown'}: {self.message}"

class Class(models.Model):
    class_id = models.CharField(max_length=10, unique=True)
    section = models.CharField(max_length=5)
    academic_year = models.DateField()

    department = models.ForeignKey(to='department.Department', on_delete=models.SET_NULL, null=True, blank=True)
    teachers = models.ManyToManyField(to='teacher.Teacher', blank=True)

    class Meta:
        # ensure no duplicate classes for same section and academic year
        unique_together = ['class_id', 'section', 'academic_year'] # Composite business key
        ordering = ['academic_year', 'class_id', 'section']

    def __str__(self):
        return f"{self.class_id} - {self.section} ({self.academic_year.year})"
    

class ClassTeacherAssignment(models.Model):
    class_assigned = models.ForeignKey(to='Class', on_delete=models.CASCADE)
    teacher = models.ForeignKey(to='teacher.Teacher', on_delete=models.CASCADE)
    subject = models.ForeignKey(to='subject.Subject', on_delete=models.CASCADE)

    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)   # to mark current assignments

    class Meta:
        unique_together = ['class_assigned', 'teacher', 'subject']  # prevent duplicate assignments
        ordering = ['class_assigned', 'teacher', 'subject']
        verbose_name = 'Class Teacher Assignment'   # for better readability in admin
        verbose_name_plural = 'Class Teacher Assignments'

    def __str__(self):
        return f"{self.teacher.name} teaches {self.subject.name} in {self.class_assigned.class_id}-{self.class_assigned.section}"