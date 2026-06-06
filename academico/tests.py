from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from autenticacion.models import CustomUser
from escuela.models import Class, ClassTeacherAssignment
from estudiante.models import Parent, Student
from materia.models import Subject
from profesor.models import Teacher
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

    def test_profesor_no_carga_nota_fuera_de_sus_secciones(self):
        teacher_user = CustomUser.objects.create_user(email='teacher-acad@test.com', password='ClaveSegura123', is_teacher=True)
        teacher = Teacher.objects.create(
            teacher_id='T-AC-1',
            name='Profesor A',
            gender='Male',
            date_of_birth='1990-01-01',
            joining_date='2025-01-01',
            mobile_number='0414000002',
            qualification='Docente',
            experience='5',
            email=teacher_user.email,
            address='Direccion',
            city='Ciudad',
            state='Estado',
            country='VE',
            zip_code='0000',
        )
        class_a = Class.objects.create(class_id='1RO', section='A', academic_year='2025-01-01')
        ClassTeacherAssignment.objects.create(class_assigned=class_a, teacher=teacher, subject=self.subject)
        other_student = Student.objects.create(
            student_id='AC-002', first_name='Luis', last_name='Gomez', student_class='1',
            section='B', admission_number='A2', joining_date='2025-01-01',
            gender='Male', date_of_birth='2018-01-01',
        )

        self.client.force_login(teacher_user)
        response = self.client.post(reverse('grade_create'), {
            'student': other_student.pk,
            'subject': self.subject.pk,
            'teacher': teacher.pk,
            'academic_year': '2025-2026',
            'period': '2',
            'grade': '19',
            'weight': '100',
            'qualitative': '',
            'notes': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(AcademicGrade.objects.filter(student=other_student, period='2').exists())
