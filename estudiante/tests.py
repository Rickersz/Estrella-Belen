from django.test import TestCase
from django.urls import reverse

from autenticacion.models import CustomUser
from .forms import EnrollmentForm, StudentForm
from .models import Student


class StudentFormTests(TestCase):
    def test_rechaza_cedula_escolar_duplicada(self):
        Student.objects.create(
            student_id='CE-001', first_name='Ana', last_name='Pérez', student_class='1',
            section='A', admission_number='ADM1', joining_date='2025-01-01',
            gender='Female', date_of_birth='2018-01-01'
        )
        form = StudentForm(data={
            'student_id': 'CE-001', 'first_name': 'Luis', 'last_name': 'Gómez',
            'student_class': '1', 'section': 'A', 'admission_number': 'ADM2',
            'joining_date': '2025-01-01', 'gender': 'Male', 'date_of_birth': '2018-01-01',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('student_id', form.errors)

    def test_rechaza_monto_negativo(self):
        form = EnrollmentForm(data={'monto_inscripcion': '-1'})
        self.assertFalse(form.is_valid())
        self.assertIn('monto_inscripcion', form.errors)


class StudentPermissionTests(TestCase):
    def test_usuario_estudiante_no_puede_inscribir(self):
        user = CustomUser.objects.create_user(email='estudiante@test.com', password='ClaveSegura123', is_student=True)
        self.client.force_login(user)
        response = self.client.get(reverse('add_student'))
        self.assertEqual(response.status_code, 302)
