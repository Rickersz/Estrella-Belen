from django.test import TestCase

from .forms import TeacherForm
from .models import Teacher


class TeacherFormTests(TestCase):
    def test_rechaza_correo_duplicado(self):
        Teacher.objects.create(
            teacher_id='P-001', name='María Pérez', gender='Female', date_of_birth='1990-01-01',
            joining_date='2024-01-01', mobile_number='04140000000', qualification='Licenciada',
            experience='5 años', email='profesor@test.com', address='Dirección', city='Ciudad',
            state='Estado', country='País', zip_code='0000'
        )
        form = TeacherForm(data={
            'teacher_id': 'P-002', 'name': 'Juan Pérez', 'gender': 'Male',
            'date_of_birth': '1991-01-01', 'joining_date': '2024-01-01',
            'mobile_number': '04141111111', 'qualification': 'Licenciado', 'experience': '3 años',
            'email': 'profesor@test.com', 'address': 'Dirección', 'city': 'Ciudad',
            'state': 'Estado', 'country': 'País', 'zip_code': '0000'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
