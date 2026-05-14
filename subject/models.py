from django.db import models

# Create your models here.

class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    class_level = models.ManyToManyField(to='school.Class', blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

