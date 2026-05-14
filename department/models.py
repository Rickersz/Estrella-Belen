from django.db import models

# Create your models here.

class Department(models.Model):
    # id : surrogate primary key (default by Django) used for internal relations
    department_id = models.CharField(max_length=10, unique=True)    # business key
    name = models.CharField(max_length=100)
    hod = models.CharField(max_length=100)  # Head of Department
    start_date = models.DateField()
    no_of_students = models.IntegerField()

    def __str__(self):
        return f"{self.department_id} - {self.name}"