from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from autenticacion.models import CustomUser
from estudiante.models import Parent, Student
from materia.models import Subject
from .models import AcademicGrade


class AcademicAccessTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(email='admin-acad@test.com', password='ClaveSegura123', is_admin=True)
        self.rep_user = CustomUser.objects.create_user(email='rep-acad@test.com', password='ClaveSegura123', is_representative=True)
        self.parent = Parent.objects.create(
            user=self.rep_user,
            father_name='Padre', father_mobile='04140000000',
            mother_name='Madre', mother_mobile='04140000001',
        )
        self.student = Student.objects.create(
            student_id='AC-001', first_name='Ana', last_name='Perez', student_class='1',
            section='A', admission_number='A1', joining_date='2025-01-01',
            gender='Female', date_of_birth='2018-01-01', parent=self.parent,
        )
        self.subject = Subject.objects.create(code='MAT-A', name='Matematica')
        self.grade = AcademicGrade.objects.create(
            student=self.student,
            subject=self.subject,
            academic_year='2025-2026',
            period='1',
            grade=Decimal('18.00'),
        )

    def test_representante_ve_su_historial(self):
        self.client.force_login(self.rep_user)
        response = self.client.get(reverse('academic_history_student', args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)

    def test_boletin_pdf_responde(self):
        self.client.force_login(self.rep_user)
        response = self.client.get(reverse('report_card_pdf', args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_exportar_excel_responde(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('export_grades_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])
