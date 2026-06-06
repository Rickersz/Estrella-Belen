from django.test import TestCase
from django.urls import reverse

from autenticacion.models import CustomUser
from .forms import TeacherForm
from .models import Teacher


class TeacherFormTests(TestCase):
    def test_rechaza_correo_duplicado(self):
        Teacher.objects.create(
            teacher_id='P-001', name='Maria Perez', gender='Female', date_of_birth='1990-01-01',
            joining_date='2024-01-01', mobile_number='04140000000', qualification='Licenciada',
            experience='5 anos', email='profesor@test.com', address='Direccion', city='Ciudad',
            state='Estado', country='Pais', zip_code='0000'
        )
        form = TeacherForm(data={
            'teacher_id': 'P-002', 'name': 'Juan Perez', 'gender': 'Male',
            'date_of_birth': '1991-01-01', 'joining_date': '2024-01-01',
            'mobile_number': '04141111111', 'qualification': 'Licenciado', 'experience': '3 anos',
            'email': 'profesor@test.com', 'address': 'Direccion', 'city': 'Ciudad',
            'state': 'Estado', 'country': 'Pais', 'zip_code': '0000'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class TeacherArchiveTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(email='admin-prof@test.com', password='ClaveSegura123', is_admin=True)
        self.teacher = Teacher.objects.create(
            teacher_id='P-900', name='Profesor Archivo', gender='Male', date_of_birth='1990-01-01',
            joining_date='2024-01-01', mobile_number='04140000000', qualification='Licenciado',
            experience='5', email='prof-archivo@test.com', address='Direccion', city='Ciudad',
            state='Estado', country='Pais', zip_code='0000'
        )

    def test_delete_teacher_archiva_en_lugar_de_borrar(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('delete_teacher', args=[self.teacher.teacher_id]))
        self.teacher.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.teacher.is_archived)
        self.assertTrue(Teacher.objects.filter(pk=self.teacher.pk).exists())

    def test_restore_teacher_reactiva_archivado(self):
        self.teacher.is_archived = True
        self.teacher.save(update_fields=['is_archived'])
        self.client.force_login(self.admin)

        response = self.client.post(reverse('restore_teacher', args=[self.teacher.teacher_id]))
        self.teacher.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.teacher.is_archived)
