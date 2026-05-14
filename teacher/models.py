from django.db import models

# Create your models here.


class Teacher(models.Model):
    teacher_id = models.CharField(max_length=20)
    name = models.CharField(max_length=50)    
    gender = models.CharField(max_length=10, choices= [('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')])
    date_of_birth = models.DateField()
    joining_date = models.DateField()
    mobile_number = models.CharField(max_length=10)
    qualification = models.CharField(max_length=100)
    experience = models.CharField(max_length=100)
    teacher_image = models.ImageField(upload_to='teacher_images/', null=True, blank=True)

    # login credentials
    email = models.EmailField(max_length=100, unique=True)   

    # Address fields
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)

    department = models.ForeignKey(to='department.Department', on_delete=models.SET_NULL, null=True, blank=True)
    subjects = models.ManyToManyField(to='subject.Subject', blank=True)

    def __str__(self):
        return f"{self.teacher_id} - {self.name}"

